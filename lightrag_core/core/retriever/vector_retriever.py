"""Vector retriever implementation."""

from typing import Any, Dict, List, Optional

from lightrag_core.core import BaseEmbedding, BaseRetriever, BaseVectorStore


class VectorRetriever(BaseRetriever):
    """Retriever that uses vector similarity search."""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding: BaseEmbedding,
    ) -> None:
        """Initialize the vector retriever.

        Args:
            vector_store: The vector store to search.
            embedding: The embedding provider.
        """
        self._vector_store = vector_store
        self._embedding = embedding

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: The search query.
            top_k: Number of results to return.
            filters: Optional exact-match metadata filters.

        Returns:
            List of retrieval results with content and score.
        """
        query_vectors = self._embedding.embed([query])
        if not query_vectors:
            return []

        results = self._vector_store.search(query_vectors[0], top_k=top_k, filters=filters)

        return [
            {
                "id": doc_id,
                "score": score,
            }
            for doc_id, score in results
        ]
