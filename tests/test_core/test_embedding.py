"""Tests for BGEmbedding."""

from lightrag_core.core.embedding.bge_embedding import BGEmbedding


class TestBGEmbedding:
    """Test suite for BGEmbedding."""

    def test_dimension(self) -> None:
        """Test that dimension is set correctly."""
        embedding = BGEmbedding()
        assert embedding.dimension == 1024

    def test_embed_single_text(self) -> None:
        """Test embedding a single text."""
        embedding = BGEmbedding()
        texts = ["Hello world"]
        vectors = embedding.embed(texts)

        assert len(vectors) == 1
        assert len(vectors[0]) == 1024

    def test_embed_multiple_texts(self) -> None:
        """Test embedding multiple texts."""
        embedding = BGEmbedding()
        texts = ["Hello world", "Another text", "Third text"]
        vectors = embedding.embed(texts)

        assert len(vectors) == 3
        for vector in vectors:
            assert len(vector) == 1024

    def test_embed_empty_list(self) -> None:
        """Test embedding an empty list."""
        embedding = BGEmbedding()
        vectors = embedding.embed([])
        assert vectors == []

    def test_vectors_are_normalized(self) -> None:
        """Test that vectors are normalized (unit length)."""
        import numpy as np

        embedding = BGEmbedding()
        texts = ["Test text"]
        vectors = embedding.embed(texts)

        vector = np.array(vectors[0])
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 1e-5
