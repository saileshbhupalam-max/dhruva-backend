"""JWT token utilities for authentication.

Provides functions for creating and validating JWT access tokens.
Uses python-jose with cryptography backend for secure token handling.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.config import settings


class TokenData(BaseModel):
    """Data extracted from JWT token.

    Used for type-safe access to token payload after validation.
    """

    user_id: str = Field(..., description="User UUID as string")
    username: Optional[str] = Field(None, description="Username for officials")
    role: str = Field(..., description="User role (citizen, officer, supervisor, admin)")
    department_id: Optional[str] = Field(None, description="Department UUID for officers")
    district_id: Optional[str] = Field(None, description="District UUID for officers")
    exp: datetime = Field(..., description="Token expiration timestamp")


class TokenPayload(BaseModel):
    """JWT token payload for creation.

    Contains all data that will be encoded in the token.
    """

    sub: str = Field(..., description="Subject - user UUID")
    username: Optional[str] = None
    role: str = Field(default="citizen")
    department_id: Optional[str] = None
    district_id: Optional[str] = None
    exp: datetime
    iat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def create_access_token(
    user_id: UUID | str,
    role: str,
    username: Optional[str] = None,
    department_id: Optional[UUID | str] = None,
    district_id: Optional[UUID | str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User UUID
        role: User role (citizen, officer, supervisor, admin)
        username: Username for officials (optional)
        department_id: Department UUID for officers (optional)
        district_id: District UUID for officers (optional)
        expires_delta: Custom expiration time (optional)

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token(
        ...     user_id="123e4567-e89b-12d3-a456-426614174000",
        ...     role="officer",
        ...     username="officer_vijayawada",
        ...     department_id="dept-uuid",
        ...     district_id="district-uuid",
        ... )
        >>> print(token)
        eyJhbGciOiJIUzI1NiIs...
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": now,
    }

    # Add optional fields
    if username:
        payload["username"] = username
    if department_id:
        payload["department_id"] = str(department_id)
    if district_id:
        payload["district_id"] = str(district_id)

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return str(encoded_jwt)


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData with extracted payload

    Raises:
        JWTError: If token is invalid, expired, or malformed
        ValueError: If token payload is missing required fields

    Example:
        >>> try:
        ...     data = decode_token("eyJhbGciOiJIUzI1NiIs...")
        ...     print(f"User: {data.user_id}, Role: {data.role}")
        ... except JWTError as e:
        ...     print(f"Invalid token: {e}")
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise

    # Extract required fields
    user_id = payload.get("sub")
    role = payload.get("role")
    exp = payload.get("exp")

    if not user_id or not role or not exp:
        raise ValueError("Token missing required fields (sub, role, exp)")

    # Convert exp to datetime if it's a timestamp
    if isinstance(exp, (int, float)):
        exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
    else:
        exp_datetime = exp

    return TokenData(
        user_id=user_id,
        username=payload.get("username"),
        role=role,
        department_id=payload.get("department_id"),
        district_id=payload.get("district_id"),
        exp=exp_datetime,
    )


def verify_token(token: str) -> Optional[TokenData]:
    """Verify a JWT token without raising exceptions.

    Convenience function that returns None instead of raising on invalid tokens.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None if invalid or expired

    Example:
        >>> data = verify_token("eyJhbGciOiJIUzI1NiIs...")
        >>> if data:
        ...     print(f"Valid token for user: {data.user_id}")
        ... else:
        ...     print("Invalid token")
    """
    try:
        return decode_token(token)
    except (JWTError, ValueError):
        return None


def is_token_expired(token: str) -> bool:
    """Check if a JWT token is expired.

    Args:
        token: JWT token string

    Returns:
        True if expired or invalid, False if still valid

    Example:
        >>> if is_token_expired(token):
        ...     print("Token has expired, please login again")
    """
    try:
        data = decode_token(token)
        return datetime.now(timezone.utc) > data.exp
    except (JWTError, ValueError):
        return True


def get_token_expiry(token: str) -> Optional[datetime]:
    """Get the expiration datetime of a token.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime if valid, None if invalid

    Example:
        >>> expiry = get_token_expiry(token)
        >>> if expiry:
        ...     remaining = expiry - datetime.now(timezone.utc)
        ...     print(f"Token expires in {remaining.total_seconds()} seconds")
    """
    try:
        data = decode_token(token)
        return data.exp
    except (JWTError, ValueError):
        return None
