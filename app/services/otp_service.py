"""OTP Service for generating and verifying One-Time Passwords.

Manages OTP lifecycle with Redis storage:
- Generation of secure random OTPs
- Storage with TTL in Redis
- Verification with attempt tracking
- Rate limiting integration
"""

import logging
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class OTPResult:
    """Result of OTP operations."""

    def __init__(
        self,
        success: bool,
        otp: Optional[str] = None,
        message: Optional[str] = None,
        attempts_remaining: Optional[int] = None,
        expires_at: Optional[datetime] = None,
        error: Optional[str] = None,
    ) -> None:
        self.success = success
        self.otp = otp
        self.message = message
        self.attempts_remaining = attempts_remaining
        self.expires_at = expires_at
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {
            "success": self.success,
            "message": self.message,
        }
        if self.attempts_remaining is not None:
            result["attempts_remaining"] = self.attempts_remaining
        if self.expires_at is not None:
            result["expires_at"] = self.expires_at.isoformat()
        if self.error:
            result["error"] = self.error
        return result


class IOTPService(ABC):
    """Interface for OTP service.

    All implementations must provide OTP generation and verification.
    """

    @abstractmethod
    async def generate_otp(
        self,
        identifier: str,
        phone: str,
    ) -> OTPResult:
        """Generate and store a new OTP.

        Args:
            identifier: Unique identifier (e.g., grievance_id)
            phone: Phone number for verification

        Returns:
            OTPResult with generated OTP
        """
        pass

    @abstractmethod
    async def verify_otp(
        self,
        identifier: str,
        phone: str,
        otp: str,
    ) -> OTPResult:
        """Verify an OTP.

        Args:
            identifier: Unique identifier (e.g., grievance_id)
            phone: Phone number used during generation
            otp: OTP code to verify

        Returns:
            OTPResult with verification status
        """
        pass

    @abstractmethod
    async def invalidate_otp(
        self,
        identifier: str,
    ) -> bool:
        """Invalidate/delete an OTP.

        Args:
            identifier: Unique identifier

        Returns:
            True if OTP was invalidated
        """
        pass

    @abstractmethod
    async def get_remaining_attempts(
        self,
        identifier: str,
    ) -> int:
        """Get remaining verification attempts.

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining attempts
        """
        pass


