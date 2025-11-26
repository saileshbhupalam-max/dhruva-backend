"""Token Blacklist Service.

Provides JWT token blacklisting using Redis for logout functionality.
Tokens are stored with TTL matching their remaining validity time.

Security Features:
- Tokens are blacklisted by JTI (JWT ID) for efficiency
- TTL matches token expiry to auto-cleanup expired entries
- Graceful degradation when Redis unavailable (logs warning)
- In-memory fallback for development/testing
"""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class ITokenBlacklist(ABC):
    """Interface for token blacklist service."""

    @abstractmethod
    async def blacklist_token(
        self,
        token: str,
        expires_at: datetime,
        user_id: Optional[str] = None,
        reason: str = "logout",
    ) -> bool:
        """Add a token to the blacklist.

        Args:
            token: The JWT token string
            expires_at: Token expiration datetime (for TTL calculation)
            user_id: Optional user ID for logging
            reason: Reason for blacklisting (logout, revoked, etc.)

        Returns:
            True if successfully blacklisted, False otherwise
        """
        pass

    @abstractmethod
    async def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted.

        Args:
            token: The JWT token string

        Returns:
            True if token is blacklisted, False otherwise
        """
        pass

    @abstractmethod
    async def blacklist_all_user_tokens(
        self,
        user_id: str,
        reason: str = "security",
    ) -> bool:
        """Blacklist all tokens for a user (e.g., password change, security concern).

        Args:
            user_id: User UUID string
            reason: Reason for mass blacklisting

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get_blacklist_stats(self) -> Dict[str, Any]:
        """Get blacklist statistics.

        Returns:
            Dict with stats like count, memory usage, etc.
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check blacklist service health."""
        pass


def _get_token_hash(token: str) -> str:
    """Generate a hash of the token for storage.

    Using hash instead of full token for:
    1. Privacy - don't store full tokens
    2. Efficiency - shorter keys
    3. Security - even if Redis compromised, tokens not exposed

    Args:
        token: JWT token string

    Returns:
        SHA-256 hash of token (first 32 chars)
    """
    return hashlib.sha256(token.encode()).hexdigest()[:32]


