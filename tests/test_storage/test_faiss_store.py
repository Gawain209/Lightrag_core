"""Tests for FaissStore."""

import numpy as np
import pytest

from lightrag_core.storage.vectorstore.faiss_store import FaissStore


class TestFaissStore:
    """Test suite for FaissStore."""

    def test_init(self) -> None:
        """Test FaissStore initialization."""
        store = FaissStore(dimension=768)
        assert store.dimension == 768

    def test_add_and_search(self) -> None:
        """Test adding vectors and searching."""
        store = FaissStore(dimension=768)

        # Generate random normalized vectors
        rng = np.random.default_rng(seed=42)
        vectors = rng.random((5, 768)).astype(np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = (vectors / norms).tolist()

        ids = [f"doc-{i}" for i in range(5)]
        store.add(vectors, ids)

        # Search with the first vector
        results = store.search(vectors[0], top_k=3)
        assert len(results) == 3
        assert results[0][0] == "doc-0"  # Most similar to itself

    def test_search_filters_by_metadata(self) -> None:
        """Test searching vectors with metadata filters."""
        store = FaissStore(dimension=3)
        vectors = [
            [1.0, 0.0, 0.0],
            [0.9, 0.1, 0.0],
            [0.8, 0.2, 0.0],
        ]
        ids = ["kb-a-doc", "kb-b-doc", "kb-a-doc-2"]
        metadatas = [
            {"kb_id": "kb-a"},
            {"kb_id": "kb-b"},
            {"kb_id": "kb-a"},
        ]

        store.add(vectors, ids, metadatas=metadatas)

        results = store.search([1.0, 0.0, 0.0], top_k=3, filters={"kb_id": "kb-b"})
        assert results == [("kb-b-doc", results[0][1])]

    def test_search_empty_store(self) -> None:
        """Test searching in an empty store."""
        store = FaissStore(dimension=768)
        query = np.random.randn(768).astype(np.float32).tolist()
        results = store.search(query, top_k=5)
        assert len(results) == 0

    def test_add_empty_vectors(self) -> None:
        """Test adding empty list of vectors."""
        store = FaissStore(dimension=768)
        store.add([], [])
        query = np.random.randn(768).astype(np.float32).tolist()
        results = store.search(query, top_k=5)
        assert len(results) == 0

    def test_delete_not_implemented(self) -> None:
        """Test that delete raises NotImplementedError."""
        store = FaissStore(dimension=768)
        with pytest.raises(NotImplementedError):
            store.delete(["doc-0"])
