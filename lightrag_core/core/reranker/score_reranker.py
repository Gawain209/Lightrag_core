"""Simple score-based reranker implementation."""

from typing import List

import numpy as np

from lightrag_core.core.reranker import BaseReranker


class ScoreReranker(BaseReranker):
    """Simple reranker using dot product similarity.

    Uses the same embedding model to compute query-document similarity.
    Falls back to random scores if embedding is not available.
    """

    def __init__(self, embedding_dimension: int = 1024) -> None:
        """Initialize the score reranker.

        Args:
            embedding_dimension: Dimension of the embedding vectors.
        """
        self._dimension = embedding_dimension
        self._embedding = None

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer("BAAI/bge-reranker-base")
            self._embedding = self._model.encode
        except ImportError:
            pass

    def rerank(self, query: str, documents: List[str]) -> List[tuple[int, float]]:
        """Rerank documents based on relevance to the query.

        Args:
            query: The search query.
            documents: List of document texts to rerank.

        Returns:
            List of (index, score) tuples, sorted by score descending.
        """
        if not documents:
            return []

        if self._embedding is not None:
            # Compute cross-encoder scores
            pairs = [[query, doc] for doc in documents]
            scores = self._model.predict(pairs)
            indexed_scores = [(i, float(score)) for i, score in enumerate(scores)]
            return sorted(indexed_scores, key=lambda x: x[1], reverse=True)

        # Fallback: random scores
        rng = np.random.default_rng(seed=42)
        scores = [(i, float(rng.random())) for i in range(len(documents))]
        return sorted(scores, key=lambda x: x[1], reverse=True)
