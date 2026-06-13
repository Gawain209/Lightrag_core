"""Tests for the integrated document processing pipeline."""

from fastapi.testclient import TestClient

from lightrag_core.api import main as api_main
from lightrag_core.api.main import app


class TestDocumentPipeline:
    """Test suite for the complete document processing pipeline."""

    def test_upload_and_query_document(self, mock_llm) -> None:
        """Test uploading a document and querying it."""
        client = TestClient(app)

        response = client.post("/documents", json={
            "kb_id": "test-kb-pipeline-new",
            "title": "Test Document",
            "content": "The cat sat on the mat. The dog ran in the park.",
            "metadata": {},
        })
        assert response.status_code == 200
        doc = response.json()
        assert doc["title"] == "Test Document"
        assert doc["status"] == "completed"

        response = client.post("/query", json={
            "kb_id": "test-kb-pipeline-new",
            "query": "cat",
            "top_k": 2,
        })
        assert response.status_code == 200
        result = response.json()
        assert result["query"] == "cat"
        assert len(result["sources"]) > 0
        assert result["sources"][0]["content"] != ""

    def test_index_and_query(self, mock_llm) -> None:
        """Test indexing texts and querying."""
        client = TestClient(app)

        response = client.post("/index", json={
            "kb_id": "test-kb-2",
            "texts": [
                "Python is a programming language",
                "JavaScript is used for web development",
                "Rust provides memory safety",
            ],
        })
        assert response.status_code == 200
        index_result = response.json()
        assert index_result["status"] == "completed"
        assert index_result["total_documents"] == 3
        assert len(index_result["document_ids"]) == 3

        response = client.post("/query", json={
            "kb_id": "test-kb-2",
            "query": "programming language",
            "top_k": 2,
        })
        assert response.status_code == 200
        result = response.json()
        assert result["query"] == "programming language"
        assert len(result["sources"]) > 0

    def test_query_isolated_by_kb_id(self, monkeypatch) -> None:
        """Test that query results are filtered to the requested knowledge base."""
        api_main._embedding = None
        api_main._vector_store = None
        api_main._retriever = None
        api_main._chunk_cache.clear()
        from tests.conftest import DummyLLM
        monkeypatch.setattr(api_main, "_llm", DummyLLM())

        client = TestClient(app)

        client.post("/index", json={
            "kb_id": "kb-source-only",
            "ids": ["source-doc"],
            "texts": ["Only the source knowledge base contains this sentence."],
        })

        response = client.post("/query", json={
            "kb_id": "kb-empty-target",
            "query": "source knowledge base sentence",
            "top_k": 5,
        })

        assert response.status_code == 200
        result = response.json()
        assert result["sources"] == []

    def test_create_knowledge_base(self) -> None:
        """Test creating a knowledge base."""
        client = TestClient(app)

        response = client.post("/knowledge-bases", json={
            "name": "My KB",
            "description": "My knowledge base",
        })
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "My KB"
        assert result["description"] == "My knowledge base"
