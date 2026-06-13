# LightRAG-Core

LightRAG-Core is a lightweight, extensible RAG framework built with Python and FastAPI.

The project focuses on reusable RAG framework capabilities rather than a full application platform. It does not depend on LangChain, LlamaIndex, or Haystack. The current MVP supports text/document ingestion, chunking, embedding, FAISS-based vector search, SQLite metadata storage, pluggable LLM providers, and REST APIs.

## Security Use Case

This project can be used as the foundation for an enterprise security knowledge-base assistant.

Example scenario:

- Security policy Q&A
- Incident response procedure lookup
- Vulnerability handling SOP retrieval
- Compliance document search
- Internal security standard explanation

A security team can index documents such as password policies, emergency response playbooks, vulnerability remediation guides, baseline hardening standards, and compliance requirements. Users can then ask natural-language questions and receive LLM-generated answers with source references.

## Project Status

LightRAG-Core is currently an MVP / early-stage framework prototype.

Verified capabilities:

- FastAPI service startup
- Health check endpoint
- Text indexing and query flow
- SQLite metadata storage
- FAISS vector store
- Knowledge-base filtering
- Basic document upload for text and Markdown
- LLM provider abstraction
- Core interface abstraction
- Unit tests for core retrieval, chunking, FAISS, embedding fallback, and API basics

Known limitations:

- Real semantic search requires `sentence-transformers` and the BGE-M3 model.
- Without a configured LLM provider, `/query` can retrieve sources but cannot generate final answers.
- PDF parsing exists but should be treated as experimental in the current MVP.
- Authentication, authorization, rate limiting, and multi-tenant security controls are not implemented yet.
- Qdrant support is planned but not implemented as the default vector backend.
- The top-level Python RAG facade is not yet exposed as a stable public API.

## Tech Stack

- Runtime: Python 3.12+
- API: FastAPI
- Metadata store: SQLite
- Vector store: FAISS
- Embedding: BGE-M3 via `sentence-transformers`
- Reranking: BGE reranker-style component / score reranker prototype
- LLM providers: Ollama, DeepSeek / OpenAI-compatible API
- Deployment: Docker, Docker Compose

## Architecture

LightRAG-Core follows a framework-first design. Core capabilities are accessed through interfaces so that concrete implementations can be replaced later.

```text
Indexing pipeline:

Document
  -> Parser
  -> Chunker
  -> Embedding
  -> VectorStore + SQLite metadata

Query pipeline:

Question
  -> Embedding
  -> Vector Search
  -> Optional BM25 / Hybrid Retrieval
  -> Optional Rerank
  -> Context Builder
  -> LLM Provider
  -> Answer + Sources
```

Core abstractions:

```python
from lightrag_core import BaseEmbedding, BaseLLM, BaseRetriever, BaseVectorStore
```

Implemented components:

| Capability | Current implementation |
| --- | --- |
| Embedding | `BGEmbedding` |
| Vector store | `FaissStore` |
| Retriever | `VectorRetriever`, `BM25Retriever`, `HybridRetriever` |
| LLM provider | `OllamaProvider`, `DeepSeekProvider` |
| Metadata store | `SQLiteStore` |
| Chunker | `FixedSizeChunker` |
| Parser | Text, Markdown, PDF prototype |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

For real semantic retrieval, install `sentence-transformers`:

```bash
pip install sentence-transformers
```

The first run with BGE-M3 may download a large model.

### 2. Configure LLM Provider

Do not write real API keys into source files.

For PowerShell:

```powershell
$env:LIGHTRAG_LLM_PROVIDER="deepseek"
$env:LIGHTRAG_LLM_MODEL="deepseek-chat"
$env:LIGHTRAG_LLM_API_KEY = Read-Host "Enter API Key"
```

For Bash:

```bash
export LIGHTRAG_LLM_PROVIDER="deepseek"
export LIGHTRAG_LLM_MODEL="deepseek-chat"
export LIGHTRAG_LLM_API_KEY="your-api-key"
```

For local Ollama:

```powershell
$env:LIGHTRAG_LLM_PROVIDER="ollama"
$env:LIGHTRAG_LLM_MODEL="llama3"
```

Make sure the Ollama service is running before using the Ollama provider.

### 3. Start the API Service

```bash
uvicorn lightrag_core.api.main:app --host 127.0.0.1 --port 8000
```

### 4. Health Check

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","version":"0.1.0"}
```

## API Examples

### Create a Knowledge Base

```bash
curl -X POST http://127.0.0.1:8000/knowledge-bases \
  -H "Content-Type: application/json" \
  -d '{"name":"security-policy","description":"Enterprise security policy knowledge base"}'
```

### Index Text

```bash
curl -X POST http://127.0.0.1:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "security-policy",
    "texts": [
      "Privileged accounts must enable MFA and use separate administrator identities.",
      "Critical vulnerabilities must be triaged within 24 hours and remediated according to SLA."
    ]
  }'
```

### Upload a Text Document

```bash
curl -X POST "http://127.0.0.1:8000/documents/upload?kb_id=security-policy" \
  -F "file=@policy.txt"
```

Supported formats in the MVP:

- `.txt`
- `.md`
- `.pdf` experimental

### Query

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "security-policy",
    "query": "What is required for privileged accounts?",
    "top_k": 3
  }'
```

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
| `LIGHTRAG_DB_PATH` | SQLite database path |
| `LIGHTRAG_DEBUG` | Enable debug logging |

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

debug: false
```

## Testing

Run the core test suite:

```bash
python -m pytest tests/test_core -q
python -m pytest tests/test_storage/test_faiss_store.py -q
python -m pytest tests/test_api/test_main.py -q
python -m pytest tests/test_api/test_pipeline.py -q
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

- Stable public Python RAG facade
- Qdrant vector store support
- Better PDF/document parsing pipeline
- Structured error response model
- Authentication and authorization
- Request rate limiting
- Plugin-based security extensions
- Security knowledge-base demo dataset
- Dockerized local demo with Ollama

## License

MIT
