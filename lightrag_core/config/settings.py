"""Configuration module for LightRAG-Core.

Supports loading configuration from:
- Environment variables (highest priority)
- config.yaml file
- Default values (lowest priority)
"""

import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM configuration."""

    provider: str = "ollama"  # ollama, deepseek
    model: str = "llama3"
    base_url: str = "http://localhost:11434"
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 0.9
    timeout: int = 120


@dataclass
class EmbeddingConfig:
    """Embedding configuration."""

    model: str = "BAAI/bge-m3"
    dimension: int = 1024


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""

    type: str = "faiss"  # faiss, qdrant
    dimension: int = 1024
    index_path: str = ""


@dataclass
class ChunkerConfig:
    """Chunker configuration."""

    chunk_size: int = 500
    chunk_overlap: int = 50


@dataclass
class RerankerConfig:
    """Reranker configuration."""

    enabled: bool = True
    model: str = "BAAI/bge-reranker-base"


@dataclass
class DatabaseConfig:
    """Database configuration."""

    type: str = "sqlite"
    path: str = "lightrag.db"


@dataclass
class AppConfig:
    """Application configuration."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    chunker: ChunkerConfig = field(default_factory=ChunkerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    reranker: RerankerConfig = field(default_factory=RerankerConfig)
    debug: bool = False


def _load_yaml_config(path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except ImportError:
        logger.warning("PyYAML not installed. Install with: pip install pyyaml")
        return {}


def _apply_env_overrides(config: AppConfig) -> AppConfig:
    """Apply environment variable overrides."""
    # LLM
    if llm_provider := os.getenv("LIGHTRAG_LLM_PROVIDER"):
        config.llm.provider = llm_provider
    if llm_model := os.getenv("LIGHTRAG_LLM_MODEL"):
        config.llm.model = llm_model
    if llm_base_url := os.getenv("LIGHTRAG_LLM_BASE_URL"):
        config.llm.base_url = llm_base_url
    if api_key := os.getenv("LIGHTRAG_LLM_API_KEY"):
        config.llm.api_key = api_key
    if temp := os.getenv("LIGHTRAG_LLM_TEMPERATURE"):
        config.llm.temperature = float(temp)
    if max_tokens := os.getenv("LIGHTRAG_LLM_MAX_TOKENS"):
        config.llm.max_tokens = int(max_tokens)
    if top_p := os.getenv("LIGHTRAG_LLM_TOP_P"):
        config.llm.top_p = float(top_p)

    # Embedding
    if emb_model := os.getenv("LIGHTRAG_EMBEDDING_MODEL"):
        config.embedding.model = emb_model

    # Vector Store
    if vs_type := os.getenv("LIGHTRAG_VECTOR_STORE_TYPE"):
        config.vector_store.type = vs_type

    # Database
    if db_path := os.getenv("LIGHTRAG_DB_PATH"):
        config.database.path = db_path

    # Reranker
    if reranker_enabled := os.getenv("LIGHTRAG_RERANKER_ENABLED"):
        config.reranker.enabled = reranker_enabled.lower() in ("true", "1", "yes")

    # Debug
    if debug := os.getenv("LIGHTRAG_DEBUG"):
        config.debug = debug.lower() in ("true", "1", "yes")

    return config


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load application configuration.

    Priority:
    1. Environment variables (highest)
    2. config.yaml file
    3. Default values (lowest)

    Args:
        config_path: Path to YAML config file. If None, tries to find config.yaml.

    Returns:
        Application configuration.
    """
    config = AppConfig()

    # Load from YAML file
    if config_path is None:
        # Try to find config.yaml in current directory or project root
        possible_paths = ["config.yaml", "config.yml", "../config.yaml"]
        for path in possible_paths:
            if Path(path).exists():
                config_path = path
                break

    if config_path and Path(config_path).exists():
        yaml_data = _load_yaml_config(config_path)

        # Apply YAML config
        if llm_data := yaml_data.get("llm"):
            for key, value in llm_data.items():
                if hasattr(config.llm, key):
                    setattr(config.llm, key, value)

        if emb_data := yaml_data.get("embedding"):
            for key, value in emb_data.items():
                if hasattr(config.embedding, key):
                    setattr(config.embedding, key, value)

        if vs_data := yaml_data.get("vector_store"):
            for key, value in vs_data.items():
                if hasattr(config.vector_store, key):
                    setattr(config.vector_store, key, value)

        if chunker_data := yaml_data.get("chunker"):
            for key, value in chunker_data.items():
                if hasattr(config.chunker, key):
                    setattr(config.chunker, key, value)

        if db_data := yaml_data.get("database"):
            for key, value in db_data.items():
                if hasattr(config.database, key):
                    setattr(config.database, key, value)

        if reranker_data := yaml_data.get("reranker"):
            for key, value in reranker_data.items():
                if hasattr(config.reranker, key):
                    setattr(config.reranker, key, value)

        if "debug" in yaml_data:
            config.debug = yaml_data["debug"]

    # Apply environment variable overrides (highest priority)
    config = _apply_env_overrides(config)

    return config


# Global config instance
_config: Optional[AppConfig] = None
_config_lock = threading.Lock()


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        with _config_lock:
            if _config is None:
                _config = load_config()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from files and environment."""
    global _config
    with _config_lock:
        _config = load_config()
    return _config
