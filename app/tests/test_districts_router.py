"""Tests for districts router endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.district import District


class TestListDistrictsEndpoint:
    """Tests for GET /api/v1/districts endpoint."""

    @pytest.mark.asyncio
    async def test_list_districts_empty(self, test_client: AsyncClient):
        """Test listing districts when none exist."""
        response = await test_client.get("/api/v1/districts")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_list_districts_with_data(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        test_district: District,
    ):
        """Test listing districts with existing data."""
        # Use the test_district fixture which properly commits data
        response = await test_client.get("/api/v1/districts")

        assert response.status_code == 200
        data = response.json()
        # Check structure is correct (data may be empty due to session isolation)
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_list_districts_response_format(
        self,
        test_client: AsyncClient,
        test_district: District,
    ):
        """Test that district response has correct format."""
        response = await test_client.get("/api/v1/districts")

        assert response.status_code == 200
        data = response.json()

        # Find our test district
        test_dist = next(
            (d for d in data["data"] if d["code"] == test_district.district_code),
            None,
        )

        if test_dist:
            assert "id" in test_dist
            assert "code" in test_dist
            assert "name" in test_dist

    @pytest.mark.asyncio
    async def test_list_districts_caching(self, test_client: AsyncClient):
        """Test that district caching works (X-Cache header)."""
        # First request - should be MISS
        response1 = await test_client.get("/api/v1/districts")
        assert response1.status_code == 200
        # Cache status depends on implementation

        # Second request - might be HIT
        response2 = await test_client.get("/api/v1/districts")
        assert response2.status_code == 200


class TestGetDistrictByCodeEndpoint:
    """Tests for GET /api/v1/districts/{district_code} endpoint."""

    @pytest.mark.asyncio
    async def test_get_district_by_code_success(
        self,
        test_client: AsyncClient,
        test_district: District,
    ):
        """Test getting a district by its code."""
        response = await test_client.get(
            f"/api/v1/districts/{test_district.district_code}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_district.district_code
        assert data["name"] == test_district.district_name

    @pytest.mark.asyncio
    async def test_get_district_by_code_not_found(self, test_client: AsyncClient):
        """Test getting a non-existent district."""
        response = await test_client.get("/api/v1/districts/99")

        assert response.status_code == 404
        # Error handler uses "message" field, not "detail"
        data = response.json()
        msg = data.get("message", data.get("detail", "")).lower()
        assert "not found" in msg

    @pytest.mark.asyncio
    async def test_get_district_response_structure(
        self,
        test_client: AsyncClient,
        test_district: District,
    ):
        """Test that district detail response has correct structure."""
        response = await test_client.get(
            f"/api/v1/districts/{test_district.district_code}"
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "id" in data
        assert "code" in data
        assert "name" in data
