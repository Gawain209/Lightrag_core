"""Base document parser interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, file_path: str | Path) -> str:
        """Parse a document and return its text content.

        Args:
            file_path: Path to the document file.

        Returns:
            Extracted text content.
        """
        ...

    @abstractmethod
    def supports(self, file_path: str | Path) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to the document file.

        Returns:
            True if supported, False otherwise.
        """
        ...
