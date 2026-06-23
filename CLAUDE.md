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
python -m lightrag_core.ui.gradio_app       # Gradio Web UI (内嵌 API + UI 一键启动)
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
| Web UI | `lightrag_core/ui/` | Gradio Web UI（chat、文件上传、知识库管理），thin layer on API |

### 数据流

**索引流水线:** Document → Parser → Chunker → Embedding → VectorStore + SQLite metadata

**查询流水线:** Question → Embedding → VectorSearch → (可选 BM25/Hybrid) → (可选 Rerank) → Context → LLM → Answer + Sources

### API 层关键模式

- **双重检查锁定（double-checked locking）** 的延迟单例初始化（`_get_embedding()`、`_get_vector_store()` 等），通过 `_init_lock` / `_chunk_lock` 保证线程安全
- **LRU 缓存** `_ChunkCache`（max 10000 条），缓存未命中回退到 SQLite
- **启动时** 急切初始化 embedding 以提前暴露模型加载失败
- 测试中通过 `conftest.py` 的 `mock_llm` fixture 替换全局 `_llm` 单例

### Gradio UI 架构

UI 层（`lightrag_core/ui/gradio_app.py`）是 API 之上的薄封装，**不含任何 RAG 逻辑**。所有操作通过 `_api()` → httpx → FastAPI 端点完成：
- `rag_chat()` → `POST /query`
- `upload_file()` / `index_text()` → `POST /documents` 或 `/documents/upload`
- `create_kb()` → `POST /knowledge-bases`

`_client` 默认超时 120s。`main()` 在 daemon 线程启动 uvicorn 后启动 Gradio，UI 默认端口 7860。

Gradio 6.x API 变更（从 5.x 升级时需注意）：
- `gr.ChatInterface` 移除: `type`, `clear_btn`, `retry_btn`, `undo_btn`, `placeholder`
- `gr.Blocks()` 移除 `css` 和 `theme` 参数，改为 `demo.launch(css=..., theme=...)`

## 配置

- 配置文件: `config.yaml`（git 未跟踪），模板见 `config.example.yaml`
- 环境变量优先级高于 YAML: `LIGHTRAG_LLM_PROVIDER`、`LIGHTRAG_LLM_MODEL`、`LIGHTRAG_LLM_API_KEY`、`LIGHTRAG_LLM_BASE_URL`、`LIGHTRAG_EMBEDDING_MODEL`、`LIGHTRAG_DB_PATH`、`LIGHTRAG_DEBUG`、`LIGHTRAG_API_BASE`、`DEEPSEEK_API_KEY` 等
- API key 等敏感信息只能通过环境变量注入，禁止写入 `config.yaml` 或源码
- 编程方式使用: `from lightrag_core.config.settings import get_config`

### 配置加载时序（重要）

`load_config()` 内部使用模块级 `_config` 单例缓存，**第一次调用之后环境变量的变更不会生效**。因此环境变量必须在任何 `lightrag_core` 模块导入之前设置。

Windows 上 Git Bash 设置的环境变量（`export LIGHTRAG_LLM_API_KEY=xxx`）**不会传递到 Python 子进程**。解决方案：
- 使用 PowerShell 的 `$env:LIGHTRAG_LLM_API_KEY="xxx"` 在启动 Python 前设置
- 或在启动脚本中通过 `os.environ["LIGHTRAG_LLM_API_KEY"] = "xxx"` 在 import 之前设置

### DeepSeek API Key 回退链

`DeepSeekProvider.__init__` 的 api_key 回退：参数 `api_key` → 环境变量 `DEEPSEEK_API_KEY`（注意不是 `LIGHTRAG_LLM_API_KEY`）。配置系统通过 `LIGHTRAG_LLM_API_KEY` → `config.llm.api_key` 这条链路将 key 传给构造函数参数，因此正常情况下设置 `LIGHTRAG_LLM_API_KEY` 即可。`DEEPSEEK_API_KEY` 仅作为不通过配置系统的备用回退。

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
