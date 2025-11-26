"""PostgreSQL database connection service with async support."""

import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.config import settings
from app.models.base import Base


class PostgreSQLDatabaseService:
    """PostgreSQL implementation of IDatabaseService with connection pooling."""

    def __init__(self, database_url: str) -> None:
        """Initialize database service.

        Args:
            database_url: PostgreSQL connection string (must use asyncpg driver)
        """
        self.database_url = database_url
        self.engine: AsyncEngine | None = None
        self.async_session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        """Initialize connection pool with antifragile settings.

        Creates async engine with:
        - Connection pooling (10 base, 20 overflow)
        - Pre-ping health checks
        - Automatic connection recycling
        - Graceful degradation on connection failures
        """
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.DATABASE_ECHO,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.DATABASE_POOL_SIZE,  # 10 connections in pool
            max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Max 30 total
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,  # Wait 30s for connection
            pool_recycle=settings.DATABASE_POOL_RECYCLE,  # Recycle after 1 hour
            pool_pre_ping=True,  # Check connection before using (graceful degradation)
        )

        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        # Create tables only in development (in production, use Alembic migrations)
        if settings.ENVIRONMENT == "development":
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    async def disconnect(self) -> None:
        """Close all connections gracefully and dispose of engine."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.async_session_factory = None

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup and rollback on error.

        Yields:
            AsyncSession instance

        Raises:
            RuntimeError: If database not connected (call connect() first)

        Example:
            async with db_service.get_session() as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
        """
        if self.async_session_factory is None:
            raise RuntimeError("Database not connected. Call connect() first.")

        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def health_check(self) -> Dict[str, Any]:
        """Check database health and measure latency.

        Returns:
            Dictionary with health status, latency, and pool statistics:
            {
                "status": "healthy" | "unhealthy",
                "latency_ms": float,
                "connection_pool_size": int,
                "connections_in_use": int,
                "database_url": str (masked)
            }
        """
        start_time = time.time()

        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()

            latency_ms = (time.time() - start_time) * 1000

            # Pool statistics (cast to Any to avoid mypy strict pool typing issues)
            from typing import cast
            pool: Any = self.engine.pool if self.engine else None
            pool_size = pool.size() if pool and hasattr(pool, 'size') else 0
            pool_checked_out = pool.checkedout() if pool and hasattr(pool, 'checkedout') else 0

            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "connection_pool_size": pool_size,
                "connections_in_use": pool_checked_out,
                "database_url": self._mask_db_url(self.database_url),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

    @staticmethod
    def _mask_db_url(url: str) -> str:
        """Mask password in database URL for logging.

        Args:
            url: Full database URL with credentials

        Returns:
            Masked URL showing only host/database (password hidden)
        """
        if "@" in url:
            return url.split("@")[1]  # Return only host/database part
        return "hidden"


# Global database instance (singleton)
_db_service: PostgreSQLDatabaseService | None = None


async def init_db() -> None:
    """Initialize database connection at app startup.

    Creates the global database service and establishes connection pool.
    Should be called from FastAPI lifespan context.
    """
    global _db_service
    _db_service = PostgreSQLDatabaseService(settings.DATABASE_URL)
    await _db_service.connect()


async def close_db() -> None:
    """Close database connection at app shutdown.

    Gracefully disconnects from database and releases resources.
    Should be called from FastAPI lifespan context.
    """
    global _db_service
    if _db_service is not None:
        await _db_service.disconnect()
        _db_service = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Provides an async database session that is automatically
    committed on success or rolled back on error.

    Yields:
        AsyncSession instance

    Raises:
        RuntimeError: If database not initialized

    Usage:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    if _db_service is None:
        raise RuntimeError("Database not initialized. Call init_db() at startup.")

    async with _db_service.get_session() as session:
        yield session


def get_db_service() -> PostgreSQLDatabaseService | None:
    """Get the current database service instance.

    Returns:
        PostgreSQLDatabaseService or None if not initialized
    """
    return _db_service
