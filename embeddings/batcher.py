"""Batching helper for embedding and other batch processing."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TypeVar

T = TypeVar("T")


def batch_iter(items: Sequence[T], batch_size: int) -> Iterator[list[T]]:
    """
    Yield items in batches of size batch_size.

    Generic over item type. Yields lists; last batch may be smaller.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    n = len(items)
    for start in range(0, n, batch_size):
        yield list(items[start : start + batch_size])
