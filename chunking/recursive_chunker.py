"""Recursive text chunker: configurable chunk_size and overlap; chunk_strategy=recursive."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import List

from chunking.base import BaseChunker
from rag.token_counter import estimate_token_count
from schemas.chunk_document import ChunkDocument
from schemas.parsed_unit import ParsedUnit


def _split_by_separators(text: str, separators: list[str]) -> List[str]:
    """Split text by first matching separator; recurse on rest with remaining separators."""
    if not separators:
        return [text] if text.strip() else []
    sep = separators[0]
    parts = re.split(re.escape(sep), text) if sep else [text]
    rest_seps = separators[1:]
    result: List[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if rest_seps:
            result.extend(_split_by_separators(part, rest_seps))
        else:
            result.append(part)
    return result


def _merge_small(chunks: List[str], chunk_size: int, overlap: int) -> List[str]:
    """Merge small chunks up to chunk_size with overlap."""
    if chunk_size <= 0:
        return chunks
    result: List[str] = []
    buf: List[str] = []
    buf_len = 0
    for c in chunks:
        c_len = len(c) + (1 if buf else 0)
        if buf_len + c_len > chunk_size and buf:
            combined = " ".join(buf)
            result.append(combined)
            if overlap > 0 and buf:
                buf = [buf[-1]] if len(buf[-1]) <= overlap else [buf[-1][-overlap:]]
                buf_len = sum(len(x) for x in buf) + len(buf) - 1
            else:
                buf = []
                buf_len = 0
        buf.append(c)
        buf_len += c_len + (1 if len(buf) > 1 else 0)
    if buf:
        result.append(" ".join(buf))
    return result


class RecursiveChunker(BaseChunker):
    """
    Recursive text splitter: split by separators (paragraph, newline, space), then merge to chunk_size with overlap.

    Sets chunk_strategy="recursive". Configurable chunk_size and overlap.

    Rule: chunk() runs per ParsedUnit only. It does NOT merge across units (e.g. across pages).
    Each unit is chunked independently so page_number and unit boundaries are preserved.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        """Initialize with chunk_size, overlap, and optional separator list."""
        self.chunk_size = max(100, chunk_size)
        self.overlap = max(0, min(overlap, chunk_size // 2))
        self.separators = separators if separators is not None else self.DEFAULT_SEPARATORS.copy()

    def chunk(self, unit: ParsedUnit) -> list[ChunkDocument]:
        """
        Split this single ParsedUnit's text by separators and merge to chunk_size.

        Does not merge across ParsedUnits; each unit is chunked independently (page boundaries preserved).
        """
        text = (unit.text or "").strip()
        if not text:
            return []
        created_at = datetime.now(timezone.utc)
        source_uri = ""
        if unit.metadata:
            source_uri = unit.metadata.get("source_uri", "")
        page_number = unit.metadata.get("page_number") if unit.metadata else None
        section_title = unit.metadata.get("section_title") if unit.metadata else None
        doc_id = unit.doc_id
        chunks = _split_by_separators(text, self.separators)
        merged = _merge_small(chunks, self.chunk_size, self.overlap)
        result: list[ChunkDocument] = []
        start = 0
        for i, block in enumerate(merged):
            chunk_id = str(uuid.uuid4())
            end = start + len(block)
            metadata: dict = {
                "unit_index": unit.unit_index,
                "unit_type": unit.unit_type,
                "page_number": page_number,
                "section_title": section_title,
            }
            token_count = estimate_token_count(block)
            result.append(
                ChunkDocument(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    chunk_index=i,
                    text=block,
                    start_char=start,
                    end_char=end,
                    chunk_strategy="recursive",
                    token_count=token_count,
                    page_number=page_number,
                    section_title=section_title,
                    source_uri=source_uri,
                    metadata=metadata,
                    created_at=created_at,
                )
            )
            start = end
        return result
