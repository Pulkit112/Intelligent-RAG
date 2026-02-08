"""Abstract vector store interface for similarity search and persistence.

No embedder or ingestion logic — assumes vectors are already produced
and L2-normalized before being passed to the store.
"""

from abc import ABC, abstractmethod


class BaseVectorStore(ABC):
    """Abstract interface for a vector store with add, search, and delete operations."""

    @abstractmethod
    def add_embeddings(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        """Add embedding vectors with ids and metadata.

        Args:
            ids: Unique identifiers for each vector (e.g. chunk_id).
            vectors: L2-normalized embedding vectors.
            metadatas: One metadata dict per vector (e.g. doc_id, source_uri).

        Raises:
            ValueError: If ids, vectors, and metadatas lengths differ.
        """
        ...

    @abstractmethod
    def has_id(self, id: str) -> bool:
        """Return True if a vector with the given id exists in the store."""
        ...

    @abstractmethod
    def delete_by_doc(self, doc_id: str) -> int:
        """Delete all vectors whose metadata has doc_id equal to the given value.

        Args:
            doc_id: Value of metadata["doc_id"] for vectors to delete.

        Returns:
            Number of vectors deleted.
        """
        ...

    @abstractmethod
    def similarity_search(
        self,
        query_vector: list[float],
        k: int,
    ) -> list[dict]:
        """Return the k nearest vectors to the query by similarity.

        Args:
            query_vector: L2-normalized query embedding.
            k: Maximum number of results to return.

        Returns:
            List of dicts with keys: id, score, metadata.
            score is a similarity score (higher is more similar).
        """
        ...

    @abstractmethod
    def count(self) -> int:
        """Return the total number of vectors in the store."""
        ...
