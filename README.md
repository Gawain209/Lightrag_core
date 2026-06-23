# LightRAG-Core

LightRAG-Core is a lightweight, extensible RAG framework built with Python and FastAPI.

LightRAG-Core 是一个基于 Python 和 FastAPI 构建的轻量级、可扩展的 RAG 框架。

The project focuses on reusable RAG framework capabilities rather than a full application platform. It does not depend on LangChain, LlamaIndex, or Haystack. The current MVP supports text/document ingestion (txt, md, pdf, docx, doc, csv, json, html, xlsx), chunking, embedding (BGE-M3), hybrid retrieval (Vector + BM25 + RRF fusion), dynamic relevance-based retrieval with CrossEncoder score threshold (BGE-Reranker), FAISS-based vector search, SQLite metadata storage, pluggable LLM providers, REST APIs, and a Gradio Web UI.

项目专注于可复用的 RAG 框架能力，而非完整的应用平台。不依赖 LangChain、LlamaIndex 或 Haystack。当前 MVP 支持文本/文档导入（txt、md、pdf、docx、doc、csv、json、html、xlsx）、分块、向量嵌入（BGE-M3）、混合检索（向量 + BM25 + RRF 融合）、基于 CrossEncoder 评分阈值的动态相关性检索（BGE-Reranker）、FAISS 向量检索、SQLite 元数据存储、可插拔 LLM 提供商、REST API 以及 Gradio Web UI。

## Security Use Case

This project can be used as the foundation for an enterprise security knowledge-base assistant. A key optimization is **dynamic relevance-based retrieval**: instead of returning a fixed number of results (e.g., top-5), the system uses CrossEncoder score thresholding to include ALL strongly relevant items and exclude weak ones. This is critical for compliance auditing and security policy enumeration — you don't want to miss a single compliance requirement buried in the sources.

本项目可作为企业安全知识库助手的基础框架。核心优化之一是**动态相关性检索**：不返回固定数量的结果（如 top-5），而是使用 CrossEncoder 评分阈值，纳入全部强相关条目、过滤弱相关噪音。这对合规审计和安全规范条目罗列至关重要 —— 不应遗漏任何一项来源中的合规要求。

Example scenario / 示例场景：

- Security policy Q&A — 安全策略问答
- **Compliance requirement enumeration** — 合规要求条目完整罗列
- **Security baseline checklist generation** — 安全基线清单自动生成
- Incident response procedure lookup — 应急响应流程查询
- Vulnerability handling SOP retrieval — 漏洞处理 SOP 检索
- Compliance document search — 合规文档搜索
- Internal security standard explanation — 内部安全规范解读

A security team can index documents such as password policies, emergency response playbooks, vulnerability remediation guides, baseline hardening standards, and compliance requirements. Users can then ask natural-language questions and receive LLM-generated answers with source references.

安全团队可导入密码策略、应急响应预案、漏洞修复指南、基线加固标准、合规要求等文档，用户通过自然语言提问即可获取 LLM 生成的答案及来源引用。

## Project Status

LightRAG-Core is currently an MVP / early-stage framework prototype.

LightRAG-Core 当前处于 MVP / 早期框架原型阶段。

Verified capabilities / 已验证能力：

- FastAPI service startup — 服务启动
- Health check endpoint — 健康检查
- Text indexing and query flow — 文本索引与查询流水线
- Hybrid retrieval (Vector + BM25 + RRF fusion) — 混合检索（向量 + BM25 + RRF 融合）
- CrossEncoder reranking (BGE-Reranker) — CrossEncoder 重排序
- Dynamic relevance-based retrieval with score threshold — 基于评分阈值的动态相关性检索
- SQLite metadata storage — SQLite 元数据存储
- FAISS vector store — FAISS 向量存储
- Knowledge-base filtering — 知识库过滤
- Document upload for 9 file formats (txt, md, pdf, docx, doc, csv, json, html, xlsx) — 9 种文件格式上传
- LLM provider abstraction — LLM 提供商抽象
- Core interface abstraction — 核心接口抽象
- Gradio Web UI (chat, file upload, KB management) — Gradio Web UI（对话、文件上传、知识库管理）
- Unit tests (68 tests covering core, storage, API, ingestion) — 68 项单元测试

Known limitations / 已知局限：

