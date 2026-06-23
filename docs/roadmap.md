# Roadmap

## Vision

构建开发者优先的 RAG Framework。

目标：

成为轻量级、可嵌入、可扩展的 RAG 基础设施。

---

# Phase 1

MVP

状态：

✅ 已完成

功能：

* ✅ 文档导入
* ✅ Fixed Chunk
* ✅ BGE Embedding
* ✅ FAISS 检索
* ✅ Ollama 集成
* ✅ Query API

交付：

Library Mode

---

# Phase 2

Core RAG

状态：

✅ 已完成

新增：

* ✅ BM25
* ✅ Hybrid Search
* ✅ Reranker (BGE-Reranker CrossEncoder)
* ✅ Context Builder
* ✅ 多知识库
* ✅ 多格式解析器 (txt, md, pdf, docx, csv, json, html)
* ✅ Gradio Web UI

交付：

Server Mode

---

# Phase 3

Developer Platform

预计：

1~2 个月

新增：

* Plugin System
* Provider Registry
* 配置中心
* Retrieval Debug API
* Query Trace

目标：

形成完整框架。

---

# Phase 4

Enterprise Ready

预计：

2 个月

新增：

* Qdrant
* Redis
* 多租户
* ACL
* 审计日志

目标：

支持企业场景。

---

# Phase 5

Agent Extension

预计：

长期

新增：

Tool Interface

Tool Registry

Workflow Engine

Agent Runtime

支持：

* Search Tool
* SQL Tool
* API Tool

---

# Phase 6

Advanced RAG

研究方向：

Graph RAG

Multi-Hop RAG

Agentic RAG

Self-RAG

Adaptive RAG

---

# Non Goals

当前阶段不实现：

* Dify 式工作流编辑器
* 插件市场
* SaaS 平台
* 多组织运营后台

优先保证：

RAG 核心能力质量。

---

# Success Metrics

MVP：

单机运行

< 1GB 系统资源占用

---

V1：

支持 10 万级 Chunk

稳定检索

---

V2：

支持企业级部署

---

长期目标：

形成可独立演进的 LightRAG-Core 生态。
