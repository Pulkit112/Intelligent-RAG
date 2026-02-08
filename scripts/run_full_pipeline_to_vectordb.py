#!/usr/bin/env python3
"""Run full pipeline to vector DB: ensure chunks exist, run embedding pipeline, verify.

Flow:
  1. If --path <file> given: run ingestion (connector → extract → chunk → persist).
  2. Else: ensure data/chunks has at least one doc (writes test chunk JSON if empty).
  3. Run embedding pipeline (--all).
  4. Verify vector store count and idempotency (second run skips).

Usage:
  PYTHONPATH=. python scripts/run_full_pipeline_to_vectordb.py
  PYTHONPATH=. python scripts/run_full_pipeline_to_vectordb.py --path /path/to/file.pdf
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent


def _ensure_test_chunks() -> str | None:
    """If data/chunks is empty, write one test doc (2 chunks). Returns doc_id or None."""
    chunks_dir = ROOT / "data" / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    existing = list(chunks_dir.glob("*.json"))
    if existing:
        return existing[0].stem

    doc_id = "full_pipeline_test"
    now = datetime.now(timezone.utc).isoformat()
    chunks = [
        {
            "chunk_id": "full_pipeline_test_c0",
            "doc_id": doc_id,
            "chunk_index": 0,
            "text": "This is the first chunk for the full pipeline test.",
            "start_char": None,
            "end_char": None,
            "chunk_strategy": "recursive",
            "token_count": 10,
            "page_number": 1,
            "section_title": "",
            "source_uri": "file:///test/doc.pdf",
            "metadata": {},
            "created_at": now,
        },
        {
            "chunk_id": "full_pipeline_test_c1",
            "doc_id": doc_id,
            "chunk_index": 1,
            "text": "This is the second chunk to verify embedding and vector store.",
            "start_char": None,
            "end_char": None,
            "chunk_strategy": "recursive",
            "token_count": 12,
            "page_number": 1,
            "section_title": "",
            "source_uri": "file:///test/doc.pdf",
            "metadata": {},
            "created_at": now,
        },
    ]
    path = chunks_dir / f"{doc_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"Created test chunks: {path}", file=sys.stderr)
    return doc_id


def _run_ingestion(path: str, *, no_skip: bool = False) -> bool:
    """Run ingestion orchestrator on path. Returns True on success.
    no_skip: if True, pass --no-skip so already-processed docs are re-ingested.
    """
    cmd = [
        sys.executable,
        "-m",
        "pipelines.ingestion_orchestrator",
        "--path",
        path,
    ]
    if no_skip:
        cmd.append("--no-skip")
    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return False
    # Ingestion prints JSON (possibly with leading/trailing log output)
    raw = result.stdout.strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start < 0 or end <= start:
        print("Ingestion did not output valid JSON", file=sys.stderr)
        return False
    out = json.loads(raw[start:end])
    if out.get("errors"):
        print("Ingestion errors:", out["errors"], file=sys.stderr)
    print(f"Ingestion: documents={out.get('documents', 0)} chunks={out.get('chunks', 0)} skipped={out.get('skipped', 0)}", file=sys.stderr)
    return out.get("chunks", 0) > 0


def _run_embedding_pipeline() -> dict:
    """Run embedding pipeline --all. Returns summary dict."""
    cmd = [
        sys.executable,
        "-m",
        "pipelines.embedding_pipeline",
        "--all",
        "-v",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT)},
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        return {"embedded": -1, "skipped": 0, "errors": 1}
    # Last line is "embedded=N skipped=M errors=E"
    line = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    summary = {"embedded": 0, "skipped": 0, "errors": 0}
    for part in line.split():
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                summary[k] = int(v)
            except ValueError:
                pass
    return summary


def _verify_vector_store() -> tuple[int, bool]:
    """Check vector store count and idempotency (run embed again, expect skips). Returns (count, idempotency_ok)."""
    sys.path.insert(0, str(ROOT))
    from vector_store import ChromaVectorStore

    store = ChromaVectorStore(persist_dir=str(ROOT / "data" / "vector_store"))
    count = store.count()
    if count == 0:
        return 0, False

    # Second run: should skip all
    summary2 = _run_embedding_pipeline()
    idempotency_ok = summary2.get("embedded", -1) == 0 and summary2.get("skipped", 0) >= 1
    return count, idempotency_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full pipeline to vector DB and verify.")
    parser.add_argument("--path", type=str, help="Optional: path to file to ingest (e.g. PDF) before embedding.")
    parser.add_argument("--no-skip", action="store_true", help="Re-ingest even if file was already processed (ignore sync state).")
    args = parser.parse_args()

    if args.path:
        path = Path(args.path)
        if not path.exists():
            print(f"Path not found: {path}", file=sys.stderr)
            return 1
        print("Running ingestion...", file=sys.stderr)
        if not _run_ingestion(str(path.resolve()), no_skip=args.no_skip):
            print("Ingestion produced no chunks or failed.", file=sys.stderr)
            # Fall back to test chunks
            _ensure_test_chunks()
    else:
        doc_id = _ensure_test_chunks()
        if not doc_id:
            print("No chunk files in data/chunks and no --path provided.", file=sys.stderr)
            return 1

    print("Running embedding pipeline (--all)...", file=sys.stderr)
    summary = _run_embedding_pipeline()
    if summary.get("errors", 0) > 0 and summary.get("embedded", 0) == 0:
        print("Embedding pipeline failed.", file=sys.stderr)
        return 1

    print("Verifying vector store...", file=sys.stderr)
    count, idempotency_ok = _verify_vector_store()
    print(f"Vector store count: {count}", file=sys.stderr)
    print(f"Idempotency (second run skips): {idempotency_ok}", file=sys.stderr)

    if count > 0:
        print("OK: Full pipeline till vector DB is working.", file=sys.stderr)
        return 0
    print("FAIL: Vector store has no vectors.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
