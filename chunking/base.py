"""Base chunker: ParsedUnit -> list[ChunkDocument]."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.chunk_document import ChunkDocument
    from schemas.parsed_unit import ParsedUnit


class BaseChunker(ABC):
    """
    Chunk a ParsedUnit into one or more ChunkDocument(s).

    Strategy pattern; all chunkers return ChunkDocument with chunk_strategy set.
    """

    @abstractmethod
    def chunk(self, unit: "ParsedUnit") -> list["ChunkDocument"]:
        """Split unit into chunks; return list of ChunkDocument with strategy metadata."""
        ...
