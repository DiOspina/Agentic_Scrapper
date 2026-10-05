"""
Document endpoints.
"""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models.document import Document, DocumentStatus, DocumentType
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadResponse,
)
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import get_vector_store
from app.services.metrics import get_metrics_service
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()

document_processor = DocumentProcessor()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a document."""
    # Read file content
    content = await file.read()
    await file.seek(0)

    # Process document
    processed = await document_processor.process_document(
        file=file.file,
        filename=file.filename,
    )

    if processed.error:
        raise HTTPException(status_code=400, detail=processed.error)

    # Create database record
    document = Document(
        document_id=processed.document_id,
        filename=processed.filename,
        original_filename=processed.original_filename,
        file_path=processed.file_path,
        file_size=processed.file_size,
        mime_type=processed.mime_type,
        document_type=processed.document_type,
        status=DocumentStatus.PROCESSING,
        content=processed.content,
        summary=processed.summary,
        metadata=processed.metadata,
        chunk_count=processed.chunk_count,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Index in vector store asynchronously
    try:
        vector_store = get_vector_store()
        from langchain_core.documents import Document as LCDocument

        lc_doc = LCDocument(
            page_content=processed.content,
            metadata={
                "document_id": processed.document_id,
                "filename": processed.original_filename,
                **(processed.metadata or {}),
            },
        )
        await vector_store.add_documents([lc_doc])

        # Update document with vector IDs
        document.status = DocumentStatus.PROCESSED
        document.vector_ids = [processed.document_id]
        document.embedding_model = "text-embedding-3-large"
        document.processed_at = __import__("datetime").datetime.utcnow()
        await db.commit()

        get_metrics_service().record_document(processed.document_type.value, True)

    except Exception as e:
        logger.error("Vector indexing failed", document_id=processed.document_id, error=str(e))
        document.status = DocumentStatus.FAILED
        document.error_message = f"Vector indexing failed: {str(e)}"
        await db.commit()
        get_metrics_service().record_document(processed.document_type.value, False)

    return DocumentUploadResponse(
        document_id=processed.document_id,
        filename=processed.original_filename,
        status=document.status,
        message="Document uploaded and processed successfully",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[DocumentStatus] = None,
    document_type: Optional[DocumentType] = None,
    db: AsyncSession = Depends(get_db),
):
    """List documents with pagination and filters."""
    query = select(Document).order_by(desc(Document.created_at))

    if status:
        query = query.where(Document.status == status)
    if document_type:
        query = query.where(Document.document_type == document_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get document by ID."""
    result = await db.execute(select(Document).where(Document.document_id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full document content."""
    result = await db.execute(select(Document).where(Document.document_id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"content": document.content, "metadata": document.metadata}


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update document metadata."""
    result = await db.execute(select(Document).where(Document.document_id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    if "status" in update_data and update_data["status"] == DocumentStatus.PROCESSED:
        document.processed_at = __import__("datetime").datetime.utcnow()

    await db.commit()
    await db.refresh(document)
    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    result = await db.execute(select(Document).where(Document.document_id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from vector store
    try:
        vector_store = get_vector_store()
        await vector_store.delete_by_metadata({"document_id": document_id})
    except Exception as e:
        logger.warning("Failed to delete from vector store", document_id=document_id, error=str(e))

    # Delete file
    document_processor.delete_file(document.file_path)

    # Delete from database
    await db.delete(document)
    await db.commit()

    return {"message": "Document deleted successfully"}


@router.post("/batch-process")
async def batch_process_documents(
    document_ids: List[str],
    db: AsyncSession = Depends(get_db),
):
    """Process multiple documents for vector indexing."""
    result = await db.execute(select(Document).where(Document.document_id.in_(document_ids)))
    documents = result.scalars().all()

    if not documents:
        raise HTTPException(status_code=404, detail="No documents found")

    vector_store = get_vector_store()
    from langchain_core.documents import Document as LCDocument

    lc_docs = []
    for doc in documents:
        if doc.content and doc.status != DocumentStatus.PROCESSED:
            lc_docs.append(LCDocument(
                page_content=doc.content,
                metadata={
                    "document_id": doc.document_id,
                    "filename": doc.original_filename,
                    **(doc.metadata or {}),
                },
            ))

    if lc_docs:
        await vector_store.add_documents(lc_docs)

        for doc in documents:
            doc.status = DocumentStatus.PROCESSED
            doc.vector_ids = [doc.document_id]
            doc.embedding_model = "text-embedding-3-large"
            doc.processed_at = __import__("datetime").datetime.utcnow()

        await db.commit()

    return {"processed": len(lc_docs), "message": "Batch processing complete"}