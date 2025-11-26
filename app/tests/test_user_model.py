"""Test User model CRUD operations and soft delete."""

from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.integration
async def test_create_user(
    db_session: AsyncSession,
    sample_user_data: dict[str, Any],
) -> None:
    """Test creating a new user."""
    user = User(**sample_user_data)
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.mobile_number == sample_user_data["mobile_number"]
    assert user.email == sample_user_data["email"]
    assert user.full_name == sample_user_data["full_name"]
    assert user.role == sample_user_data["role"]
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.deleted_at is None


@pytest.mark.integration
async def test_soft_delete_user(
    db_session: AsyncSession,
    sample_user_data: dict[str, Any],
) -> None:
    """Test soft delete functionality."""
    # Create user
    user = User(**sample_user_data)
    db_session.add(user)
    await db_session.flush()
    user_id = user.id

    # Soft delete
    user.soft_delete()
    await db_session.flush()
    await db_session.refresh(user)

    assert user.deleted_at is not None
    assert user.is_deleted is True

    # User should still exist in database
    stmt = select(User).where(User.id == user_id)
    result = await db_session.execute(stmt)
    found_user = result.scalar_one_or_none()
    assert found_user is not None


@pytest.mark.integration
async def test_unique_mobile_number(
    db_session: AsyncSession,
    sample_user_data: dict[str, Any],
) -> None:
    """Test that mobile number must be unique."""
    # Create first user
    user1 = User(**sample_user_data)
    db_session.add(user1)
    await db_session.flush()

    # Try to create duplicate
    user2 = User(**sample_user_data)
    db_session.add(user2)

    with pytest.raises(Exception):  # Should raise integrity error
        await db_session.flush()
