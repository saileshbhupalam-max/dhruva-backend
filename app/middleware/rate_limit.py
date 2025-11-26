"""Rate Limiting Middleware.

Provides request rate limiting middleware for FastAPI.
Uses Redis-based rate limiter with in-memory fallback.
"""

import logging
from typing import Awaitable, Callable, Dict, Optional, Tuple

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.services.rate_limiter import get_rate_limiter, RateLimitResult

logger = logging.getLogger(__name__)


# Rate limit configurations by endpoint pattern
ENDPOINT_RATE_LIMITS: Dict[str, Tuple[int, int]] = {
    # (limit, window_seconds)
    "POST:/api/v1/grievances": (settings.RATE_LIMIT_GRIEVANCE_SUBMIT, 3600),  # 10/hour
    "POST:/api/v1/grievances/public/": (settings.RATE_LIMIT_OTP_REQUEST, 300),  # 3/5min
    "POST:/api/v1/auth/login": (10, 300),  # 10/5min per IP
}


def get_rate_limit_key(request: Request) -> str:
    """Generate rate limit key from request.

    Uses combination of:
    - User ID (if authenticated)
    - IP address (for unauthenticated)
    - Endpoint path

    Args:
        request: FastAPI request

    Returns:
        Rate limit key string
    """
    # Try to get user ID from state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)

    if user_id:
        identifier = f"user:{user_id}"
    else:
        # Use IP address for unauthenticated requests
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_ip}"

    # Include method and path
    method = request.method
    path = request.url.path

    return f"{method}:{path}:{identifier}"


def get_endpoint_limits(request: Request) -> Tuple[int, int]:
    """Get rate limits for endpoint.

    Args:
        request: FastAPI request

    Returns:
        Tuple of (limit, window_seconds)
    """
    method = request.method
    path = request.url.path

    # Check for exact match first
    key = f"{method}:{path}"
    if key in ENDPOINT_RATE_LIMITS:
        return ENDPOINT_RATE_LIMITS[key]

    # Check for prefix matches
    for endpoint_key, limits in ENDPOINT_RATE_LIMITS.items():
        if key.startswith(endpoint_key):
            return limits

    # Default limits
    return (settings.RATE_LIMIT_DEFAULT_REQUESTS, settings.RATE_LIMIT_DEFAULT_WINDOW)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware.

    Checks rate limits before processing requests.
    Adds X-RateLimit-* headers to all responses.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response with rate limit headers
        """
        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            response = await call_next(request)
            return response

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/database", "/"]:
            response = await call_next(request)
            return response

        # Get rate limit key and limits
        key = get_rate_limit_key(request)
        limit, window = get_endpoint_limits(request)

        # Check rate limit
        rate_limiter = get_rate_limiter()
        result = await rate_limiter.check_rate_limit(key, limit, window)

        if not result.allowed:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for key: {key}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Try again in {result.retry_after} seconds.",
                    "status_code": 429,
                    "retry_after": result.retry_after,
                },
                headers=result.to_headers(),
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for header_name, header_value in result.to_headers().items():
            response.headers[header_name] = header_value

        return response


def configure_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting middleware.

    Args:
        app: FastAPI application
    """
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
        logger.info("Rate limiting middleware enabled")
    else:
        logger.info("Rate limiting middleware disabled")
