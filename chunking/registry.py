"""Chunker registry: name -> chunker class/factory for pluggable strategies."""

from __future__ import annotations

from typing import Type

from chunking.base import BaseChunker

_registry: dict[str, type[BaseChunker]] = {}


def register_chunker(name: str, chunker_class: type[BaseChunker]) -> None:
    """Register a chunker class under the given name."""
    _registry[name] = chunker_class


def get_chunker(name: str, **kwargs: object) -> BaseChunker:
    """Return a chunker instance for the given name. kwargs passed to constructor."""
    if name not in _registry:
        raise KeyError(f"Unknown chunker: {name}. Registered: {list(_registry)}")
    return _registry[name](**kwargs)
