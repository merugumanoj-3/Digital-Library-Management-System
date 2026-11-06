"""
Pydantic schemas for LIBRIX AI
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


# ──────────────────────────── Auth Schemas ────────────────────────────────────

class UserRole(str, Enum):
    student = "student"
    admin = "admin"
    librarian = "librarian"


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (underscores/hyphens allowed)")
        return v.lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


# ──────────────────────────── User Schemas ────────────────────────────────────

class UserOut(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    role: UserRole
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


# ──────────────────────────── Author Schemas ─────────────────────────────────

class AuthorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    nationality: Optional[str] = None


class AuthorOut(BaseModel):
    id: UUID
    name: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    nationality: Optional[str] = None

    model_config = {"from_attributes": True}


# ──────────────────────────── Category Schemas ───────────────────────────────

class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryOut(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    book_count: Optional[int] = 0

    model_config = {"from_attributes": True}


# ──────────────────────────── Book Schemas ────────────────────────────────────

class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    language: str = "English"
    pages: Optional[int] = Field(None, gt=0)
    cover_url: Optional[str] = None
    author_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    is_featured: bool = False
    tags: List[str] = []


class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    language: Optional[str] = None
    pages: Optional[int] = None
    cover_url: Optional[str] = None
    author_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    is_featured: Optional[bool] = None
    is_trending: Optional[bool] = None
    is_published: Optional[bool] = None
    tags: Optional[List[str]] = None


class BookOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    language: str
    pages: Optional[int] = None
    cover_url: Optional[str] = None
    average_rating: float
    total_ratings: int
    total_reads: int
    is_featured: bool
    is_trending: bool
    is_new_arrival: bool
    tags: List[str] = []
    author: Optional[AuthorOut] = None
    category: Optional[CategoryOut] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    books: List[BookOut]
    total: int
    page: int
    page_size: int
    total_pages: int


# ──────────────────────────── Reading Schemas ─────────────────────────────────

class ReadingProgressUpdate(BaseModel):
    current_page: int = Field(ge=1)
    total_pages: Optional[int] = None


class ReadingHistoryOut(BaseModel):
    id: UUID
    book: BookOut
    current_page: int
    total_pages: Optional[int] = None
    progress_percent: float
    is_completed: bool
    last_read_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────── Bookmark/Highlight Schemas ─────────────────────

class BookmarkCreate(BaseModel):
    book_id: UUID
    page_number: int = Field(ge=1)
    label: Optional[str] = None


class BookmarkOut(BaseModel):
    id: UUID
    book_id: UUID
    page_number: int
    label: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HighlightCreate(BaseModel):
    book_id: UUID
    page_number: int = Field(ge=1)
    selected_text: str = Field(min_length=1)
    color: str = "#FFD700"
    note: Optional[str] = None


class HighlightOut(BaseModel):
    id: UUID
    book_id: UUID
    page_number: int
    selected_text: str
    color: str
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────── Review Schemas ─────────────────────────────────

class ReviewCreate(BaseModel):
    book_id: UUID
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: UUID
    rating: int
    comment: Optional[str] = None
    user: UserOut
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────── AI Schemas ─────────────────────────────────────

class AIChatRequest(BaseModel):
    book_id: Optional[UUID] = None
    question: str = Field(min_length=1, max_length=2000)
    conversation_history: List[dict] = []


class AIChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []
    book_title: Optional[str] = None


class SummaryRequest(BaseModel):
    book_id: UUID
    chapter_hint: Optional[str] = None


class MCQRequest(BaseModel):
    book_id: UUID
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = "medium"


class MCQQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: str
    page_reference: Optional[int] = None


# ──────────────────────────── Notification Schemas ───────────────────────────

class NotificationOut(BaseModel):
    id: UUID
    title: str
    message: str
    type: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────── Dashboard Schemas ──────────────────────────────

class DashboardStats(BaseModel):
    total_books: int
    currently_reading: int
    completed_books: int
    total_reading_time_hours: float
    reading_streak_days: int
    favourite_count: int


class AdminStats(BaseModel):
    total_books: int
    total_users: int
    total_reading_sessions: int
    books_added_this_month: int
    new_users_this_month: int
    most_read_books: List[dict]
    popular_categories: List[dict]
    monthly_activity: List[dict]
