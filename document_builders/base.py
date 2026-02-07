"""Base document builder: records -> documents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from schemas.source_document import SourceDocument
from schemas.source_record import SourceRecord


class BaseDocumentBuilder(ABC):
    """
    Build ingestion documents from one or more source records.

    Design supports 1:1 (file) or N:1 (chat thread, email conversation) grouping.
    """

    @abstractmethod
    def build(self, records: list[SourceRecord]) -> list[SourceDocument]:
        """
        Build one or more SourceDocuments from the given records.

        May group multiple records into a single document (e.g. conversation).
        """
        ...
