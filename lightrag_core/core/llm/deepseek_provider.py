"""DeepSeek LLM provider implementation."""

import logging
from typing import Optional

import httpx

from lightrag_core.core import BaseLLM

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseLLM):
    """LLM provider using DeepSeek API (OpenAI-compatible format)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
        timeout: int = 120,
    ) -> None:
        import os

        self._api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
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
            RuntimeError: If API key is not configured or the API request fails.
        """
        if not self._api_key:
            raise RuntimeError(
                "DeepSeek API key not configured. "
                "Set LIGHTRAG_LLM_API_KEY environment variable or api_key in config.yaml."
            )

        try:
            client = self._get_client()
            response = client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"])
        except RuntimeError:
            raise
        except Exception as e:
            logger.error("DeepSeek API request failed: %s", e)
            raise RuntimeError(f"DeepSeek API request failed: {e}") from e

    def __del__(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
