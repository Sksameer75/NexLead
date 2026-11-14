"""Unit and integration tests for health and database endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_health():
    """Verify root health check returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data


def test_api_v1_health():
    """Verify API v1 health endpoint returns 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == "development"


def test_database_health():
    """Verify database connectivity endpoint."""
    response = client.get("/api/v1/health/db")
    # In an environment with MySQL running, status should be 200 with connected status
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert data["database"] == "mysql"


def test_detailed_health():
    """Verify detailed combined health endpoint."""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "database" in data

