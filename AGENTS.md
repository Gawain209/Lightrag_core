# LightRAG-Core

## Project Goal

LightRAG-Core 是一个轻量级、可扩展、可移植的 RAG Framework。

项目目标：

- 从零实现 RAG 内核
- 不依赖 LangChain
- 不依赖 LlamaIndex
- 支持本地部署
- 支持插件扩展
- 支持多知识库
- 支持未来扩展 Agent 能力

参考项目：

- Dify
- RagFlow
- LlamaIndex

但不直接复刻上述项目。

项目定位：

Framework First，Application Second。

即优先建设可复用的 RAG Framework，而非完整 AI 应用平台。

---

## Technology Stack

Runtime

- Python 3.12+

API

- FastAPI

Database

- SQLite

Vector Store

- FAISS（MVP）
- Qdrant（V2）

Embedding

- BGE-M3

Reranker

- BGE Reranker

LLM Provider

- Ollama
- OpenAI Compatible API

Deployment

- Docker

---

## Architecture Principles

### Rule 1

所有核心能力必须抽象为接口。

禁止业务代码直接依赖具体实现。

正确：

BaseEmbedding

错误：

直接调用 BGEEmbedding

---

### Rule 2

向量数据库必须可替换。

禁止业务层直接访问 FAISS。

必须通过：

BaseVectorStore

访问。

---

### Rule 3

LLM 必须 Provider 化。

支持：

- Ollama
- OpenAI
- DeepSeek
- vLLM

统一接口。

---

### Rule 4

插件优先。

新增功能优先通过 Plugin 实现。

避免修改核心代码。

---

### Rule 5

保持轻量化。

禁止引入：

- LangChain
- Haystack

作为核心依赖。

---

## Coding Standards

所有公共类必须：

- 类型注解
- Docstring
- 单元测试

公共接口变更必须：

- 更新文档
- 更新测试

---

## Testing Requirements

所有新模块：

至少包含：

- 正常路径测试
- 异常路径测试

覆盖率目标：

80%+

---

## Definition of Done

功能完成必须满足：

- 代码通过 lint
- pytest 全部通过
- 文档同步更新
- 不破坏公共接口
- 不引入循环依赖
