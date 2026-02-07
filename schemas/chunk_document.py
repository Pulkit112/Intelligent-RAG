"""Chunk document schema — chunker output (atomic retrieval and embedding unit)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChunkDocument(BaseModel):
    """
    Atomic unit for retrieval and embedding produced by a chunker.

    RAG and agent-ready: includes strategy, optional token count, page/section context,
    and source_uri for citations. Supports multiple chunking strategies.
    """

    chunk_id: str = Field(..., description="Unique identifier for this chunk.")
    doc_id: str = Field(..., description="ID of the parsed document this chunk came from.")
    chunk_index: int = Field(..., description="Zero-based index of this chunk within the document.")
    text: str = Field(..., description="Chunk text content.")
    start_char: int | None = Field(None, description="Start character offset in source text.")
    end_char: int | None = Field(None, description="End character offset in source text.")
    chunk_strategy: str = Field(
        ...,
        description="Strategy used: recursive, markdown, layout, semantic, llm.",
    )
    token_count: int | None = Field(None, description="Token count when available for embedding/RAG.")
    page_number: int | None = Field(None, description="Page number in source document when applicable.")
    section_title: str | None = Field(None, description="Section or heading for context and citations.")
    source_uri: str = Field(..., description="Source URI for citations and provenance.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="RAG and agent-ready metadata.")
    created_at: datetime = Field(..., description="When this chunk was produced by the chunker.")
