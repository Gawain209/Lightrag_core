"""FastAPI application for LightRAG-Core."""

import logging
import threading
import time
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile

from lightrag_core.api.schemas import (
    DocumentResponse,
    DocumentUploadRequest,
    IndexRequest,
    IndexResponse,
    KnowledgeBaseCreateRequest,
    KnowledgeBaseListResponse,
    KnowledgeBaseResponse,
    QueryRequest,
    QueryResponse,
    SourceResult,
)
from lightrag_core.config.settings import get_config
from lightrag_core.core.chunker.fixed_chunker import FixedSizeChunker
from lightrag_core.core.embedding.bge_embedding import BGEmbedding
from lightrag_core.core.llm.deepseek_provider import DeepSeekProvider
from lightrag_core.core.llm.ollama_provider import OllamaProvider
from lightrag_core.core.retriever.hybrid_retriever import HybridRetriever
from lightrag_core.core.retriever.vector_retriever import VectorRetriever
from lightrag_core.core.reranker.score_reranker import ScoreReranker
from lightrag_core.ingestion.parser.pdf_parser import PDFParser
from lightrag_core.ingestion.parser.text_parser import TextParser
from lightrag_core.ingestion.parser.docx_parser import WordParser
from lightrag_core.ingestion.parser.csv_parser import CSVParser
from lightrag_core.ingestion.parser.json_parser import JSONParser
from lightrag_core.ingestion.parser.html_parser import HTMLParser
from lightrag_core.ingestion.parser.doc_parser import DocParser
from lightrag_core.ingestion.parser.xlsx_parser import XlsxParser
from lightrag_core.storage.metadata.sqlite_store import SQLiteStore
from lightrag_core.storage.vectorstore.faiss_store import FaissStore

logger = logging.getLogger(__name__)

app = FastAPI(title="LightRAG-Core", version="0.1.0")

# Global state for MVP
_db_store: Optional[SQLiteStore] = None
_embedding: Optional[BGEmbedding] = None
_vector_store: Optional[FaissStore] = None
_retriever: Optional[HybridRetriever] = None
_chunker: Optional[FixedSizeChunker] = None
_llm: Optional[OllamaProvider] = None
_reranker: Optional[ScoreReranker] = None

# Thread-safety: locks for lazy singleton init and shared mutable state.
# Lazy initializers call each other, so the init lock must be re-entrant.
_init_lock = threading.RLock()
_chunk_lock = threading.Lock()

# Bounded LRU cache for chunk content to prevent unbounded memory growth.
# Misses fall back to SQLite (chunks are always persisted at index time).
_CHUNK_CACHE_MAXSIZE = 10000


class _ChunkCache:
    """Thread-safe, size-bounded LRU cache for chunk content.

    Must be accessed under _chunk_lock.
    """

    def __init__(self, maxsize: int = _CHUNK_CACHE_MAXSIZE) -> None:
        self._maxsize = maxsize
        self._cache: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> Optional[str]:
        val = self._cache.pop(key, None)
        if val is not None:
            self._cache[key] = val  # move to end (most recently used)
        return val

    def set(self, key: str, value: str) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self._maxsize:
            self._cache.popitem(last=False)  # evict oldest
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


_chunk_cache = _ChunkCache()


def _get_chunk_content(chunk_id: str, db_store) -> str:
    """Get chunk content from cache, falling back to SQLite on miss."""
    with _chunk_lock:
        content = _chunk_cache.get(chunk_id)
    if content is not None:
        return content
    row = db_store.get_chunk(chunk_id)
    if row is None:
        return ""
    content = row["content"]
    with _chunk_lock:
        _chunk_cache.set(chunk_id, content)
    return content


def _get_llm() -> OllamaProvider | DeepSeekProvider:
    """Get or initialize the LLM provider based on configuration."""
    global _llm
    if _llm is None:
        with _init_lock:
            if _llm is None:
                config = get_config()
                llm_config = config.llm
                if llm_config.provider == "deepseek":
                    logger.info("Initializing DeepSeek provider: model=%s base_url=%s",
                                llm_config.model, llm_config.base_url)
                    _llm = DeepSeekProvider(
                        api_key=llm_config.api_key,
                        model=llm_config.model,
                        base_url=llm_config.base_url,
                        timeout=llm_config.timeout,
                    )
                else:
                    logger.info("Initializing Ollama provider: model=%s base_url=%s",
                                llm_config.model, llm_config.base_url)
                    _llm = OllamaProvider(
                        model=llm_config.model,
                        base_url=llm_config.base_url,
                        timeout=llm_config.timeout,
                    )
    return _llm


