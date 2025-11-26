"""Database service interface for swappability (antifragile optionality)."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class IDatabaseService(ABC, Generic[T]):
    """Abstract interface for database operations.

    Provides optionality for swapping database implementations
    without affecting dependent code (Taleb's antifragility principle).
    """

    @abstractmethod
    async def create(self, session: AsyncSession, **kwargs: Any) -> T:
        """Create a new record."""
        pass

    @abstractmethod
    async def get_by_id(self, session: AsyncSession, record_id: UUID) -> T | None:
        """Retrieve record by UUID."""
        pass

    @abstractmethod
    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[T]:
        """Retrieve all records with pagination."""
        pass

    @abstractmethod
    async def update(
        self,
        session: AsyncSession,
        record_id: UUID,
        **kwargs: Any,
    ) -> T | None:
        """Update existing record."""
        pass

    @abstractmethod
    async def delete(self, session: AsyncSession, record_id: UUID) -> bool:
        """Soft delete record (never hard delete)."""
        pass

    @abstractmethod
    async def exists(self, session: AsyncSession, record_id: UUID) -> bool:
        """Check if record exists."""
        pass
