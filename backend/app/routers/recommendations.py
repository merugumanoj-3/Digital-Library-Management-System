"""
Recommendations router – personalized, similar books, trending.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.database import get_db
from app.models import Book, ReadingHistory, Favourite, User, Category
from app.schemas import BookOut
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/personalized", response_model=List[BookOut])
def get_personalized(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Content-based filtering: recommend books in categories the user reads/favourites."""
    # Get user's category preferences from reading history
    read_categories = (
        db.query(Book.category_id)
        .join(ReadingHistory, ReadingHistory.book_id == Book.id)
        .filter(ReadingHistory.user_id == current_user.id, Book.category_id.isnot(None))
        .distinct()
        .all()
    )
    fav_categories = (
        db.query(Book.category_id)
        .join(Favourite, Favourite.book_id == Book.id)
        .filter(Favourite.user_id == current_user.id, Book.category_id.isnot(None))
        .distinct()
        .all()
    )

    preferred_cats = list({r[0] for r in read_categories + fav_categories})

    # Books already read/favourited
    already_read = (
        db.query(ReadingHistory.book_id)
        .filter(ReadingHistory.user_id == current_user.id)
        .all()
    )
    exclude_ids = [r[0] for r in already_read]

    if preferred_cats:
        books = (
            db.query(Book)
            .options(joinedload(Book.author), joinedload(Book.category))
            .filter(
                Book.category_id.in_(preferred_cats),
                Book.is_published == True,
                Book.id.notin_(exclude_ids),
            )
            .order_by(desc(Book.average_rating))
            .limit(limit)
            .all()
        )
    else:
        # Fallback: top-rated books
        books = (
            db.query(Book)
            .options(joinedload(Book.author), joinedload(Book.category))
            .filter(Book.is_published == True)
            .order_by(desc(Book.average_rating))
            .limit(limit)
            .all()
        )

    return [BookOut.model_validate(b) for b in books]


@router.get("/similar/{book_id}", response_model=List[BookOut])
def get_similar(
    book_id: UUID,
    limit: int = 6,
    db: Session = Depends(get_db),
):
    """Return books in the same category."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return []

    similar = (
        db.query(Book)
        .options(joinedload(Book.author), joinedload(Book.category))
        .filter(
            Book.category_id == book.category_id,
            Book.id != book_id,
            Book.is_published == True,
        )
        .order_by(desc(Book.average_rating))
        .limit(limit)
        .all()
    )
    return [BookOut.model_validate(b) for b in similar]


@router.get("/trending", response_model=List[BookOut])
def get_trending(limit: int = 10, db: Session = Depends(get_db)):
    books = (
        db.query(Book)
        .options(joinedload(Book.author), joinedload(Book.category))
        .filter(Book.is_trending == True, Book.is_published == True)
        .order_by(desc(Book.total_reads))
        .limit(limit)
        .all()
    )
    return [BookOut.model_validate(b) for b in books]
