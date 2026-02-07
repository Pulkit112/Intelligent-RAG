"""Basic tests for PDF extractor stream. Mock/small inputs; no LLM."""

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from extractors.pdf_extractor import PDFExtractor
from schemas.parsed_unit import ParsedUnit
from schemas.source_document import SourceDocument
from storage.raw_store import RawStore


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Minimal PDF that pypdf can read (single empty or short page)."""
    try:
        from pypdf import PdfWriter

        buf = PdfWriter()
        buf.add_blank_page(width=100, height=100)
        from io import BytesIO

        out = BytesIO()
        buf.write(out)
        return out.getvalue()
    except ImportError:
        return b""


def test_pdf_extractor_stream_yields_parsed_units_when_pypdf_installed(
    tmp_path: Path, sample_pdf_bytes: bytes
) -> None:
    """When pypdf is installed and doc has PDF content_ref, extract_stream yields ParsedUnit(s)."""
    if not sample_pdf_bytes:
        pytest.skip("pypdf not installed")
    store = RawStore(base_path=tmp_path / "raw")
    content_ref, _ = store.save_raw_bytes("doc1", sample_pdf_bytes)
    doc = SourceDocument(
        doc_id="doc1",
        source_type="file",
        source_uri="file:///test.pdf",
        content_ref=content_ref,
        content_type="application/pdf",
        record_ids=[],
        fetched_at=datetime.now(timezone.utc),
        built_at=datetime.now(timezone.utc),
    )
    extractor = PDFExtractor(raw_store=store)
    units = list(extractor.extract_stream(doc))
    assert len(units) >= 1
    for u in units:
        assert isinstance(u, ParsedUnit)
        assert u.doc_id == "doc1"
        assert u.unit_type == "page"
        assert u.unit_index >= 0
        assert u.parse_status in ("success", "failed")


def test_pdf_extractor_stream_failed_unit_on_missing_content_ref(tmp_path: Path) -> None:
    """When content_ref cannot be loaded, yield one failed ParsedUnit."""
    doc = SourceDocument(
        doc_id="doc1",
        source_type="file",
        source_uri="file:///missing.pdf",
        content_ref=str(tmp_path / "raw" / "nonexistent"),
        content_type="application/pdf",
        record_ids=[],
        fetched_at=datetime.now(timezone.utc),
        built_at=datetime.now(timezone.utc),
    )
    store = RawStore(base_path=tmp_path / "raw")
    extractor = PDFExtractor(raw_store=store)
    units = list(extractor.extract_stream(doc))
    assert len(units) == 1
    assert units[0].parse_status == "failed"
    assert units[0].error
