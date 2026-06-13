"""Tests for chunkers."""

from lightrag_core.core.chunker.fixed_chunker import FixedSizeChunker


class TestFixedSizeChunker:
    """Test suite for FixedSizeChunker."""

    def test_chunk_simple(self) -> None:
        """Test basic chunking."""
        chunker = FixedSizeChunker(chunk_size=10, chunk_overlap=2)
        text = "Hello world, this is a test for chunking."
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(len(chunk) <= 10 for chunk in chunks)

    def test_chunk_empty(self) -> None:
        """Test chunking empty text."""
        chunker = FixedSizeChunker(chunk_size=10, chunk_overlap=2)
        chunks = chunker.chunk("")
        assert chunks == []

    def test_chunk_overlap(self) -> None:
        """Test that chunks have overlap."""
        chunker = FixedSizeChunker(chunk_size=20, chunk_overlap=5)
        text = "a" * 50
        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        # Check overlap: last part of chunk 0 should match first part of chunk 1
        if len(chunks) >= 2:
            assert chunks[0][-5:] == chunks[1][:5]
