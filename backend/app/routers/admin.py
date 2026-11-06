"""
Admin router – manage users, books, categories, authors, view analytics.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models import (
    User, Book, Author, Category, Review, ActivityLog,
    ReadingSession, ReadingHistory,
)
from app.schemas import (
    UserOut, AuthorCreate, AuthorOut, CategoryCreate, CategoryOut,
    AdminStats,
)
from app.middleware.auth_middleware import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc)
    month_ago = now - timedelta(days=30)

    total_books = db.query(func.count(Book.id)).scalar()
    total_users = db.query(func.count(User.id)).scalar()
    total_sessions = db.query(func.count(ReadingSession.id)).scalar()
    books_this_month = db.query(func.count(Book.id)).filter(Book.created_at >= month_ago).scalar()
    users_this_month = db.query(func.count(User.id)).filter(User.created_at >= month_ago).scalar()

    # Top 5 most-read books
    most_read = (
        db.query(Book.title, Book.total_reads)
        .order_by(desc(Book.total_reads))
        .limit(5)
        .all()
    )

    # Popular categories
    popular_cats = (
        db.query(Category.name, func.count(Book.id).label("book_count"))
        .join(Book, Book.category_id == Category.id, isouter=True)
        .group_by(Category.id)
        .order_by(desc("book_count"))
        .limit(5)
        .all()
    )

    return AdminStats(
        total_books=total_books or 0,
        total_users=total_users or 0,
        total_reading_sessions=total_sessions or 0,
        books_added_this_month=books_this_month or 0,
        new_users_this_month=users_this_month or 0,
        most_read_books=[{"title": r.title, "reads": r.total_reads} for r in most_read],
        popular_categories=[{"name": c.name, "count": c.book_count} for c in popular_cats],
        monthly_activity=[],  # TODO: populate with monthly data
    )


# ─── Users Management ────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserOut])
def list_users(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    users = db.query(User).offset((page - 1) * page_size).limit(page_size).all()
    return [UserOut.model_validate(u) for u in users]


@router.put("/users/{user_id}/activate")
def activate_user(user_id: UUID, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    return {"message": "User activated"}


@router.put("/users/{user_id}/deactivate")
def deactivate_user(user_id: UUID, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"message": "User deactivated"}


# ─── Authors ─────────────────────────────────────────────────────────────────

@router.get("/authors", response_model=List[AuthorOut])
def list_authors(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return [AuthorOut.model_validate(a) for a in db.query(Author).all()]


@router.post("/authors", response_model=AuthorOut, status_code=201)
def create_author(
    payload: AuthorCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    author = Author(**payload.model_dump())
    db.add(author)
    db.commit()
    db.refresh(author)
    return AuthorOut.model_validate(author)


@router.delete("/authors/{author_id}", status_code=204)
def delete_author(author_id: UUID, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    db.delete(author)
    db.commit()


# ─── Categories ──────────────────────────────────────────────────────────────

@router.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return [CategoryOut.model_validate(c) for c in db.query(Category).all()]


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    import re
    slug = re.sub(r"[^a-z0-9]+", "-", payload.name.lower()).strip("-")
    cat = Category(slug=slug, **payload.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return CategoryOut.model_validate(cat)


# ─── Reviews Moderation ──────────────────────────────────────────────────────

@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: UUID, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()


# ─── Activity Logs ───────────────────────────────────────────────────────────

@router.get("/activity-logs")
def get_activity_logs(
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    logs = (
        db.query(ActivityLog)
        .order_by(desc(ActivityLog.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [
        {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "created_at": log.created_at,
        }
        for log in logs
    ]
