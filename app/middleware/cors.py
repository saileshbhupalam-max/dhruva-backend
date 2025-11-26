"""CORS Middleware configuration.

Configures Cross-Origin Resource Sharing for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the application.

    Adds CORS middleware with settings from configuration.
    Should be called during application startup.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.cors_methods_list,
        allow_headers=settings.cors_headers_list,
        max_age=3600,  # Cache preflight for 1 hour
    )