- Real semantic search requires `sentence-transformers` and the BGE-M3 model.（真正的语义检索需安装 `sentence-transformers` 和 BGE-M3 模型）
- Reranking requires `sentence-transformers` and the BGE-Reranker CrossEncoder model.（重排序需安装 `sentence-transformers` 和 BGE-Reranker CrossEncoder 模型）
- Without a configured LLM provider, `/query` can retrieve sources but cannot generate final answers.（未配置 LLM 时 `/query` 可检索来源但无法生成答案）
- PDF parsing is experimental due to pypdf limitations with presentation-oriented PDFs.（PDF 解析因 pypdf 对展示型 PDF 的限制，当前为实验性功能）
- Authentication, authorization, rate limiting, and multi-tenant security controls are not implemented yet.（认证、授权、速率限制、多租户安全控制尚未实现）
- Qdrant support is planned but not implemented as the default vector backend.（Qdrant 支持已规划但尚未作为默认向量后端）
- The top-level Python RAG facade is not yet exposed as a stable public API.（顶层 Python RAG 门面尚未作为稳定公开 API 暴露）

## Tech Stack

| Component | Technology |
| --- | --- |
| Runtime / 运行时 | Python 3.12+ |
| API | FastAPI |
| Metadata store / 元数据存储 | SQLite |
| Vector store / 向量存储 | FAISS |
| Embedding / 向量嵌入 | BGE-M3 via `sentence-transformers` |
| Reranking / 重排序 | BGE-Reranker CrossEncoder via `sentence-transformers` |
| Retrieval / 检索 | Hybrid (Vector + BM25 + RRF fusion) |
| LLM providers | Ollama, DeepSeek / OpenAI-compatible API |
| Parsers / 解析器 | Text/Markdown, PDF, DOCX, DOC, CSV, JSON, HTML, XLSX |
| Deployment / 部署 | Docker, Docker Compose |

## Architecture

LightRAG-Core follows a framework-first design. Core capabilities are accessed through interfaces so that concrete implementations can be replaced later.

LightRAG-Core 遵循"框架优先"设计理念。核心能力均通过接口访问，具体实现可随时替换。

```text
Indexing pipeline:

Document
  -> Parser (txt/md/pdf/docx/doc/csv/json/html/xlsx)
  -> Chunker
  -> Embedding
  -> VectorStore + SQLite metadata + BM25 index

Query pipeline (dynamic relevance-based):

Question
  -> Embedding
  -> Hybrid Retrieval (Vector + BM25 + RRF fusion, expanded candidate pool)
  -> Rerank (BGE-Reranker CrossEncoder with score threshold filtering)
  -> Fallback (top-3 if threshold filters all)
  -> Cap to max results
  -> Context Builder (list all relevant items)
  -> LLM Provider
  -> Answer + Sources
```

Core abstractions / 核心抽象：

```python
from lightrag_core import BaseEmbedding, BaseLLM, BaseRetriever, BaseVectorStore
```

Implemented components / 已实现组件：

| Capability | Current implementation |
| --- | --- |
| Embedding | `BGEmbedding` |
| Vector store / 向量存储 | `FaissStore` |
| Retriever / 检索器 | `VectorRetriever`, `BM25Retriever`, `HybridRetriever` |
| Reranker / 重排序 | `ScoreReranker` (BGE-Reranker CrossEncoder) |
| LLM provider | `OllamaProvider`, `DeepSeekProvider` |
| Metadata store / 元数据存储 | `SQLiteStore` |
| Chunker / 分块器 | `FixedSizeChunker` |
| Parser / 解析器 | `TextParser`, `PDFParser`, `WordParser`, `DocParser`, `CSVParser`, `JSONParser`, `HTMLParser`, `XlsxParser` |

## Quick Start / 快速开始

### 1. Install Dependencies / 安装依赖

```bash
pip install -r requirements.txt
```

For real semantic retrieval, install `sentence-transformers`:

如需真正的语义检索，请安装 `sentence-transformers`：

```bash
pip install sentence-transformers
```

The first run with BGE-M3 may download a large model.

首次运行 BGE-M3 时会下载较大的模型文件。

### 2. Configure LLM Provider / 配置 LLM 提供商

Do not write real API keys into source files.

切勿将真实 API key 写入源码文件。

For PowerShell / PowerShell 用户：

```powershell
$env:LIGHTRAG_LLM_PROVIDER="deepseek"
$env:LIGHTRAG_LLM_MODEL="deepseek-chat"
$env:LIGHTRAG_LLM_API_KEY = Read-Host "Enter API Key"
```

