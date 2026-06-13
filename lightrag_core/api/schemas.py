"""Pydantic schemas for API requests and responses."""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    kb_id: str = Field("default", description="Knowledge base ID")
    query: str = Field(..., min_length=1, description="The search query")
    top_k: int = Field(5, ge=1, le=100, description="Number of results to return")


class SourceResult(BaseModel):
    """A single source result from retrieval."""

    doc_id: str = Field(..., description="Document ID")
    chunk_id: str = Field(..., description="Chunk ID")
    content: str = Field(..., description="Retrieved content")
    score: float = Field(..., description="Retrieval score")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceResult] = Field(default_factory=list, description="Source documents")
    latency_ms: int = Field(0, description="Query latency in milliseconds")


class IndexRequest(BaseModel):
    """Request model for index endpoint."""

    kb_id: str = Field("default", description="Knowledge base ID")
    texts: List[str] = Field(..., min_length=1, description="Texts to index")
    ids: Optional[List[str]] = Field(None, description="Optional IDs for the texts")


class IndexResponse(BaseModel):
    """Response model for index endpoint."""

    task_id: str = Field(..., description="Indexing task ID")
    status: str = Field(..., description="Indexing status")
    total_documents: int = Field(0, description="Total documents indexed")
    document_ids: List[str] = Field(default_factory=list, description="IDs of indexed documents")


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""

    kb_id: str = Field("default", description="Knowledge base ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")


class DocumentResponse(BaseModel):
    """Response model for document operations."""

    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    status: str = Field(..., description="Document status")
    created_at: str = Field(..., description="Creation timestamp")


class KnowledgeBaseCreateRequest(BaseModel):
    """Request model for creating a knowledge base."""

    name: str = Field(..., min_length=1, max_length=100, description="Knowledge base name")
    description: Optional[str] = Field(None, description="Optional description")


class KnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base operations."""

    id: str = Field(..., description="Knowledge base ID")
    name: str = Field(..., description="Knowledge base name")
    description: Optional[str] = Field(None, description="Description")
    created_at: str = Field("", description="Creation timestamp")
    updated_at: str = Field("", description="Last update timestamp")


class KnowledgeBaseListResponse(BaseModel):
    """Response model for listing knowledge bases."""

    items: List[KnowledgeBaseResponse] = Field(default_factory=list, description="Knowledge bases")
    total: int = Field(0, description="Total count")
