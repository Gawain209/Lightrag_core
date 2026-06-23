"""Hybrid retriever combining vector and BM25 search.

Uses Reciprocal Rank Fusion (RRF) to merge results.
"""

from typing import Any, Dict, List, Optional

from lightrag_core.core import BaseEmbedding, BaseRetriever, BaseVectorStore
from lightrag_core.core.retriever.bm25_retriever import BM25Retriever
from lightrag_core.core.retriever.vector_retriever import VectorRetriever


class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining vector and BM25 search.

    Uses Reciprocal Rank Fusion (RRF) to merge results:
    score = Σ(1 / (k + rank))
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding: BaseEmbedding,
        bm25: BM25Retriever | None = None,
        k: int = 60,
    ) -> None:
        """Initialize the hybrid retriever.

        Args:
            vector_store: Vector store for semantic search.
            embedding: Embedding provider.
            bm25: BM25 retriever for keyword search.
            k: RRF constant (default 60).
        """
        self._vector_retriever = VectorRetriever(
            vector_store=vector_store,
            embedding=embedding,
        )
        self._bm25 = bm25 or BM25Retriever()
        self._k = k

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] | None = None) -> None:
        """Add a document to the BM25 index.

        Args:
            doc_id: Document ID.
            text: Document text.
            metadata: Optional metadata for filtering (e.g. kb_id).
        """
        self._bm25.add_document(doc_id, text, metadata=metadata)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using hybrid search.

        Args:
            query: Search query.
            top_k: Number of results to return.
            filters: Optional exact-match metadata filters passed to both retrievers.

        Returns:
            List of retrieval results with fused scores.
        """
        # Get vector results
        vector_results = self._vector_retriever.retrieve(
            query, top_k=top_k * 2, filters=filters
        )

        # Get BM25 results
        bm25_results = self._bm25.retrieve(query, top_k=top_k * 2, filters=filters)

        # RRF fusion
        scores: Dict[str, float] = {}

        # Add vector scores
        for rank, result in enumerate(vector_results):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (self._k + rank + 1)

        # Add BM25 scores
        for rank, result in enumerate(bm25_results):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (self._k + rank + 1)

        # Sort by RRF score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [
            {"id": doc_id, "score": score}
            for doc_id, score in sorted_results
        ]
