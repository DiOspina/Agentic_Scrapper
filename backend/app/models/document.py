import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, Enum, Index, ForeignKey, JSON, Integer, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    CSV = "csv"
    TXT = "txt"
    MARKDOWN = "markdown"
    DOCX = "docx"
    XLSX = "xlsx"
    HTML = "html"
    JSON = "json"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)

    # Content
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Vector Store
    vector_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Processing
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Relationships
    uploaded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    execution_id: Mapped[Optional[int]] = mapped_column(ForeignKey("executions.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_documents_status_type", "status", "document_type"),
        Index("ix_documents_created_at", "created_at"),
        Index("ix_documents_filename", "filename"),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, document_id='{self.document_id}', filename='{self.filename}', type='{self.document_type}', status='{self.status}')>"