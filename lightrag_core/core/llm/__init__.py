"""LLM module for LightRAG-Core."""

from lightrag_core.core.llm.deepseek_provider import DeepSeekProvider
from lightrag_core.core.llm.ollama_provider import OllamaProvider

__all__ = ["OllamaProvider", "DeepSeekProvider"]
