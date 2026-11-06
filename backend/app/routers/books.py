"""
Books router – CRUD, search, filter, trending, new arrivals.
"""
from typing import Optional, List
from uuid import UUID
import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc

from app.database import get_db
from app.models import Book, Author, Category, Favourite, Review
from app.schemas import (
    BookCreate, BookUpdate, BookOut, BookListResponse,
    ReviewCreate, ReviewOut,
)
from app.middleware.auth_middleware import get_current_user, require_admin
from app.models import User

router = APIRouter(prefix="/books", tags=["Books"])


def _book_query(db: Session):
    return db.query(Book).options(
        joinedload(Book.author),
        joinedload(Book.category),
    ).filter(Book.is_published == True)


@router.get("", response_model=BookListResponse)
def list_books(
    q: Optional[str] = Query(None, description="Search by title, author, or keyword"),
    category_id: Optional[UUID] = None,
    language: Optional[str] = None,
    sort: str = Query("newest", enum=["newest", "rating", "popular", "title"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = _book_query(db)

    if q:
        search_term = f"%{q.lower()}%"
        query = query.join(Author, isouter=True).filter(
            or_(
                func.lower(Book.title).like(search_term),
                func.lower(Author.name).like(search_term),
                func.lower(Book.description).like(search_term),
            )
        )
    if category_id:
        query = query.filter(Book.category_id == category_id)
    if language:
        query = query.filter(func.lower(Book.language) == language.lower())

    sort_map = {
        "newest": desc(Book.created_at),
        "rating": desc(Book.average_rating),
        "popular": desc(Book.total_reads),
        "title": Book.title,
    }
    query = query.order_by(sort_map[sort])

    total = query.count()
    books = query.offset((page - 1) * page_size).limit(page_size).all()
    return BookListResponse(
        books=[BookOut.model_validate(b) for b in books],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/featured", response_model=List[BookOut])
def get_featured(db: Session = Depends(get_db)):
    books = _book_query(db).filter(Book.is_featured == True).limit(8).all()
    return [BookOut.model_validate(b) for b in books]


@router.get("/trending", response_model=List[BookOut])
def get_trending(db: Session = Depends(get_db)):
    books = _book_query(db).filter(Book.is_trending == True).order_by(desc(Book.total_reads)).limit(10).all()
    return [BookOut.model_validate(b) for b in books]


@router.get("/new-arrivals", response_model=List[BookOut])
def get_new_arrivals(db: Session = Depends(get_db)):
    books = _book_query(db).filter(Book.is_new_arrival == True).order_by(desc(Book.created_at)).limit(10).all()
    return [BookOut.model_validate(b) for b in books]


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: UUID, db: Session = Depends(get_db)):
    book = _book_query(db).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookOut.model_validate(book)


@router.post("", response_model=BookOut, status_code=201)
def create_book(
    payload: BookCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    book = Book(**payload.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    # Reload with relationships
    return BookOut.model_validate(
        _book_query(db).filter(Book.id == book.id).first()
    )


@router.put("/{book_id}", response_model=BookOut)
def update_book(
    book_id: UUID,
    payload: BookUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(book, k, v)
    db.commit()
    db.refresh(book)
    return BookOut.model_validate(_book_query(db).filter(Book.id == book.id).first())


@router.delete("/{book_id}", status_code=204)
def delete_book(
    book_id: UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()


# ─── Reviews ─────────────────────────────────────────────────────────────────

@router.get("/{book_id}/reviews", response_model=List[ReviewOut])
def get_reviews(book_id: UUID, db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.book_id == book_id, Review.is_reported == False)
        .order_by(desc(Review.created_at))
        .all()
    )
    return [ReviewOut.model_validate(r) for r in reviews]


@router.post("/{book_id}/reviews", response_model=ReviewOut, status_code=201)
def add_review(
    book_id: UUID,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Review).filter(
        Review.book_id == book_id, Review.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this book")

    review = Review(book_id=book_id, user_id=current_user.id, rating=payload.rating, comment=payload.comment)
    db.add(review)

    # Update book average rating
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        total = book.total_ratings + 1
        book.average_rating = (book.average_rating * book.total_ratings + payload.rating) / total
        book.total_ratings = total

    db.commit()
    db.refresh(review)
    return ReviewOut.model_validate(db.query(Review).options(joinedload(Review.user)).filter(Review.id == review.id).first())


# ─── Favourites ──────────────────────────────────────────────────────────────

@router.post("/{book_id}/favourite", status_code=201)
def add_favourite(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Favourite).filter(
        Favourite.book_id == book_id, Favourite.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already in favourites")
    db.add(Favourite(book_id=book_id, user_id=current_user.id))
    db.commit()
    return {"message": "Added to favourites"}


@router.delete("/{book_id}/favourite", status_code=204)
def remove_favourite(
    book_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fav = db.query(Favourite).filter(
        Favourite.book_id == book_id, Favourite.user_id == current_user.id
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
