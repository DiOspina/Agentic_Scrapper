"""
Document Processor Service for handling file uploads and text extraction.
"""
import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional, BinaryIO
from dataclasses import dataclass

import pandas as pd
import pdfplumber
from pypdf import PdfReader
from docx import Document as DocxDocument
from openpyxl import load_workbook

from app.core.config import settings
from app.models.document import DocumentType, DocumentStatus


@dataclass
class ProcessedDocument:
    """Result of document processing."""
    document_id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    document_type: DocumentType
    content: str
    summary: Optional[str] = None
    metadata: Dict[str, Any] = None
    chunk_count: int = 0
    error: Optional[str] = None


class DocumentProcessor:
    """Service for processing uploaded documents."""

    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS

    def validate_file(self, filename: str, file_size: int) -> tuple[bool, Optional[str]]:
        """Validate file before processing."""
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            return False, f"File extension {ext} not allowed. Allowed: {self.allowed_extensions}"

        # Check size
        if file_size > self.max_file_size:
            return False, f"File size {file_size} exceeds maximum {self.max_file_size}"

        return True, None

    def get_document_type(self, filename: str, mime_type: str) -> DocumentType:
        """Determine document type from filename and MIME type."""
        ext = Path(filename).suffix.lower()

        ext_map = {
            ".pdf": DocumentType.PDF,
            ".csv": DocumentType.CSV,
            ".txt": DocumentType.TXT,
            ".md": DocumentType.MARKDOWN,
            ".docx": DocumentType.DOCX,
            ".xlsx": DocumentType.XLSX,
            ".html": DocumentType.HTML,
            ".json": DocumentType.JSON,
        }

        return ext_map.get(ext, DocumentType.TXT)

    async def save_file(
        self,
        file: BinaryIO,
        filename: str,
    ) -> tuple[str, str, int]:
        """Save uploaded file to disk."""
        document_id = str(uuid.uuid4())
        ext = Path(filename).suffix.lower()
        saved_filename = f"{document_id}{ext}"
        file_path = self.upload_dir / saved_filename

        # Read and save
        content = file.read()
        file_size = len(content)

        with open(file_path, "wb") as f:
            f.write(content)

        return document_id, str(file_path), file_size

    async def process_document(
        self,
        file: BinaryIO,
        filename: str,
    ) -> ProcessedDocument:
        """Process a document: save, extract text, generate metadata."""
        # Validate
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)

        valid, error = self.validate_file(filename, file_size)
        if not valid:
            return ProcessedDocument(
                document_id="",
                filename=filename,
                original_filename=filename,
                file_path="",
                file_size=file_size,
                mime_type="",
                document_type=DocumentType.TXT,
                content="",
                error=error,
            )

        # Save file
        document_id, file_path, file_size = await self.save_file(file, filename)

        # Determine types
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "application/octet-stream"
        doc_type = self.get_document_type(filename, mime_type)

        # Extract content
        try:
            content, metadata = await self._extract_content(file_path, doc_type)
        except Exception as e:
            return ProcessedDocument(
                document_id=document_id,
                filename=Path(file_path).name,
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
                document_type=doc_type,
                content="",
                error=f"Content extraction failed: {str(e)}",
            )

        # Generate summary
        summary = await self._generate_summary(content) if content else None

        # Count chunks (approximate)
        chunk_count = len(content) // settings.RAG_CHUNK_SIZE + 1 if content else 0

        return ProcessedDocument(
            document_id=document_id,
            filename=Path(file_path).name,
            original_filename=filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            document_type=doc_type,
            content=content,
            summary=summary,
            metadata=metadata,
            chunk_count=chunk_count,
        )

    async def _extract_content(
        self,
        file_path: str,
        doc_type: DocumentType,
    ) -> tuple[str, Dict[str, Any]]:
        """Extract text content from document based on type."""
        metadata = {"file_path": file_path}

        if doc_type == DocumentType.PDF:
            return await self._extract_pdf(file_path)
        elif doc_type == DocumentType.CSV:
            return await self._extract_csv(file_path)
        elif doc_type == DocumentType.DOCX:
            return await self._extract_docx(file_path)
        elif doc_type == DocumentType.XLSX:
            return await self._extract_xlsx(file_path)
        elif doc_type == DocumentType.TXT or doc_type == DocumentType.MARKDOWN:
            return await self._extract_text(file_path)
        elif doc_type == DocumentType.JSON:
            return await self._extract_json(file_path)
        else:
            # Fallback to text extraction
            return await self._extract_text(file_path)

    async def _extract_pdf(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract text from PDF."""
        content_parts = []
        metadata = {"pages": 0, "file_path": file_path}

        try:
            with pdfplumber.open(file_path) as pdf:
                metadata["pages"] = len(pdf.pages)
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        content_parts.append(f"--- Page {i+1} ---\n{text}")

                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        for j, table in enumerate(tables):
                            content_parts.append(f"\n--- Table {j+1} (Page {i+1}) ---\n")
                            for row in table:
                                content_parts.append(" | ".join([str(c) if c else "" for c in row]))

            content = "\n\n".join(content_parts)
            return content, metadata

        except Exception as e:
            # Fallback to pypdf
            try:
                reader = PdfReader(file_path)
                metadata["pages"] = len(reader.pages)
                content_parts = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        content_parts.append(f"--- Page {i+1} ---\n{text}")
                return "\n\n".join(content_parts), metadata
            except Exception:
                raise e

    async def _extract_csv(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract content from CSV."""
        df = pd.read_csv(file_path)
        metadata = {
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "file_path": file_path,
        }

        # Convert to readable text
        content = df.to_string(index=False)
        return content, metadata

    async def _extract_docx(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract content from DOCX."""
        doc = DocxDocument(file_path)
        content_parts = []
        metadata = {"paragraphs": 0, "tables": 0, "file_path": file_path}

        for para in doc.paragraphs:
            if para.text.strip():
                content_parts.append(para.text)
                metadata["paragraphs"] += 1

        for table in doc.tables:
            metadata["tables"] += 1
            content_parts.append("\n--- Table ---")
            for row in table.rows:
                content_parts.append(" | ".join([cell.text for cell in row.cells]))

        return "\n\n".join(content_parts), metadata

    async def _extract_xlsx(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract content from XLSX."""
        wb = load_workbook(file_path, read_only=True, data_only=True)
        content_parts = []
        metadata = {"sheets": [], "file_path": file_path}

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            metadata["sheets"].append({
                "name": sheet_name,
                "rows": ws.max_row,
                "cols": ws.max_column,
            })

            content_parts.append(f"\n--- Sheet: {sheet_name} ---")
            for row in ws.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    content_parts.append(" | ".join([str(c) if c is not None else "" for c in row]))

        wb.close()
        return "\n\n".join(content_parts), metadata

    async def _extract_text(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract content from text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        metadata = {
            "lines": content.count("\n") + 1,
            "chars": len(content),
            "file_path": file_path,
        }
        return content, metadata

    async def _extract_json(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract content from JSON."""
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        content = json.dumps(data, indent=2, ensure_ascii=False)
        metadata = {
            "keys": list(data.keys()) if isinstance(data, dict) else [],
            "type": type(data).__name__,
            "file_path": file_path,
        }
        return content, metadata

    async def _generate_summary(self, content: str, max_length: int = 500) -> str:
        """Generate a brief summary of the content."""
        # Simple extractive summary - first N characters
        if len(content) <= max_length:
            return content

        # Find a good breaking point
        summary = content[:max_length]
        last_period = summary.rfind(".")
        last_newline = summary.rfind("\n")

        break_point = max(last_period, last_newline)
        if break_point > max_length * 0.5:
            summary = summary[:break_point + 1]

        return summary + "..."

    def delete_file(self, file_path: str) -> bool:
        """Delete a processed file."""
        try:
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception:
            return False

    def get_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()