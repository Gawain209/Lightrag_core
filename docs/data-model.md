# Data Model

## Design Principles

数据与向量必须解耦。

任何时候都必须保留：

* 原始文档
* Chunk
* Metadata

禁止只保存向量。

---

## KnowledgeBase

知识库。

字段：

id

name

description

created_at

updated_at

---

## Document

原始文档。

字段：

id

kb_id

title

source

content

version

created_at

updated_at

---

说明：

source 用于记录：

* pdf
* docx
* markdown
* html

来源。

version 用于重建索引。

---

## Chunk

文档切片。

字段：

id

doc_id

chunk_index

content

token_count

metadata

---

metadata 示例：

{
"page":12,
"section":"Deployment",
"tenant":"default"
}

---

## EmbeddingRecord

向量索引映射。

字段：

chunk_id

vector_id

embedding_model

created_at

---

作用：

支持：

* 重建索引
* 模型升级
* 向量迁移

---

## QueryLog

查询日志。

字段：

id

query

answer

latency_ms

retrieval_count

created_at

---

用途：

分析：

* 命中率
* 召回质量
* 用户行为

---

## RetrievalTrace

调试数据。

字段：

id

query_id

chunk_id

score

rerank_score

selected

---

用于：

Retrieval Debug API

查看：

* 召回结果
* 重排序结果
* 最终上下文

---

## Relationships

KnowledgeBase

1 → N

Document

Document

1 → N

Chunk

Chunk

1 → 1

EmbeddingRecord

QueryLog

1 → N

RetrievalTrace

---

## Future Extension

预留字段：

tenant_id

用于：

* 多租户
* 企业隔离

预留 ACL 模型：

支持未来权限系统。
