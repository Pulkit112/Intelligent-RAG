"""Parsed unit schema — streaming extractor output block."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ParsedUnit(BaseModel):
    """
    Smallest parsed block produced by an extractor: format-agnostic.

    May represent a page, section, JSON record, message window, or generic block.
    Supports streaming extraction and partial failures via parse_status and error.
    """

    doc_id: str = Field(..., description="ID of the source document this unit belongs to.")
    unit_index: int = Field(..., description="Zero-based index of this unit within the document.")
    unit_type: str = Field(
        ...,
        description="Kind of unit: page, section, json_record, message_window, block.",
    )
    text: str | None = Field(None, description="Extracted text; may be None on partial or failed parse.")
    structure: dict[str, Any] | None = Field(
        None,
        description="Optional structure (headings, blocks, spans) for layout-aware chunking.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible unit metadata.")
    parse_status: str = Field(
        ...,
        description="Outcome: success, partial, or failed.",
    )
    error: str | None = Field(None, description="Error message or code when parse_status is not success (legacy).")
    error_type: str | None = Field(None, description="Error type for retry policies, e.g. ExtractionError, PageReadError.")
    error_message: str | None = Field(None, description="Full error message when parse_status is not success.")
    created_at: datetime = Field(..., description="When this unit was produced by the extractor.")
