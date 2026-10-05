from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.document import DocumentStatus, DocumentType


class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    document_type: DocumentType


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    status: Optional[DocumentStatus] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    vector_ids: Optional[List[str]] = None
    chunk_count: Optional[int] = None
    embedding_model: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    processed_at: Optional[datetime] = None


class DocumentResponse(BaseModel):
    id: int
    document_id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    document_type: DocumentType
    status: DocumentStatus
    summary: Optional[str] = None
    chunk_count: int
    embedding_model: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    uploaded_by: Optional[int] = None
    execution_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    message: str