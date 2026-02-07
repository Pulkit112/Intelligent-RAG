"""Base extractor: streaming SourceDocument -> ParsedUnit."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from schemas.parsed_unit import ParsedUnit
from schemas.source_document import SourceDocument


class BaseExtractor(ABC):
    """
    Stream parse a SourceDocument into ParsedUnit(s).

    No LLM calls. Yields page/section/block units; supports partial/failed via parse_status.
    """

    @abstractmethod
    def extract_stream(self, doc: SourceDocument) -> Iterator[ParsedUnit]:
        """
        Yield ParsedUnit(s) for the document. Page-by-page or section-by-section.

        Do not load entire document text into memory for large docs.
        """
        ...
