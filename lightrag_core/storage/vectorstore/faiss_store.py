"""FAISS-based vector store implementation."""

import json
import os
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

from lightrag_core.core import BaseVectorStore


class FaissStore(BaseVectorStore):
    """Vector store implementation using FAISS.

    Supports both in-memory and persistent storage.
    """

    def __init__(self, dimension: int, index_path: Optional[str] = None) -> None:
        """Initialize the FAISS store.

        Args:
            dimension: Dimension of the embedding vectors.
            index_path: Optional path to persist/load the index.
        """
        self.dimension = dimension
        self.index_path = index_path
        self._id_map: List[str] = []
        self._metadata_map: List[Dict[str, Any]] = []
        self._index: Optional[faiss.Index] = None

        if index_path and os.path.exists(index_path):
            self._load()
        else:
            self._index = faiss.IndexFlatIP(dimension)

    def _load(self) -> None:
        """Load the index from disk."""
        if not self.index_path:
            return
        self._index = faiss.read_index(self.index_path)
        id_map_path = self.index_path + ".ids"
        if os.path.exists(id_map_path):
            with open(id_map_path, "r", encoding="utf-8") as f:
                self._id_map = [line.strip() for line in f]
        metadata_path = self.index_path + ".metadata"
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                self._metadata_map = [json.loads(line) for line in f]

        while len(self._metadata_map) < len(self._id_map):
            self._metadata_map.append({})

    def _save(self) -> None:
        """Save the index to disk."""
        if not self.index_path or self._index is None:
            return
        faiss.write_index(self._index, self.index_path)
        id_map_path = self.index_path + ".ids"
        with open(id_map_path, "w", encoding="utf-8") as f:
            for vid in self._id_map:
                f.write(vid + "\n")
        metadata_path = self.index_path + ".metadata"
        with open(metadata_path, "w", encoding="utf-8") as f:
            for metadata in self._metadata_map:
                f.write(json.dumps(metadata, ensure_ascii=False) + "\n")

    def add(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add vectors to the store.

        Args:
            vectors: List of embedding vectors.
            ids: Corresponding IDs for the vectors.
            metadatas: Optional metadata for each vector.
        """
        if not vectors:
            return
        if self._index is None:
            raise RuntimeError("Index is not initialized")
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        if metadatas is not None and len(metadatas) != len(ids):
            raise ValueError("metadatas and ids must have the same length")

        np_vectors = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(np_vectors)
        self._index.add(np_vectors)  # type: ignore[union-attr]
        self._id_map.extend(ids)
        self._metadata_map.extend(metadatas or [{} for _ in ids])
        self._save()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[str, float]]:
        """Search for the top-k most similar vectors.

        Args:
            query_vector: The query embedding vector.
            top_k: Number of results to return.
            filters: Optional exact-match metadata filters.

        Returns:
            List of (id, score) tuples.
        """
        if self._index is None:
            raise RuntimeError("Index is not initialized")
        if top_k <= 0:
            return []

        np_query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(np_query)
        fetch_k = self._index.ntotal if filters else min(top_k, self._index.ntotal)
        if fetch_k == 0:
            return []
        distances, indices = self._index.search(np_query, fetch_k)  # type: ignore[union-attr]

        results: List[tuple[str, float]] = []
        for idx, score in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self._id_map):
                continue
            metadata = self._metadata_map[idx] if idx < len(self._metadata_map) else {}
            if filters and not all(metadata.get(key) == value for key, value in filters.items()):
                continue
            results.append((self._id_map[idx], float(score)))
            if len(results) >= top_k:
                break
        return results

    def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs.

        Note: FAISS does not support direct deletion.
        This requires rebuilding the index.

        Args:
            ids: List of vector IDs to delete.
        """
        # FAISS does not support direct deletion.
        # In a production scenario, this would rebuild the index.
        raise NotImplementedError("FAISS does not support direct deletion")
