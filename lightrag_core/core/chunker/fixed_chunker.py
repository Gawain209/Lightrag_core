"""Fixed-size chunker implementation."""

from typing import List

from lightrag_core.core.chunker import BaseChunker


class FixedSizeChunker(BaseChunker):
    """Chunker that splits text into fixed-size chunks with optional overlap."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        """Initialize the chunker.

        Args:
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of overlapping characters between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> List[str]:
        """Split text into fixed-size chunks.

        Args:
            text: Input text to chunk.

        Returns:
            List of text chunks.
        """
        if not text:
            return []

        chunks = []
        step = self.chunk_size - self.chunk_overlap
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += step

        return chunks
