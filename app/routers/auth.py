"""Authentication Router.

Provides authentication endpoints:
- POST /auth/login - Login with username/password
- POST /auth/logout - Logout (invalidate token via blacklist)
- POST /auth/logout-all - Logout from all devices
- GET /auth/me - Get current user info
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import get_db_session
from app.dependencies.auth import get_current_active_user, get_current_user, oauth2_scheme
from app.models.user import User
from app.schemas.auth import DepartmentResponse, DistrictResponse, LoginRequest, LoginResponse, UserResponse, UserRole
from app.services.token_blacklist import blacklist_token, get_token_blacklist
from app.utils.jwt import create_access_token, decode_token
from app.utils.password import verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth")


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: UserResponse = Field(..., description="User information")


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with credentials",
    description="Authenticate user with username and password. Returns JWT access token.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate user and return access token.

    Validates username and password against database.
    Returns JWT token on success.

    Args:
        form_data: OAuth2 form with username and password
        db: Database session

    Returns:
        TokenResponse with access token and user info

    Raises:
        HTTPException 401: Invalid credentials
        HTTPException 403: User account is disabled
    """
    # Find user by username
    stmt = select(User).where(
        User.username == form_data.username,
        User.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"Login failed: user not found - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not user.password_hash or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Login failed: invalid password - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login failed: user disabled - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    # Create access token
    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
        username=user.username,
        department_id=user.department_id,
        district_id=user.district_id,
    )

    logger.info(f"User logged in: {user.username}")

    # Build user response
    user_response = UserResponse(
        id=str(user.id),
        username=user.username or "",
        email=user.email or "",
        full_name=user.full_name,
        phone=user.mobile_number,
        role=UserRole(user.role),
        department=_build_department_response(user),
        district=_build_district_response(user),
        is_active=user.is_active,
        last_login_at=user.last_login_at,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Invalidate the current access token by adding it to the blacklist.",
)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
) -> None:
    """Logout user by blacklisting the token.

    The token is added to a Redis-based blacklist with TTL matching
    the token's remaining validity time. The token will be automatically
    removed from the blacklist when it expires.

    Args:
        token: JWT token from Authorization header
        current_user: Current authenticated user

    Raises:
        HTTPException 500: If blacklisting fails
    """
    try:
        # Decode token to get expiration time
        token_data = decode_token(token)

        # Blacklist the token
        success = await blacklist_token(
            token=token,
            expires_at=token_data.exp,
            user_id=str(current_user.id),
            reason="logout",
        )

        if not success:
            logger.warning(f"Failed to blacklist token for user: {current_user.username}")
            # Still return success - token will expire naturally

        logger.info(f"User logged out: {current_user.username}")

    except Exception as e:
        logger.error(f"Logout error for {current_user.username}: {e}")
        # Still succeed - worst case, token expires naturally


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout from all devices",
    description="Invalidate all tokens for the current user (e.g., after password change).",
)
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
) -> None:
    """Logout user from all devices by invalidating all their tokens.

    This is useful after a password change or security concern.
    All tokens issued before this call will be invalid.

    Args:
        current_user: Current authenticated user
    """
    try:
        blacklist_service = get_token_blacklist()
        success = await blacklist_service.blacklist_all_user_tokens(
            user_id=str(current_user.id),
            reason="logout_all",
        )

        if not success:
            logger.warning(f"Failed to blacklist all tokens for user: {current_user.username}")

        logger.info(f"User logged out from all devices: {current_user.username}")

    except Exception as e:
        logger.error(f"Logout-all error for {current_user.username}: {e}")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get details of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get current user information.

    Returns detailed information about the authenticated user,
    including department and district assignments.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse with user details
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username or "",
        email=current_user.email or "",
        full_name=current_user.full_name,
        phone=current_user.mobile_number,
        role=UserRole(current_user.role),
        department=_build_department_response(current_user),
        district=_build_district_response(current_user),
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
    )


def _build_department_response(user: User) -> Optional[DepartmentResponse]:
    """Build department response from user."""
    if user.department:
        return DepartmentResponse(
            id=str(user.department.id),
            code=user.department.dept_code,
            name=user.department.dept_name,
            name_telugu=user.department.name_telugu,
            sla_days=user.department.sla_days,
        )
    return None


def _build_district_response(user: User) -> Optional[DistrictResponse]:
    """Build district response from user."""
    if user.district:
        return DistrictResponse(
            id=str(user.district.id),
            code=user.district.district_code,
            name=user.district.district_name,
        )
    return None
