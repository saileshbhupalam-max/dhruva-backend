"""Authentication and authorization dependencies for FastAPI.

Provides dependency injection functions for:
- Extracting and validating JWT tokens
- Getting the current authenticated user
- Role-based access control
- Token blacklist checking for logout support
"""

from typing import Awaitable, Callable, List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import get_db_session
from app.models.user import User
from app.services.token_blacklist import is_token_blacklisted
from app.utils.jwt import TokenData, decode_token

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=True,
)

# Optional OAuth2 scheme that doesn't raise error if token missing
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Get the current authenticated user from JWT token.

    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Validates and decodes the token
    3. Checks if token is blacklisted (logout check)
    4. Retrieves the user from the database
    5. Validates the user is active and not deleted

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException 401: If token is invalid, expired, blacklisted, or user not found
        HTTPException 403: If user is inactive or deleted

    Example:
        @router.get("/protected")
        async def protected_route(
            current_user: User = Depends(get_current_user)
        ):
            return {"message": f"Hello, {current_user.full_name}"}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = decode_token(token)
    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception

    # Check if token is blacklisted (user logged out)
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    try:
        user_id = UUID(token_data.user_id)
    except ValueError:
        raise credentials_exception

    stmt = select(User).where(
        User.id == user_id,
        User.deleted_at.is_(None),  # Not soft-deleted
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user.

    Alias for get_current_user that explicitly checks is_active.
    The check is already done in get_current_user, but this provides
    a more explicit dependency name.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Active User model instance

    Raises:
        HTTPException 403: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """Get the current user if authenticated, None otherwise.

    Use this for endpoints that work for both authenticated
    and unauthenticated users.

    Args:
        token: Optional JWT token from Authorization header
        db: Database session

    Returns:
        User model instance if authenticated, None otherwise

    Example:
        @router.get("/public")
        async def public_route(
            current_user: Optional[User] = Depends(get_optional_user)
        ):
            if current_user:
                return {"message": f"Hello, {current_user.full_name}"}
            return {"message": "Hello, guest"}
    """
    if token is None:
        return None

    try:
        token_data = decode_token(token)
        user_id = UUID(token_data.user_id)
    except (JWTError, ValueError):
        return None

    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        return None

    stmt = select(User).where(
        User.id == user_id,
        User.deleted_at.is_(None),
        User.is_active.is_(True),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def require_role(allowed_roles: List[str]) -> Callable[[User], Awaitable[User]]:
    """Create a dependency that requires specific roles.

    Factory function that creates a dependency to enforce
    role-based access control.

    Args:
        allowed_roles: List of role names that can access the endpoint

    Returns:
        Dependency function that validates user role

    Example:
        @router.delete("/grievances/{id}")
        async def delete_grievance(
            current_user: User = Depends(require_role(["admin"]))
        ):
            # Only admins can delete grievances
            pass

        @router.patch("/grievances/{id}")
        async def update_grievance(
            current_user: User = Depends(require_role(["officer", "supervisor", "admin"]))
        ):
            # Officers, supervisors, and admins can update
            pass
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


def require_admin() -> Callable[[User], Awaitable[User]]:
    """Shortcut dependency for admin-only endpoints.

    Returns:
        Dependency function that requires admin role

    Example:
        @router.delete("/users/{id}")
        async def delete_user(
            current_user: User = Depends(require_admin())
        ):
            pass
    """
    return require_role(["admin"])


def require_supervisor_or_admin() -> Callable[[User], Awaitable[User]]:
    """Shortcut dependency for supervisor or admin endpoints.

    Returns:
        Dependency function that requires supervisor or admin role

    Example:
        @router.post("/grievances/bulk")
        async def bulk_update(
            current_user: User = Depends(require_supervisor_or_admin())
        ):
            pass
    """
    return require_role(["supervisor", "admin"])


def require_officer_or_above() -> Callable[[User], Awaitable[User]]:
    """Shortcut dependency for officer, supervisor, or admin endpoints.

    Returns:
        Dependency function that requires officer or higher role

    Example:
        @router.get("/grievances")
        async def list_grievances(
            current_user: User = Depends(require_officer_or_above())
        ):
            pass
    """
    return require_role(["officer", "supervisor", "admin"])


async def get_token_data(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    """Get token data without fetching user from database.

    Use this when you only need the token payload and don't need
    the full user object. More efficient for simple authorization checks.

    Args:
        token: JWT token from Authorization header

    Returns:
        TokenData with decoded payload

    Raises:
        HTTPException 401: If token is invalid or expired

    Example:
        @router.get("/quick-check")
        async def quick_check(
            token_data: TokenData = Depends(get_token_data)
        ):
            return {"user_id": token_data.user_id, "role": token_data.role}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        return decode_token(token)
    except (JWTError, ValueError):
        raise credentials_exception
