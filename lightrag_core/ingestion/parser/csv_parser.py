"""CSV file parser implementation."""

import csv
import io
from pathlib import Path

from lightrag_core.ingestion.parser import BaseParser


class CSVParser(BaseParser):
    """Parser for CSV files.

    Converts rows to text lines with column headers as prefix.
    """

    SUPPORTED_EXTENSIONS = {".csv"}

    def parse(self, file_path: str | Path) -> str:
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")

        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return ""

        headers = rows[0] if rows else []
        lines: list[str] = []

        for row in rows[1:]:
            parts = [f"{headers[i]}: {row[i]}" for i in range(min(len(headers), len(row))) if row[i].strip()]
            if parts:
                lines.append("; ".join(parts))

        return "\n".join(lines)

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
