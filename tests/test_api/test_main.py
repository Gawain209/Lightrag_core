"""Tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from lightrag_core.api.main import app


class TestAPI:
    """Test suite for API endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"

    def test_create_knowledge_base(self, client: TestClient) -> None:
        """Test creating a knowledge base."""
        response = client.post("/knowledge-bases", json={
            "name": "test-kb",
            "description": "Test knowledge base",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-kb"
        assert data["description"] == "Test knowledge base"
        assert data["created_at"] != ""
        assert data["created_at"] != "2024-01-01T00:00:00Z"

    def test_list_knowledge_bases(self, client: TestClient) -> None:
        """Test listing knowledge bases."""
        response = client.get("/knowledge-bases")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 0

    def test_upload_document(self, client: TestClient) -> None:
        """Test uploading a document."""
        response = client.post("/documents", json={
            "title": "Test Document",
            "content": "This is a test document.",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Document"
        assert data["status"] == "completed"
        assert data["created_at"] != ""
        assert data["created_at"] != "2024-01-01T00:00:00Z"

    def test_index(self, client: TestClient) -> None:
        """Test indexing documents."""
        response = client.post("/index", json={
            "texts": [
                "The cat sat on the mat",
                "The dog ran in the park",
            ],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_documents"] == 2
        assert len(data["document_ids"]) == 2

    def test_index_and_query(self, client: TestClient, mock_llm) -> None:
        """Test indexing and querying."""
        response = client.post("/index", json={
            "texts": [
                "The cat sat on the mat",
                "The dog ran in the park",
            ],
        })
        assert response.status_code == 200

        response = client.post("/query", json={
            "query": "cat",
            "top_k": 2,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "cat"
        assert len(data["sources"]) <= 2
