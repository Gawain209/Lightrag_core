"""Pytest configuration for local test isolation."""

import os
import tempfile
from pathlib import Path

import pytest

_TEMP_ROOT = Path(__file__).resolve().parents[1] / ".test-tmp"
_TEMP_DIR = _TEMP_ROOT / "temp"
_TEMP_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("TMP", str(_TEMP_DIR))
os.environ.setdefault("TEMP", str(_TEMP_DIR))
os.environ.setdefault("TMPDIR", str(_TEMP_DIR))
tempfile.tempdir = str(_TEMP_DIR)


class DummyLLM:
    """LLM stub for API tests that don't require a real LLM."""

    def generate(self, prompt: str) -> str:
        return "mock answer"


@pytest.fixture
def mock_llm(monkeypatch):
    """Fixture that replaces the global LLM singleton with a mock."""
    import lightrag_core.api.main as api_main

    monkeypatch.setattr(api_main, "_llm", DummyLLM())
    yield
