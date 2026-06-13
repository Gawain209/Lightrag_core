# LightRAG-Core Architecture

## Design Goals

系统设计目标：

* Lightweight
* Extensible
* Portable
* Provider-Based
* Plugin-Based

---

## High-Level Architecture

User Query

↓

Query Engine

↓

Retriever

↓

Reranker

↓

Context Builder

↓

Prompt Builder

↓

LLM Provider

↓

Response

---

## Core Modules

### Embedding Layer

负责：

文本 → 向量

抽象接口：

BaseEmbedding

实现：

* BGEEmbedding
* OllamaEmbedding
* OpenAIEmbedding

---

### Vector Store Layer

负责：

向量存储与检索

抽象接口：

BaseVectorStore

实现：

* FaissStore
* QdrantStore

---

### Retriever Layer

负责：

知识召回

抽象接口：

BaseRetriever

实现：

* VectorRetriever
* BM25Retriever
* HybridRetriever

推荐默认：

HybridRetriever

---

### Reranker Layer

负责：

结果重排序

抽象接口：

BaseReranker

实现：

* BGEReranker
* CrossEncoderReranker

---

### Context Builder

负责：

构建最终上下文。

职责：

* 去重
* 聚合
* 长度控制
* Token 控制

---

### Prompt Builder

负责：

构建 Prompt。

支持：

* Jinja2
* F-string

---

### LLM Provider

抽象接口：

BaseLLM

实现：

* OllamaProvider
* OpenAIProvider
* DeepSeekProvider

---

## Index Pipeline

Document

↓

Parser

↓

Cleaner

↓

Chunker

↓

Embedding

↓

Vector Store

---

## Query Pipeline

Question

↓

Query Rewrite

↓

Hybrid Retrieve

↓

Rerank

↓

Context Build

↓

Prompt Build

↓

LLM Generate

↓

Answer

---

## Plugin System

所有插件通过 Registry 注册。

支持：

* Embedding Plugin
* Retriever Plugin
* Reranker Plugin
* LLM Plugin
* Parser Plugin

动态加载：

importlib

---

## Deployment Modes

### Library Mode

Python SDK

### Server Mode

REST API

### Docker Mode

Container Deployment

三种模式共用同一套核心代码。
