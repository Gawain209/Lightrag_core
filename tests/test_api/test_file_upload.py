"""Tests for file upload API."""

import io

import pytest
from fastapi.testclient import TestClient

from lightrag_core.api.main import app


class TestFileUpload:
    """Test suite for file upload endpoints."""

    def test_upload_txt_file(self) -> None:
        """Test uploading a .txt file."""
        client = TestClient(app)

        file_content = b"The cat sat on the mat. The dog ran in the park."
        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            data={"kb_id": "test-kb"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "test.txt"
        assert data["status"] == "completed"
        assert data["created_at"] != ""
        assert data["created_at"] != "2024-01-01T00:00:00Z"

    def test_upload_md_file(self) -> None:
        """Test uploading a .md file."""
        client = TestClient(app)

        file_content = b"# Title\n\nThis is a markdown document."
        response = client.post(
            "/documents/upload",
            files={"file": ("test.md", io.BytesIO(file_content), "text/markdown")},
            data={"kb_id": "test-kb-md"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "test.md"
        assert data["status"] == "completed"

    def test_upload_pdf_file(self) -> None:
        """Test uploading a .pdf file."""
        pytest.importorskip("pypdf")
        from pypdf import PageObject, PdfWriter

        client = TestClient(app)
        pdf = io.BytesIO()
        writer = PdfWriter()
        writer.add_page(PageObject.create_blank_page(width=612, height=792))
        writer.write(pdf)
        pdf.seek(0)

        response = client.post(
            "/documents/upload",
            files={"file": ("test.pdf", pdf, "application/pdf")},
            data={"kb_id": "test-kb-pdf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "test.pdf"
        assert data["status"] == "completed"

    def test_upload_and_query_file(self, mock_llm) -> None:
        """Test uploading a file and querying it."""
        client = TestClient(app)

        file_content = b"Python is a programming language. It is widely used for web development."
        client.post(
            "/documents/upload",
            params={"kb_id": "test-kb-query"},
            files={"file": ("python.txt", io.BytesIO(file_content), "text/plain")},
        )

        response = client.post("/query", json={
            "kb_id": "test-kb-query",
            "query": "programming language",
            "top_k": 2,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "programming language"
        assert len(data["sources"]) > 0
