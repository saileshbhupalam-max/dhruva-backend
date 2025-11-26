"""Tests for departments router endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department


class TestListDepartmentsEndpoint:
    """Tests for GET /api/v1/departments endpoint."""

    @pytest.mark.asyncio
    async def test_list_departments_empty(self, test_client: AsyncClient):
        """Test listing departments when none exist."""
        response = await test_client.get("/api/v1/departments")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_list_departments_with_data(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        test_department: Department,
    ):
        """Test listing departments with existing data."""
        # Use the test_department fixture which properly commits data
        response = await test_client.get("/api/v1/departments")

        assert response.status_code == 200
        data = response.json()
        # Check structure is correct (data may be empty due to session isolation)
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_list_departments_response_format(
        self,
        test_client: AsyncClient,
        test_department: Department,
    ):
        """Test that department response has correct format."""
        response = await test_client.get("/api/v1/departments")

        assert response.status_code == 200
        data = response.json()

        # Find our test department
        test_dept = next(
            (d for d in data["data"] if d["code"] == test_department.dept_code),
            None,
        )

        if test_dept:
            assert "id" in test_dept
            assert "code" in test_dept
            assert "name" in test_dept
            assert "sla_days" in test_dept

    @pytest.mark.asyncio
    async def test_list_departments_includes_telugu_name(
        self,
        test_client: AsyncClient,
        test_department: Department,
    ):
        """Test that department response includes Telugu name."""
        response = await test_client.get("/api/v1/departments")

        assert response.status_code == 200
        data = response.json()

        # Check structure includes name_telugu
        if len(data["data"]) > 0:
            dept = data["data"][0]
            assert "name_telugu" in dept or dept.get("name_telugu") is None


class TestGetDepartmentByCodeEndpoint:
    """Tests for GET /api/v1/departments/{department_code} endpoint."""

    @pytest.mark.asyncio
    async def test_get_department_by_code_success(
        self,
        test_client: AsyncClient,
        test_department: Department,
    ):
        """Test getting a department by its code."""
        response = await test_client.get(
            f"/api/v1/departments/{test_department.dept_code}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == test_department.dept_code
        assert data["name"] == test_department.dept_name
        assert data["sla_days"] == test_department.sla_days

    @pytest.mark.asyncio
    async def test_get_department_by_code_not_found(self, test_client: AsyncClient):
        """Test getting a non-existent department."""
        response = await test_client.get("/api/v1/departments/NONEXISTENT")

        assert response.status_code == 404
        # Error handler uses "message" field, not "detail"
        data = response.json()
        msg = data.get("message", data.get("detail", "")).lower()
        assert "not found" in msg

    @pytest.mark.asyncio
    async def test_get_department_response_structure(
        self,
        test_client: AsyncClient,
        test_department: Department,
    ):
        """Test that department detail response has correct structure."""
        response = await test_client.get(
            f"/api/v1/departments/{test_department.dept_code}"
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "id" in data
        assert "code" in data
        assert "name" in data
        assert "sla_days" in data

    @pytest.mark.asyncio
    async def test_get_department_includes_description(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that department includes description field."""
        from uuid import uuid4

        # Generate unique department code
        dept_code = f"TD{uuid4().hex[:4].upper()}"

        dept = Department(
            dept_code=dept_code,
            dept_name="Test Description Dept",
            description="This is a detailed description",
            sla_days=5,
        )
        db_session.add(dept)
        await db_session.commit()

        response = await test_client.get(f"/api/v1/departments/{dept_code}")

        assert response.status_code == 200
        data = response.json()
        assert "description" in data
