"""Ollama LLM provider implementation."""

import logging
from typing import Optional

import httpx

from lightrag_core.core import BaseLLM

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLM):
    """LLM provider using Ollama API."""

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout)
        return self._client

    def generate(self, prompt: str) -> str:
        """Generate a response from the LLM.

        Raises:
            RuntimeError: If the Ollama API request fails.
        """
        try:
            client = self._get_client()
            response = client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", ""))
        except Exception as e:
            logger.error("Ollama API request failed (url=%s): %s", self._base_url, e)
            raise RuntimeError(
                f"Ollama API unavailable at {self._base_url}. "
                f"Ensure the Ollama service is running. Error: {e}"
            ) from e

    def __del__(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