For Bash / Bash 用户：

```bash
export LIGHTRAG_LLM_PROVIDER="deepseek"
export LIGHTRAG_LLM_MODEL="deepseek-chat"
export LIGHTRAG_LLM_API_KEY="your-api-key"
```

For local Ollama / 本地 Ollama 用户：

```powershell
$env:LIGHTRAG_LLM_PROVIDER="ollama"
$env:LIGHTRAG_LLM_MODEL="llama3"
```

Make sure the Ollama service is running before using the Ollama provider.

使用 Ollama 前请确保 Ollama 服务已在运行。

### 3. Start the API Service / 启动 API 服务

```bash
uvicorn lightrag_core.api.main:app --host 127.0.0.1 --port 8000
```

### 4. Launch the Web UI / 启动 Web UI (Gradio)

```bash
python -m lightrag_core.ui.gradio_app
```

This starts both the FastAPI server and the Gradio Web UI at `http://127.0.0.1:7860`. The UI provides chat (with a Max Results slider to control the answer cap), file upload (.txt / .md / .pdf / .docx / .doc / .csv / .json / .html / .xlsx), and knowledge base management. No need to start uvicorn separately — the UI embeds the API server.

此命令同时启动 FastAPI 服务端和 Gradio Web UI（地址 `http://127.0.0.1:7860`）。UI 提供对话（含 Max Results 滑块控制返回条目上限）、文件上传（.txt / .md / .pdf / .docx / .doc / .csv / .json / .html / .xlsx）和知识库管理功能。无需单独启动 uvicorn——UI 内嵌了 API 服务。

To connect the UI to an already-running API server instead:

如需将 UI 连接到已在运行的 API 服务：

```bash
$env:LIGHTRAG_API_BASE="http://127.0.0.1:8000"
python -m lightrag_core.ui.gradio_app
```

On Windows, environment variables set in shells like Git Bash may not propagate to Python subprocesses. If the API key is not detected, use PowerShell or set it inline:

Windows 上，Git Bash 等 shell 中设置的环境变量可能无法传递到 Python 子进程。如果 API key 未被检测到，请使用 PowerShell 或内联设置：

```powershell
$env:LIGHTRAG_LLM_API_KEY="your-api-key"
python -m lightrag_core.ui.gradio_app
```

### 5. Health Check / 健康检查

```bash
curl http://127.0.0.1:8000/health
```

Expected response / 预期响应：

```json
{"status":"ok","version":"0.1.0"}
```

## API Examples / API 示例

### Create a Knowledge Base / 创建知识库

```bash
curl -X POST http://127.0.0.1:8000/knowledge-bases \
  -H "Content-Type: application/json" \
  -d '{"name":"security-policy"}'
```

### Index Text / 索引文本

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "<KB_ID>",
    "title": "security-policy",
    "content": "Privileged accounts must enable MFA and use separate administrator identities.\n\nCritical vulnerabilities must be triaged within 24 hours and remediated according to SLA."
  }'
```

### Upload a Text Document / 上传文本文档

```bash
curl -X POST "http://127.0.0.1:8000/documents/upload?kb_id=<KB_ID>" \
  -F "file=@policy.txt"
```

Supported formats in the MVP / MVP 支持的文件格式：

- `.txt` / `.md` — plain text / Markdown
- `.pdf` — PDF (experimental)
- `.docx` — Word documents (OpenXML)
- `.doc` — Word 97-2003 (legacy binary)
- `.csv` — tabular data
- `.json` — structured data
- `.html` / `.htm` — web pages
- `.xlsx` — Excel spreadsheets

### Query

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "<KB_ID>",
    "query": "What are the security policy requirements?",
    "top_k": 10,
    "score_threshold": 0.3
  }'
```

Parameters:
- `top_k` — maximum results to return (1–200, default 10). Serves as the absolute cap after filtering.
- `score_threshold` — minimum CrossEncoder relevance score (0.0–1.0, optional). If omitted, uses the config default (0.3). Set to `0.0` to disable threshold filtering.

Example response shape:

```json
{
  "query": "What is required for privileged accounts?",
  "answer": "Privileged accounts must enable MFA and use separate administrator identities.",
  "sources": [
    {
      "doc_id": "doc-0",
      "chunk_id": "doc-0",
      "content": "Privileged accounts must enable MFA and use separate administrator identities.",
      "score": 0.98
    }
  ],
  "latency_ms": 245
}
```

