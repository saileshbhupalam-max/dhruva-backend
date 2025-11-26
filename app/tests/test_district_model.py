"""Test District model CRUD operations."""

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.district import District


@pytest.mark.integration
async def test_create_district(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
) -> None:
    """Test creating a new district."""
    district = District(**sample_district_data)
    db_session.add(district)
    await db_session.flush()
    await db_session.refresh(district)

    assert district.id is not None
    assert district.district_code == sample_district_data["district_code"]
    assert district.district_name == sample_district_data["district_name"]
    assert district.created_at is not None
    assert district.updated_at is not None


@pytest.mark.integration
async def test_read_district(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
) -> None:
    """Test reading a district by ID."""
    # Create district
    district = District(**sample_district_data)
    db_session.add(district)
    await db_session.flush()
    district_id = district.id

    # Read district
    stmt = select(District).where(District.id == district_id)
    result = await db_session.execute(stmt)
    found_district = result.scalar_one_or_none()

    assert found_district is not None
    assert found_district.id == district_id
    assert found_district.district_code == sample_district_data["district_code"]


@pytest.mark.integration
async def test_unique_district_code(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
) -> None:
    """Test that district code must be unique."""
    # Create first district
    district1 = District(**sample_district_data)
    db_session.add(district1)
    await db_session.flush()

    # Try to create duplicate
    district2 = District(**sample_district_data)
    db_session.add(district2)

    with pytest.raises(Exception):  # Should raise integrity error
        await db_session.flush()
