"""Health check endpoints for monitoring database and application status."""

from typing import Any, Dict

from fastapi import APIRouter

from app.config import settings
from app.database.connection import get_db_service
from app.services.rate_limiter import get_rate_limiter

router = APIRouter()


@router.get("/health/database")
async def database_health_check() -> Dict[str, Any]:
    """
    Check database health (connection pool, latency).

    Returns comprehensive health metrics:
    - Connection status (healthy/unhealthy)
    - Query latency in milliseconds
    - Connection pool size and usage
    - Masked database URL

    Returns:
        {
            "status": "healthy" | "unhealthy",
            "latency_ms": float,
            "connection_pool_size": int,
            "connections_in_use": int,
            "database_url": str (masked for security)
        }

    Status Codes:
        200: Database is healthy
        200: Database is unhealthy (still returns 200 but status="unhealthy")

    Example Response (Healthy):
        {
            "status": "healthy",
            "latency_ms": 12.34,
            "connection_pool_size": 10,
            "connections_in_use": 2,
            "database_url": "localhost:5432/dhruva_pgrs"
        }

    Example Response (Unhealthy):
        {
            "status": "unhealthy",
            "error": "Database not initialized",
            "latency_ms": 0.0
        }
    """
    db_service = get_db_service()

    if db_service is None:
        return {"status": "unhealthy", "error": "Database not initialized"}

    health = await db_service.health_check()
    return health


@router.get("/health")
async def general_health_check() -> Dict[str, Any]:
    """
    General application health check.

    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "database": {...database health...},
            "redis": {...redis health...},
            "version": "1.0.0",
            "environment": "development" | "production"
        }
    """
    db_service = get_db_service()

    # Check database health
    db_health = {"connected": False, "status": "unknown"}
    overall_status = "healthy"

    if db_service is not None:
        db_health = await db_service.health_check()
        if db_health["status"] != "healthy":
            overall_status = "degraded"
    else:
        overall_status = "degraded"
        db_health = {"connected": False, "error": "Database not initialized"}

    # Check Redis health
    rate_limiter = get_rate_limiter()
    redis_health = await rate_limiter.health_check()
    if redis_health.get("status") == "unhealthy":
        # Redis unhealthy is degraded, not critical (we have in-memory fallback)
        if overall_status == "healthy":
            overall_status = "degraded"

    return {
        "status": overall_status,
        "database": db_health,
        "redis": redis_health,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/redis")
async def redis_health_check() -> Dict[str, Any]:
    """
    Check Redis health (connection, latency).

    Returns health metrics for Redis:
    - Connection status (healthy/unhealthy/disabled)
    - Backend type (redis/in_memory)
    - URL (masked for security)

    Returns:
        {
            "status": "healthy" | "unhealthy" | "disabled",
            "backend": "redis" | "in_memory",
            "enabled": bool
        }

    Example Response (Healthy):
        {
            "status": "healthy",
            "enabled": true,
            "backend": "redis",
            "url": "localhost:6379/0"
        }

    Example Response (Degraded - using in-memory):
        {
            "status": "healthy",
            "enabled": true,
            "backend": "in_memory",
            "tracked_keys": 42
        }
    """
    rate_limiter = get_rate_limiter()
    health = await rate_limiter.health_check()
    return health
