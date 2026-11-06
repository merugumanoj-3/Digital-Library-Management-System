"""
File upload router – PDF processing, cover image upload, embedding generation.
"""
import io
import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book, BookFile, DocumentChunk
from app.middleware.auth_middleware import require_admin
from app.models import User
from app.config import settings

router = APIRouter(prefix="/upload", tags=["File Upload"])

MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_PDF_TYPES = {"application/pdf"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def get_supabase():
    try:
        from supabase import create_client
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Storage unavailable: {str(e)}")


@router.post("/cover/{book_id}")
async def upload_cover(
    book_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are allowed")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit for images
        raise HTTPException(status_code=400, detail="Image must be under 10MB")

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    supabase = get_supabase()
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    path = f"covers/{book_id}.{ext}"

    try:
        supabase.storage.from_(settings.COVER_BUCKET).upload(
            path, content, {"content-type": file.content_type, "upsert": "true"}
        )
        public_url = supabase.storage.from_(settings.COVER_BUCKET).get_public_url(path)
        book.cover_url = public_url
        db.commit()
        return {"cover_url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/pdf/{book_id}")
async def upload_pdf(
    book_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if file.content_type not in ALLOWED_PDF_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"File must be under {settings.MAX_FILE_SIZE_MB}MB")

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    supabase = get_supabase()
    path = f"pdfs/{book_id}/{file.filename}"

    try:
        supabase.storage.from_(settings.PDF_BUCKET).upload(
            path, content, {"content-type": "application/pdf", "upsert": "true"}
        )
        file_url = supabase.storage.from_(settings.PDF_BUCKET).get_public_url(path)

        size_mb = len(content) / (1024 * 1024)
        book_file = BookFile(
            book_id=book_id,
            file_type="pdf",
            file_url=file_url,
            file_size_mb=size_mb,
            is_processed=False,
        )
        db.add(book_file)
        db.commit()
        db.refresh(book_file)

        return {"file_url": file_url, "file_id": str(book_file.id), "size_mb": round(size_mb, 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/process-pdf/{book_id}")
async def process_pdf_for_rag(
    book_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Extract text from PDF, chunk it, and store chunks for RAG."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book_file = db.query(BookFile).filter(
        BookFile.book_id == book_id,
        BookFile.file_type == "pdf"
    ).first()
    if not book_file:
        raise HTTPException(status_code=404, detail="No PDF uploaded for this book")

    # Download the PDF
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(book_file.file_url, timeout=30)
            pdf_bytes = resp.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not download PDF: {str(e)}")

    # Extract text
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(e)}")

    # Delete existing chunks
    db.query(DocumentChunk).filter(DocumentChunk.book_id == book_id).delete()

    # Chunk text (by page, with overlap)
    CHUNK_SIZE = 1000  # characters
    chunks_created = 0
    chunk_index = 0

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        if not text.strip():
            continue

        # Split page into sub-chunks if long
        words = text.split()
        current_chunk = []
        char_count = 0

        for word in words:
            current_chunk.append(word)
            char_count += len(word) + 1
            if char_count >= CHUNK_SIZE:
                chunk_text = " ".join(current_chunk)
                db.add(DocumentChunk(
                    book_id=book_id,
                    chunk_index=chunk_index,
                    page_number=page_num,
                    content=chunk_text,
                    token_count=len(current_chunk),
                ))
                chunk_index += 1
                chunks_created += 1
                current_chunk = []
                char_count = 0

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            db.add(DocumentChunk(
                book_id=book_id,
                chunk_index=chunk_index,
                page_number=page_num,
                content=chunk_text,
                token_count=len(current_chunk),
            ))
            chunk_index += 1
            chunks_created += 1

    book_file.is_processed = True
    if total_pages and not book.pages:
        book.pages = total_pages
    db.commit()

    return {
        "book_id": str(book_id),
        "chunks_created": chunks_created,
        "total_pages": total_pages,
        "message": "PDF processed successfully. Ready for AI chat.",
    }
