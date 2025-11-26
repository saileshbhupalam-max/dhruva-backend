"""Password hashing utilities using bcrypt.

Provides secure password hashing and verification functions.
Uses passlib with bcrypt backend for industry-standard security.
"""

from passlib.context import CryptContext

from app.config import settings

# Configure passlib with bcrypt
# Using bcrypt with configurable rounds (default 12)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.PASSWORD_HASH_ROUNDS,
)


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hashed password string

    Example:
        >>> hashed = hash_password("securepassword123")
        >>> print(hashed)
        $2b$12$abc123...
    """
    return str(pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password to check against

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("securepassword123")
        >>> verify_password("securepassword123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    return bool(pwd_context.verify(plain_password, hashed_password))


def needs_rehash(hashed_password: str) -> bool:
    """Check if a password hash needs to be rehashed.

    This can happen when:
    - The hashing algorithm has been changed
    - The number of rounds has been increased
    - The hash uses a deprecated scheme

    Args:
        hashed_password: Existing bcrypt hashed password

    Returns:
        True if password should be rehashed, False otherwise

    Example:
        >>> if needs_rehash(user.password_hash):
        ...     user.password_hash = hash_password(plain_password)
        ...     await session.commit()
    """
    return bool(pwd_context.needs_update(hashed_password))


def generate_temporary_password(length: int = 12) -> str:
    """Generate a secure temporary password.

    Useful for password reset flows or initial user creation.

    Args:
        length: Password length (default 12, minimum 8)

    Returns:
        Randomly generated password string

    Example:
        >>> temp_password = generate_temporary_password()
        >>> print(f"Your temporary password is: {temp_password}")
    """
    import secrets
    import string

    if length < 8:
        length = 8

    # Use a mix of letters, digits, and special characters
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))

    return password
