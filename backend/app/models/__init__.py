"""
SQLAlchemy ORM Models for LIBRIX AI
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, UniqueConstraint, Index, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    student = "student"
    admin = "admin"
    librarian = "librarian"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.student, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    reading_history = relationship("ReadingHistory", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    highlights = relationship("Highlight", back_populates="user", cascade="all, delete-orphan")
    favourites = relationship("Favourite", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reading_sessions = relationship("ReadingSession", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")


class Author(Base):
    __tablename__ = "authors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    bio = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    nationality = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    books = relationship("Book", back_populates="author")


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    books = relationship("Book", back_populates="category")


class Book(Base):
    __tablename__ = "books"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    isbn = Column(String(20), unique=True, nullable=True)
    publication_year = Column(Integer, nullable=True)
    language = Column(String(50), default="English")
    pages = Column(Integer, nullable=True)
    cover_url = Column(String(500), nullable=True)
    average_rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)
    total_reads = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_trending = Column(Boolean, default=False)
    is_new_arrival = Column(Boolean, default=True)
    is_published = Column(Boolean, default=True)
    tags = Column(JSONB, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # FKs
    author_id = Column(UUID(as_uuid=True), ForeignKey("authors.id"), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Relationships
    author = relationship("Author", back_populates="books")
    category = relationship("Category", back_populates="books")
    files = relationship("BookFile", back_populates="book", cascade="all, delete-orphan")
    reading_history = relationship("ReadingHistory", back_populates="book")
    bookmarks = relationship("Bookmark", back_populates="book", cascade="all, delete-orphan")
    highlights = relationship("Highlight", back_populates="book", cascade="all, delete-orphan")
    favourites = relationship("Favourite", back_populates="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    document_chunks = relationship("DocumentChunk", back_populates="book", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_books_title_fts", "title"),
    )


class BookFile(Base):
    __tablename__ = "book_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, epub
    file_url = Column(String(500), nullable=False)
    file_size_mb = Column(Float, nullable=True)
    is_processed = Column(Boolean, default=False)  # whether embeddings are done
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    book = relationship("Book", back_populates="files")


class ReadingHistory(Base):
    __tablename__ = "reading_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    current_page = Column(Integer, default=1)
    total_pages = Column(Integer, nullable=True)
    progress_percent = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    last_read_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reading_history")
    book = relationship("Book", back_populates="reading_history")

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_reading_history_user_book"),
    )


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    label = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bookmarks")
    book = relationship("Book", back_populates="bookmarks")


class Highlight(Base):
    __tablename__ = "highlights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    selected_text = Column(Text, nullable=False)
    color = Column(String(20), default="#FFD700")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="highlights")
    book = relationship("Book", back_populates="highlights")


class Favourite(Base):
    __tablename__ = "favourites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="favourites")
    book = relationship("Book", back_populates="favourites")

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_favourite_user_book"),
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    is_reported = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_review_user_book"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # info, success, warning, error
    is_read = Column(Boolean, default=False)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme = Column(String(20), default="dark")
    font_size = Column(Integer, default=16)
    reading_mode = Column(String(20), default="paginated")
    preferred_language = Column(String(10), default="en")
    favourite_categories = Column(JSONB, default=list)
    email_notifications = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="preferences")


class ReadingSession(Base):
    __tablename__ = "reading_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    pages_read = Column(Integer, default=0)
    duration_minutes = Column(Float, nullable=True)

    user = relationship("User", back_populates="reading_sessions")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    book = relationship("Book", back_populates="document_chunks")
    embeddings = relationship("DocumentEmbedding", back_populates="chunk", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_chunk_book", "book_id"),
    )


class DocumentEmbedding(Base):
    __tablename__ = "document_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False)
    # pgvector column added via Alembic migration
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunk = relationship("DocumentChunk", back_populates="embeddings")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")
