"""Text file parser implementation."""

from pathlib import Path

from lightrag_core.ingestion.parser import BaseParser


class TextParser(BaseParser):
    """Parser for plain text files (.txt, .md)."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown"}

    def parse(self, file_path: str | Path) -> str:
        """Parse a text file and return its content.

        Args:
            file_path: Path to the text file.

        Returns:
            File content as string.
        """
        path = Path(file_path)
        return path.read_text(encoding="utf-8")

    def supports(self, file_path: str | Path) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to the document file.

        Returns:
            True if the file extension is supported.
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
