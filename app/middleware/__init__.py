"""Middleware module.

This module contains FastAPI middleware for:
- CORS: Cross-Origin Resource Sharing configuration
- Rate Limiting: Request rate limiting with Redis
- Error Handling: Global exception handling
- Deprecation: API versioning and deprecation headers
"""

from app.middleware.cors import configure_cors
from app.middleware.error_handler import configure_error_handlers
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.deprecation import DeprecationMiddleware

__all__ = [
    "configure_cors",
    "configure_error_handlers",
    "RateLimitMiddleware",
    "DeprecationMiddleware",
]