class RedisTokenBlacklist(ITokenBlacklist):
    """Redis-based token blacklist.

    Uses Redis SET with expiry for efficient blacklist checking.
    Keys are stored as: blacklist:token:{hash}
    User blacklist keys: blacklist:user:{user_id}
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self._client = None
        self._connection_error = False

    async def _get_client(self) -> Any:
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                await self._client.ping()
                self._connection_error = False
            except Exception as e:
                logger.error(f"Redis connection failed for token blacklist: {e}")
                self._connection_error = True
                self._client = None
                raise

        return self._client

    async def blacklist_token(
        self,
        token: str,
        expires_at: datetime,
        user_id: Optional[str] = None,
        reason: str = "logout",
    ) -> bool:
        """Add token to Redis blacklist with TTL."""
        try:
            client = await self._get_client()

            # Calculate TTL (how long until token expires)
            now = datetime.now(timezone.utc)
            ttl_seconds = int((expires_at - now).total_seconds())

            if ttl_seconds <= 0:
                # Token already expired, no need to blacklist
                logger.debug("Token already expired, skipping blacklist")
                return True

            # Create blacklist entry
            token_hash = _get_token_hash(token)
            key = f"blacklist:token:{token_hash}"

            # Store with metadata
            value = f"{user_id or 'unknown'}:{reason}:{int(now.timestamp())}"

            # Set with expiry
            await client.setex(key, ttl_seconds, value)

            logger.info(
                f"Token blacklisted: user={user_id}, reason={reason}, "
                f"ttl={ttl_seconds}s, hash={token_hash[:8]}..."
            )

            return True

        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False

    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is in Redis blacklist."""
        try:
            client = await self._get_client()

            token_hash = _get_token_hash(token)
            key = f"blacklist:token:{token_hash}"

            exists = await client.exists(key)
            return exists > 0

        except Exception as e:
            # Graceful degradation - if Redis fails, allow the request
            # but log the error for monitoring
            logger.warning(f"Blacklist check failed, allowing request: {e}")
            return False

    async def blacklist_all_user_tokens(
        self,
        user_id: str,
        reason: str = "security",
    ) -> bool:
        """Blacklist all tokens for a user.

        Sets a marker that invalidates all tokens issued before now.
        """
        try:
            client = await self._get_client()

            # Store timestamp - all tokens issued before this are invalid
            key = f"blacklist:user:{user_id}"
            timestamp = int(datetime.now(timezone.utc).timestamp())

            # Set for 24 hours (should cover max token lifetime)
            await client.setex(key, 86400, str(timestamp))

            logger.info(f"All tokens blacklisted for user {user_id}: reason={reason}")

            return True

        except Exception as e:
            logger.error(f"Failed to blacklist user tokens: {e}")
            return False

    async def is_user_token_valid(
        self,
        user_id: str,
        token_issued_at: datetime,
    ) -> bool:
        """Check if a user's token is still valid (not mass-revoked).

        Args:
            user_id: User UUID
            token_issued_at: When the token was issued (iat claim)

        Returns:
            True if token is valid, False if all tokens were revoked after issuance
        """
        try:
            client = await self._get_client()

            key = f"blacklist:user:{user_id}"
            revoked_at = await client.get(key)

            if revoked_at is None:
                return True

            # Token is invalid if issued before revocation
            revoked_timestamp = int(revoked_at)
            token_timestamp = int(token_issued_at.timestamp())

            return token_timestamp > revoked_timestamp

        except Exception as e:
            logger.warning(f"User token validity check failed: {e}")
            return True  # Graceful degradation

    async def get_blacklist_stats(self) -> Dict[str, Any]:
        """Get blacklist statistics from Redis."""
        try:
            client = await self._get_client()

            # Count blacklisted tokens
            token_keys = []
            async for key in client.scan_iter(match="blacklist:token:*"):
                token_keys.append(key)

            # Count user blacklists
            user_keys = []
            async for key in client.scan_iter(match="blacklist:user:*"):
                user_keys.append(key)

            return {
                "blacklisted_tokens": len(token_keys),
                "blacklisted_users": len(user_keys),
                "backend": "redis",
            }

        except Exception as e:
            return {
                "error": str(e),
                "backend": "redis",
            }

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis connection health."""
        try:
            client = await self._get_client()
            await client.ping()

            return {
                "status": "healthy",
                "backend": "redis",
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "redis",
                "error": str(e),
            }

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None


class InMemoryTokenBlacklist(ITokenBlacklist):
    """In-memory token blacklist for testing/development.

    Not suitable for production (not shared across processes).
    """

    def __init__(self) -> None:
        # token_hash -> (expires_at_timestamp, metadata)
        self._blacklist: Dict[str, tuple] = {}
        # user_id -> revoked_at_timestamp
        self._user_blacklist: Dict[str, int] = {}

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired = [
            k for k, v in self._blacklist.items()
            if v[0] < now
        ]
        for k in expired:
            del self._blacklist[k]

    async def blacklist_token(
        self,
        token: str,
        expires_at: datetime,
        user_id: Optional[str] = None,
        reason: str = "logout",
    ) -> bool:
        """Add token to in-memory blacklist."""
        self._cleanup_expired()

        token_hash = _get_token_hash(token)
        expires_timestamp = expires_at.timestamp()

        if expires_timestamp <= time.time():
            return True  # Already expired

        self._blacklist[token_hash] = (
            expires_timestamp,
            {"user_id": user_id, "reason": reason},
        )

        logger.info(f"Token blacklisted (in-memory): hash={token_hash[:8]}...")
        return True

    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is in in-memory blacklist."""
        self._cleanup_expired()

        token_hash = _get_token_hash(token)
        return token_hash in self._blacklist

    async def blacklist_all_user_tokens(
        self,
        user_id: str,
        reason: str = "security",
    ) -> bool:
        """Mark all user tokens as invalid."""
        self._user_blacklist[user_id] = int(time.time())
        logger.info(f"All tokens blacklisted (in-memory) for user {user_id}")
        return True

    async def is_user_token_valid(
        self,
        user_id: str,
        token_issued_at: datetime,
    ) -> bool:
        """Check if user's token is still valid."""
        if user_id not in self._user_blacklist:
            return True

        revoked_at = self._user_blacklist[user_id]
        return int(token_issued_at.timestamp()) > revoked_at

    async def get_blacklist_stats(self) -> Dict[str, Any]:
        """Get in-memory blacklist stats."""
        self._cleanup_expired()
        return {
            "blacklisted_tokens": len(self._blacklist),
            "blacklisted_users": len(self._user_blacklist),
            "backend": "in_memory",
        }

    async def health_check(self) -> Dict[str, Any]:
        """In-memory is always healthy."""
        return {
            "status": "healthy",
            "backend": "in_memory",
        }


# Singleton instance
_token_blacklist: Optional[ITokenBlacklist] = None


def get_token_blacklist() -> ITokenBlacklist:
    """Get token blacklist service instance.

    Tries Redis first, falls back to in-memory.

    Returns:
        ITokenBlacklist instance
    """
    global _token_blacklist

    if _token_blacklist is None:
        try:
            _token_blacklist = RedisTokenBlacklist()
            logger.info("Using Redis token blacklist")
        except Exception:
            logger.warning("Redis unavailable, using in-memory token blacklist")
            _token_blacklist = InMemoryTokenBlacklist()

    return _token_blacklist


def reset_token_blacklist() -> None:
    """Reset the blacklist singleton (for testing)."""
    global _token_blacklist
    _token_blacklist = None


async def blacklist_token(
    token: str,
    expires_at: datetime,
    user_id: Optional[str] = None,
    reason: str = "logout",
) -> bool:
    """Convenience function to blacklist a token.

    Args:
        token: JWT token to blacklist
        expires_at: Token expiration time
        user_id: Optional user ID
        reason: Reason for blacklisting

    Returns:
        True if successful
    """
    blacklist = get_token_blacklist()
    return await blacklist.blacklist_token(token, expires_at, user_id, reason)


async def is_token_blacklisted(token: str) -> bool:
    """Convenience function to check if token is blacklisted.

    Args:
        token: JWT token to check

    Returns:
        True if blacklisted
    """
    blacklist = get_token_blacklist()
    return await blacklist.is_blacklisted(token)
