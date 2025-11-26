"""Test DatabaseService generic CRUD operations."""

from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.service import DatabaseService
from app.models.district import District


@pytest.mark.integration
async def test_service_create(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
) -> None:
    """Test service create method."""
    service = DatabaseService(District)
    district = await service.create(db_session, **sample_district_data)

    assert district.id is not None
    assert district.district_code == sample_district_data["district_code"]


@pytest.mark.integration
async def test_service_get_by_id(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
) -> None:
    """Test service get_by_id method."""
    service = DatabaseService(District)

    # Create
    district = await service.create(db_session, **sample_district_data)
    district_id = district.id

    # Read
    found = await service.get_by_id(db_session, district_id)
    assert found is not None
    assert found.id == district_id


@pytest.mark.integration
async def test_service_get_all(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
) -> None:
    """Test service get_all method with pagination."""
    service = DatabaseService(District)

    # Create multiple districts
    for i in range(5):
        data = sample_district_data.copy()
        data["district_code"] = f"TEST{i:02d}"
        await service.create(db_session, **data)

    # Get all
    districts = await service.get_all(db_session, skip=0, limit=10)
    assert len(districts) >= 5


@pytest.mark.integration
async def test_service_update(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
) -> None:
    """Test service update method."""
    service = DatabaseService(District)

    # Create
    district = await service.create(db_session, **sample_district_data)
    district_id = district.id

    # Update
    updated = await service.update(
        db_session,
        district_id,
        district_name="Updated District Name",
    )
    assert updated is not None
    assert updated.district_name == "Updated District Name"


@pytest.mark.integration
async def test_service_delete(
    db_session: AsyncSession,
    sample_user_data: dict[str, Any],
) -> None:
    """Test service soft delete method."""
    from app.database.service import DatabaseService
    from app.models.user import User

    service = DatabaseService(User)

    # Create user
    user = await service.create(db_session, **sample_user_data)
    user_id = user.id

    # Delete (soft)
    result = await service.delete(db_session, user_id)
    assert result is True

    # Verify soft delete
    found = await service.get_by_id(db_session, user_id)
    assert found is None  # Should not be found (filtered out)


@pytest.mark.integration
async def test_service_exists(
    db_session: AsyncSession,
    sample_district_data: dict[str, Any],
) -> None:
    """Test service exists method."""
    service = DatabaseService(District)

    # Create
    district = await service.create(db_session, **sample_district_data)
    district_id = district.id

    # Check exists
    exists = await service.exists(db_session, district_id)
    assert exists is True
