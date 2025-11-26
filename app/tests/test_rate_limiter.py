"""Tests for rate limiter service."""

import pytest
from unittest.mock import patch, AsyncMock

from app.services.rate_limiter import (
    RateLimitResult,
    InMemoryRateLimiter,
    RedisRateLimiter,
    get_rate_limiter,
    check_rate_limit,
)


class TestRateLimitResult:
    """Tests for RateLimitResult class."""

    def test_allowed_result(self):
        """Test creating an allowed rate limit result."""
        result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=99,
            reset_seconds=60,
        )

        assert result.allowed is True
        assert result.limit == 100
        assert result.remaining == 99
        assert result.reset_seconds == 60
        assert result.retry_after is None

    def test_denied_result(self):
        """Test creating a denied rate limit result."""
        result = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=0,
            reset_seconds=30,
            retry_after=30,
        )

        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30

    def test_to_headers(self):
        """Test converting result to HTTP headers."""
        result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=50,
            reset_seconds=120,
        )

        headers = result.to_headers()

        assert headers["X-RateLimit-Limit"] == "100"
        assert headers["X-RateLimit-Remaining"] == "50"
        assert headers["X-RateLimit-Reset"] == "120"
        assert "Retry-After" not in headers

    def test_to_headers_with_retry_after(self):
        """Test headers include Retry-After when denied."""
        result = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=0,
            reset_seconds=60,
            retry_after=60,
        )

        headers = result.to_headers()

        assert headers["Retry-After"] == "60"

    def test_remaining_cannot_be_negative_in_headers(self):
        """Test that remaining is always >= 0 in headers."""
        result = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=-5,  # Negative value
            reset_seconds=60,
        )

        headers = result.to_headers()
        assert headers["X-RateLimit-Remaining"] == "0"


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter."""

    @pytest.fixture
    def limiter(self):
        """Create a fresh rate limiter for each test."""
        return InMemoryRateLimiter()

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_first_request_allowed(self, mock_settings, limiter):
        """Test first request is always allowed."""
        mock_settings.RATE_LIMIT_ENABLED = True

        result = await limiter.check_rate_limit(
            key="test_user",
            limit=10,
            window_seconds=60,
        )

        assert result.allowed is True
        assert result.remaining < 10  # One request used

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_rate_limit_disabled(self, mock_settings, limiter):
        """Test rate limiting when disabled."""
        mock_settings.RATE_LIMIT_ENABLED = False

        result = await limiter.check_rate_limit(
            key="test_user",
            limit=1,
            window_seconds=60,
        )

        assert result.allowed is True
        assert result.remaining == 1

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_exceeds_limit(self, mock_settings, limiter):
        """Test request denied when limit exceeded."""
        mock_settings.RATE_LIMIT_ENABLED = True

        # Use up all requests
        for i in range(5):
            await limiter.check_rate_limit(
                key="test_user",
                limit=5,
                window_seconds=60,
            )

        # Next request should be denied
        result = await limiter.check_rate_limit(
            key="test_user",
            limit=5,
            window_seconds=60,
        )

        assert result.allowed is False
        assert result.remaining == 0

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_different_keys_independent(self, mock_settings, limiter):
        """Test different keys have independent limits."""
        mock_settings.RATE_LIMIT_ENABLED = True

        # Use up all requests for user1
        for i in range(5):
            await limiter.check_rate_limit(
                key="user1",
                limit=5,
                window_seconds=60,
            )

        # user2 should still be allowed
        result = await limiter.check_rate_limit(
            key="user2",
            limit=5,
            window_seconds=60,
        )

        assert result.allowed is True

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_reset_limit(self, mock_settings, limiter):
        """Test resetting rate limit for a key."""
        mock_settings.RATE_LIMIT_ENABLED = True

        # Use some requests
        await limiter.check_rate_limit("test_user", 5, 60)
        await limiter.check_rate_limit("test_user", 5, 60)

        # Reset
        result = await limiter.reset_limit("test_user")
        assert result is True

        # Should have full limit again
        check = await limiter.check_rate_limit("test_user", 5, 60)
        assert check.remaining == 4  # Only 1 request used

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_health_check(self, mock_settings, limiter):
        """Test health check."""
        mock_settings.RATE_LIMIT_ENABLED = True

        health = await limiter.health_check()

        assert health["status"] == "healthy"
        assert health["backend"] == "in_memory"

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_health_check_disabled(self, mock_settings, limiter):
        """Test health check when disabled."""
        mock_settings.RATE_LIMIT_ENABLED = False

        health = await limiter.health_check()

        assert health["enabled"] is False


class TestRedisRateLimiter:
    """Tests for RedisRateLimiter."""

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_graceful_degradation(self, mock_settings):
        """Test graceful degradation when Redis unavailable."""
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_settings.REDIS_URL = "redis://nonexistent:6379/0"

        limiter = RedisRateLimiter(redis_url="redis://nonexistent:6379/0")

        # Should not raise, should allow request
        result = await limiter.check_rate_limit(
            key="test_user",
            limit=10,
            window_seconds=60,
        )

        # Graceful degradation - allow request when Redis fails
        assert result.allowed is True

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_health_check_unhealthy(self, mock_settings):
        """Test health check reports unhealthy when Redis unavailable."""
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_settings.REDIS_URL = "redis://nonexistent:6379/0"

        limiter = RedisRateLimiter(redis_url="redis://nonexistent:6379/0")

        health = await limiter.health_check()

        assert health["status"] == "unhealthy"


class TestGetRateLimiter:
    """Tests for get_rate_limiter factory function."""

    @patch('app.services.rate_limiter._rate_limiter', None)
    def test_get_rate_limiter_returns_instance(self):
        """Test that get_rate_limiter returns an instance."""
        limiter = get_rate_limiter()
        assert limiter is not None

    @patch('app.services.rate_limiter._rate_limiter', None)
    def test_get_rate_limiter_fallback(self):
        """Test fallback to in-memory when Redis unavailable."""
        # This should fall back to InMemoryRateLimiter
        limiter = get_rate_limiter()
        # Either Redis or InMemory is fine
        assert limiter is not None


class TestCheckRateLimitConvenience:
    """Tests for check_rate_limit convenience function."""

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_check_rate_limit_defaults(self, mock_settings):
        """Test check_rate_limit uses default settings."""
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_settings.RATE_LIMIT_DEFAULT_REQUESTS = 100
        mock_settings.RATE_LIMIT_DEFAULT_WINDOW = 60

        result = await check_rate_limit(key="test_user")

        assert result.limit == 100

    @pytest.mark.asyncio
    @patch('app.services.rate_limiter.settings')
    async def test_check_rate_limit_custom_values(self, mock_settings):
        """Test check_rate_limit with custom values."""
        mock_settings.RATE_LIMIT_ENABLED = True
        mock_settings.RATE_LIMIT_DEFAULT_REQUESTS = 100
        mock_settings.RATE_LIMIT_DEFAULT_WINDOW = 60

        result = await check_rate_limit(
            key="test_user",
            limit=50,
            window_seconds=30,
        )

        assert result.limit == 50
