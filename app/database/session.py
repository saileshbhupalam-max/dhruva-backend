"""Database session management for FastAPI dependency injection."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import PostgreSQLDatabaseService

# Global database instance (initialized at startup)
_db_service: PostgreSQLDatabaseService | None = None


async def init_database() -> None:
    """Initialize database connection (call at app startup).

    Example usage in FastAPI:
        @app.on_event("startup")
        async def startup_event():
            await init_database()
    """
    global _db_service
    _db_service = PostgreSQLDatabaseService(settings.DATABASE_URL)
    await _db_service.connect()


async def close_database() -> None:
    """Close database connection (call at app shutdown).

    Example usage in FastAPI:
        @app.on_event("shutdown")
        async def shutdown_event():
            await close_database()
    """
    global _db_service
    if _db_service is not None:
        await _db_service.disconnect()
        _db_service = None


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database session.

    Provides automatic:
    - Session creation
    - Transaction management (commit/rollback)
    - Resource cleanup

    Usage in FastAPI:
        from fastapi import Depends
        from app.database.session import get_db

        @router.get("/grievances")
        async def list_grievances(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Grievance))
            return result.scalars().all()

    Raises:
        RuntimeError: If database not initialized (call init_database() at startup)
    """
    if _db_service is None:
        raise RuntimeError("Database not initialized. Call init_database() at startup.")

    async with _db_service.get_session() as session:
        yield session


# Convenience function to get async session generator (non-dependency version)
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async session outside of FastAPI dependency injection.

    Use this for background tasks, CLI scripts, or testing.

    Example:
        async with get_async_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
    """
    async with get_db() as session:
        yield session


# Alias for backward compatibility
AsyncSessionLocal = get_async_session
