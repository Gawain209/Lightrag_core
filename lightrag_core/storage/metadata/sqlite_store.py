"""SQLite metadata storage implementation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

Base = declarative_base()


class KnowledgeBaseModel(Base):
    """KnowledgeBase database model."""

    __tablename__ = "knowledge_bases"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("DocumentModel", back_populates="knowledge_base")


class DocumentModel(Base):
    """Document database model."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    kb_id = Column(String, ForeignKey("knowledge_bases.id"))
    title = Column(String, nullable=False)
    source = Column(String)
    content = Column(Text)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    knowledge_base = relationship("KnowledgeBaseModel", back_populates="documents")
    chunks = relationship("ChunkModel", back_populates="document")


class ChunkModel(Base):
    """Chunk database model."""

    __tablename__ = "chunks"

    id = Column(String, primary_key=True)
    doc_id = Column(String, ForeignKey("documents.id"))
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer)
    metadata_json = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="chunks")


class SQLiteStore:
    """SQLite storage for metadata."""

    def __init__(self, db_path: str = "lightrag.db") -> None:
        """Initialize the SQLite store.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._db_path = db_path

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Get a chunk by ID."""
        with self.Session() as session:
            chunk = session.query(ChunkModel).filter_by(id=chunk_id).first()
            if chunk:
                return {
                    "id": chunk.id,
                    "doc_id": chunk.doc_id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "token_count": chunk.token_count,
                    "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
                }
            return None

    def list_all_chunks_with_kb(self) -> List[Dict[str, Any]]:
        """List all chunks with their knowledge base ID.

        Returns:
            List of dicts with keys: id, content, kb_id.
        """
        with self.Session() as session:
            rows = (
                session.query(ChunkModel.id, ChunkModel.content, DocumentModel.kb_id)
                .join(DocumentModel, ChunkModel.doc_id == DocumentModel.id)
                .all()
            )
            return [
                {"id": row.id, "content": row.content, "kb_id": row.kb_id}
                for row in rows
            ]

    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """List all knowledge bases."""
        with self.Session() as session:
            kbs = session.query(KnowledgeBaseModel).order_by(
                KnowledgeBaseModel.created_at.desc()
            ).all()
            return [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "description": kb.description,
                    "created_at": kb.created_at.isoformat() if kb.created_at else None,
                    "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
                }
                for kb in kbs
            ]

    def close(self) -> None:
        """Close the database connection."""
        self.engine.dispose()

    def create_knowledge_base(self, kb_id: str, name: str, description: Optional[str] = None) -> None:
        """Create a new knowledge base."""
        with self.Session() as session:
            kb = KnowledgeBaseModel(id=kb_id, name=name, description=description)
            session.add(kb)
            session.commit()

    def get_knowledge_base(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """Get a knowledge base by ID."""
        with self.Session() as session:
            kb = session.query(KnowledgeBaseModel).filter_by(id=kb_id).first()
            if kb:
                return {
                    "id": kb.id,
                    "name": kb.name,
                    "description": kb.description,
                    "created_at": kb.created_at.isoformat() if kb.created_at else None,
                    "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
                }
            return None

    def create_document(self, doc_id: str, kb_id: str, title: str, source: str, content: str) -> None:
        """Create a new document."""
        with self.Session() as session:
            doc = DocumentModel(
                id=doc_id,
                kb_id=kb_id,
                title=title,
                source=source,
                content=content,
            )
            session.add(doc)
            session.commit()

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        with self.Session() as session:
            doc = session.query(DocumentModel).filter_by(id=doc_id).first()
            if doc:
                return {
                    "id": doc.id,
                    "kb_id": doc.kb_id,
                    "title": doc.title,
                    "source": doc.source,
                    "content": doc.content,
                    "version": doc.version,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                }
            return None

    def create_chunk(self, chunk_id: str, doc_id: str, chunk_index: int, content: str, token_count: Optional[int] = None) -> None:
        """Create a new chunk."""
        with self.Session() as session:
            chunk = ChunkModel(
                id=chunk_id,
                doc_id=doc_id,
                chunk_index=chunk_index,
                content=content,
                token_count=token_count,
            )
            session.add(chunk)
            session.commit()
