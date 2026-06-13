"""Tests for LLM integration."""

from fastapi.testclient import TestClient

from lightrag_core.api.main import app


class TestLLMIntegration:
    """Test suite for LLM integration.

    Uses mock_llm fixture to avoid dependency on external LLM services.
    """

    def test_query_returns_answer(self, mock_llm) -> None:
        """Test that query endpoint returns an answer (mock LLM)."""
        client = TestClient(app)

        client.post("/index", json={
            "kb_id": "test-kb-llm",
            "texts": [
                "Python is a programming language created by Guido van Rossum.",
                "Python is widely used for web development, data science, and AI.",
            ],
        })

        response = client.post("/query", json={
            "kb_id": "test-kb-llm",
            "query": "What is Python?",
            "top_k": 2,
        })
        assert response.status_code == 200
        result = response.json()
        assert result["query"] == "What is Python?"
        assert "answer" in result
        assert result["answer"] != ""
        assert len(result["sources"]) > 0

    def test_query_with_sources(self, mock_llm) -> None:
        """Test that query returns sources with content (mock LLM)."""
        client = TestClient(app)

        client.post("/index", json={
            "kb_id": "test-kb-llm-sources",
            "texts": [
                "The cat sat on the mat.",
                "The dog ran in the park.",
            ],
        })

        response = client.post("/query", json={
            "kb_id": "test-kb-llm-sources",
            "query": "cat",
            "top_k": 2,
        })
        assert response.status_code == 200
        result = response.json()
        assert len(result["sources"]) > 0
        assert result["sources"][0]["content"] != ""
