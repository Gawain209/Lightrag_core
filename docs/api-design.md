# API Design

## Overview

LightRAG-Core 提供 RESTful API，支持两种使用模式：

- **Server Mode**: 独立运行的 FastAPI 服务
- **Library Mode**: 直接导入 Python 包使用

本文档描述 Server Mode 的 API 设计。

---

## Base URL

```
http://localhost:8000/api/v1
```

> **Note (MVP):** The current v0.1.0 API uses root-level paths (e.g. `/query`, `/knowledge-bases`, `/documents`) without the `/api/v1` prefix. The `/api/v1` prefix scheme documented here is the target for a future version. Refer to the code in `lightrag_core/api/main.py` for the current actual routes.

---

## Authentication

MVP 阶段暂不支持认证。

Phase 3 计划支持：
- API Key
- Bearer Token

---

## Content-Type

所有请求和响应均为 JSON：

```
Content-Type: application/json
```

---

## 通用响应格式

### 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 错误响应

```json
{
  "code": 400,
  "message": "error description",
  "detail": { ... }
}
```

---

## 错误码定义

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 200 | 200 | Success |
| 400 | 400 | Bad Request |
| 404 | 404 | Not Found |
| 422 | 422 | Validation Error |
| 500 | 500 | Internal Server Error |
| 500 | 501 | Not Implemented |

---

## API Endpoints

### 1. Knowledge Base Management

#### Create Knowledge Base

```http
POST /knowledge-bases
```

**Request:**

```json
{
  "name": "my-docs",
  "description": "My documentation knowledge base"
}
```

**Response:**

```json
{
  "code": 200,
  "data": {
    "id": "kb-123",
    "name": "my-docs",
    "description": "My documentation knowledge base",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

#### List Knowledge Bases

```http
GET /knowledge-bases
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | int | No | Page number (default: 1) |
| page_size | int | No | Items per page (default: 20, max: 100) |

**Response:**

```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

#### Get Knowledge Base

```http
GET /knowledge-bases/{kb_id}
```

#### Delete Knowledge Base

```http
DELETE /knowledge-bases/{kb_id}
```

---

### 2. Document Management

#### Upload Document

```http
POST /knowledge-bases/{kb_id}/documents
```

**Request (multipart/form-data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | Document file (pdf, docx, txt, md) |
| title | string | No | Document title |

**Response:**

```json
{
  "code": 200,
  "data": {
    "id": "doc-456",
    "kb_id": "kb-123",
    "title": "document.pdf",
    "source": "upload",
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### List Documents

```http
GET /knowledge-bases/{kb_id}/documents
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | int | No | Page number |
| page_size | int | No | Items per page |
| status | string | No | Filter by status: pending, processing, completed, failed |

#### Get Document

```http
GET /knowledge-bases/{kb_id}/documents/{doc_id}
```

#### Delete Document

```http
DELETE /knowledge-bases/{kb_id}/documents/{doc_id}
```

---

### 3. Indexing

#### Trigger Index

```http
POST /knowledge-bases/{kb_id}/index
```

**Request:**

```json
{
  "chunk_size": 500,
  "chunk_overlap": 50,
  "embedding_model": "BGE-M3"
}
```

**Response:**

```json
{
  "code": 200,
  "data": {
    "task_id": "idx-789",
    "status": "running",
    "total_documents": 10,
    "processed_documents": 3,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Get Index Status

```http
GET /knowledge-bases/{kb_id}/index/{task_id}
```

---

### 4. Query

#### Simple Query

```http
POST /query
```

**Request:**

```json
{
  "kb_id": "kb-123",
  "query": "What is RAG?",
  "top_k": 5,
  "retriever": "hybrid",
  "rerank": true
}
```

**Response:**

```json
{
  "code": 200,
  "data": {
    "answer": "RAG (Retrieval-Augmented Generation) is...",
    "sources": [
      {
        "doc_id": "doc-456",
        "chunk_id": "chunk-001",
        "content": "...",
        "score": 0.95,
        "rerank_score": 0.92
      }
    ],
    "latency_ms": 1234
  }
}
```

#### Streaming Query

```http
POST /query/stream
```

**Request:**

```json
{
  "kb_id": "kb-123",
  "query": "What is RAG?",
  "top_k": 5
}
```

**Response:**

SSE (Server-Sent Events) stream:

```
data: {"type": "retrieval", "content": "..."}

data: {"type": "chunk", "content": "RAG"}

data: {"type": "chunk", "content": " (Retrieval"}

data: {"type": "done"}
```

---

### 5. Debug / Trace

#### Get Retrieval Trace

```http
GET /query/{query_id}/trace
```

**Response:**

```json
{
  "code": 200,
  "data": {
    "query_id": "qry-abc",
    "query": "What is RAG?",
    "retrieval_results": [
      {
        "chunk_id": "chunk-001",
        "vector_score": 0.95,
        "bm25_score": 0.88,
        "rerank_score": 0.92,
        "selected": true
      }
    ],
    "final_context": "...",
    "prompt": "...",
    "latency_ms": 1234
  }
}
```

---

## Pagination

所有列表接口支持统一分页：

**Request:**

```
GET /knowledge-bases?page=2&page_size=50
```

**Response:**

```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "page_size": 50,
  "total_pages": 3
}
```

---

## Rate Limiting

Phase 3 计划支持：

- 默认限制：100 requests/minute
- 按 API Key 限制

---

## Versioning

API 版本通过 URL 路径控制：

```
/api/v1/...
/api/v2/...
```

MVP 仅实现 v1。
