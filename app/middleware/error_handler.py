"""Global Error Handler Middleware.

Provides centralized exception handling for FastAPI.
Ensures all errors return JSON responses with consistent format.
"""

import logging
import traceback
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """Create a standardized error response.

    Args:
        status_code: HTTP status code
        error: Error type/name
        message: Human-readable error message
        details: Additional error details
        request_id: Unique request identifier

    Returns:
        JSONResponse with error payload
    """
    content = {
        "error": error,
        "message": message,
        "status_code": status_code,
    }

    if details:
        content["details"] = details

    if request_id:
        content["request_id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=content,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle HTTP exceptions.

    Args:
        request: FastAPI request
        exc: HTTP exception

    Returns:
        JSON error response
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))

    # Map status codes to error names
    error_names = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
    }

    error_name = error_names.get(exc.status_code, "Error")

    # Log error
    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={"request_id": request_id},
        )
    else:
        logger.warning(
            f"HTTP {exc.status_code}: {exc.detail}",
            extra={"request_id": request_id},
        )

    return create_error_response(
        status_code=exc.status_code,
        error=error_name,
        message=str(exc.detail),
        request_id=request_id,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors.

    Args:
        request: FastAPI request
        exc: Validation exception

    Returns:
        JSON error response with field details
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))

    # Extract validation error details
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        f"Validation error: {errors}",
        extra={"request_id": request_id},
    )

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error="Validation Error",
        message="Request validation failed",
        details={"errors": errors},
        request_id=request_id,
    )


async def pydantic_validation_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors.

    Args:
        request: FastAPI request
        exc: Pydantic ValidationError

    Returns:
        JSON error response
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))

    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
        })

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error="Validation Error",
        message="Data validation failed",
        details={"errors": errors},
        request_id=request_id,
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Handle database errors.

    Logs full error but returns sanitized message to client.

    Args:
        request: FastAPI request
        exc: SQLAlchemy exception

    Returns:
        JSON error response
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))

    # Log full error for debugging
    logger.error(
        f"Database error: {exc}",
        extra={
            "request_id": request_id,
            "traceback": traceback.format_exc(),
        },
    )

    # Return sanitized message
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="Database Error",
        message="A database error occurred. Please try again later.",
        request_id=request_id,
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle all unhandled exceptions.

    Catches any exception not handled by specific handlers.
    Logs full error but returns generic message to client.

    Args:
        request: FastAPI request
        exc: Any exception

    Returns:
        JSON error response
    """
    request_id = getattr(request.state, "request_id", str(uuid4()))

    # Log full error
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "traceback": traceback.format_exc(),
            "exception_type": type(exc).__name__,
        },
    )

    # In development, include more details
    if settings.DEBUG:
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=str(exc),
            details={
                "exception_type": type(exc).__name__,
            },
            request_id=request_id,
        )

    # In production, return generic message
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="Internal Server Error",
        message="An unexpected error occurred. Please try again later.",
        request_id=request_id,
    )


def configure_error_handlers(app: FastAPI) -> None:
    """Configure all error handlers for the application.

    Args:
        app: FastAPI application
    """
    # HTTP exceptions (401, 403, 404, etc.)
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,  # type: ignore[arg-type]
    )

    # Request validation errors (Pydantic)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )

    # Pydantic validation errors
    app.add_exception_handler(
        ValidationError,
        pydantic_validation_handler,  # type: ignore[arg-type]
    )

    # Database errors
    app.add_exception_handler(
        SQLAlchemyError,
        database_exception_handler,  # type: ignore[arg-type]
    )

    # Generic catch-all (must be last)
    app.add_exception_handler(
        Exception,
        generic_exception_handler,
    )

    logger.info("Error handlers configured")