## Configuration

Default configuration is stored in `config.yaml`.

Environment variables have higher priority than `config.yaml`.

| Variable | Description |
| --- | --- |
| `LIGHTRAG_LLM_PROVIDER` | `deepseek` or `ollama` |
| `LIGHTRAG_LLM_MODEL` | LLM model name |
| `LIGHTRAG_LLM_BASE_URL` | LLM provider base URL |
| `LIGHTRAG_LLM_API_KEY` | API key for OpenAI-compatible providers |
| `LIGHTRAG_LLM_TEMPERATURE` | Generation temperature |
| `LIGHTRAG_LLM_MAX_TOKENS` | Maximum generation tokens |
| `LIGHTRAG_EMBEDDING_MODEL` | Embedding model name |
| `LIGHTRAG_RERANKER_ENABLED` | Enable/disable reranker (`true` / `false`) |
| `LIGHTRAG_RERANKER_SCORE_THRESHOLD` | CrossEncoder minimum score (0.0–1.0, default: 0.3) |
| `LIGHTRAG_RERANKER_CANDIDATE_MULTIPLIER` | Candidate pool multiplier (default: 3) |
| `LIGHTRAG_DB_PATH` | SQLite database path |
| `LIGHTRAG_DEBUG` | Enable debug logging |
| `LIGHTRAG_API_BASE` | API base URL for Gradio UI (default: `http://127.0.0.1:8000`) |
| `DEEPSEEK_API_KEY` | Alternative fallback for DeepSeek LLM provider |

Example `config.yaml`:

```yaml
llm:
  provider: deepseek
  model: deepseek-chat
  base_url: https://api.deepseek.com/v1
  api_key: ""
  temperature: 0.7
  max_tokens: 1024
  top_p: 0.9
  timeout: 120

embedding:
  model: BAAI/bge-m3
  dimension: 1024

vector_store:
  type: faiss
  dimension: 1024

chunker:
  chunk_size: 500
  chunk_overlap: 50

database:
  type: sqlite
  path: lightrag.db

reranker:
  enabled: true
  model: BAAI/bge-reranker-base
  score_threshold: 0.3
  candidate_multiplier: 3

debug: false
```

## Testing

Run the core test suite:

```bash
python -m pytest tests/test_core -q                  # core: embedding, chunker, retriever, reranker
python -m pytest tests/test_storage/ -q              # FAISS vector store
python -m pytest tests/test_api/ -q                  # API endpoints, pipeline, LLM, file upload
python -m pytest tests/test_ingestion/ -q            # parsers (txt, pdf, docx, csv, json, html)
```

Run lint if `ruff` is installed:

```bash
python -m ruff check .
```

Note: local temporary-directory permissions may affect tests that create temporary files on Windows. If tests fail around `.pytest-tmp`, clean or recreate the temporary test directory before running the full suite.

## Docker

```bash
docker-compose up -d
```

The service starts on port `8000`.

Use environment variables to inject credentials at runtime. Do not hard-code API keys in tracked files.

## Repository Hygiene Before Publishing

Before pushing this project to a public GitHub repository, check that the following files are not committed:

- `.env`
- `*.db`
- `*.sqlite`
- `.pytest_cache/`
- `.pytest-tmp/`
- `__pycache__/`
- `*.pyc`
- local logs
- personal test documents
- real API keys or tokens

Recommended secret scan:

```bash
rg -n "api_key|API_KEY|secret|token|password|Bearer|your-api-key" .
```

The string `your-api-key` should only appear as documentation placeholder text.

## Roadmap

**Completed (MVP):**
- Core interfaces (Embedding, VectorStore, Retriever, LLM, Chunker, Reranker)
- Hybrid retrieval (Vector + BM25 + RRF fusion)
- CrossEncoder reranking (BGE-Reranker)
- Multi-format parsers (txt, md, pdf, docx, doc, csv, json, html, xlsx)
- REST API + Gradio Web UI
- Docker / Docker Compose deployment

**Planned:**
- Stable public Python RAG facade
- Qdrant vector store support
- Better PDF/document parsing pipeline
- Structured error response model
- Authentication and authorization
- Request rate limiting
- Plugin-based security extensions
- Security knowledge-base demo dataset
- Query trace / debug API

## License

MIT
