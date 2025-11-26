"""Test health check endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.integration
def test_root_endpoint() -> None:
    """Test root endpoint returns app info."""
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


@pytest.mark.integration
def test_health_check_endpoint() -> None:
    """Test health check endpoint with database connectivity."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert data["status"] in ["healthy", "unhealthy", "degraded"]
    # database is a dict with health details
    assert isinstance(data["database"], dict)


@pytest.mark.integration
def test_health_check_includes_environment() -> None:
    """Test health check returns environment information."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "environment" in data


@pytest.mark.integration
def test_health_check_includes_redis() -> None:
    """Test health check returns Redis information."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "redis" in data
    assert "status" in data["redis"]


@pytest.mark.integration
def test_redis_health_endpoint() -> None:
    """Test Redis health check endpoint."""
    client = TestClient(app)
    response = client.get("/health/redis")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # Either healthy, unhealthy, or disabled
    assert data["status"] in ["healthy", "unhealthy", "disabled"]


@pytest.mark.integration
def test_database_health_endpoint() -> None:
    """Test database health check endpoint."""
    client = TestClient(app)
    response = client.get("/health/database")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.integration
def test_health_check_includes_version() -> None:
    """Test health check returns version information."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "version" in data
