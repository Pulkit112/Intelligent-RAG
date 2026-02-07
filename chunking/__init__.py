"""Pluggable chunking strategies. All chunkers return ChunkDocument."""

from chunking.base import BaseChunker
from chunking.recursive_chunker import RecursiveChunker
from chunking.registry import get_chunker, register_chunker

register_chunker("recursive", RecursiveChunker)

__all__ = ["BaseChunker", "RecursiveChunker", "get_chunker", "register_chunker"]
