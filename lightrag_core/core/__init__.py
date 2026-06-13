"""Base interfaces for the RAG framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseEmbedding(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts into vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embedding vectors."""
        ...


class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def add(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add vectors to the store.

        Args:
            vectors: List of embedding vectors.
            ids: Corresponding IDs for the vectors.
            metadatas: Optional metadata for each vector.
        """
        ...

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[tuple[str, float]]:
        """Search for the top-k most similar vectors.

        Args:
            query_vector: The query embedding vector.
            top_k: Number of results to return.
            filters: Optional exact-match metadata filters.

        Returns:
            List of (id, score) tuples.
        """
        ...

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete vectors by IDs.

        Args:
            ids: List of vector IDs to delete.
        """
        ...


class BaseRetriever(ABC):
    """Abstract base class for retrievers."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: The search query.
            top_k: Number of results to return.

        Returns:
            List of retrieval results.
        """
        ...


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt.

        Returns:
            Generated text response.
        """
        ...
