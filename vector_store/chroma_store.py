"""ChromaDB-backed vector store with persistence and cosine similarity."""

from __future__ import annotations

import chromadb

from vector_store.base import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    """Production-ready vector store using ChromaDB with persistent storage.

    Uses cosine distance; assumes embeddings are L2-normalized before add.
    Stores only vectors and metadata — no document text.
    """

    def __init__(
        self,
        persist_dir: str = "data/vector_store",
        collection_name: str = "chunks",
    ) -> None:
        """Initialize Chroma client and get or create the collection.

        Args:
            persist_dir: Directory for Chroma persistence.
            collection_name: Name of the collection for chunk vectors.
        """
        self._persist_dir = persist_dir
        self._collection_name = collection_name
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

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
            metadatas: One metadata dict per vector (must include doc_id, etc.).

        Raises:
            ValueError: If ids, vectors, and metadatas have different lengths.
        """
        if not (len(ids) == len(vectors) == len(metadatas)):
            raise ValueError(
                f"Length mismatch: ids={len(ids)}, vectors={len(vectors)}, "
                f"metadatas={len(metadatas)}; all must be equal."
            )
        if len(ids) == 0:
            return
        # Ensure each vector is list[float] (e.g. from numpy)
        embeddings = [
            list(v) if not isinstance(v, list) else v for v in vectors
        ]
        try:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as e:
            raise RuntimeError(
                f"Chroma add failed: {e!s}"
            ) from e

    def has_id(self, id: str) -> bool:
        """Return True if a vector with the given id exists in the store."""
        try:
            result = self._collection.get(ids=[id])
            return len(result["ids"]) > 0
        except Exception as e:
            raise RuntimeError(
                f"Chroma get failed for id={id!r}: {e!s}"
            ) from e

    def delete_by_doc(self, doc_id: str) -> int:
        """Delete all vectors whose metadata has doc_id equal to the given value.

        Args:
            doc_id: Value of metadata["doc_id"] for vectors to delete.

        Returns:
            Number of vectors deleted.
        """
        try:
            result = self._collection.get(
                where={"doc_id": doc_id},
                include=[],
            )
            ids_to_delete = result["ids"]
            count = len(ids_to_delete)
            if count > 0:
                self._collection.delete(ids=ids_to_delete)
            return count
        except Exception as e:
            raise RuntimeError(
                f"Chroma delete_by_doc failed for doc_id={doc_id!r}: {e!s}"
            ) from e

    def list_chunks(self, limit: int = 1000) -> list[dict]:
        """List stored chunk ids and metadata (for inspection). No embeddings returned.

        Args:
            limit: Max number of entries to return.

        Returns:
            List of dicts with keys: id, metadata.
        """
        try:
            result = self._collection.get(
                limit=limit,
                include=["metadatas"],
            )
            ids = result["ids"] or []
            metadatas = result["metadatas"] or []
            out: list[dict] = []
            for i, id in enumerate(ids):
                meta = metadatas[i] if i < len(metadatas) else {}
                out.append({"id": id, "metadata": meta})
            return out
        except Exception as e:
            raise RuntimeError(
                f"Chroma list_chunks failed: {e!s}"
            ) from e

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
            score is cosine similarity (higher is more similar).
        """
        try:
            q_emb = (
                list(query_vector)
                if not isinstance(query_vector, list)
                else query_vector
            )
            result = self._collection.query(
                query_embeddings=[q_emb],
                n_results=k,
                include=["metadatas"],
            )
        except Exception as e:
            raise RuntimeError(
                f"Chroma similarity_search failed: {e!s}"
            ) from e

        ids = result["ids"]
        distances = result["distances"]
        metadatas = result["metadatas"]

        if not ids or not ids[0]:
            return []

        # Cosine distance: 0 = identical, 2 = opposite. Convert to similarity.
        # similarity = 1 - distance (so 1 = identical, -1 = opposite).
        out: list[dict] = []
        for i, id in enumerate(ids[0]):
            dist = distances[0][i] if distances else 0.0
            meta = metadatas[0][i] if metadatas and metadatas[0] else {}
            score = float(1.0 - dist)
            out.append({"id": id, "score": score, "metadata": meta})
        return out

    def count(self) -> int:
        """Return the total number of vectors in the store."""
        try:
            return self._collection.count()
        except Exception as e:
            raise RuntimeError(
                f"Chroma count failed: {e!s}"
            ) from e
