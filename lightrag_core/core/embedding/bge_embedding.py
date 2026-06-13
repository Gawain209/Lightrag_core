"""BGE-M3 embedding provider implementation."""

import logging
from typing import List

import numpy as np

from lightrag_core.core import BaseEmbedding

logger = logging.getLogger(__name__)


class BGEmbedding(BaseEmbedding):
    """Embedding provider using BGE-M3 model.

    Uses sentence-transformers as the backend.
    Falls back to random vectors if model is not available.
    """

    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        """Initialize the BGE embedding provider.

        Args:
            model_name: Name of the sentence-transformers model to use.
        """
        self._model_name = model_name
        self._model = None
        self._dimension = 1024  # BGE-M3 default dimension

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()
        except ImportError:
            logger.warning("sentence-transformers not installed — using random embeddings")
        except Exception as e:
            logger.warning("Failed to load model %s: %s — using random embeddings", model_name, e)

    @property
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        return self._dimension

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts into vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        if self._model is not None:
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()

        # Fallback: generate random normalized vectors
        rng = np.random.default_rng(seed=42)
        vectors = rng.random((len(texts), self._dimension)).astype(np.float32)
        # Normalize to unit length
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / norms
        return vectors.tolist()
