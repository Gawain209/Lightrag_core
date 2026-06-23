"""JSON file parser implementation."""

import json
from pathlib import Path

from lightrag_core.ingestion.parser import BaseParser


class JSONParser(BaseParser):
    """Parser for JSON files.

    Handles both JSON objects and arrays of objects.
    """

    SUPPORTED_EXTENSIONS = {".json"}

    def parse(self, file_path: str | Path) -> str:
        path = Path(file_path)
        data = json.loads(path.read_text(encoding="utf-8"))

        if isinstance(data, list):
            lines: list[str] = []
            for item in data:
                if isinstance(item, dict):
                    parts = [f"{k}: {v}" for k, v in item.items() if v is not None]
                    lines.append("; ".join(parts))
                else:
                    lines.append(str(item))
            return "\n".join(lines)

        if isinstance(data, dict):
            return self._flatten_dict(data)

        return str(data)

    def _flatten_dict(self, d: dict, prefix: str = "") -> str:
        lines: list[str] = []
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                lines.append(self._flatten_dict(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        lines.append(self._flatten_dict(item, f"{full_key}[{i}]"))
                    else:
                        lines.append(f"{full_key}[{i}]: {item}")
            else:
                lines.append(f"{full_key}: {value}")
        return "\n".join(lines)

    def supports(self, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
