"""Smoke tests for BGE-M3 embedder: small batch, normalization, dimension."""

from __future__ import annotations

import math
import pytest

from embeddings.bge_m3_embedder import BgeM3Embedder


@pytest.fixture
def embedder() -> BgeM3Embedder:
    """BgeM3Embedder with small batch_size for tests. Uses GPU (cuda) if available."""
    return BgeM3Embedder(model_name="BAAI/bge-m3", batch_size=4, normalize=True, device=None)


def test_embed_two_sentences_returns_vectors(embedder: BgeM3Embedder) -> None:
    """Embed 2 short sentences; vectors returned, same dimension, dimension equals embedder.vector_dim."""
    texts = ["First short sentence.", "Second short sentence."]
    vectors = embedder.embed_texts(texts)
    assert len(vectors) == 2
    assert all(isinstance(v, list) and all(isinstance(x, float) for x in v) for v in vectors)
    dim = embedder.vector_dim
    assert all(len(v) == dim for v in vectors)
    assert len(vectors[0]) == embedder.vector_dim
    assert len(vectors[1]) == embedder.vector_dim


def test_normalized_vectors_have_unit_norm(embedder: BgeM3Embedder) -> None:
    """When normalize=True, each vector has L2 norm approx 1.0."""
    texts = ["Unit norm check.", "Another short text."]
    vectors = embedder.embed_texts(texts)
    assert len(vectors) >= 1
    for v in vectors:
        norm = math.sqrt(sum(x * x for x in v))
        assert abs(norm - 1.0) < 0.01, f"Expected norm ~1.0, got {norm}"
