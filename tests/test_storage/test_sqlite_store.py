"""Tests for SQLite metadata storage."""

import os
import tempfile

import pytest

from lightrag_core.storage.metadata.sqlite_store import SQLiteStore


class TestSQLiteStore:
    """Test suite for SQLiteStore."""

    def test_create_and_get_knowledge_base(self) -> None:
        """Test creating and retrieving a knowledge base."""
        db_path = tempfile.mktemp(suffix=".db")

        store = SQLiteStore(db_path=db_path)
        store.create_knowledge_base("kb-1", "Test KB", "Description")

        kb = store.get_knowledge_base("kb-1")
        assert kb is not None
        assert kb["name"] == "Test KB"
        assert kb["description"] == "Description"

        store.close()
        os.unlink(db_path)

    def test_create_and_get_document(self) -> None:
        """Test creating and retrieving a document."""
        db_path = tempfile.mktemp(suffix=".db")

        store = SQLiteStore(db_path=db_path)
        store.create_knowledge_base("kb-1", "Test KB")
        store.create_document("doc-1", "kb-1", "Title", "txt", "Content")

        doc = store.get_document("doc-1")
        assert doc is not None
        assert doc["title"] == "Title"
        assert doc["content"] == "Content"

        store.close()
        os.unlink(db_path)
