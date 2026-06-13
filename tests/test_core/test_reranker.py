"""Tests for reranker."""

from lightrag_core.core.reranker.score_reranker import ScoreReranker


class TestScoreReranker:
    """Test suite for ScoreReranker."""

    def test_rerank_basic(self) -> None:
        """Test basic reranking."""
        reranker = ScoreReranker()
        documents = [
            "Python is a programming language",
            "JavaScript is used for web development",
            "Rust provides memory safety",
        ]

        results = reranker.rerank("programming language", documents)
        assert len(results) == 3
        # Results should be sorted by score descending
        assert results[0][1] >= results[1][1]
        assert results[1][1] >= results[2][1]

    def test_rerank_empty(self) -> None:
        """Test reranking empty documents."""
        reranker = ScoreReranker()
        results = reranker.rerank("query", [])
        assert results == []

    def test_rerank_indices(self) -> None:
        """Test that returned indices are correct."""
        reranker = ScoreReranker()
        documents = ["doc-0", "doc-1", "doc-2"]

        results = reranker.rerank("query", documents)
        indices = [idx for idx, _ in results]
        assert sorted(indices) == [0, 1, 2]
