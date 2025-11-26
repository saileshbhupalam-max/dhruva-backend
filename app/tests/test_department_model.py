"""Test Department model CRUD operations."""

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department


@pytest.mark.integration
async def test_create_department(
    db_session: AsyncSession,
    sample_department_data: dict[str, Any],
) -> None:
    """Test creating a new department."""
    department = Department(**sample_department_data)
    db_session.add(department)
    await db_session.flush()
    await db_session.refresh(department)

    assert department.id is not None
    assert department.dept_code == sample_department_data["dept_code"]
    assert department.dept_name == sample_department_data["dept_name"]
    assert department.created_at is not None
    assert department.updated_at is not None


@pytest.mark.integration
async def test_read_department(
    db_session: AsyncSession,
    sample_department_data: dict[str, Any],
) -> None:
    """Test reading a department by ID."""
    # Create department
    department = Department(**sample_department_data)
    db_session.add(department)
    await db_session.flush()
    dept_id = department.id

    # Read department
    stmt = select(Department).where(Department.id == dept_id)
    result = await db_session.execute(stmt)
    found_dept = result.scalar_one_or_none()

    assert found_dept is not None
    assert found_dept.id == dept_id
    assert found_dept.dept_code == sample_department_data["dept_code"]


@pytest.mark.integration
async def test_unique_department_code(
    db_session: AsyncSession,
    sample_department_data: dict[str, Any],
) -> None:
    """Test that department code must be unique."""
    # Create first department
    dept1 = Department(**sample_department_data)
    db_session.add(dept1)
    await db_session.flush()

    # Try to create duplicate
    dept2 = Department(**sample_department_data)
    db_session.add(dept2)

    with pytest.raises(Exception):  # Should raise integrity error
        await db_session.flush()
