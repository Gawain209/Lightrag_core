"""Cross-encoder based reranker implementation."""

import logging
from typing import List

import numpy as np

from lightrag_core.core.reranker import BaseReranker

logger = logging.getLogger(__name__)


class ScoreReranker(BaseReranker):
    """Reranker using a cross-encoder model (BGE-Reranker).

    Uses sentence_transformers.CrossEncoder to compute relevance scores
    for (query, document) pairs. Falls back to random scores if the
    model is not available.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        """Initialize the score reranker.

        Args:
            model_name: Name of the cross-encoder model to use.
        """
        self._model_name = model_name
        self._model = None

        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(model_name)
            logger.info("Cross-encoder loaded: %s", model_name)
        except ImportError:
            logger.warning("sentence-transformers not installed — using random reranker")
        except Exception as e:
            logger.warning("Failed to load cross-encoder %s: %s — using random reranker", model_name, e)

    def rerank(
        self, query: str, documents: List[str], score_threshold: float = 0.0
    ) -> List[tuple[int, float]]:
        """Rerank documents based on relevance to the query.

        Args:
            query: The search query.
            documents: List of document texts to rerank.
            score_threshold: Minimum relevance score (0-1). Documents below this
                threshold are filtered out. Default 0.0 = no filtering.

        Returns:
            List of (index, score) tuples, sorted by score descending.
            Index corresponds to the position in the input documents list.
        """
        if not documents:
            return []

        if self._model is not None:
            pairs = [[query, doc] for doc in documents]
            scores = self._model.predict(pairs)
            indexed_scores = [(i, float(score)) for i, score in enumerate(scores)]
            indexed_scores.sort(key=lambda x: x[1], reverse=True)
            if score_threshold > 0.0:
                indexed_scores = [(i, s) for i, s in indexed_scores if s >= score_threshold]
            return indexed_scores

        # Fallback: random scores
        rng = np.random.default_rng(seed=42)
        scores = [(i, float(rng.random())) for i in range(len(documents))]
        return sorted(scores, key=lambda x: x[1], reverse=True)
