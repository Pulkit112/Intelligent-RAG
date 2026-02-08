"""Base embedder interface. No vector DB logic."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """
    Abstract embedder: map text to vectors. No vector DB logic.

    Implementations handle model loading, batching, and optional normalization.
    """

    @property
    @abstractmethod
    def vector_dim(self) -> int:
        """Dimension of the embedding vector produced by this embedder."""
        ...

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts; return list of embedding vectors.

        Caller is responsible for batching; implementer may batch internally.
        """
        ...

    def embed_one(self, text: str) -> list[float]:
        """
        Embed a single text; return one embedding vector.

        Default implementation uses embed_texts([text]). Override for efficiency.
        """
        if not text.strip():
            return [0.0] * self.vector_dim
        return self.embed_texts([text])[0]
