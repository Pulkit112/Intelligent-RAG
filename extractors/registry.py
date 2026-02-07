"""Extractor registry: content_type -> extractor class for pluggable routing."""

from __future__ import annotations

from typing import Type

from extractors.base import BaseExtractor

_registry: dict[str, Type[BaseExtractor]] = {}


def register_extractor(content_type: str, extractor_class: Type[BaseExtractor]) -> None:
    """Register an extractor class for the given content_type (e.g. application/pdf)."""
    _registry[content_type] = extractor_class


def get_extractor(content_type: str, **kwargs: object) -> BaseExtractor:
    """Return an extractor instance for the given content_type. kwargs passed to constructor."""
    if content_type not in _registry:
        raise KeyError(f"Unknown content_type: {content_type}. Registered: {list(_registry)}")
    return _registry[content_type](**kwargs)
