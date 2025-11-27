"""FastAPI application entry point.

Configures the application with all middleware, routers, and event handlers.
Build: 2024-11-27-refresh
"""

import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from app.config import settings
from app.database.connection import close_db, init_db
from app.middleware.cors import configure_cors
from app.middleware.deprecation import configure_deprecation_middleware
from app.middleware.error_handler import configure_error_handlers
from app.middleware.rate_limit import configure_rate_limiting

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Handles startup and shutdown events.
    Railway-compatible: Gracefully handles missing services.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Try to initialize database, but don't fail if not available
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed (will retry on first request): {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    try:
        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Public Grievance Redressal System API for Andhra Pradesh",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# Request ID middleware (must be first)
@app.middleware("http")
async def add_request_id(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Add unique request ID to each request."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


# Configure middleware (order matters!)
# 1. CORS (must be early to handle preflight)
configure_cors(app)

# 2. Rate limiting
configure_rate_limiting(app)

# 3. Deprecation headers
configure_deprecation_middleware(app)

# 4. Error handlers (catches all exceptions)
configure_error_handlers(app)


# Import routers (after app is created)
from app.routers import admin, auth, departments, districts, empathy, empowerment, grievances, health, ml, public, public_dashboard, resolution, verifier

# Register routers
app.include_router(
    health.router,
    tags=["Health"],
)

app.include_router(
    auth.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Authentication"],
)

app.include_router(
    districts.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Districts"],
)

app.include_router(
    departments.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Departments"],
)

app.include_router(
    grievances.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Grievances"],
)

app.include_router(
    public.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Public"],
)

app.include_router(
    public_dashboard.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Public Dashboard"],
)

app.include_router(
    empathy.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Empathy Engine"],
)

app.include_router(
    resolution.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Smart Resolution"],
)

app.include_router(
    empowerment.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Citizen Empowerment"],
)

app.include_router(
    ml.router,
    prefix=settings.API_V1_PREFIX,
    tags=["ML Pipeline"],
)

app.include_router(
    admin.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Admin Analytics"],
)

app.include_router(
    verifier.router,
    prefix=settings.API_V1_PREFIX,
    tags=["Verifier Portal"],
)


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# Simple health check (Railway-compatible - no DB dependency)
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Quick health check endpoint for Railway/load balancers.

    This endpoint does NOT check database - it only confirms the app is running.
    For detailed health info including DB, use /health/database.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


