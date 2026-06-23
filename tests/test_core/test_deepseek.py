"""Tests for DeepSeek provider."""

import pytest

from lightrag_core.core.llm.deepseek_provider import DeepSeekProvider


class FakeResponse:
    """Minimal httpx response stand-in for provider tests."""

    def __init__(self, payload=None, error: Exception | None = None) -> None:
        self._payload = payload or {}
        self._error = error

    def raise_for_status(self) -> None:
        """Raise the configured error, if any."""
        if self._error is not None:
            raise self._error

    def json(self) -> dict:
        """Return the configured JSON payload."""
        return self._payload


class FakeClient:
    """Minimal httpx client stand-in for provider tests."""

    def __init__(self, response: FakeResponse) -> None:
        self._response = response

    def post(self, *args, **kwargs) -> FakeResponse:
        """Return the configured fake response."""
        return self._response


class TestDeepSeekProvider:
    """Test suite for DeepSeekProvider."""

    def test_init_without_api_key(self) -> None:
        """Test that generate raises RuntimeError when no API key is configured."""
        provider = DeepSeekProvider(api_key="")
        with pytest.raises(RuntimeError, match="API key not configured"):
            provider.generate("Hello")

    def test_generate_raises_on_api_error(self) -> None:
        """Test that generate raises RuntimeError when API returns an error."""
        provider = DeepSeekProvider(api_key="invalid-key")
        provider._client = FakeClient(FakeResponse(error=Exception("401 Unauthorized")))

        with pytest.raises(RuntimeError, match="API request failed"):
            provider.generate("Hello")

    def test_generate_returns_content(self) -> None:
        """Test that generate returns content from an OpenAI-compatible response."""
        provider = DeepSeekProvider(api_key="fake-key")
        provider._client = FakeClient(
            FakeResponse(
                payload={
                    "choices": [
                        {"message": {"content": "Hello from DeepSeek"}},
                    ],
                }
            )
        )

        assert provider.generate("Hello") == "Hello from DeepSeek"
