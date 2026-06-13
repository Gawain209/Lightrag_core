"""PDF document parser implementation."""

from pathlib import Path

from lightrag_core.ingestion.parser import BaseParser


class PDFParser(BaseParser):
    """Parser for PDF files.

    Uses pypdf as the backend for text extraction.
    Falls back to error message if pypdf is not installed.
    """

    SUPPORTED_EXTENSIONS = {".pdf"}

    def __init__(self) -> None:
        """Initialize the PDF parser."""
        self._pypdf_available = False
        try:
            from pypdf import PdfReader

            self._PdfReader = PdfReader
            self._pypdf_available = True
        except ImportError:
            pass

    def parse(self, file_path: str | Path) -> str:
        """Parse a PDF file and return its text content.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text content.

        Raises:
            RuntimeError: If pypdf is not installed.
        """
        if not self._pypdf_available:
            raise RuntimeError(
                "pypdf is not installed. "
                "Install it with: pip install pypdf"
            )

        reader = self._PdfReader(str(file_path))
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        return "\n\n".join(text_parts)

    def supports(self, file_path: str | Path) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to the document file.

        Returns:
            True if the file extension is supported.
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
