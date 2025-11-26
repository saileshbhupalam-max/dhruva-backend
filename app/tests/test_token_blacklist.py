"""Tests for token blacklist service."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
from uuid import uuid4

from app.services.token_blacklist import (
    InMemoryTokenBlacklist,
    RedisTokenBlacklist,
    get_token_blacklist,
    reset_token_blacklist,
    blacklist_token,
    is_token_blacklisted,
    _get_token_hash,
)
from app.utils.jwt import create_access_token


class TestTokenHash:
    """Tests for token hashing function."""

    def test_hash_is_consistent(self):
        """Test that same token always produces same hash."""
        token = "test_token_string"
        hash1 = _get_token_hash(token)
        hash2 = _get_token_hash(token)
        assert hash1 == hash2

    def test_different_tokens_different_hashes(self):
        """Test that different tokens produce different hashes."""
        token1 = "token_one"
        token2 = "token_two"
        hash1 = _get_token_hash(token1)
        hash2 = _get_token_hash(token2)
        assert hash1 != hash2

    def test_hash_length(self):
        """Test that hash is 32 characters."""
        token = "any_token"
        token_hash = _get_token_hash(token)
        assert len(token_hash) == 32

    def test_hash_is_alphanumeric(self):
        """Test that hash contains only alphanumeric characters."""
        token = "test_token"
        token_hash = _get_token_hash(token)
        assert token_hash.isalnum()


class TestInMemoryTokenBlacklist:
    """Tests for in-memory token blacklist."""

    @pytest.fixture
    def blacklist(self):
        """Create a fresh blacklist for each test."""
        return InMemoryTokenBlacklist()

    @pytest.fixture
    def sample_token(self):
        """Create a sample JWT token."""
        return create_access_token(
            user_id=uuid4(),
            role="officer",
            username="test_user",
        )

    @pytest.mark.asyncio
    async def test_blacklist_token(self, blacklist, sample_token):
        """Test blacklisting a token."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        result = await blacklist.blacklist_token(
            token=sample_token,
            expires_at=expires_at,
            user_id=str(uuid4()),
            reason="test",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_is_blacklisted_after_blacklist(self, blacklist, sample_token):
        """Test that blacklisted token is detected."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        await blacklist.blacklist_token(
            token=sample_token,
            expires_at=expires_at,
        )

        is_blocked = await blacklist.is_blacklisted(sample_token)
        assert is_blocked is True

    @pytest.mark.asyncio
    async def test_non_blacklisted_token(self, blacklist, sample_token):
        """Test that non-blacklisted token is not detected."""
        is_blocked = await blacklist.is_blacklisted(sample_token)
        assert is_blocked is False

    @pytest.mark.asyncio
    async def test_expired_token_not_blacklisted(self, blacklist, sample_token):
        """Test that expired tokens don't need blacklisting."""
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Already expired

        result = await blacklist.blacklist_token(
            token=sample_token,
            expires_at=expires_at,
        )

        assert result is True  # Returns True but doesn't store

    @pytest.mark.asyncio
    async def test_blacklist_all_user_tokens(self, blacklist):
        """Test blacklisting all tokens for a user."""
        user_id = str(uuid4())

        result = await blacklist.blacklist_all_user_tokens(
            user_id=user_id,
            reason="security",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_user_token_validity_before_revocation(self, blacklist):
        """Test token is valid if issued before revocation."""
        user_id = str(uuid4())
        token_issued_at = datetime.now(timezone.utc)

        # Token is valid before any revocation
        is_valid = await blacklist.is_user_token_valid(user_id, token_issued_at)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_user_token_invalid_after_revocation(self, blacklist):
        """Test token is invalid if issued before mass revocation."""
        user_id = str(uuid4())

        # Issue token time
        token_issued_at = datetime.now(timezone.utc) - timedelta(minutes=5)

        # Revoke all tokens
        await blacklist.blacklist_all_user_tokens(user_id, "security")

        # Token should be invalid (issued before revocation)
        is_valid = await blacklist.is_user_token_valid(user_id, token_issued_at)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_get_blacklist_stats(self, blacklist, sample_token):
        """Test getting blacklist statistics."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        await blacklist.blacklist_token(sample_token, expires_at)

        stats = await blacklist.get_blacklist_stats()

        assert "blacklisted_tokens" in stats
        assert "blacklisted_users" in stats
        assert stats["backend"] == "in_memory"
        assert stats["blacklisted_tokens"] >= 1

    @pytest.mark.asyncio
    async def test_health_check(self, blacklist):
        """Test health check."""
        health = await blacklist.health_check()

        assert health["status"] == "healthy"
        assert health["backend"] == "in_memory"


class TestRedisTokenBlacklist:
    """Tests for Redis token blacklist."""

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_connection_failure(self):
        """Test graceful degradation when Redis unavailable."""
        blacklist = RedisTokenBlacklist(redis_url="redis://nonexistent:6379/0")

        # Should not raise, should return False (allow request)
        is_blocked = await blacklist.is_blacklisted("any_token")
        assert is_blocked is False

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check reports unhealthy when Redis unavailable."""
        blacklist = RedisTokenBlacklist(redis_url="redis://nonexistent:6379/0")

        health = await blacklist.health_check()
        assert health["status"] == "unhealthy"


class TestTokenBlacklistFactory:
    """Tests for blacklist factory function."""

    def test_get_token_blacklist_returns_instance(self):
        """Test that get_token_blacklist returns an instance."""
        reset_token_blacklist()  # Reset singleton
        blacklist = get_token_blacklist()
        assert blacklist is not None

    def test_get_token_blacklist_singleton(self):
        """Test that get_token_blacklist returns same instance."""
        reset_token_blacklist()
        blacklist1 = get_token_blacklist()
        blacklist2 = get_token_blacklist()
        assert blacklist1 is blacklist2


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        reset_token_blacklist()
        yield
        reset_token_blacklist()

    @pytest.mark.asyncio
    async def test_blacklist_token_function(self):
        """Test blacklist_token convenience function."""
        token = create_access_token(
            user_id=uuid4(),
            role="officer",
            username="test",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        result = await blacklist_token(
            token=token,
            expires_at=expires_at,
            user_id=str(uuid4()),
            reason="test",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_function(self):
        """Test is_token_blacklisted convenience function."""
        token = create_access_token(
            user_id=uuid4(),
            role="officer",
            username="test",
        )

        # Not blacklisted initially
        is_blocked = await is_token_blacklisted(token)
        assert is_blocked is False

        # Blacklist it
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await blacklist_token(token, expires_at)

        # Now should be blacklisted
        is_blocked = await is_token_blacklisted(token)
        assert is_blocked is True


class TestLogoutIntegration:
    """Integration tests for logout with blacklist."""

    @pytest.fixture
    def sample_user_id(self):
        return uuid4()

    @pytest.fixture
    def sample_token(self, sample_user_id):
        return create_access_token(
            user_id=sample_user_id,
            role="officer",
            username="test_officer",
            expires_delta=timedelta(hours=1),
        )

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        reset_token_blacklist()
        yield
        reset_token_blacklist()

    @pytest.mark.asyncio
    async def test_token_usable_before_logout(self, sample_token):
        """Test token is not blacklisted before logout."""
        is_blocked = await is_token_blacklisted(sample_token)
        assert is_blocked is False

    @pytest.mark.asyncio
    async def test_token_blocked_after_logout(self, sample_token, sample_user_id):
        """Test token is blacklisted after logout."""
        from app.utils.jwt import decode_token

        token_data = decode_token(sample_token)

        # Simulate logout by blacklisting
        await blacklist_token(
            token=sample_token,
            expires_at=token_data.exp,
            user_id=str(sample_user_id),
            reason="logout",
        )

        # Token should now be blocked
        is_blocked = await is_token_blacklisted(sample_token)
        assert is_blocked is True

    @pytest.mark.asyncio
    async def test_different_token_not_affected(self, sample_user_id):
        """Test that blacklisting one token doesn't affect others."""
        from app.utils.jwt import decode_token
        import time
        from datetime import timedelta

        # Create first token with explicit expiry
        token1 = create_access_token(
            user_id=sample_user_id,
            role="officer",
            username="test_officer",
            expires_delta=timedelta(hours=1),
        )

        # Wait to ensure different timestamp (JWT uses seconds)
        time.sleep(1.1)

        # Create second token - different user to ensure different content
        other_user_id = uuid4()
        token2 = create_access_token(
            user_id=other_user_id,
            role="officer",
            username="different_officer",
            expires_delta=timedelta(hours=1),
        )

        token_data = decode_token(token1)

        # Blacklist first token
        await blacklist_token(
            token=token1,
            expires_at=token_data.exp,
        )

        # First token is blocked
        assert await is_token_blacklisted(token1) is True

        # Second token (different user) is NOT blocked
        assert await is_token_blacklisted(token2) is False
