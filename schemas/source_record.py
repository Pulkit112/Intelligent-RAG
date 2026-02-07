"""Source record schema — connector atom (smallest fetched unit)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SourceRecord(BaseModel):
    """
    Smallest unit produced by a connector: one file, one message, one row, one email.

    Connectors return one or more SourceRecords. No parsing; content is referenced
    via content_ref (path, URI, or storage key), not raw bytes.
    """

    record_id: str = Field(..., description="Unique identifier for this fetched record.")
    source_type: str = Field(..., description="Connector type: file, web, api, db, slack, teams, etc.")
    source_uri: str = Field(..., description="Canonical URI or identifier of the source.")
    content_ref: str = Field(
        ...,
        description="Reference to content (file path, blob key, API ref). No raw binary.",
    )
    content_type: str = Field(..., description="MIME or format hint: application/pdf, text/html, etc.")
    checksum: str | None = Field(None, description="Content hash for change detection and idempotency.")
    size_bytes: int | None = Field(None, description="Content size when known.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible connector metadata.")
    version: str | None = Field(None, description="Source version or ETag when applicable.")
    created_at: datetime | None = Field(None, description="Source system creation time if available.")
    fetched_at: datetime = Field(..., description="When this record was fetched by the connector.")
