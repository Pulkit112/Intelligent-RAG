"""Base connector interface. Connectors return SourceRecord only; no parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from schemas.source_record import SourceRecord


class BaseConnector(ABC):
    """
    Abstract connector: fetches raw content and yields SourceRecords.

    Connectors do not parse content; they stream into storage and emit
    SourceRecord with content_ref. No chunking or extraction logic.
    """

    @abstractmethod
    def fetch(self, *args: object, **kwargs: object) -> Iterator[SourceRecord]:
        """
        Fetch from source and yield SourceRecord(s).

        Caller provides source-specific args (e.g. path, URI). Each record
        must have content_ref pointing to stored blob; no raw bytes in schema.
        """
        ...
