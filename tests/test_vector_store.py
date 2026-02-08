"""Tests for vector store: ChromaVectorStore with temp dir and fake vectors.

Uses small numeric vectors (dim=4); does not call the real embedder.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from vector_store import ChromaVectorStore


@pytest.fixture
def temp_persist_dir() -> Path:
    """Create a temporary directory for Chroma persistence."""
    with tempfile.TemporaryDirectory(prefix="chroma_test_") as d:
        yield Path(d)


@pytest.fixture
def store(temp_persist_dir: Path) -> ChromaVectorStore:
    """ChromaVectorStore backed by a temp directory."""
    return ChromaVectorStore(
        persist_dir=str(temp_persist_dir),
        collection_name="chunks",
    )


def _meta(doc_id: str, chunk_id: str, source_uri: str = "file:///doc.pdf") -> dict:
    """Minimal metadata matching contract (chunk_id, doc_id, source_uri, etc.)."""
    return {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "source_uri": source_uri,
        "page_number": 1,
        "section_title": "",
        "chunk_strategy": "recursive",
        "token_count": 10,
    }


def test_add_and_count(store: ChromaVectorStore) -> None:
    """Adding 3 fake embeddings yields count() == 3."""
    ids = ["c1", "c2", "c3"]
    # Small L2-normalized-like vectors (dim=4)
    vectors = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ]
    metadatas = [
        _meta("doc_a", "c1"),
        _meta("doc_a", "c2"),
        _meta("doc_b", "c3"),
    ]
    store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)
    assert store.count() == 3


def test_has_id(store: ChromaVectorStore) -> None:
    """has_id returns True for existing id, False for missing."""
    store.add_embeddings(
        ids=["c1"],
        vectors=[[1.0, 0.0, 0.0, 0.0]],
        metadatas=[_meta("doc_a", "c1")],
    )
    assert store.has_id("c1") is True
    assert store.has_id("c_nonexistent") is False


def test_similarity_search_returns_k_results(store: ChromaVectorStore) -> None:
    """similarity_search returns up to k results with id, score, metadata."""
    ids = ["c1", "c2", "c3"]
    vectors = [
        [1.0, 0.0, 0.0, 0.0],
        [0.9, 0.1, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ]
    metadatas = [_meta("doc_a", i) for i in ids]
    store.add_embeddings(ids=ids, vectors=vectors, metadatas=metadatas)

    # Query with same as c1 -> c1 should be top
    query = [1.0, 0.0, 0.0, 0.0]
    results = store.similarity_search(query_vector=query, k=2)

    assert len(results) == 2
    for r in results:
        assert "id" in r and "score" in r and "metadata" in r
        assert isinstance(r["metadata"], dict)
    assert results[0]["id"] == "c1"
    assert results[0]["score"] >= results[1]["score"]


def test_delete_by_doc_removes_subset(store: ChromaVectorStore) -> None:
    """delete_by_doc removes only vectors with matching doc_id; count reflects deletion."""
    store.add_embeddings(
        ids=["c1", "c2", "c3"],
        vectors=[
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
        metadatas=[
            _meta("doc_a", "c1"),
            _meta("doc_a", "c2"),
            _meta("doc_b", "c3"),
        ],
    )
    assert store.count() == 3

    deleted = store.delete_by_doc("doc_a")
    assert deleted == 2
    assert store.count() == 1
    assert store.has_id("c1") is False
    assert store.has_id("c2") is False
    assert store.has_id("c3") is True

    deleted2 = store.delete_by_doc("doc_b")
    assert deleted2 == 1
    assert store.count() == 0


def test_add_embeddings_length_mismatch_raises(store: ChromaVectorStore) -> None:
    """add_embeddings raises ValueError when ids, vectors, metadatas lengths differ."""
    with pytest.raises(ValueError, match="Length mismatch"):
        store.add_embeddings(
            ids=["a", "b"],
            vectors=[[1.0, 0.0, 0.0, 0.0]],
            metadatas=[_meta("d", "a")],
        )


def test_add_embeddings_empty_no_op(store: ChromaVectorStore) -> None:
    """add_embeddings with empty lists does not raise and count stays 0."""
    store.add_embeddings(ids=[], vectors=[], metadatas=[])
    assert store.count() == 0
