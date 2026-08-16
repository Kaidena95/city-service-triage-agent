"""
test_api.py — Tests for the FastAPI endpoints

Uses FastAPI's TestClient to send real HTTP requests to the API
without needing uvicorn running. Tests a fresh in-memory database
for each test session so tests never affect your real database.db.

Run with:
    cd backend
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

# Import your app and database components
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import get_session


# ── TEST DATABASE SETUP ─────────────────────────────────────────────
# Use an in-memory SQLite database for tests
# This means:
#   - Tests never touch your real database.db
#   - Every test run starts with a clean empty database
#   - Tests are fast and isolated

@pytest.fixture(name="session")
def session_fixture():
    """
    Creates a fresh in-memory database for each test session.
    StaticPool keeps the same connection so the database persists
    across the test but is destroyed when the test ends.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Creates a TestClient that uses the test database session
    instead of the real database session.
    """
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ── POST /requests TESTS ────────────────────────────────────────────

def test_create_request_success(client):
    """POST /requests should create and return a classified request."""
    response = client.post("/requests", json={
        "description": "Broken streetlight near 5th and Main",
        "location": "5th Street and Main Street, Los Angeles"
    })
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    assert data["description"] == "Broken streetlight near 5th and Main"
    assert data["location"] == "5th Street and Main Street, Los Angeles"
    assert data["category"] == "maintenance"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert data["recommended_action"] is not None


def test_create_request_auto_classifies(client):
    """POST /requests should automatically classify the request."""
    response = client.post("/requests", json={
        "description": "Gas leak near the park, dangerous emergency",
        "location": "MacArthur Park, Los Angeles"
    })
    assert response.status_code == 200

    data = response.json()
    assert data["category"] == "safety"
    assert data["priority"] == "critical"


def test_create_request_missing_description(client):
    """POST /requests without description should return 422."""
    response = client.post("/requests", json={
        "location": "5th Street"
    })
    assert response.status_code == 422


def test_create_request_missing_location(client):
    """POST /requests without location should return 422."""
    response = client.post("/requests", json={
        "description": "Broken streetlight"
    })
    assert response.status_code == 422


def test_create_request_default_status(client):
    """New requests should always have status 'open'."""
    response = client.post("/requests", json={
        "description": "Pothole on Wilshire Blvd",
        "location": "Wilshire Boulevard, Los Angeles"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "open"


# ── GET /requests TESTS ─────────────────────────────────────────────

def test_get_all_requests_empty(client):
    """GET /requests on empty database should return empty list."""
    response = client.get("/requests")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_requests_returns_list(client):
    """GET /requests should return all submitted requests."""
    # Create two requests first
    client.post("/requests", json={
        "description": "Broken streetlight",
        "location": "5th and Main"
    })
    client.post("/requests", json={
        "description": "Pothole on Wilshire",
        "location": "Wilshire Blvd"
    })

    response = client.get("/requests")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_requests_filter_by_category(client):
    """GET /requests?category=maintenance should filter correctly."""
    client.post("/requests", json={
        "description": "Broken streetlight near Main",
        "location": "Main Street"
    })
    client.post("/requests", json={
        "description": "Gas leak emergency dangerous",
        "location": "Park Avenue"
    })

    response = client.get("/requests?category=maintenance")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "maintenance"


def test_get_requests_filter_by_status(client):
    """GET /requests?status=open should return only open requests."""
    response = client.get("/requests?status=open")
    assert response.status_code == 200
    # All new requests default to open
    for r in response.json():
        assert r["status"] == "open"


# ── GET /requests/{id} TESTS ────────────────────────────────────────

def test_get_single_request(client):
    """GET /requests/{id} should return the correct request."""
    create_response = client.post("/requests", json={
        "description": "Broken streetlight near 5th",
        "location": "5th Street, Los Angeles"
    })
    request_id = create_response.json()["id"]

    response = client.get(f"/requests/{request_id}")
    assert response.status_code == 200
    assert response.json()["id"] == request_id
    assert response.json()["description"] == "Broken streetlight near 5th"


def test_get_request_not_found(client):
    """GET /requests/999 should return 404 when ID does not exist."""
    response = client.get("/requests/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ── PATCH /requests/{id}/status TESTS ──────────────────────────────

def test_update_status_success(client):
    """PATCH status should update the request status correctly."""
    create_response = client.post("/requests", json={
        "description": "Broken streetlight",
        "location": "Main Street"
    })
    request_id = create_response.json()["id"]

    response = client.patch(
        f"/requests/{request_id}/status?status=in_progress"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_status_resolved(client):
    """PATCH status to resolved should work correctly."""
    create_response = client.post("/requests", json={
        "description": "Pothole on Wilshire",
        "location": "Wilshire Blvd"
    })
    request_id = create_response.json()["id"]

    response = client.patch(
        f"/requests/{request_id}/status?status=resolved"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"


def test_update_status_invalid(client):
    """PATCH with invalid status should return 400."""
    create_response = client.post("/requests", json={
        "description": "Broken streetlight",
        "location": "Main Street"
    })
    request_id = create_response.json()["id"]

    response = client.patch(
        f"/requests/{request_id}/status?status=invalid_status"
    )
    assert response.status_code == 400


def test_update_status_not_found(client):
    """PATCH status on non-existent ID should return 404."""
    response = client.patch("/requests/999/status?status=resolved")
    assert response.status_code == 404


# ── HEALTH CHECK TESTS ──────────────────────────────────────────────

def test_health_check(client):
    """GET /health should return ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint(client):
    """GET / should return running message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "running" in response.json()["message"].lower()