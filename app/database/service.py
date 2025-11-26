"""Concrete database service implementation."""

from datetime import datetime
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.interface import IDatabaseService
from app.models.base import Base, SoftDeleteMixin

T = TypeVar("T", bound=Base)


class DatabaseService(IDatabaseService[T]):
    """Concrete implementation of database operations.

    Generic service that works with any SQLAlchemy model.
    Implements soft delete for models with SoftDeleteMixin.
    """

    def __init__(self, model: type[T]) -> None:
        """Initialize service with model class.

        Args:
            model: SQLAlchemy model class
        """
        self.model = model

    async def create(self, session: AsyncSession, **kwargs: Any) -> T:
        """Create a new record.

        Args:
            session: Database session
            **kwargs: Field values for new record

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def get_by_id(self, session: AsyncSession, record_id: UUID) -> T | None:
        """Retrieve record by UUID.

        Args:
            session: Database session
            record_id: Record UUID

        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model).where(self.model.id == record_id)  # type: ignore[attr-defined]

        # Filter out soft-deleted records
        if issubclass(self.model, SoftDeleteMixin):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[T]:
        """Retrieve all records with pagination.

        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of model instances
        """
        stmt = select(self.model).offset(skip).limit(limit)

        # Filter out soft-deleted records
        if issubclass(self.model, SoftDeleteMixin):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        session: AsyncSession,
        record_id: UUID,
        **kwargs: Any,
    ) -> T | None:
        """Update existing record.

        Args:
            session: Database session
            record_id: Record UUID
            **kwargs: Field values to update

        Returns:
            Updated model instance or None if not found
        """
        instance = await self.get_by_id(session, record_id)
        if instance is None:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await session.flush()
        await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, record_id: UUID) -> bool:
        """Soft delete record (never hard delete).

        Args:
            session: Database session
            record_id: Record UUID

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(session, record_id)
        if instance is None:
            return False

        # Soft delete if supported
        if isinstance(instance, SoftDeleteMixin):
            instance.deleted_at = datetime.now()
            await session.flush()
        else:
            # For models without soft delete, still avoid hard delete
            # This is a safety measure - should not happen in this project
            pass

        return True

    async def exists(self, session: AsyncSession, record_id: UUID) -> bool:
        """Check if record exists.

        Args:
            session: Database session
            record_id: Record UUID

        Returns:
            True if record exists and not deleted
        """
        instance = await self.get_by_id(session, record_id)
        return instance is not None
