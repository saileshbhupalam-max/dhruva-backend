"""FastAPI dependency injection module.

This module contains FastAPI dependencies for:
- Authentication: JWT token validation and user extraction
- Authorization: Role-based access control
- Database: Session management
"""

from app.dependencies.auth import (
    get_current_user,
    get_current_active_user,
    require_role,
    oauth2_scheme,
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_role",
    "oauth2_scheme",
]
