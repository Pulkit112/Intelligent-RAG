"""Ingestion orchestrator: connector -> document_builder -> extractor -> chunker -> persist -> sync state."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chunking.registry import get_chunker
from connectors.file_connector import FileConnector
from document_builders.file_document_builder import FileDocumentBuilder
from extractors.registry import get_extractor
from observability.logger import get_logger
from schemas.chunk_document import ChunkDocument
from schemas.parsed_unit import ParsedUnit
from schemas.source_document import SourceDocument
from storage.parsed_unit_store import persist_parsed_units
from storage.raw_store import RawStore
from state.sync_state import load_sync_state, update_sync_state
from state.unit_progress import load_unit_progress, update_unit_progress

CHUNKS_DIR = Path("data/chunks")
logger = get_logger("pipelines.ingestion_orchestrator")


def _persist_chunks(doc_id: str, chunks: list[ChunkDocument]) -> None:
    """Persist chunks to JSON under data/chunks/ (one file per doc_id)."""
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    path = CHUNKS_DIR / f"{doc_id}.json"
    data = [c.model_dump(mode="json") for c in chunks]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def run_ingestion(
    source_config: dict[str, Any],
    *,
    raw_store: RawStore | None = None,
    chunker_name: str = "recursive",
    skip_if_processed: bool = True,
    save_parsed_units: bool = False,
    use_unit_checkpoint: bool = True,
    preview: bool = False,
    before_extract: Callable[[SourceDocument], None] | None = None,
    after_extract: Callable[[ParsedUnit], None] | None = None,
    after_chunk: Callable[[ChunkDocument], None] | None = None,
) -> dict[str, Any]:
    """
    Run full ingestion: connector -> document_builder -> extract_stream -> chunk -> persist -> sync state.

    source_config: e.g. {"path": "/path/to/file.pdf"} for file.
    skip_if_processed: skip document when checksum already in sync state (restart-safe).
    save_parsed_units: if True, write ParsedUnits to data/parsed_units/<doc_id>.jsonl.
    use_unit_checkpoint: if True, resume at last_unit_index (restart-at-page-N).
    preview: if True, do not persist chunks or state; return chunks_by_doc and parsed_units_by_doc for inspection.
    before_extract(doc), after_extract(unit), after_chunk(chunk): optional hooks for metrics/tracing/eval.
    """
    store = raw_store if raw_store is not None else RawStore()
    connector = FileConnector(raw_store=store)
    doc_builder = FileDocumentBuilder()
    path = source_config.get("path")
    if not path:
        logger.warning("ingestion | source_config missing path")
        out = {"documents": 0, "chunks": 0, "skipped": 0, "errors": ["missing path"]}
        if preview:
            out["chunks_by_doc"] = []
            out["parsed_units_by_doc"] = []
        return out
    path = Path(path)
    if not path.exists():
        logger.warning("ingestion | path not found: %s", path)
        out = {"documents": 0, "chunks": 0, "skipped": 0, "errors": [f"path not found: {path}"]}
        if preview:
            out["chunks_by_doc"] = []
            out["parsed_units_by_doc"] = []
        return out
    records = list(connector.fetch(path))
    if not records:
        logger.info("ingestion | no records from path: %s", path)
        out = {"documents": 0, "chunks": 0, "skipped": 0, "errors": []}
        if preview:
            out["chunks_by_doc"] = []
            out["parsed_units_by_doc"] = []
        return out
    docs = doc_builder.build(records)
    total_chunks = 0
    skipped = 0
    chunks_by_doc_list: list[dict[str, Any]] = []
    parsed_units_by_doc_list: list[dict[str, Any]] = []
    sync_state = load_sync_state() if skip_if_processed and not preview else {}
    for doc in docs:
        if skip_if_processed and doc.checksum:
            rec = sync_state.get(doc.source_uri)
            if rec and rec.last_checksum == doc.checksum and rec.status == "processed":
                skipped += 1
                logger.info(
                    "ingestion | skip already processed doc_id=%s checksum=%s",
                    doc.doc_id,
                    (doc.checksum or "")[:16],
                )
                continue
        try:
            extractor = get_extractor(doc.content_type, raw_store=store)
        except KeyError:
            logger.warning("ingestion | no extractor for content_type=%s doc_id=%s", doc.content_type, doc.doc_id)
            continue
        if before_extract is not None:
            before_extract(doc)
        chunker = get_chunker(chunker_name)
        doc_chunks: list[ChunkDocument] = []
        doc_units: list[ParsedUnit] = []
        unit_progress = load_unit_progress() if use_unit_checkpoint and not preview else {}
        last_index = unit_progress.get(doc.doc_id)
        resume_after = (last_index.last_unit_index + 1) if last_index else 0
        for unit in extractor.extract_stream(doc):
            if use_unit_checkpoint and not preview and unit.unit_index < resume_after:
                continue
            if after_extract is not None:
                after_extract(unit)
            if save_parsed_units or preview:
                doc_units.append(unit)
            if unit.parse_status == "failed" and not unit.text:
                if use_unit_checkpoint and not preview:
                    update_unit_progress(doc.doc_id, unit.unit_index, doc.checksum)
                continue
            text = unit.text or ""
            if text.strip():
                for chunk in chunker.chunk(unit):
                    if after_chunk is not None:
                        after_chunk(chunk)
                    doc_chunks.append(chunk)
            if use_unit_checkpoint and not preview:
                update_unit_progress(doc.doc_id, unit.unit_index, doc.checksum)
        if preview:
            chunks_by_doc_list.append({
                "doc_id": doc.doc_id,
                "source_uri": doc.source_uri,
                "chunks": [c.model_dump(mode="json") for c in doc_chunks],
            })
            parsed_units_by_doc_list.append({
                "doc_id": doc.doc_id,
                "units": [u.model_dump(mode="json") for u in doc_units],
            })
        if not preview and save_parsed_units and doc_units:
            persist_parsed_units(doc.doc_id, doc_units)
        if doc_chunks:
            if not preview:
                _persist_chunks(doc.doc_id, doc_chunks)
                if doc.checksum:
                    update_sync_state(
                        doc.source_uri,
                        last_checksum=doc.checksum,
                        last_processed_at=datetime.now(timezone.utc),
                        status="processed",
                    )
            total_chunks += len(doc_chunks)
            logger.info(
                "ingestion | doc_id=%s source_uri=%s chunks=%d",
                doc.doc_id,
                doc.source_uri,
                len(doc_chunks),
            )
    result: dict[str, Any] = {
        "documents": len(docs),
        "chunks": total_chunks,
        "skipped": skipped,
        "errors": [],
    }
    if preview:
        result["chunks_by_doc"] = chunks_by_doc_list
        result["parsed_units_by_doc"] = parsed_units_by_doc_list
    return result


def main() -> None:
    """CLI entrypoint: python -m pipelines.ingestion_orchestrator --path <file>."""
    parser = argparse.ArgumentParser(description="Run ingestion on a file path.")
    parser.add_argument("--path", required=True, help="Path to file to ingest")
    parser.add_argument("--no-skip", action="store_true", help="Do not skip already processed (by checksum)")
    parser.add_argument("--save-parsed-units", action="store_true", help="Persist ParsedUnits to data/parsed_units/<doc_id>.jsonl")
    parser.add_argument("--no-unit-checkpoint", action="store_true", help="Disable unit-level checkpoint (restart-at-page-N)")
    parser.add_argument("--preview", action="store_true", help="Do not persist; return chunks_by_doc and parsed_units_by_doc for inspection")
    parser.add_argument("--preview-out", metavar="PATH", help="When using --preview, write chunks/units to this JSON file")
    args = parser.parse_args()
    result = run_ingestion(
        {"path": args.path},
        skip_if_processed=not args.no_skip,
        save_parsed_units=args.save_parsed_units,
        use_unit_checkpoint=not args.no_unit_checkpoint,
        preview=args.preview,
    )
    if args.preview and args.preview_out:
        out_path = Path(args.preview_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {"chunks_by_doc": result.get("chunks_by_doc", []), "parsed_units_by_doc": result.get("parsed_units_by_doc", [])},
                f,
                indent=2,
            )
        print(f"Preview written to {out_path}", file=sys.stderr)
    if args.preview and result.get("chunks_by_doc"):
        for entry in result["chunks_by_doc"]:
            doc_id = entry["doc_id"]
            chunks = entry["chunks"]
            first_preview = (chunks[0]["text"][:200] + "...") if chunks and len(chunks[0]["text"]) > 200 else (chunks[0]["text"] if chunks else "")
            print(f"Doc {doc_id}: {len(chunks)} chunks; first chunk preview: {first_preview!r}", file=sys.stderr)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
