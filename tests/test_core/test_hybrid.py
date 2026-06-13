"""Tests for hybrid retriever."""

from lightrag_core.core.embedding.bge_embedding import BGEmbedding
from lightrag_core.core.retriever.hybrid_retriever import HybridRetriever
from lightrag_core.storage.vectorstore.faiss_store import FaissStore


class TestHybridRetriever:
    """Test suite for HybridRetriever."""

    def test_retrieve(self) -> None:
        """Test hybrid retrieval."""
        embedding = BGEmbedding()
        store = FaissStore(dimension=embedding.dimension)
        retriever = HybridRetriever(vector_store=store, embedding=embedding)

        # Index documents
        texts = [
            "The cat sat on the mat",
            "The dog ran in the park",
            "A bird flew over the tree",
        ]
        vectors = embedding.embed(texts)
        store.add(vectors, ["doc-0", "doc-1", "doc-2"])

        # Add to BM25
        for i, text in enumerate(texts):
            retriever.add_document(f"doc-{i}", text)

        # Retrieve
        results = retriever.retrieve("cat", top_k=2)
        assert len(results) > 0
        assert results[0]["id"] == "doc-0"

    def test_retrieve_empty(self) -> None:
        """Test retrieval from empty index."""
        embedding = BGEmbedding()
        store = FaissStore(dimension=embedding.dimension)
        retriever = HybridRetriever(vector_store=store, embedding=embedding)

        results = retriever.retrieve("query", top_k=5)
        assert results == []
