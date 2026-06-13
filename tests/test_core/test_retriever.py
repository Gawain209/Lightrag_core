"""Tests for VectorRetriever."""

import numpy as np

from lightrag_core.core.embedding.bge_embedding import BGEmbedding
from lightrag_core.core.retriever.vector_retriever import VectorRetriever
from lightrag_core.storage.vectorstore.faiss_store import FaissStore


class TestVectorRetriever:
    """Test suite for VectorRetriever."""

    def test_retrieve(self) -> None:
        """Test basic retrieval."""
        embedding = BGEmbedding()
        store = FaissStore(dimension=embedding.dimension)
        retriever = VectorRetriever(vector_store=store, embedding=embedding)

        # Index some texts
        texts = [
            "The cat sat on the mat",
            "The dog ran in the park",
            "A bird flew over the tree",
        ]
        vectors = embedding.embed(texts)
        store.add(vectors, ["doc-0", "doc-1", "doc-2"])

        # Retrieve
        results = retriever.retrieve("cat", top_k=2)
        assert len(results) == 2
        assert results[0]["id"] == "doc-0"

    def test_retrieve_empty_store(self) -> None:
        """Test retrieval from empty store."""
        embedding = BGEmbedding()
        store = FaissStore(dimension=embedding.dimension)
        retriever = VectorRetriever(vector_store=store, embedding=embedding)

        results = retriever.retrieve("query", top_k=5)
        assert results == []
