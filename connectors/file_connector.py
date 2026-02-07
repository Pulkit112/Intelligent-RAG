"""File connector: read from disk, stream into raw_store, emit SourceRecord."""

from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from connectors.base import BaseConnector
from schemas.source_record import SourceRecord
from storage.raw_store import RawStore


class FileConnector(BaseConnector):
    """
    Connector for local files: streams file into raw_store, computes checksum, emits SourceRecord.

    No parsing or chunking. content_ref is the path returned by raw_store.
    """

    def __init__(self, raw_store: RawStore | None = None, base_path: str | Path = "data/raw") -> None:
        """Initialize with optional RawStore; uses default under base_path if not provided."""
        self._store = raw_store if raw_store is not None else RawStore(base_path=base_path)

    def fetch(self, path: str | Path, *, source_type: str = "file") -> Iterator[SourceRecord]:
        """
        Read file at path, stream into raw_store, yield one SourceRecord.

        Checksum is computed inside raw_store while streaming. No full file load.
        """
        path = Path(path)
        if not path.exists() or not path.is_file():
            return
        source_uri = str(path.resolve())
        record_id = str(uuid.uuid4())
        content_type, _ = mimetypes.guess_type(str(path), strict=False)
        if content_type is None:
            content_type = "application/octet-stream"
        size_bytes = path.stat().st_size
        fetched_at = datetime.now(timezone.utc)

        with open(path, "rb") as f:
            content_ref, checksum = self._store.save_raw_bytes(record_id, f)

        yield SourceRecord(
            record_id=record_id,
            source_type=source_type,
            source_uri=source_uri,
            content_ref=content_ref,
            content_type=content_type,
            checksum=checksum,
            size_bytes=size_bytes,
            metadata={},
            version=None,
            created_at=None,
            fetched_at=fetched_at,
        )
