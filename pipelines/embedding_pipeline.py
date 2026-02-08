"""Embedding pipeline: ChunkDocument storage → batch embed → vector store + audit log.

Reads chunk JSON files, filters by idempotency (has_id), batches embed, writes
vectors and EmbeddingRecord JSONL. No retrieval or RAG logic.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from schemas.chunk_document import ChunkDocument
from schemas.embedding_record import EmbeddingRecord

from embeddings.base import BaseEmbedder
from vector_store.base import BaseVectorStore

logger = logging.getLogger(__name__)

DEFAULT_CHUNKS_DIR = "data/chunks"
DEFAULT_AUDIT_LOG_PATH = "data/embeddings/records.jsonl"


class EmbeddingPipeline:
    """
    Pipeline: load chunk JSON → filter by has_id → batch embed → add to vector store
    → append EmbeddingRecord audit log. Idempotent per chunk.
    """

    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore,
        batch_size: int = 32,
        audit_log_path: str = DEFAULT_AUDIT_LOG_PATH,
        chunks_dir: str = DEFAULT_CHUNKS_DIR,
    ) -> None:
        """
        Initialize the embedding pipeline.

        Args:
            embedder: Embedder used to produce vectors from text.
            vector_store: Store for vectors and metadata (idempotency via has_id).
            batch_size: Max texts per embed_texts call.
            audit_log_path: Path to JSONL file for EmbeddingRecord rows.
            chunks_dir: Directory containing <doc_id>.json chunk files.
        """
        self._embedder = embedder
        self._vector_store = vector_store
        self._batch_size = max(1, batch_size)
        self._audit_log_path = audit_log_path
        self._chunks_dir = Path(chunks_dir)

    def load_chunks(self, doc_id: str) -> list[ChunkDocument]:
        """
        Read and parse chunk JSON for a document.

        Args:
            doc_id: Document id; file read from chunks_dir / f"{doc_id}.json".

        Returns:
            List of ChunkDocument instances.

        Raises:
            FileNotFoundError: If the chunk file does not exist.
            ValueError: If JSON is invalid or does not match ChunkDocument schema.
        """
        path = self._chunks_dir / f"{doc_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Chunk file not found: {path}")

        with open(path, encoding="utf-8") as f:
            raw = json.load(f)

        if not isinstance(raw, list):
            raise ValueError(f"Expected JSON array in {path}, got {type(raw).__name__}")

        chunks: list[ChunkDocument] = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                raise ValueError(f"Expected object at index {i} in {path}")
            chunks.append(ChunkDocument.model_validate(item))
        return chunks

    def build_metadata(self, chunk: ChunkDocument) -> dict[str, Any]:
        """
        Build metadata dict for vector store and audit (contract fields).

        Includes: chunk_id, doc_id, source_uri, page_number, section_title,
        chunk_strategy, token_count. Values are store-safe (str, int).
        """
        return {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "source_uri": chunk.source_uri,
            "page_number": chunk.page_number if chunk.page_number is not None else 0,
            "section_title": chunk.section_title if chunk.section_title is not None else "",
            "chunk_strategy": chunk.chunk_strategy,
            "token_count": chunk.token_count if chunk.token_count is not None else 0,
        }

    def run_for_doc(self, doc_id: str) -> dict[str, int]:
        """
        Run embedding pipeline for one document: load, filter, batch embed, store, audit.

        Idempotent: skips chunks already present in vector store (has_id).

        Args:
            doc_id: Document id (chunk file: chunks_dir / f"{doc_id}.json").

        Returns:
            Summary dict: {"embedded": int, "skipped": int, "errors": int}.
        """
        summary: dict[str, int] = {"embedded": 0, "skipped": 0, "errors": 0}

        try:
            chunks = self.load_chunks(doc_id)
        except (FileNotFoundError, ValueError) as e:
            logger.exception("load_chunks failed for doc_id=%s: %s", doc_id, e)
            summary["errors"] += 1
            return summary

        # Idempotency: only embed chunks not already in the store
        to_embed: list[ChunkDocument] = []
        for chunk in chunks:
            if self._vector_store.has_id(chunk.chunk_id):
                summary["skipped"] += 1
            else:
                to_embed.append(chunk)

        if not to_embed:
            return summary

        # Batch by batch_size
        audit_log_path = Path(self._audit_log_path)
        audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        model_name = self._embedder.__class__.__name__
        vector_dim = self._embedder.vector_dim

        for start in range(0, len(to_embed), self._batch_size):
            batch = to_embed[start : start + self._batch_size]
            ids_batch = [c.chunk_id for c in batch]
            texts_batch = [c.text for c in batch]
            metadatas_batch = [self.build_metadata(c) for c in batch]

            # Embed (retry once on failure)
            vectors = None
            for attempt in range(2):
                try:
                    vectors = self._embedder.embed_texts(texts_batch)
                    break
                except Exception as e:
                    logger.warning(
                        "embed_texts failed for doc_id=%s batch start=%s (attempt %s): %s",
                        doc_id,
                        start,
                        attempt + 1,
                        e,
                        exc_info=attempt > 0,
                    )
            if vectors is None:
                summary["errors"] += len(batch)
                continue

            if len(vectors) != len(ids_batch):
                logger.warning(
                    "embedder returned %s vectors for %s texts, skipping batch",
                    len(vectors),
                    len(texts_batch),
                )
                summary["errors"] += len(batch)
                continue

            # Add to vector store
            try:
                self._vector_store.add_embeddings(
                    ids=ids_batch,
                    vectors=vectors,
                    metadatas=metadatas_batch,
                )
            except Exception as e:
                logger.warning(
                    "vector_store.add_embeddings failed for doc_id=%s batch: %s",
                    doc_id,
                    e,
                    exc_info=True,
                )
                summary["errors"] += len(batch)
                continue

            # Append audit log (one EmbeddingRecord per chunk in batch)
            now = datetime.now(timezone.utc)
            try:
                with open(audit_log_path, "a", encoding="utf-8") as f:
                    for i, chunk in enumerate(batch):
                        rec = EmbeddingRecord(
                            embedding_id=chunk.chunk_id,
                            chunk_id=chunk.chunk_id,
                            doc_id=chunk.doc_id,
                            model_name=model_name,
                            vector_dim=vector_dim,
                            created_at=now,
                            metadata=self.build_metadata(chunk),
                        )
                        f.write(rec.model_dump_json() + "\n")
            except Exception as e:
                logger.warning(
                    "audit log append failed for doc_id=%s batch: %s",
                    doc_id,
                    e,
                    exc_info=True,
                )
                # Count as embedded; log already written best-effort
            summary["embedded"] += len(batch)

        return summary

    def run_for_all(self) -> dict[str, int]:
        """
        Run pipeline for every doc_id found under chunks_dir (*.json).

        Returns:
            Aggregated summary: {"embedded": int, "skipped": int, "errors": int}.
        """
        total: dict[str, int] = {"embedded": 0, "skipped": 0, "errors": 0}
        if not self._chunks_dir.exists():
            logger.warning("Chunks dir does not exist: %s", self._chunks_dir)
            return total

        for path in sorted(self._chunks_dir.glob("*.json")):
            doc_id = path.stem
            summary = self.run_for_doc(doc_id)
            total["embedded"] += summary["embedded"]
            total["skipped"] += summary["skipped"]
            total["errors"] += summary["errors"]

        return total


def _main() -> None:
    """CLI: --doc-id X or --all. Uses embedder and vector store from env/config."""
    parser = argparse.ArgumentParser(
        description="Embedding pipeline: chunks → vector store + audit log."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--doc-id", type=str, help="Process single document by doc_id.")
    group.add_argument("--all", action="store_true", help="Process all docs in data/chunks.")
    parser.add_argument(
        "--chunks-dir",
        type=str,
        default=DEFAULT_CHUNKS_DIR,
        help="Directory containing <doc_id>.json chunk files.",
    )
    parser.add_argument(
        "--audit-log",
        type=str,
        default=DEFAULT_AUDIT_LOG_PATH,
        help="Path to EmbeddingRecord JSONL audit log.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Max texts per embed batch.",
    )
    parser.add_argument(
        "--vector-store-path",
        type=str,
        default="data/vector_store",
        help="Chroma persist directory.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable INFO logging.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    # Lazy imports so CLI works without heavy deps if only --help
    from embeddings.bge_m3_embedder import BgeM3Embedder
    from vector_store import ChromaVectorStore

    embedder = BgeM3Embedder(batch_size=args.batch_size)
    vector_store = ChromaVectorStore(persist_dir=args.vector_store_path)

    pipeline = EmbeddingPipeline(
        embedder=embedder,
        vector_store=vector_store,
        batch_size=args.batch_size,
        audit_log_path=args.audit_log,
        chunks_dir=args.chunks_dir,
    )

    if args.all:
        summary = pipeline.run_for_all()
        print(f"embedded={summary['embedded']} skipped={summary['skipped']} errors={summary['errors']}")
    else:
        assert args.doc_id is not None
        summary = pipeline.run_for_doc(args.doc_id)
        print(f"embedded={summary['embedded']} skipped={summary['skipped']} errors={summary['errors']}")


if __name__ == "__main__":
    _main()
