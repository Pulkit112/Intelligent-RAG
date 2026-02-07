"""Source document schema — ingestion document built from one or more records."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    """
    Document assembled for ingestion from one or more source records.

    Supports multi-record → single-document grouping (e.g. email thread, conversation).
    Content is referenced via content_ref; no raw binary. Used as input to extractors.
    """

    doc_id: str = Field(..., description="Unique identifier for this ingestion document.")
    source_type: str = Field(..., description="Source type: file, web, api, slack, teams, etc.")
    source_uri: str = Field(..., description="Primary or composite URI for the document.")
    content_ref: str = Field(
        ...,
        description="Reference to content (path, blob key). No raw binary.",
    )
    content_type: str = Field(..., description="MIME or format: application/pdf, text/html, etc.")
    record_ids: list[str] = Field(
        default_factory=list,
        description="IDs of source records that were grouped into this document.",
    )
    checksum: str | None = Field(None, description="Content hash for change detection and checkpoints.")
    size_bytes: int | None = Field(None, description="Total content size when known.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible document metadata.")
    version: str | None = Field(None, description="Document version or ETag when applicable.")
    fetched_at: datetime = Field(..., description="When the underlying records were fetched.")
    built_at: datetime = Field(..., description="When this document was built from records.")
