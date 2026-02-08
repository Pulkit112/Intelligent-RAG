"""Embedding layer: text -> vectors. No vector DB logic."""

from embeddings.base import BaseEmbedder
from embeddings.batcher import batch_iter
from embeddings.bge_m3_embedder import BgeM3Embedder

__all__ = ["BaseEmbedder", "batch_iter", "BgeM3Embedder"]
