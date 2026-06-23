"""HTML file parser implementation."""

import logging
from pathlib import Path

from lightrag_core.ingestion.parser import BaseParser

logger = logging.getLogger(__name__)


class HTMLParser(BaseParser):
    """Parser for HTML files (.html, .htm).

    Uses beautifulsoup4 to extract visible text.
    """

    SUPPORTED_EXTENSIONS = {".html", ".htm"}

    def __init__(self) -> None:
        try:
            from bs4 import BeautifulSoup  # noqa: F401

            self._available = True
        except ImportError:
            logger.warning("beautifulsoup4 not installed — HTML parsing unavailable")
            self._available = False

    def parse(self, file_path: str | Path) -> str:
        if not self._available:
            raise RuntimeError(
                "beautifulsoup4 is not installed. Install with: pip install beautifulsoup4"
            )

        from bs4 import BeautifulSoup

        path = Path(file_path)
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")

        for tag in soup(["script", "style", "meta", "noscript", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
