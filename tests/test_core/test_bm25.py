"""Tests for BM25 retriever."""

from lightrag_core.core.retriever.bm25_retriever import BM25Retriever


class TestBM25Retriever:
    """Test suite for BM25Retriever."""

    def test_retrieve_basic(self) -> None:
        """Test basic BM25 retrieval."""
        retriever = BM25Retriever()
        retriever.add_document("doc-1", "The cat sat on the mat")
        retriever.add_document("doc-2", "The dog ran in the park")
        retriever.add_document("doc-3", "A bird flew over the tree")

        results = retriever.retrieve("cat", top_k=2)
        assert len(results) > 0
        assert results[0]["id"] == "doc-1"

    def test_retrieve_empty_index(self) -> None:
        """Test retrieval from empty index."""
        retriever = BM25Retriever()
        results = retriever.retrieve("query", top_k=5)
        assert results == []

    def test_retrieve_no_match(self) -> None:
        """Test retrieval with no matching terms."""
        retriever = BM25Retriever()
        retriever.add_document("doc-1", "The cat sat on the mat")
        results = retriever.retrieve("xyz123", top_k=5)
        assert results == []
