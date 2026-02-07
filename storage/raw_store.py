"""Raw blob storage under data/raw/ with streaming write and checksum index."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import BinaryIO

CHUNK_SIZE = 65536  # 64 KiB for streaming copy
INDEX_FILENAME = "checksum_index.json"


class RawStore:
    """
    Store raw bytes by doc_id; resolve by content_ref; index by checksum.

    Uses streaming write (chunked copy) to avoid loading entire content into memory.
    Stores blobs under base_path; maintains checksum -> content_ref index for
    exists_by_checksum (restart-safe / skip-if-processed).
    """

    def __init__(self, base_path: str | Path = "data/raw") -> None:
        """Initialize store with base directory for blobs and index."""
        self._base = Path(base_path)
        self._index_path = self._base / INDEX_FILENAME
        self._index: dict[str, str] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load checksum -> content_ref index from disk if present."""
        if self._index_path.exists():
            try:
                with open(self._index_path, encoding="utf-8") as f:
                    self._index = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._index = {}
        else:
            self._index = {}

    def _save_index(self) -> None:
        """Persist checksum index to disk."""
        self._base.mkdir(parents=True, exist_ok=True)
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)

    def save_raw_bytes(
        self,
        doc_id: str,
        stream_or_bytes: BinaryIO | bytes,
        *,
        checksum: str | None = None,
    ) -> tuple[str, str]:
        """
        Write content to storage under doc_id; return (content_ref, checksum).

        Uses chunked copy for streams to avoid full memory load. Registers
        checksum in index for exists_by_checksum. Caller gets checksum for records.
        """
        self._base.mkdir(parents=True, exist_ok=True)
        blob_path = self._base / doc_id
        hasher = hashlib.sha256()

        if isinstance(stream_or_bytes, bytes):
            blob_path.write_bytes(stream_or_bytes)
            hasher.update(stream_or_bytes)
        else:
            with open(blob_path, "wb") as out:
                while True:
                    chunk = stream_or_bytes.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    out.write(chunk)
                    hasher.update(chunk)

        computed = hasher.hexdigest()
        if checksum is None:
            checksum = computed
        self._index[checksum] = str(blob_path)
        self._save_index()
        return (str(blob_path), checksum)

    def load_raw_bytes(self, content_ref: str) -> bytes:
        """Read content from path given by content_ref; return bytes."""
        path = Path(content_ref)
        if not path.is_absolute():
            path = self._base / path.name
        return path.read_bytes()

    def exists_by_checksum(self, checksum: str) -> bool:
        """Return True if a blob is already stored for this checksum (restart-safe)."""
        return checksum in self._index


_default_store: RawStore | None = None


def _get_default_store() -> RawStore:
    """Return module-level default store; create once. No global mutable state for API."""
    global _default_store
    if _default_store is None:
        _default_store = RawStore()
    return _default_store


def save_raw_bytes(
    doc_id: str,
    stream_or_bytes: BinaryIO | bytes,
    *,
    checksum: str | None = None,
    store: RawStore | None = None,
) -> tuple[str, str]:
    """
    Save raw bytes; return (content_ref, checksum). Uses default RawStore if store not provided.
    """
    s = store if store is not None else _get_default_store()
    return s.save_raw_bytes(doc_id, stream_or_bytes, checksum=checksum)


def load_raw_bytes(content_ref: str, store: RawStore | None = None) -> bytes:
    """Load bytes for content_ref. Uses default RawStore if store not provided."""
    s = store if store is not None else _get_default_store()
    return s.load_raw_bytes(content_ref)


def exists_by_checksum(checksum: str, store: RawStore | None = None) -> bool:
    """Return whether checksum is already stored. Uses default RawStore if store not provided."""
    s = store if store is not None else _get_default_store()
    return s.exists_by_checksum(checksum)