def _get_db_store() -> SQLiteStore:
    """Get or initialize the database store."""
    global _db_store
    if _db_store is None:
        with _init_lock:
            if _db_store is None:
                config = get_config()
                logger.info("Initializing SQLite store: path=%s", config.database.path)
                _db_store = SQLiteStore(db_path=config.database.path)
    return _db_store


def _get_embedding() -> BGEmbedding:
    """Get or initialize the embedding provider."""
    global _embedding
    if _embedding is None:
        with _init_lock:
            if _embedding is None:
                config = get_config()
                logger.info("Initializing embedding provider: model=%s dimension=%d",
                            config.embedding.model, config.embedding.dimension)
                _embedding = BGEmbedding(model_name=config.embedding.model)
    return _embedding


def _get_vector_store() -> FaissStore:
    """Get or initialize the vector store."""
    global _vector_store
    if _vector_store is None:
        with _init_lock:
            if _vector_store is None:
                config = get_config()
                embedding = _get_embedding()
                logger.info("Initializing FAISS vector store: type=%s dimension=%d",
                            config.vector_store.type, embedding.dimension)
                _vector_store = FaissStore(dimension=embedding.dimension)
    return _vector_store


def _get_retriever() -> HybridRetriever:
    """Get or initialize the hybrid retriever (vector + BM25)."""
    global _retriever
    if _retriever is None:
        with _init_lock:
            if _retriever is None:
                embedding = _get_embedding()
                vector_store = _get_vector_store()
                _retriever = HybridRetriever(
                    vector_store=vector_store,
                    embedding=embedding,
                )
    return _retriever


def _get_reranker() -> ScoreReranker | None:
    """Get or initialize the reranker."""
    global _reranker
    if _reranker is None:
        with _init_lock:
            if _reranker is None:
                config = get_config()
                if config.reranker.enabled:
                    logger.info("Initializing reranker: model=%s", config.reranker.model)
                    _reranker = ScoreReranker(model_name=config.reranker.model)
    return _reranker


def _build_bm25_index() -> None:
    """Populate the BM25 index from all chunks in SQLite."""
    db_store = _get_db_store()
    chunks = db_store.list_all_chunks_with_kb()
    if not chunks:
        return
    retriever = _get_retriever()
    for row in chunks:
        retriever.add_document(row["id"], row["content"], metadata={"kb_id": row["kb_id"]})
    logger.info("BM25 index built: %d chunks loaded", len(chunks))


def _get_chunker() -> FixedSizeChunker:
    """Get or initialize the chunker."""
    global _chunker
    if _chunker is None:
        with _init_lock:
            if _chunker is None:
                config = get_config()
                logger.info("Initializing chunker: size=%d overlap=%d",
                            config.chunker.chunk_size, config.chunker.chunk_overlap)
                _chunker = FixedSizeChunker(
                    chunk_size=config.chunker.chunk_size,
                    chunk_overlap=config.chunker.chunk_overlap,
                )
    return _chunker


