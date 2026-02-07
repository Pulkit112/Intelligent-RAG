"""Streaming extractors: SourceDocument -> Iterator[ParsedUnit]. No LLM."""

from extractors.base import BaseExtractor
from extractors.pdf_extractor import PDFExtractor
from extractors.registry import get_extractor, register_extractor

register_extractor("application/pdf", PDFExtractor)

__all__ = ["BaseExtractor", "PDFExtractor", "get_extractor", "register_extractor"]
