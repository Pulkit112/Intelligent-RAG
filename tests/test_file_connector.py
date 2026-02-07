"""Basic tests for FileConnector. Mock/small inputs; no LLM."""

from pathlib import Path

import pytest

from connectors.file_connector import FileConnector
from schemas.source_record import SourceRecord
from storage.raw_store import RawStore


def test_file_connector_fetch_yields_source_record(tmp_path: Path) -> None:
    """Fetch from a small file yields one SourceRecord with content_ref and checksum."""
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    store = RawStore(base_path=tmp_path / "raw")
    connector = FileConnector(raw_store=store)
    records = list(connector.fetch(f))
    assert len(records) == 1
    rec = records[0]
    assert isinstance(rec, SourceRecord)
    assert rec.source_type == "file"
    assert rec.source_uri == str(f.resolve())
    assert rec.content_ref
    assert rec.checksum
    assert rec.content_type
    assert rec.size_bytes == 11
    raw = store.load_raw_bytes(rec.content_ref)
    assert raw == b"hello world"


def test_file_connector_nonexistent_path_yields_nothing() -> None:
    """Fetch from nonexistent path yields no records."""
    connector = FileConnector()
    records = list(connector.fetch("/nonexistent/file.txt"))
    assert len(records) == 0


def test_file_connector_checksum_stable(tmp_path: Path) -> None:
    """Same content produces same checksum; content_ref stored."""
    f = tmp_path / "same.txt"
    f.write_text("same content")
    store = RawStore(base_path=tmp_path / "raw")
    connector = FileConnector(raw_store=store)
    records = list(connector.fetch(f))
    assert len(records) == 1
    checksum = records[0].checksum
    assert store.exists_by_checksum(checksum)
