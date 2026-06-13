"""BM25 keyword-based retriever implementation."""

import math
import re
from collections import Counter
from typing import Any, Dict, List

from lightrag_core.core import BaseRetriever


class BM25Retriever(BaseRetriever):
    """BM25 retriever for keyword-based search.

    Implements the BM25 algorithm for ranking documents based on
    term frequency and inverse document frequency.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize the BM25 retriever.

        Args:
            k1: BM25 parameter (default 1.5).
            b: BM25 parameter (default 0.75).
        """
        self._k1 = k1
        self._b = b
        self._documents: Dict[str, str] = {}  # id -> text
        self._tokenized: Dict[str, List[str]] = {}  # id -> tokens
        self._avg_doc_len = 0.0
        self._total_docs = 0

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words."""
        return re.findall(r"\b\w+\b", text.lower())

    def add_document(self, doc_id: str, text: str) -> None:
        """Add a document to the index.

        Args:
            doc_id: Document ID.
            text: Document text.
        """
        self._documents[doc_id] = text
        tokens = self._tokenize(text)
        self._tokenized[doc_id] = tokens

        # Update average document length
        total_len = sum(len(t) for t in self._tokenized.values())
        self._total_docs = len(self._tokenized)
        self._avg_doc_len = total_len / self._total_docs if self._total_docs > 0 else 0

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve documents using BM25 scoring.

        Args:
            query: Search query.
            top_k: Number of results to return.

        Returns:
            List of retrieval results with scores.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens or not self._documents:
            return []

        # Calculate IDF for each query term
        idf = {}
        for term in set(query_tokens):
            doc_count = sum(1 for tokens in self._tokenized.values() if term in tokens)
            idf[term] = math.log((self._total_docs - doc_count + 0.5) / (doc_count + 0.5) + 1)

        # Score each document
        scores = {}
        for doc_id, tokens in self._tokenized.items():
            score = 0.0
            doc_len = len(tokens)
            token_counts = Counter(tokens)

            for term in query_tokens:
                if term not in idf:
                    continue

                tf = token_counts.get(term, 0)
                numerator = tf * (self._k1 + 1)
                denominator = tf + self._k1 * (1 - self._b + self._b * (doc_len / self._avg_doc_len))
                score += idf[term] * (numerator / denominator)

            if score > 0:
                scores[doc_id] = score

        # Sort by score and return top-k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {"id": doc_id, "score": score}
            for doc_id, score in sorted_results[:top_k]
        ]