def configure_logging(debug: bool = False) -> None:
    """Configure application logging.

    Args:
        debug: If True, set log level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    # Quiet noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _log_startup() -> None:
    """Log startup configuration summary."""
    config = get_config()
    logger.info("LightRAG-Core v0.1.0 starting")
    logger.info("LLM provider: %s  model: %s  base_url: %s",
                config.llm.provider, config.llm.model, config.llm.base_url)
    logger.info("Embedding: %s  dimension: %d",
                config.embedding.model, config.embedding.dimension)
    logger.info("Vector store: %s  dimension: %d",
                config.vector_store.type, config.vector_store.dimension)
    logger.info("Chunker: size=%d  overlap=%d",
                config.chunker.chunk_size, config.chunker.chunk_overlap)
    logger.info("Database: %s  path: %s",
                config.database.type, config.database.path)
    if config.debug:
        logger.info("Debug mode: ON")
    # Eager-init embedding & retriever to surface load failures at startup
    try:
        emb = _get_embedding()
        logger.info("Embedding model loaded: dimension=%d", emb.dimension)
    except Exception:
        logger.warning("Embedding model not available — will use random fallback vectors")
    # Pre-populate BM25 index from persistent chunks
    _build_bm25_index()
    # Eager-init reranker
    reranker = _get_reranker()
    if reranker is not None:
        logger.info("Reranker initialized: model=%s", config.reranker.model)


@app.on_event("startup")
async def startup() -> None:
    config = get_config()
    configure_logging(debug=config.debug)
    _log_startup()


@app.on_event("shutdown")
async def shutdown() -> None:
    logger.info("LightRAG-Core shutting down")
    if _db_store is not None:
        _db_store.close()
        logger.info("Database connection closed")
    if _llm is not None:
        try:
            _llm.__del__()
        except Exception:
            pass


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    """Query the knowledge base with LLM-generated answer.

    Uses CrossEncoder score threshold for dynamic result filtering
    when available, falling back to top-k behavior otherwise.
    """
    start_time = time.time()
    config = get_config()

    # Resolve threshold: request override > config default
    effective_threshold = (
        req.score_threshold
        if req.score_threshold is not None
        else config.reranker.score_threshold
    )

    logger.info(
        "Query: kb_id=%s top_k=%d threshold=%.2f query='%s'",
        req.kb_id, req.top_k, effective_threshold, req.query[:80],
    )

    retriever = _get_retriever()
    db_store = _get_db_store()

    # Fetch larger candidate pool for threshold-based filtering
    fetch_k = req.top_k * config.reranker.candidate_multiplier
    results = retriever.retrieve(req.query, top_k=fetch_k, filters={"kb_id": req.kb_id})
    logger.info("Retrieved %d candidates (fetch_k=%d)", len(results), fetch_k)

    # Rerank with threshold
    reranker = _get_reranker()
    if reranker is not None and len(results) > 1:
        chunk_ids = [r["id"] for r in results]
        texts = [_get_chunk_content(cid, db_store) for cid in chunk_ids]
        idx_to_result = {i: dict(results[i]) for i in range(len(results))}

        reranked = reranker.rerank(req.query, texts, score_threshold=effective_threshold)

        # Fallback: if threshold filters everything, use top 3 unfiltered
        if not reranked:
            logger.warning(
                "Threshold %.2f filtered all %d results; falling back to top 3",
                effective_threshold, len(texts),
            )
            reranked = reranker.rerank(req.query, texts, score_threshold=0.0)[:3]

        # Reconstruct results with cross-encoder scores, cap to top_k
        results = []
        for idx, score in reranked[:req.top_k]:
            r = idx_to_result[idx]
            r["score"] = score
            results.append(r)

        logger.info(
            "Reranked: %d pass threshold >= %.2f (returning top %d)",
            len(reranked), effective_threshold, len(results),
        )
    else:
        # No reranker: just cap results to top_k
        results = results[:req.top_k]

    sources = []
    for result in results:
        chunk_id = result["id"]
        content = _get_chunk_content(chunk_id, db_store)
        sources.append(
            SourceResult(
                doc_id=chunk_id.split("_chunk_")[0] if "_chunk_" in chunk_id else chunk_id,
                chunk_id=chunk_id,
                content=content,
                score=result["score"],
            )
        )

    if sources:
        context = "\n\n".join(
            f"[Source {i+1}]\n{source.content}"
            for i, source in enumerate(sources)
        )
        prompt = (
            "Based on the following context, answer the question comprehensively. "
            "Include ALL relevant items, facts, or entities mentioned in the context. "
            "Do not omit any information that is supported by the sources.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {req.query}\n\n"
            "Answer:"
        )
    else:
        prompt = req.query

    try:
        llm = _get_llm()
        answer = llm.generate(prompt)
    except RuntimeError as e:
        logger.error("LLM generation failed: %s", e)
        raise HTTPException(status_code=503, detail=str(e))

    latency_ms = int((time.time() - start_time) * 1000)
    logger.info("Query completed: latency=%dms sources=%d", latency_ms, len(sources))

    return QueryResponse(
        query=req.query,
        answer=answer,
        sources=sources,
        latency_ms=latency_ms,
    )


@app.post("/index", response_model=IndexResponse)
async def index_documents(req: IndexRequest) -> IndexResponse:
    """Index documents into the vector store."""
    logger.info("Index: kb_id=%s texts=%d", req.kb_id, len(req.texts))

    embedding = _get_embedding()
    vector_store = _get_vector_store()
    db_store = _get_db_store()

    kb = db_store.get_knowledge_base(req.kb_id)
    if kb is None:
        db_store.create_knowledge_base(req.kb_id, f"KB-{req.kb_id}")
        logger.info("Auto-created knowledge base: kb_id=%s", req.kb_id)

    ids = req.ids or [f"doc-{i}" for i in range(len(req.texts))]

    vectors = embedding.embed(req.texts)
    vector_store.add(vectors, ids, metadatas=[{"kb_id": req.kb_id} for _ in ids])
    logger.info("Indexed %d vectors into kb_id=%s", len(vectors), req.kb_id)

    # Sync BM25 index
    retriever = _get_retriever()
    for doc_id, text in zip(ids, req.texts):
        retriever.add_document(doc_id, text, metadata={"kb_id": req.kb_id})

    with _chunk_lock:
        for doc_id, text in zip(ids, req.texts):
            _chunk_cache.set(doc_id, text)

    return IndexResponse(
        task_id=str(uuid.uuid4()),
        status="completed",
        total_documents=len(req.texts),
        document_ids=ids,
    )


@app.get("/knowledge-bases", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases() -> KnowledgeBaseListResponse:
    """List all knowledge bases."""
    db_store = _get_db_store()
    kbs = db_store.list_knowledge_bases()
    logger.info("Listed %d knowledge bases", len(kbs))
    return KnowledgeBaseListResponse(
        items=[
            KnowledgeBaseResponse(
                id=kb["id"],
                name=kb["name"],
                description=kb.get("description"),
                created_at=kb.get("created_at", ""),
                updated_at=kb.get("updated_at", ""),
            )
            for kb in kbs
        ],
        total=len(kbs),
    )


@app.post("/knowledge-bases", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(req: KnowledgeBaseCreateRequest) -> KnowledgeBaseResponse:
    """Create a new knowledge base."""
    db_store = _get_db_store()
    kb_id = str(uuid.uuid4())
    db_store.create_knowledge_base(kb_id, req.name, req.description)

    kb = db_store.get_knowledge_base(kb_id)
    logger.info("Created knowledge base: id=%s name='%s'", kb_id, req.name)

    return KnowledgeBaseResponse(
        id=kb_id,
        name=kb["name"],
        description=kb.get("description"),
        created_at=kb["created_at"] if kb else "",
        updated_at=kb["updated_at"] if kb else "",
    )


@app.post("/documents", response_model=DocumentResponse)
async def upload_document(req: DocumentUploadRequest) -> DocumentResponse:
    """Upload and index a document (JSON body).

    Pipeline: content -> chunk -> embed -> store
    """
    logger.info("Document upload (JSON): kb_id=%s title='%s'", req.kb_id, req.title)

    db_store = _get_db_store()
    embedding = _get_embedding()
    vector_store = _get_vector_store()
    chunker = _get_chunker()

    kb = db_store.get_knowledge_base(req.kb_id)
    if kb is None:
        db_store.create_knowledge_base(req.kb_id, f"KB-{req.kb_id}")
        logger.info("Auto-created knowledge base: kb_id=%s", req.kb_id)

    doc_id = str(uuid.uuid4())

    db_store.create_document(
        doc_id=doc_id,
        kb_id=req.kb_id,
        title=req.title,
        source="upload",
        content=req.content,
    )

    chunks = chunker.chunk(req.content)
    logger.info("Document chunked: doc_id=%s chunks=%d", doc_id, len(chunks))

    chunk_ids = []
    for idx, chunk_text in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{idx}"
        chunk_ids.append(chunk_id)
        with _chunk_lock:
            _chunk_cache.set(chunk_id, chunk_text)

        db_store.create_chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_index=idx,
            content=chunk_text,
        )

    if chunks:
        vectors = embedding.embed(chunks)
        vector_store.add(vectors, chunk_ids, metadatas=[{"kb_id": req.kb_id} for _ in chunk_ids])

    # Sync BM25 index
    retriever = _get_retriever()
    for chunk_id, chunk_text in zip(chunk_ids, chunks):
        retriever.add_document(chunk_id, chunk_text, metadata={"kb_id": req.kb_id})

    doc = db_store.get_document(doc_id)
    logger.info("Document indexed: doc_id=%s chunks=%d title='%s'", doc_id, len(chunks), req.title)

    return DocumentResponse(
        id=doc_id,
        title=req.title,
        status="completed",
        created_at=doc["created_at"] if doc else "",
    )


@app.post("/documents/upload")
async def upload_file(
    file: UploadFile = File(...),
    kb_id: str = Query("default"),
) -> DocumentResponse:
    """Upload a file via multipart/form-data.

    Supports: .txt, .md, .pdf, .docx, .doc, .csv, .json, .html, .htm, .xlsx
    Pipeline: upload -> parse -> chunk -> embed -> store
    """
    filename = file.filename or "untitled"
    logger.info("File upload: kb_id=%s filename='%s'", kb_id, filename)

    db_store = _get_db_store()
    embedding = _get_embedding()
    vector_store = _get_vector_store()
    chunker = _get_chunker()

    kb = db_store.get_knowledge_base(kb_id)
    if kb is None:
        db_store.create_knowledge_base(kb_id, f"KB-{kb_id}")
        logger.info("Auto-created knowledge base: kb_id=%s", kb_id)

    suffix = Path(filename).suffix.lower()
    file_bytes = await file.read()

    import os
    import tempfile

    if suffix in (".pdf", ".docx", ".doc", ".xlsx"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        try:
            if suffix == ".pdf":
                parser = PDFParser()
            elif suffix == ".docx":
                parser = WordParser()
            elif suffix == ".doc":
                parser = DocParser()
            else:
                parser = XlsxParser()
            text = parser.parse(tmp_path)
            logger.info("%s parsed: %d characters", suffix, len(text))
        finally:
            os.unlink(tmp_path)
    elif suffix == ".html" or suffix == ".htm":
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        try:
            text = HTMLParser().parse(tmp_path)
            logger.info("HTML parsed: %d characters", len(text))
        finally:
            os.unlink(tmp_path)
    elif suffix in (".csv", ".json"):
        try:
            content = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File encoding must be UTF-8")
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", suffix=suffix, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            if suffix == ".csv":
                text = CSVParser().parse(tmp_path)
            else:
                text = JSONParser().parse(tmp_path)
            logger.info("%s parsed: %d characters", suffix, len(text))
        finally:
            os.unlink(tmp_path)
    else:
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File encoding must be UTF-8")

    doc_id = str(uuid.uuid4())

    db_store.create_document(
        doc_id=doc_id,
        kb_id=kb_id,
        title=filename,
        source=file.content_type or "unknown",
        content=text,
    )

    chunks = chunker.chunk(text)
    logger.info("Document chunked: doc_id=%s chunks=%d", doc_id, len(chunks))

    chunk_ids = []
    for idx, chunk_text in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{idx}"
        chunk_ids.append(chunk_id)
        with _chunk_lock:
            _chunk_cache.set(chunk_id, chunk_text)

        db_store.create_chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_index=idx,
            content=chunk_text,
        )

    if chunks:
        vectors = embedding.embed(chunks)
        vector_store.add(
            vectors,
            chunk_ids,
            metadatas=[{"kb_id": kb_id} for _ in chunk_ids],
        )

    # Sync BM25 index
    retriever = _get_retriever()
    for chunk_id, chunk_text in zip(chunk_ids, chunks):
        retriever.add_document(chunk_id, chunk_text, metadata={"kb_id": kb_id})

    doc = db_store.get_document(doc_id)
    logger.info("File indexed: doc_id=%s chunks=%d filename='%s'", doc_id, len(chunks), filename)

    return DocumentResponse(
        id=doc_id,
        title=filename,
        status="completed",
        created_at=doc["created_at"] if doc else "",
    )


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
