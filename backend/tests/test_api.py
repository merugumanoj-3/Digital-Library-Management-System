"""
LIBRIX AI – Backend Test Suite
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Use SQLite for testing (no PostgreSQL required for unit tests)
TEST_DATABASE_URL = "sqlite:///./test_librix.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def auth_headers(client):
    """Register a test user and return auth headers."""
    register_data = {
        "email": "test@librix.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "TestPass123!",
    }
    resp = client.post("/api/auth/register", json=register_data)
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─── Health ───────────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "LIBRIX" in data["app"]


# ─── Auth ─────────────────────────────────────────────────────────────────────

def test_register_success(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@librix.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "Password123!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@librix.com"


def test_register_duplicate_email(client):
    payload = {
        "email": "dup@librix.com",
        "username": "dup1",
        "full_name": "Dup User",
        "password": "Password123!",
    }
    client.post("/api/auth/register", json=payload)
    resp = client.post(
        "/api/auth/register",
        json={**payload, "username": "dup2"},
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_login_success(client, auth_headers):
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@librix.com", "password": "TestPass123!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@librix.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@librix.com"


def test_unauthenticated_access(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 403  # No token = 403 (HTTPBearer rejects)


# ─── Books ────────────────────────────────────────────────────────────────────

def test_list_books_public(client):
    resp = client.get("/api/books")
    assert resp.status_code == 200
    data = resp.json()
    assert "books" in data
    assert "total" in data


def test_get_nonexistent_book(client):
    resp = client.get("/api/books/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_create_book_requires_admin(client, auth_headers):
    resp = client.post(
        "/api/books",
        json={"title": "Test Book", "language": "English"},
        headers=auth_headers,
    )
    # Regular users cannot create books
    assert resp.status_code == 403


# ─── User Profile ─────────────────────────────────────────────────────────────

def test_get_profile(client, auth_headers):
    resp = client.get("/api/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_get_dashboard(client, auth_headers):
    resp = client.get("/api/users/me/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_books" in data
    assert "currently_reading" in data


def test_update_profile(client, auth_headers):
    resp = client.put(
        "/api/users/me",
        json={"full_name": "Updated Name", "bio": "I love reading!"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"


def test_get_reading_history(client, auth_headers):
    resp = client.get("/api/users/me/reading-history", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_notifications(client, auth_headers):
    resp = client.get("/api/users/me/notifications", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ─── Recommendations ──────────────────────────────────────────────────────────

def test_get_trending(client):
    resp = client.get("/api/recommendations/trending")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_personalized(client, auth_headers):
    resp = client.get("/api/recommendations/personalized", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ─── Forgot Password ──────────────────────────────────────────────────────────

def test_forgot_password(client):
    resp = client.post(
        "/api/auth/forgot-password",
        json={"email": "doesnotexist@librix.com"},
    )
    assert resp.status_code == 200
    # Should not reveal whether email exists
    assert "reset link" in resp.json()["message"].lower()
