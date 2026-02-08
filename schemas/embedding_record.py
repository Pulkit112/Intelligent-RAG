"""Embedding record schema — audit and trace mapping. Vector lives only in vector DB."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EmbeddingRecord(BaseModel):
    """
    Audit record for an embedded chunk. Does not store the vector.

    Vector lives only in the vector DB. This schema is for trace mapping:
    embedding_id, chunk_id, doc_id, model, dimension, created_at, metadata.
    """

    embedding_id: str = Field(..., description="Unique identifier for this embedding record.")
    chunk_id: str = Field(..., description="ID of the chunk that was embedded.")
    doc_id: str = Field(..., description="ID of the source document.")
    model_name: str = Field(..., description="Name of the embedding model used.")
    vector_dim: int = Field(..., description="Dimension of the embedding vector.")
    created_at: datetime = Field(..., description="When this embedding was produced.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible audit metadata.")
