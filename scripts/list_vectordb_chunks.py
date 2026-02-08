#!/usr/bin/env python3
"""List chunks stored in the vector DB (ids and metadata). No embeddings.

Usage:
  PYTHONPATH=. python scripts/list_vectordb_chunks.py
  PYTHONPATH=. python scripts/list_vectordb_chunks.py --limit 50
  PYTHONPATH=. python scripts/list_vectordb_chunks.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="List chunks in the vector DB (ids + metadata).")
    parser.add_argument("--limit", type=int, default=100, help="Max entries to show (default 100).")
    parser.add_argument("--vector-store-path", type=str, default="data/vector_store", help="Chroma persist directory.")
    parser.add_argument("--json", action="store_true", help="Output raw JSON (one dict per line).")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    from vector_store import ChromaVectorStore

    store = ChromaVectorStore(persist_dir=str(ROOT / args.vector_store_path))
    count = store.count()
    print(f"Total vectors: {count}", file=sys.stderr)
    if count == 0:
        return 0

    entries = store.list_chunks(limit=args.limit)
    if args.json:
        for e in entries:
            print(json.dumps(e, default=str))
    else:
        for i, e in enumerate(entries, 1):
            mid = e.get("metadata") or {}
            doc_id = mid.get("doc_id", "")
            source_uri = mid.get("source_uri", "")
            chunk_id = e.get("id", "")
            print(f"{i}. id={chunk_id} doc_id={doc_id} source_uri={source_uri[:60]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
