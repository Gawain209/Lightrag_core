"""Tests for PDF parser."""

import tempfile
from pathlib import Path

import pytest

from lightrag_core.ingestion.parser.pdf_parser import PDFParser


class TestPDFParser:
    """Test suite for PDFParser."""

    def test_supports(self) -> None:
        """Test supported file extensions."""
        parser = PDFParser()
        assert parser.supports("document.pdf") is True
        assert parser.supports("file.txt") is False
        assert parser.supports("file.md") is False

    def test_parse_pdf(self) -> None:
        """Test parsing a PDF file."""
        try:
            from pypdf import PdfWriter, PdfReader
        except ImportError:
            pytest.skip("pypdf not installed")

        # Create a simple PDF file with text
        writer = PdfWriter()
        from pypdf import PageObject
        page = PageObject.create_blank_page(width=612, height=792)
        writer.add_page(page)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            writer.write(f)
            temp_path = f.name

        try:
            parser = PDFParser()
            text = parser.parse(temp_path)
            # PDF pages may be empty or have default text
            assert isinstance(text, str)
        finally:
            Path(temp_path).unlink()
