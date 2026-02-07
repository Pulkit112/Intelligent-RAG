"""Basic tests for RecursiveChunker. Mock/small inputs; no LLM."""

from datetime import datetime, timezone

import pytest

from chunking.recursive_chunker import RecursiveChunker
from chunking.registry import get_chunker
from schemas.chunk_document import ChunkDocument
from schemas.parsed_unit import ParsedUnit


@pytest.fixture
def small_unit() -> ParsedUnit:
    """One ParsedUnit with short text."""
    return ParsedUnit(
        doc_id="doc1",
        unit_index=0,
        unit_type="page",
        text="First sentence. Second sentence. Third sentence.",
        structure=None,
        metadata={"page_number": 1, "source_uri": "file:///test.txt"},
        parse_status="success",
        error=None,
        created_at=datetime.now(timezone.utc),
    )


def test_recursive_chunker_returns_chunk_documents(small_unit: ParsedUnit) -> None:
    """chunk(unit) returns list of ChunkDocument with chunk_strategy=recursive and RAG metadata."""
    chunker = RecursiveChunker(chunk_size=1000, overlap=0)
    chunks = chunker.chunk(small_unit)
    assert len(chunks) >= 1
    for c in chunks:
        assert isinstance(c, ChunkDocument)
        assert c.chunk_strategy == "recursive"
        assert c.doc_id == "doc1"
        assert c.text
        assert c.source_uri == "file:///test.txt"
        assert c.metadata.get("unit_type") == "page"
        assert c.metadata.get("page_number") == 1


def test_recursive_chunker_splits_large_text() -> None:
    """Large text is split into multiple chunks when chunk_size is small."""
    unit = ParsedUnit(
        doc_id="d1",
        unit_index=0,
        unit_type="block",
        text="A. " * 200,
        structure=None,
        metadata={"source_uri": "file:///big.txt"},
        parse_status="success",
        error=None,
        created_at=datetime.now(timezone.utc),
    )
    chunker = RecursiveChunker(chunk_size=100, overlap=10)
    chunks = chunker.chunk(unit)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.chunk_strategy == "recursive"
        assert len(c.text) <= 150


def test_recursive_chunker_empty_text_returns_empty_list() -> None:
    """Unit with no text yields no chunks."""
    unit = ParsedUnit(
        doc_id="d1",
        unit_index=0,
        unit_type="page",
        text="",
        structure=None,
        metadata={},
        parse_status="success",
        error=None,
        created_at=datetime.now(timezone.utc),
    )
    chunker = RecursiveChunker()
    assert chunker.chunk(unit) == []


def test_registry_get_recursive_chunker() -> None:
    """get_chunker('recursive') returns RecursiveChunker instance."""
    chunker = get_chunker("recursive", chunk_size=500)
    assert isinstance(chunker, RecursiveChunker)
    assert chunker.chunk_size == 500
