"""Base reranker interface."""

from abc import ABC, abstractmethod
from typing import List


class BaseReranker(ABC):
    """Abstract base class for rerankers."""

    @abstractmethod
    def rerank(self, query: str, documents: List[str]) -> List[tuple[int, float]]:
        """Rerank documents based on relevance to the query.

        Args:
            query: The search query.
            documents: List of document texts to rerank.

        Returns:
            List of (index, score) tuples, sorted by score descending.
            Index corresponds to the position in the input documents list.
        """
        ...
