"""Test Grievance model with relationships."""

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.district import District
from app.models.grievance import Grievance
from app.models.user import User


@pytest.mark.integration
async def test_create_grievance_with_relationships(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
    sample_department_data: dict[str, Any],
    sample_user_data: dict[str, Any],
    sample_grievance_data: dict[str, Any],
) -> None:
    """Test creating a grievance with all required relationships."""
    # Create related entities
    district = District(**sample_district_data)
    department = Department(**sample_department_data)
    user = User(**sample_user_data)

    db_session.add(district)
    db_session.add(department)
    db_session.add(user)
    await db_session.flush()

    # Create grievance
    grievance = Grievance(
        **sample_grievance_data,
        citizen_id=user.id,
        district_id=district.id,
        department_id=department.id,
    )
    db_session.add(grievance)
    await db_session.flush()
    await db_session.refresh(grievance)

    assert grievance.id is not None
    assert grievance.grievance_id == sample_grievance_data["grievance_id"]
    assert grievance.citizen_id == user.id
    assert grievance.district_id == district.id
    assert grievance.department_id == department.id


@pytest.mark.integration
async def test_grievance_relationships(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
    sample_department_data: dict[str, Any],
    sample_user_data: dict[str, Any],
    sample_grievance_data: dict[str, Any],
) -> None:
    """Test grievance relationships are loaded correctly."""
    # Create related entities
    district = District(**sample_district_data)
    department = Department(**sample_department_data)
    user = User(**sample_user_data)

    db_session.add(district)
    db_session.add(department)
    db_session.add(user)
    await db_session.flush()

    # Create grievance
    grievance = Grievance(
        **sample_grievance_data,
        citizen_id=user.id,
        district_id=district.id,
        department_id=department.id,
    )
    db_session.add(grievance)
    await db_session.flush()
    grievance_id = grievance.id

    # Read with relationships
    stmt = select(Grievance).where(Grievance.id == grievance_id)
    result = await db_session.execute(stmt)
    found = result.scalar_one_or_none()

    assert found is not None
    assert found.citizen.mobile_number == sample_user_data["mobile_number"]
    assert found.district.district_code == sample_district_data["district_code"]
    assert found.department.dept_code == sample_department_data["dept_code"]


@pytest.mark.integration
async def test_grievance_soft_delete(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
    sample_department_data: dict[str, Any],
    sample_user_data: dict[str, Any],
    sample_grievance_data: dict[str, Any],
) -> None:
    """Test grievance soft delete."""
    # Create related entities
    district = District(**sample_district_data)
    department = Department(**sample_department_data)
    user = User(**sample_user_data)

    db_session.add(district)
    db_session.add(department)
    db_session.add(user)
    await db_session.flush()

    # Create grievance
    grievance = Grievance(
        **sample_grievance_data,
        citizen_id=user.id,
        district_id=district.id,
        department_id=department.id,
    )
    db_session.add(grievance)
    await db_session.flush()

    # Soft delete
    grievance.soft_delete()
    await db_session.flush()
    await db_session.refresh(grievance)

    assert grievance.deleted_at is not None
    assert grievance.is_deleted is True
