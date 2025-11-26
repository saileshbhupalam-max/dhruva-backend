"""API Versioning and Deprecation Middleware.

Handles API versioning headers and deprecation warnings.
Adds Deprecation, Sunset, and Link headers for deprecated endpoints.
"""

import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, Optional, Tuple

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


# Deprecated endpoints configuration
# Format: "METHOD:PATH" -> (sunset_date, replacement_path, message)
DEPRECATED_ENDPOINTS: Dict[str, Tuple[Optional[datetime], Optional[str], str]] = {
    # Example (no endpoints deprecated yet):
    # "GET:/api/v1/old-endpoint": (
    #     datetime(2025, 6, 1, tzinfo=timezone.utc),
    #     "/api/v2/new-endpoint",
    #     "This endpoint is deprecated. Use /api/v2/new-endpoint instead."
    # ),
}

# Sunset endpoints (completely removed)
SUNSET_ENDPOINTS: Dict[str, str] = {
    # "GET:/api/v0/endpoint": "This endpoint has been removed. Use /api/v1/endpoint."
}


class DeprecationMiddleware(BaseHTTPMiddleware):
    """Middleware for API versioning and deprecation.

    Adds deprecation headers to deprecated endpoints.
    Returns 410 Gone for sunset endpoints.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with deprecation handling.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with deprecation headers
        """
        method = request.method
        path = request.url.path
        endpoint_key = f"{method}:{path}"

        # Check for sunset (removed) endpoints
        if endpoint_key in SUNSET_ENDPOINTS:
            message = SUNSET_ENDPOINTS[endpoint_key]
            logger.warning(f"Request to sunset endpoint: {endpoint_key}")
            return JSONResponse(
                status_code=410,
                content={
                    "error": "Gone",
                    "message": message,
                    "status_code": 410,
                },
            )

        # Process request
        response = await call_next(request)

        # Check for deprecated endpoints
        if endpoint_key in DEPRECATED_ENDPOINTS:
            sunset_date, replacement, message = DEPRECATED_ENDPOINTS[endpoint_key]

            # Add Deprecation header
            response.headers["Deprecation"] = "true"

            # Add Warning header
            response.headers["Warning"] = f'299 - "{message}"'

            # Add Sunset header if date is set
            if sunset_date:
                sunset_str = sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")
                response.headers["Sunset"] = sunset_str

            # Add Link header to replacement
            if replacement:
                response.headers["Link"] = f'<{replacement}>; rel="successor-version"'

            logger.info(f"Deprecated endpoint accessed: {endpoint_key}")

        # Always add API version header
        response.headers["X-API-Version"] = "v1"

        return response


def configure_deprecation_middleware(app: FastAPI) -> None:
    """Configure deprecation middleware.

    Args:
        app: FastAPI application
    """
    app.add_middleware(DeprecationMiddleware)
    logger.info("Deprecation middleware configured")


def deprecate_endpoint(
    method: str,
    path: str,
    sunset_date: Optional[datetime] = None,
    replacement_path: Optional[str] = None,
    message: str = "This endpoint is deprecated.",
) -> None:
    """Mark an endpoint as deprecated.

    Call this function to deprecate an endpoint programmatically.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: URL path
        sunset_date: When the endpoint will be removed
        replacement_path: Path to the replacement endpoint
        message: Deprecation message
    """
    endpoint_key = f"{method}:{path}"
    DEPRECATED_ENDPOINTS[endpoint_key] = (sunset_date, replacement_path, message)
    logger.info(f"Endpoint deprecated: {endpoint_key}")


def sunset_endpoint(
    method: str,
    path: str,
    message: str = "This endpoint has been removed.",
) -> None:
    """Mark an endpoint as sunset (completely removed).

    Args:
        method: HTTP method
        path: URL path
        message: Error message
    """
    endpoint_key = f"{method}:{path}"
    SUNSET_ENDPOINTS[endpoint_key] = message
    logger.info(f"Endpoint sunset: {endpoint_key}")
