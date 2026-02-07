"""RAG business orchestration. API calls this; it delegates to rag/ and pipelines/. No logic in API."""

from __future__ import annotations

from typing import Any


class RAGService:
    """Orchestrates retrieval, prompt build, and generation. Thin layer over rag/ components."""

    def __init__(self) -> None:
        """Initialize with retriever, prompt builder, generator (injected later)."""
        pass

    def query(self, question: str, *, top_k: int = 5) -> dict[str, Any]:
        """Run RAG: retrieve, build prompt, generate answer with citations. Stub for now."""
        return {
            "answer": "",
            "citations": [],
            "confidence": 0.0,
        }

    def ingest(self, paths: list[str], *, batch: bool = True) -> dict[str, Any]:
        """Trigger ingestion for given paths. Delegates to pipelines/. Stub for now."""
        return {"ingested": 0, "errors": []}
