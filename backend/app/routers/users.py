"""
Users router – profile, reading history, bookmarks, highlights, dashboard.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.database import get_db
from app.models import (
    User, ReadingHistory, Bookmark, Highlight, Favourite,
    ReadingSession, Notification,
)
from app.schemas import (
    UserOut, UserUpdate, ReadingProgressUpdate, ReadingHistoryOut,
    BookmarkCreate, BookmarkOut, HighlightCreate, HighlightOut,
    NotificationOut, DashboardStats,
)
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.put("/me", response_model=UserOut)
def update_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(current_user, k, v)
    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.get("/me/dashboard", response_model=DashboardStats)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reading_history = db.query(ReadingHistory).filter(ReadingHistory.user_id == current_user.id).all()
    total_time = db.query(func.sum(ReadingSession.duration_minutes)).filter(
        ReadingSession.user_id == current_user.id
    ).scalar() or 0
    favourites_count = db.query(Favourite).filter(Favourite.user_id == current_user.id).count()
    currently_reading = sum(1 for rh in reading_history if not rh.is_completed)
    completed = sum(1 for rh in reading_history if rh.is_completed)

    return DashboardStats(
        total_books=db.query(func.count()).select_from(ReadingHistory).filter(
            ReadingHistory.user_id == current_user.id
        ).scalar() or 0,
        currently_reading=currently_reading,
        completed_books=completed,
        total_reading_time_hours=round(total_time / 60, 1),
        reading_streak_days=0,  # TODO: calculate from sessions
        favourite_count=favourites_count,
    )


@router.get("/me/reading-history", response_model=List[ReadingHistoryOut])
def get_reading_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = (
        db.query(ReadingHistory)
        .options(joinedload(ReadingHistory.book).joinedload("author"), joinedload(ReadingHistory.book).joinedload("category"))
        .filter(ReadingHistory.user_id == current_user.id)
        .order_by(desc(ReadingHistory.last_read_at))
        .all()
    )
    return [ReadingHistoryOut.model_validate(h) for h in history]


@router.post("/me/reading-progress/{book_id}")
def update_reading_progress(
    book_id: UUID,
    payload: ReadingProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rh = db.query(ReadingHistory).filter(
        ReadingHistory.user_id == current_user.id,
        ReadingHistory.book_id == book_id,
    ).first()

    total = payload.total_pages or (rh.total_pages if rh else None)
    progress = (payload.current_page / total * 100) if total else 0

    if rh:
        rh.current_page = payload.current_page
        if total:
            rh.total_pages = total
        rh.progress_percent = progress
        rh.is_completed = progress >= 100
    else:
        rh = ReadingHistory(
            user_id=current_user.id,
            book_id=book_id,
            current_page=payload.current_page,
            total_pages=total,
            progress_percent=progress,
            is_completed=progress >= 100,
        )
        db.add(rh)
    db.commit()
    return {"progress_percent": progress}


# ─── Bookmarks ───────────────────────────────────────────────────────────────

@router.get("/me/bookmarks", response_model=List[BookmarkOut])
def get_bookmarks(
    book_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Bookmark).filter(Bookmark.user_id == current_user.id)
    if book_id:
        q = q.filter(Bookmark.book_id == book_id)
    return [BookmarkOut.model_validate(b) for b in q.all()]


@router.post("/me/bookmarks", response_model=BookmarkOut, status_code=201)
def add_bookmark(
    payload: BookmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bm = Bookmark(user_id=current_user.id, **payload.model_dump())
    db.add(bm)
    db.commit()
    db.refresh(bm)
    return BookmarkOut.model_validate(bm)


@router.delete("/me/bookmarks/{bookmark_id}", status_code=204)
def delete_bookmark(
    bookmark_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bm = db.query(Bookmark).filter(Bookmark.id == bookmark_id, Bookmark.user_id == current_user.id).first()
    if bm:
        db.delete(bm)
        db.commit()


# ─── Highlights ──────────────────────────────────────────────────────────────

@router.get("/me/highlights", response_model=List[HighlightOut])
def get_highlights(
    book_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Highlight).filter(Highlight.user_id == current_user.id)
    if book_id:
        q = q.filter(Highlight.book_id == book_id)
    return [HighlightOut.model_validate(h) for h in q.all()]


@router.post("/me/highlights", response_model=HighlightOut, status_code=201)
def add_highlight(
    payload: HighlightCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    hl = Highlight(user_id=current_user.id, **payload.model_dump())
    db.add(hl)
    db.commit()
    db.refresh(hl)
    return HighlightOut.model_validate(hl)


# ─── Notifications ───────────────────────────────────────────────────────────

@router.get("/me/notifications", response_model=List[NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notes = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).limit(50).all()
    return [NotificationOut.model_validate(n) for n in notes]


@router.post("/me/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == current_user.id
    ).first()
    if note:
        note.is_read = True
        db.commit()
    return {"message": "Marked as read"}
