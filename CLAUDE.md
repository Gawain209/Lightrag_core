# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目概述

LightRAG-Core 是一个轻量级、可扩展的 RAG 框架（MVP 阶段，v0.1.0）。Python 3.12+ + FastAPI，不依赖 LangChain / LlamaIndex / Haystack。

## 常用命令

### 安装与运行

```bash
pip install -r requirements.txt
pip install sentence-transformers          # 生产级语义检索所需的模型
uvicorn lightrag_core.api.main:app --host 127.0.0.1 --port 8000
```

### 测试

```bash
python -m pytest tests/test_core -q                            # 核心模块（embedding、chunker、retriever）
python -m pytest tests/test_storage/test_faiss_store.py -q     # FAISS 向量存储
python -m pytest tests/test_api/test_main.py -q                # API 基础端点
python -m pytest tests/test_api/test_pipeline.py -q            # 索引/查询完整流水线
python -m pytest tests/test_api/test_llm.py -q                 # LLM 直接测试
python -m pytest tests/test_api/test_file_upload.py -q         # 文件上传
python -m pytest tests/test_ingestion/ -q                      # 解析器
```

pytest 配置在 `pyproject.toml` 的 `[tool.pytest.ini_options]`，临时目录在 `.pytest-tmp/`。如果临时文件相关测试在 Windows 上失败，删除 `.pytest-tmp/` 后重试。

### 代码质量

```bash
python -m ruff check .        # lint
python -m mypy .              # type check（如已安装 mypy）
python -m black . --check     # 格式检查
```

## 架构

### 核心设计原则（来自 AGENTS.md）

1. **所有核心能力必须抽象为接口** — 业务代码禁止直接依赖具体实现
2. **向量数据库必须可替换** — 必须通过 `BaseVectorStore` 访问，禁止直接依赖 FAISS
3. **LLM 必须 Provider 化** — Ollama / OpenAI / DeepSeek 通过统一接口接入
4. **插件优先** — 新增功能优先通过 Plugin 实现，避免修改核心代码
5. **保持轻量化** — 禁止引入 LangChain、Haystack 作为核心依赖

### 模块结构

| 模块 | 路径 | 职责 |
|------|------|------|
| 基础接口 | `lightrag_core/core/__init__.py` | `BaseEmbedding`、`BaseLLM`、`BaseRetriever`、`BaseVectorStore`、`BaseChunker` |
| Embedding | `lightrag_core/core/embedding/` | `BGEmbedding`（BGE-M3，无模型时回退到随机向量） |
| Chunker | `lightrag_core/core/chunker/` | `FixedSizeChunker`（固定大小 + overlap） |
| Retriever | `lightrag_core/core/retriever/` | `VectorRetriever`、`BM25Retriever`、`HybridRetriever` |
| Reranker | `lightrag_core/core/reranker/` | `ScoreReranker`（原型） |
| LLM | `lightrag_core/core/llm/` | `OllamaProvider`、`DeepSeekProvider`（OpenAI 兼容） |
| 向量存储 | `lightrag_core/storage/vectorstore/` | `FaissStore`（Qdrant 规划中） |
| 元数据存储 | `lightrag_core/storage/metadata/` | `SQLiteStore`（SQLAlchemy ORM） |
| 解析器 | `lightrag_core/ingestion/parser/` | `TextParser`、`PDFParser`（实验性） |
| API | `lightrag_core/api/` | FastAPI 应用 + Pydantic v2 schemas |
| 配置 | `lightrag_core/config/settings.py` | YAML + 环境变量（env 优先级 > YAML > 默认值） |

### 数据流

**索引流水线:** Document → Parser → Chunker → Embedding → VectorStore + SQLite metadata

**查询流水线:** Question → Embedding → VectorSearch → (可选 BM25/Hybrid) → (可选 Rerank) → Context → LLM → Answer + Sources

### API 层关键模式

- **双重检查锁定（double-checked locking）** 的延迟单例初始化（`_get_embedding()`、`_get_vector_store()` 等），通过 `_init_lock` / `_chunk_lock` 保证线程安全
- **LRU 缓存** `_ChunkCache`（max 10000 条），缓存未命中回退到 SQLite
- **启动时** 急切初始化 embedding 以提前暴露模型加载失败
- 测试中通过 `conftest.py` 的 `mock_llm` fixture 替换全局 `_llm` 单例

## 配置

- 配置文件: `config.yaml`（git 未跟踪），模板见 `config.example.yaml`
- 环境变量优先级高于 YAML: `LIGHTRAG_LLM_PROVIDER`、`LIGHTRAG_LLM_MODEL`、`LIGHTRAG_LLM_API_KEY`、`LIGHTRAG_LLM_BASE_URL`、`LIGHTRAG_EMBEDDING_MODEL`、`LIGHTRAG_DB_PATH`、`LIGHTRAG_DEBUG` 等
- API key 等敏感信息只能通过环境变量注入，禁止写入 `config.yaml` 或源码
- 编程方式使用: `from lightrag_core.config.settings import get_config`

## 编码规范

- 公共类必须有类型注解 + Docstring + 单元测试
- 公共接口变更必须同步更新文档和测试
- 所有新模块至少覆盖正常路径和异常路径测试
- Python 3.12+ 语法，类型注解使用 `str | None` 而非 `Optional[str]`
- black 行宽 100，ruff 行宽 100

## Docker

```bash
docker-compose up -d    # 服务启动在 8000 端口，通过环境变量注入 API key
```
