"""Tests for document parsers."""

import tempfile
from pathlib import Path

from lightrag_core.ingestion.parser.text_parser import TextParser


class TestTextParser:
    """Test suite for TextParser."""

    def test_parse_txt(self) -> None:
        """Test parsing a .txt file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, world!")
            temp_path = f.name

        parser = TextParser()
        content = parser.parse(temp_path)
        assert content == "Hello, world!"

        Path(temp_path).unlink()

    def test_parse_md(self) -> None:
        """Test parsing a .md file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Title\n\nContent")
            temp_path = f.name

        parser = TextParser()
        content = parser.parse(temp_path)
        assert content == "# Title\n\nContent"

        Path(temp_path).unlink()

    def test_supports(self) -> None:
        """Test supported file extensions."""
        parser = TextParser()
        assert parser.supports("file.txt") is True
        assert parser.supports("file.md") is True
        assert parser.supports("file.pdf") is False
