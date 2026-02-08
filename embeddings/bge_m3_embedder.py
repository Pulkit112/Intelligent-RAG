"""BGE-M3 embedder: BAAI/bge-m3 via sentence-transformers with batching and L2 normalization."""

from __future__ import annotations

import logging
import numpy as np

from embeddings.base import BaseEmbedder
from embeddings.batcher import batch_iter

logger = logging.getLogger(__name__)

# L2 norm epsilon to avoid division by zero
_NORM_EPS = 1e-12


def _l2_normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """L2 normalize row-wise. vec = vec / max(norm(vec), 1e-12)."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, _NORM_EPS)
    return vectors / norms


class BgeM3Embedder(BaseEmbedder):
    """
    Embedder using BAAI/bge-m3 via sentence-transformers.

    Purpose: produce dense embeddings for retrieval and semantic search.
    Normalization: L2-normalized vectors enable cosine similarity as dot product.
    Cosine similarity compatibility: when normalize=True, similarity_search can use
    dot product instead of cosine (vectors are unit length).
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        batch_size: int = 32,
        normalize: bool = True,
        device: str | None = None,
    ) -> None:
        """
        Initialize BGE-M3 embedder.

        model_name: HuggingFace model id (default BAAI/bge-m3).
        batch_size: batch size for encode.
        normalize: if True, L2-normalize embeddings for cosine-as-dot-product.
        device: cuda/cpu or None for auto (cuda if available else cpu).
        """
        self.model_name = model_name
        self.batch_size = max(1, batch_size)
        self.normalize = normalize
        if device is not None:
            self._device = device
        else:
            try:
                import torch
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self._device = "cpu"
        from sentence_transformers import SentenceTransformer
        self._model: SentenceTransformer = SentenceTransformer(model_name, device=self._device)
        # Compute vector_dim once via a test encode
        test_out = self._model.encode(["dummy"], convert_to_numpy=True, normalize_embeddings=False)
        self._vector_dim = int(test_out.shape[1]) if test_out.ndim == 2 else int(test_out.shape[0])

    @property
    def vector_dim(self) -> int:
        """Dimension of the embedding vector (from model)."""
        return self._vector_dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Embed texts in batches; L2-normalize if configured; return list of vectors.

        On batch encode failure: retry once with half the batch; if still fails, raise.
        """
        if not texts:
            return []
        all_vectors: list[np.ndarray] = []
        for batch in batch_iter(texts, self.batch_size):
            vectors = self._encode_batch_with_retry(batch)
            if self.normalize:
                vectors = _l2_normalize_vectors(vectors)
            for i in range(len(vectors)):
                all_vectors.append(vectors[i])
        # Consistency check
        dim = self._vector_dim
        for v in all_vectors:
            if v.shape[0] != dim:
                raise ValueError(f"Unexpected vector dimension {v.shape[0]} vs {dim}")
        return [v.tolist() for v in all_vectors]

    def _encode_batch_with_retry(self, batch: list[str]) -> np.ndarray:
        """Encode one batch; on failure retry once with half batch if batch size > 1."""
        try:
            out = self._model.encode(
                batch,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )
            if out.ndim == 1:
                out = out.reshape(1, -1)
            return out
        except Exception as e:
            if len(batch) > 1:
                mid = len(batch) // 2
                logger.warning("BGE-M3 batch encode failed (%s), retrying with half batch", e)
                first = self._encode_batch_with_retry(batch[:mid])
                second = self._encode_batch_with_retry(batch[mid:])
                return np.vstack([first, second])
            raise
