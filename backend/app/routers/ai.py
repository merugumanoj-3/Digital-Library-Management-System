"""
AI Assistant router – chat with books, summaries, MCQs, RAG.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book, DocumentChunk
from app.schemas import AIChatRequest, AIChatResponse, SummaryRequest, MCQRequest, MCQQuestion
from app.middleware.auth_middleware import get_current_user
from app.models import User
from app.config import settings

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def get_gemini_client():
    """Return configured Gemini GenerativeModel."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        return genai.GenerativeModel("gemini-1.5-pro-latest")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")


def retrieve_relevant_chunks(db: Session, book_id: UUID, question: str, top_k: int = 5) -> list[dict]:
    """
    Basic keyword retrieval (fallback when pgvector embeddings not yet generated).
    Returns list of dicts with content and page_number.
    """
    words = [w.lower() for w in question.split() if len(w) > 3]
    if not words:
        # Return first few chunks as context
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.book_id == book_id
        ).limit(top_k).all()
    else:
        from sqlalchemy import or_, func
        conditions = [func.lower(DocumentChunk.content).contains(w) for w in words[:5]]
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.book_id == book_id,
            or_(*conditions)
        ).limit(top_k).all()

    return [{"content": c.content, "page_number": c.page_number, "chunk_id": str(c.id)} for c in chunks]


@router.post("/chat", response_model=AIChatResponse)
def chat_with_book(
    payload: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = get_gemini_client()
    sources = []
    context_text = ""
    book_title = None

    if payload.book_id:
        book = db.query(Book).filter(Book.id == payload.book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        book_title = book.title

        chunks = retrieve_relevant_chunks(db, payload.book_id, payload.question)
        if chunks:
            context_text = "\n\n---\n\n".join(
                f"[Page {c['page_number'] or 'N/A'}]: {c['content']}" for c in chunks
            )
            sources = [{"page": c["page_number"], "excerpt": c["content"][:200] + "..."} for c in chunks]

    system_prompt = f"""You are LIBRIX AI, an intelligent library assistant.
{"You have access to excerpts from the book: '" + book_title + "'." if book_title else "You are a general knowledge library assistant."}

{"RELEVANT BOOK CONTENT:" + chr(10) + context_text if context_text else ""}

Rules:
1. Answer based ONLY on the provided book content when a book is selected.
2. If the answer is not in the provided content, say: "This information is not covered in the available sections of this book."
3. Always cite page numbers when referencing specific content.
4. Be educational, clear, and concise.
5. For general questions (no book selected), use your knowledge but clarify the source.
"""

    # Build conversation
    history = []
    for msg in payload.conversation_history[-6:]:  # Last 6 messages
        role = "user" if msg.get("role") == "user" else "model"
        history.append({"role": role, "parts": [msg.get("content", "")]})

    chat = model.start_chat(history=history)
    response = chat.send_message(
        f"{system_prompt}\n\nUser question: {payload.question}"
    )

    return AIChatResponse(
        answer=response.text,
        sources=sources,
        book_title=book_title,
    )


@router.post("/summarize")
def summarize_book(
    payload: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == payload.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.book_id == payload.book_id
    ).order_by(DocumentChunk.chunk_index).limit(20).all()

    if not chunks:
        raise HTTPException(status_code=400, detail="Book has not been indexed yet. Please process the PDF first.")

    content = " ".join(c.content for c in chunks)[:8000]  # Truncate for safety

    model = get_gemini_client()
    prompt = f"""Summarize the following content from the book "{book.title}":

{content}

Provide:
1. A comprehensive summary (3-4 paragraphs)
2. Key themes and concepts
3. Main takeaways

Be structured and educational."""

    response = model.generate_content(prompt)
    return {"book_title": book.title, "summary": response.text}


@router.post("/generate-mcq")
def generate_mcq(
    payload: MCQRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == payload.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.book_id == payload.book_id
    ).limit(15).all()

    if not chunks:
        raise HTTPException(status_code=400, detail="Book has not been indexed yet.")

    content = " ".join(c.content for c in chunks)[:6000]
    model = get_gemini_client()

    prompt = f"""Based on this content from "{book.title}", generate {payload.num_questions} multiple-choice questions at {payload.difficulty} difficulty.

Content:
{content}

Return ONLY a valid JSON array with this structure:
[
  {{
    "question": "...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_answer": 0,
    "explanation": "...",
    "page_reference": null
  }}
]"""

    import json as json_lib
    response = model.generate_content(prompt)
    text = response.text.strip()

    # Strip markdown code blocks if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        questions = json_lib.loads(text)
        return {"book_title": book.title, "questions": questions}
    except Exception:
        return {"book_title": book.title, "raw_response": response.text}


@router.post("/extract-definitions")
def extract_definitions(
    payload: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.id == payload.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.book_id == payload.book_id
    ).limit(20).all()

    if not chunks:
        raise HTTPException(status_code=400, detail="Book not indexed yet.")

    content = " ".join(c.content for c in chunks)[:6000]
    model = get_gemini_client()

    prompt = f"""From this content from "{book.title}", extract all important definitions, terms, and key concepts.

Content:
{content}

Return a JSON array:
[{{"term": "...", "definition": "...", "context": "..."}}]"""

    import json as json_lib
    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        definitions = json_lib.loads(text)
        return {"book_title": book.title, "definitions": definitions}
    except Exception:
        return {"book_title": book.title, "raw_response": response.text}
