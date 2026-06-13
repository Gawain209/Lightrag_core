"""Tests for configuration module."""

import os
from pathlib import Path

import pytest

from lightrag_core.config.settings import AppConfig, LLMConfig, load_config


class TestConfig:
    """Test suite for configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = load_config("__missing_config__.yaml")
        assert isinstance(config, AppConfig)
        assert config.llm.provider == "ollama"
        assert config.llm.model == "llama3"
        assert config.llm.temperature == 0.7
        assert config.llm.max_tokens == 1024
        assert config.chunker.chunk_size == 500
        assert config.database.path == "lightrag.db"

    def test_env_override(self) -> None:
        """Test environment variable override."""
        # Set env vars
        os.environ["LIGHTRAG_LLM_PROVIDER"] = "deepseek"
        os.environ["LIGHTRAG_LLM_MODEL"] = "deepseek-chat"
        os.environ["LIGHTRAG_LLM_TEMPERATURE"] = "0.5"
        os.environ["LIGHTRAG_LLM_MAX_TOKENS"] = "2048"

        config = load_config()
        assert config.llm.provider == "deepseek"
        assert config.llm.model == "deepseek-chat"
        assert config.llm.temperature == 0.5
        assert config.llm.max_tokens == 2048

        # Clean up
        del os.environ["LIGHTRAG_LLM_PROVIDER"]
        del os.environ["LIGHTRAG_LLM_MODEL"]
        del os.environ["LIGHTRAG_LLM_TEMPERATURE"]
        del os.environ["LIGHTRAG_LLM_MAX_TOKENS"]

    def test_yaml_config(self, tmp_path: Path) -> None:
        """Test loading from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
llm:
  provider: deepseek
  model: deepseek-chat
  temperature: 0.3
  max_tokens: 512

chunker:
  chunk_size: 1000
  chunk_overlap: 100
""")

        config = load_config(str(config_file))
        assert config.llm.provider == "deepseek"
        assert config.llm.model == "deepseek-chat"
        assert config.llm.temperature == 0.3
        assert config.llm.max_tokens == 512
        assert config.chunker.chunk_size == 1000
        assert config.chunker.chunk_overlap == 100
