"""Rate Limiter Service using Redis.

Provides request rate limiting with Redis backend and in-memory fallback.
Implements sliding window rate limiting algorithm.
"""

import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimitResult:
    """Result of rate limit check."""

    def __init__(
        self,
        allowed: bool,
        limit: int,
        remaining: int,
        reset_seconds: int,
        retry_after: Optional[int] = None,
    ):
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_seconds = reset_seconds
        self.retry_after = retry_after

    def to_headers(self) -> Dict[str, str]:
        """Convert to rate limit headers.

        Returns:
            Dict with X-RateLimit-* headers
        """
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(self.reset_seconds),
        }
        if self.retry_after is not None:
            headers["Retry-After"] = str(self.retry_after)
        return headers


class IRateLimiter(ABC):
    """Interface for rate limiting service."""

    @abstractmethod
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check if request is within rate limit.

        Args:
            key: Unique identifier (e.g., user_id, ip_address)
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            RateLimitResult with allowed status and metadata
        """
        pass

    @abstractmethod
    async def reset_limit(self, key: str) -> bool:
        """Reset rate limit for a key.

        Args:
            key: Rate limit key to reset

        Returns:
            True if reset successful
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check rate limiter health."""
        pass


class RedisRateLimiter(IRateLimiter):
    """Redis-based rate limiter using sliding window algorithm.

    Uses Redis INCR with expiry for efficient rate limiting.
    Falls back to allowing requests if Redis is unavailable.
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

                self._client = redis.from_url(  # type: ignore[no-untyped-call]
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                assert self._client is not None
                await self._client.ping()
                self._connection_error = False
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self._connection_error = True
                self._client = None
                raise

        return self._client

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check rate limit using Redis.

        Uses atomic INCR with expiry for sliding window.

        Args:
            key: Rate limit key
            limit: Max requests
            window_seconds: Time window

        Returns:
            RateLimitResult
        """
        if not settings.RATE_LIMIT_ENABLED:
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                reset_seconds=0,
            )

        redis_key = f"rate:{key}:{int(time.time()) // window_seconds}"

        try:
            client = await self._get_client()

            # Atomic increment with expiry
            pipe = client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, window_seconds)
            results = await pipe.execute()

            current_count = results[0]
            remaining = max(0, limit - current_count)

            # Calculate reset time
            window_start = (int(time.time()) // window_seconds) * window_seconds
            reset_seconds = window_start + window_seconds - int(time.time())

            if current_count > limit:
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_seconds=reset_seconds,
                    retry_after=reset_seconds,
                )

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_seconds=reset_seconds,
            )

        except Exception as e:
            logger.warning(f"Rate limit check failed, allowing request: {e}")
            # Graceful degradation: allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                reset_seconds=window_seconds,
            )

    async def reset_limit(self, key: str) -> bool:
        """Reset rate limit for key.

        Args:
            key: Key to reset

        Returns:
            True if successful
        """
        try:
            client = await self._get_client()

            # Delete all windows for this key
            pattern = f"rate:{key}:*"
            async for redis_key in client.scan_iter(match=pattern):
                await client.delete(redis_key)

            return True

        except Exception as e:
            logger.error(f"Rate limit reset failed: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health."""
        if not settings.RATE_LIMIT_ENABLED:
            return {
                "status": "disabled",
                "enabled": False,
            }

        try:
            client = await self._get_client()
            await client.ping()

            return {
                "status": "healthy",
                "enabled": True,
                "backend": "redis",
                "url": self.redis_url.split("@")[-1] if "@" in self.redis_url else self.redis_url,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "enabled": True,
                "backend": "redis",
                "error": str(e),
            }

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None


class InMemoryRateLimiter(IRateLimiter):
    """In-memory rate limiter for testing or fallback.

    Uses dict-based storage. Not suitable for multi-process deployments.
    """

    def __init__(self) -> None:
        # Dict of key -> list of timestamps
        self._requests: Dict[str, List[float]] = defaultdict(list)

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        """Check rate limit using in-memory storage.

        Args:
            key: Rate limit key
            limit: Max requests
            window_seconds: Time window

        Returns:
            RateLimitResult
        """
        if not settings.RATE_LIMIT_ENABLED:
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                reset_seconds=0,
            )

        now = time.time()
        window_start = now - window_seconds

        # Clean old requests
        self._requests[key] = [
            ts for ts in self._requests[key]
            if ts > window_start
        ]

        current_count = len(self._requests[key])
        remaining = max(0, limit - current_count)

        # Calculate reset time
        if self._requests[key]:
            oldest = min(self._requests[key])
            reset_seconds = int(oldest + window_seconds - now)
        else:
            reset_seconds = window_seconds

        if current_count >= limit:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_seconds=reset_seconds,
                retry_after=reset_seconds,
            )

        # Record this request
        self._requests[key].append(now)

        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining - 1,  # Account for this request
            reset_seconds=reset_seconds,
        )

    async def reset_limit(self, key: str) -> bool:
        """Reset rate limit for key.

        Args:
            key: Key to reset

        Returns:
            True if successful
        """
        if key in self._requests:
            del self._requests[key]
        return True

    async def health_check(self) -> Dict[str, Any]:
        """Return in-memory health status."""
        return {
            "status": "healthy",
            "enabled": settings.RATE_LIMIT_ENABLED,
            "backend": "in_memory",
            "tracked_keys": len(self._requests),
        }


# Singleton instance
_rate_limiter: Optional[IRateLimiter] = None


def get_rate_limiter() -> IRateLimiter:
    """Get rate limiter instance.

    Tries Redis first, falls back to in-memory.

    Returns:
        IRateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        try:
            _rate_limiter = RedisRateLimiter()
        except Exception:
            logger.warning("Redis unavailable, using in-memory rate limiter")
            _rate_limiter = InMemoryRateLimiter()

    return _rate_limiter


async def check_rate_limit(
    key: str,
    limit: Optional[int] = None,
    window_seconds: Optional[int] = None,
) -> RateLimitResult:
    """Convenience function to check rate limit.

    Args:
        key: Rate limit key
        limit: Max requests (default from settings)
        window_seconds: Time window (default from settings)

    Returns:
        RateLimitResult
    """
    if limit is None:
        limit = settings.RATE_LIMIT_DEFAULT_REQUESTS
    if window_seconds is None:
        window_seconds = settings.RATE_LIMIT_DEFAULT_WINDOW

    limiter = get_rate_limiter()
    return await limiter.check_rate_limit(key, limit, window_seconds)
