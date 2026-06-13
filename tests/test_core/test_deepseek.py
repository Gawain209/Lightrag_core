"""Tests for DeepSeek provider."""

import pytest

from lightrag_core.core.llm.deepseek_provider import DeepSeekProvider


class TestDeepSeekProvider:
    """Test suite for DeepSeekProvider."""

    def test_init_without_api_key(self) -> None:
        """Test that generate raises RuntimeError when no API key is configured."""
        provider = DeepSeekProvider(api_key="")
        with pytest.raises(RuntimeError, match="API key not configured"):
            provider.generate("Hello")

    def test_generate_raises_on_invalid_key(self) -> None:
        """Test that generate raises RuntimeError when API returns an error."""
        provider = DeepSeekProvider(api_key="invalid-key")
        with pytest.raises(RuntimeError, match="API request failed"):
            provider.generate("Hello")