class RedisOTPService(IOTPService):
    """Production OTP service using Redis.

    Stores OTPs in Redis with TTL and tracks verification attempts.
    """

    def __init__(self, redis_client: Optional[Any] = None) -> None:
        self._redis = redis_client
        self._otp_prefix = "otp:"
        self._attempts_prefix = "otp_attempts:"

    async def _get_redis(self) -> Any:
        """Get or create Redis client."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis

                # Use OTP-specific Redis DB
                redis_url = settings.REDIS_URL.rsplit("/", 1)[0]
                self._redis = aioredis.from_url(  # type: ignore[no-untyped-call]
                    f"{redis_url}/{settings.REDIS_OTP_DB}",
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                logger.error("Redis library not installed")
                raise RuntimeError("Redis library required for OTP service")
        return self._redis

    def _generate_otp_code(self) -> str:
        """Generate a secure random OTP code.

        Returns:
            OTP string of configured length
        """
        # Generate cryptographically secure random digits
        otp = "".join(
            secrets.choice("0123456789")
            for _ in range(settings.OTP_LENGTH)
        )
        return otp

    def _get_otp_key(self, identifier: str) -> str:
        """Get Redis key for OTP storage."""
        return f"{self._otp_prefix}{identifier}"

    def _get_attempts_key(self, identifier: str) -> str:
        """Get Redis key for attempt tracking."""
        return f"{self._attempts_prefix}{identifier}"

    async def generate_otp(
        self,
        identifier: str,
        phone: str,
    ) -> OTPResult:
        """Generate and store OTP in Redis.

        Args:
            identifier: Unique identifier (grievance_id)
            phone: Phone number for verification

        Returns:
            OTPResult with generated OTP
        """
        try:
            redis = await self._get_redis()

            # Generate OTP
            otp = self._generate_otp_code()

            # Store OTP with phone for verification
            otp_key = self._get_otp_key(identifier)
            otp_data = f"{phone}:{otp}"

            # Set with TTL
            await redis.setex(
                otp_key,
                settings.OTP_EXPIRY_SECONDS,
                otp_data,
            )

            # Reset attempt counter
            attempts_key = self._get_attempts_key(identifier)
            await redis.setex(
                attempts_key,
                settings.OTP_EXPIRY_SECONDS,
                "0",
            )

            expires_at = datetime.now(timezone.utc)
            from datetime import timedelta
            expires_at = expires_at + timedelta(seconds=settings.OTP_EXPIRY_SECONDS)

            logger.info(f"Generated OTP for identifier: {identifier[:8]}...")

            return OTPResult(
                success=True,
                otp=otp,
                message="OTP generated successfully",
                attempts_remaining=settings.OTP_MAX_ATTEMPTS,
                expires_at=expires_at,
            )

        except Exception as e:
            logger.error(f"Failed to generate OTP: {e}")
            return OTPResult(
                success=False,
                error=f"Failed to generate OTP: {str(e)}",
            )

    async def verify_otp(
        self,
        identifier: str,
        phone: str,
        otp: str,
    ) -> OTPResult:
        """Verify OTP from Redis.

        Args:
            identifier: Unique identifier
            phone: Phone number used during generation
            otp: OTP code to verify

        Returns:
            OTPResult with verification status
        """
        try:
            redis = await self._get_redis()

            otp_key = self._get_otp_key(identifier)
            attempts_key = self._get_attempts_key(identifier)

            # Get stored OTP data
            stored_data = await redis.get(otp_key)

            if stored_data is None:
                return OTPResult(
                    success=False,
                    message="OTP expired or not found",
                    error="OTP not found",
                )

            # Parse stored data
            stored_phone, stored_otp = stored_data.split(":", 1)

            # Check attempts
            current_attempts = await redis.get(attempts_key)
            attempts = int(current_attempts) if current_attempts else 0

            if attempts >= settings.OTP_MAX_ATTEMPTS:
                # Max attempts reached, invalidate OTP
                await self.invalidate_otp(identifier)
                return OTPResult(
                    success=False,
                    message="Maximum verification attempts exceeded",
                    attempts_remaining=0,
                    error="Max attempts exceeded",
                )

            # Increment attempt counter
            attempts += 1
            await redis.setex(
                attempts_key,
                settings.OTP_EXPIRY_SECONDS,
                str(attempts),
            )

            remaining = settings.OTP_MAX_ATTEMPTS - attempts

            # Verify phone matches
            if phone != stored_phone:
                logger.warning(
                    f"OTP verification failed - phone mismatch for {identifier[:8]}..."
                )
                return OTPResult(
                    success=False,
                    message="Phone number does not match",
                    attempts_remaining=remaining,
                    error="Phone mismatch",
                )

            # Verify OTP (constant time comparison)
            if not secrets.compare_digest(otp, stored_otp):
                logger.warning(
                    f"OTP verification failed - invalid code for {identifier[:8]}..."
                )
                return OTPResult(
                    success=False,
                    message="Invalid OTP",
                    attempts_remaining=remaining,
                    error="Invalid OTP",
                )

            # OTP verified successfully - invalidate it
            await self.invalidate_otp(identifier)

            logger.info(f"OTP verified successfully for {identifier[:8]}...")

            return OTPResult(
                success=True,
                message="OTP verified successfully",
            )

        except Exception as e:
            logger.error(f"Failed to verify OTP: {e}")
            return OTPResult(
                success=False,
                error=f"Verification failed: {str(e)}",
            )

    async def invalidate_otp(
        self,
        identifier: str,
    ) -> bool:
        """Remove OTP from Redis.

        Args:
            identifier: Unique identifier

        Returns:
            True if removed
        """
        try:
            redis = await self._get_redis()

            otp_key = self._get_otp_key(identifier)
            attempts_key = self._get_attempts_key(identifier)

            # Delete both keys
            await redis.delete(otp_key, attempts_key)

            return True

        except Exception as e:
            logger.error(f"Failed to invalidate OTP: {e}")
            return False

    async def get_remaining_attempts(
        self,
        identifier: str,
    ) -> int:
        """Get remaining verification attempts.

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining attempts
        """
        try:
            redis = await self._get_redis()

            attempts_key = self._get_attempts_key(identifier)
            current = await redis.get(attempts_key)

            if current is None:
                return settings.OTP_MAX_ATTEMPTS

            return max(0, settings.OTP_MAX_ATTEMPTS - int(current))

        except Exception as e:
            logger.error(f"Failed to get remaining attempts: {e}")
            return 0


class InMemoryOTPService(IOTPService):
    """In-memory OTP service for testing and development.

    Stores OTPs in memory with no persistence.
    """

    def __init__(self) -> None:
        self._otps: Dict[str, Dict[str, Any]] = {}
        self._attempts: Dict[str, int] = {}

    def _generate_otp_code(self) -> str:
        """Generate a random OTP code."""
        return "".join(
            secrets.choice("0123456789")
            for _ in range(settings.OTP_LENGTH)
        )

    async def generate_otp(
        self,
        identifier: str,
        phone: str,
    ) -> OTPResult:
        """Generate and store OTP in memory."""
        otp = self._generate_otp_code()

        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.OTP_EXPIRY_SECONDS
        )

        self._otps[identifier] = {
            "phone": phone,
            "otp": otp,
            "expires_at": expires_at,
        }
        self._attempts[identifier] = 0

        return OTPResult(
            success=True,
            otp=otp,
            message="OTP generated successfully",
            attempts_remaining=settings.OTP_MAX_ATTEMPTS,
            expires_at=expires_at,
        )

    async def verify_otp(
        self,
        identifier: str,
        phone: str,
        otp: str,
    ) -> OTPResult:
        """Verify OTP from memory."""
        stored = self._otps.get(identifier)

        if stored is None:
            return OTPResult(
                success=False,
                message="OTP not found or expired",
                error="OTP not found",
            )

        # Check expiry
        if datetime.now(timezone.utc) > stored["expires_at"]:
            await self.invalidate_otp(identifier)
            return OTPResult(
                success=False,
                message="OTP expired",
                error="OTP expired",
            )

        # Check attempts
        attempts = self._attempts.get(identifier, 0)
        if attempts >= settings.OTP_MAX_ATTEMPTS:
            await self.invalidate_otp(identifier)
            return OTPResult(
                success=False,
                message="Maximum attempts exceeded",
                attempts_remaining=0,
                error="Max attempts exceeded",
            )

        # Increment attempts
        self._attempts[identifier] = attempts + 1
        remaining = settings.OTP_MAX_ATTEMPTS - self._attempts[identifier]

        # Verify phone
        if phone != stored["phone"]:
            return OTPResult(
                success=False,
                message="Phone number mismatch",
                attempts_remaining=remaining,
                error="Phone mismatch",
            )

        # Verify OTP
        if not secrets.compare_digest(otp, stored["otp"]):
            return OTPResult(
                success=False,
                message="Invalid OTP",
                attempts_remaining=remaining,
                error="Invalid OTP",
            )

        # Success - invalidate
        await self.invalidate_otp(identifier)

        return OTPResult(
            success=True,
            message="OTP verified successfully",
        )

    async def invalidate_otp(
        self,
        identifier: str,
    ) -> bool:
        """Remove OTP from memory."""
        self._otps.pop(identifier, None)
        self._attempts.pop(identifier, None)
        return True

    async def get_remaining_attempts(
        self,
        identifier: str,
    ) -> int:
        """Get remaining attempts."""
        attempts = self._attempts.get(identifier, 0)
        return max(0, settings.OTP_MAX_ATTEMPTS - attempts)


# Singleton instance
_otp_service: Optional[IOTPService] = None


def get_otp_service() -> IOTPService:
    """Get OTP service instance.

    Returns:
        IOTPService instance
    """
    global _otp_service

    if _otp_service is None:
        if settings.ENVIRONMENT == "development":
            # Use in-memory for development when Redis unavailable
            try:
                import redis.asyncio as aioredis  # noqa: F401
                _otp_service = RedisOTPService()
            except ImportError:
                logger.warning("Redis not available, using in-memory OTP service")
                _otp_service = InMemoryOTPService()
        else:
            _otp_service = RedisOTPService()

    return _otp_service
