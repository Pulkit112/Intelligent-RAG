"""PDF extractor: stream parse page-by-page, yield ParsedUnit with unit_type=page."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator

from extractors.base import BaseExtractor
from schemas.parsed_unit import ParsedUnit
from schemas.source_document import SourceDocument
from storage.raw_store import RawStore


class PDFExtractor(BaseExtractor):
    """
    Stream parse PDF page-by-page. Yield ParsedUnit with unit_type=page, unit_index=page number.

    Does not load entire PDF text into memory. On page-level failure emit ParsedUnit(parse_status=failed).
    """

    def __init__(self, raw_store: RawStore | None = None) -> None:
        """Initialize with optional RawStore to load content_ref bytes."""
        self._store = raw_store if raw_store is not None else RawStore()

    def extract_stream(self, doc: SourceDocument) -> Iterator[ParsedUnit]:
        """Yield one ParsedUnit per page; text and metadata.page_number set. Failures yield failed unit."""
        try:
            from pypdf import PdfReader
        except ImportError:
            yield ParsedUnit(
                doc_id=doc.doc_id,
                unit_index=0,
                unit_type="page",
                text=None,
                structure=None,
                metadata={},
                parse_status="failed",
                error="pypdf not installed",
                error_type="ImportError",
                error_message="pypdf not installed",
                created_at=datetime.now(timezone.utc),
            )
            return
        created_at = datetime.now(timezone.utc)
        try:
            raw = self._store.load_raw_bytes(doc.content_ref)
        except OSError as e:
            yield ParsedUnit(
                doc_id=doc.doc_id,
                unit_index=0,
                unit_type="page",
                text=None,
                structure=None,
                metadata={},
                parse_status="failed",
                error=str(e),
                error_type="LoadError",
                error_message=str(e),
                created_at=created_at,
            )
            return
        try:
            from io import BytesIO

            reader = PdfReader(BytesIO(raw))
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                    yield ParsedUnit(
                        doc_id=doc.doc_id,
                        unit_index=i,
                        unit_type="page",
                        text=text,
                        structure=None,
                        metadata={"page_number": i + 1, "source_uri": doc.source_uri},
                        parse_status="success",
                        error=None,
                        error_type=None,
                        error_message=None,
                        created_at=created_at,
                    )
                except Exception as e:
                    yield ParsedUnit(
                        doc_id=doc.doc_id,
                        unit_index=i,
                        unit_type="page",
                        text=None,
                        structure=None,
                        metadata={"page_number": i + 1, "source_uri": doc.source_uri},
                        parse_status="failed",
                        error=str(e),
                        error_type="PageReadError",
                        error_message=str(e),
                        created_at=created_at,
                    )
        except Exception as e:
            yield ParsedUnit(
                doc_id=doc.doc_id,
                unit_index=0,
                unit_type="page",
                text=None,
                structure=None,
                metadata={},
                parse_status="failed",
                error=str(e),
                error_type="ExtractionError",
                error_message=str(e),
                created_at=created_at,
            )
