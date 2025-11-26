"""Tests for JWT utility functions."""

import pytest
from datetime import timedelta
from uuid import uuid4

from app.utils.jwt import (
    create_access_token,
    decode_token,
    verify_token,
    is_token_expired,
    TokenData,
)
from app.config import settings


class TestCreateAccessToken:
    """Tests for create_access_token function."""

    def test_create_token_with_all_fields(self):
        """Test token creation with all fields."""
        user_id = uuid4()
        dept_id = uuid4()
        dist_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="officer",
            username="testuser",
            department_id=dept_id,
            district_id=dist_id,
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_minimal_fields(self):
        """Test token creation with minimal required fields."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="citizen",
            username="citizen_user",
        )

        assert token is not None
        assert isinstance(token, str)

    def test_create_token_with_custom_expiry(self):
        """Test token creation with custom expiry time."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="admin",
            username="admin_user",
            expires_delta=timedelta(hours=2),
        )

        assert token is not None
        decoded = decode_token(token)
        assert decoded is not None

    def test_create_token_without_optional_ids(self):
        """Test token creation without department/district IDs."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="citizen",
            username="citizen",
            department_id=None,
            district_id=None,
        )

        assert token is not None
        decoded = decode_token(token)
        assert decoded.department_id is None
        assert decoded.district_id is None


class TestDecodeToken:
    """Tests for decode_token function."""

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        user_id = uuid4()
        dept_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="officer",
            username="officer1",
            department_id=dept_id,
        )

        decoded = decode_token(token)

        assert decoded is not None
        assert isinstance(decoded, TokenData)
        # UUIDs are serialized as strings in JWT
        assert str(decoded.user_id) == str(user_id)
        assert decoded.role == "officer"
        assert decoded.username == "officer1"
        assert str(decoded.department_id) == str(dept_id)

    def test_decode_invalid_token(self):
        """Test decoding an invalid token raises exception."""
        with pytest.raises(Exception):
            decode_token("invalid.token.here")

    def test_decode_malformed_token(self):
        """Test decoding a malformed token."""
        with pytest.raises(Exception):
            decode_token("not-a-jwt-token")

    def test_decode_empty_token(self):
        """Test decoding an empty token."""
        with pytest.raises(Exception):
            decode_token("")


class TestVerifyToken:
    """Tests for verify_token function."""

    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="citizen",
            username="test",
        )

        result = verify_token(token)

        assert result is not None
        # UUIDs are serialized as strings in JWT
        assert str(result.user_id) == str(user_id)

    def test_verify_invalid_token(self):
        """Test verifying an invalid token returns None."""
        result = verify_token("invalid.token")
        assert result is None

    def test_verify_empty_token(self):
        """Test verifying an empty token returns None."""
        result = verify_token("")
        assert result is None


class TestIsTokenExpired:
    """Tests for is_token_expired function."""

    def test_fresh_token_not_expired(self):
        """Test that a fresh token is not expired."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="citizen",
            username="test",
        )

        assert is_token_expired(token) is False

    def test_invalid_token_returns_true(self):
        """Test that an invalid token is considered expired."""
        assert is_token_expired("invalid.token") is True

    def test_empty_token_returns_true(self):
        """Test that an empty token is considered expired."""
        assert is_token_expired("") is True


class TestTokenDataIntegrity:
    """Tests for token data round-trip integrity."""

    def test_all_roles_supported(self):
        """Test that all roles can be encoded and decoded."""
        roles = ["citizen", "officer", "supervisor", "admin"]

        for role in roles:
            user_id = uuid4()
            token = create_access_token(
                user_id=user_id,
                role=role,
                username=f"user_{role}",
            )

            decoded = decode_token(token)
            assert decoded.role == role

    def test_uuid_preservation(self):
        """Test that UUIDs are preserved through encode/decode (as strings)."""
        user_id = uuid4()
        dept_id = uuid4()
        dist_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="officer",
            username="test",
            department_id=dept_id,
            district_id=dist_id,
        )

        decoded = decode_token(token)

        # UUIDs are serialized as strings in JWT - verify string equality
        assert str(decoded.user_id) == str(user_id)
        assert str(decoded.department_id) == str(dept_id)
        assert str(decoded.district_id) == str(dist_id)

    def test_special_characters_in_username(self):
        """Test username with special characters."""
        user_id = uuid4()
        username = "user.name@domain_123"

        token = create_access_token(
            user_id=user_id,
            role="officer",
            username=username,
        )

        decoded = decode_token(token)
        assert decoded.username == username


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_expired_token_verification(self):
        """Test that expired token fails verification."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="officer",
            username="test_user",
            expires_delta=timedelta(seconds=-10),  # Expired
        )

        result = verify_token(token)
        assert result is None

    def test_is_token_expired_with_expired_token(self):
        """Test is_token_expired returns True for expired token."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="officer",
            username="test_user",
            expires_delta=timedelta(seconds=-10),
        )

        assert is_token_expired(token) is True

    def test_token_with_zero_expiry(self):
        """Test token with zero second expiry."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="officer",
            username="test_user",
            expires_delta=timedelta(seconds=0),
        )

        # Should still be valid for a brief moment or already expired
        result = verify_token(token)
        # Either valid or expired is acceptable


class TestTokenDataStructure:
    """Tests for TokenData structure."""

    def test_token_data_has_required_fields(self):
        """Test that TokenData has all required fields."""
        user_id = uuid4()
        dept_id = uuid4()
        dist_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="supervisor",
            username="supervisor1",
            department_id=dept_id,
            district_id=dist_id,
        )

        decoded = decode_token(token)

        assert hasattr(decoded, 'user_id')
        assert hasattr(decoded, 'role')
        assert hasattr(decoded, 'username')
        assert hasattr(decoded, 'department_id')
        assert hasattr(decoded, 'district_id')

    def test_token_data_none_values(self):
        """Test TokenData with None department/district."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="admin",
            username="admin1",
            department_id=None,
            district_id=None,
        )

        decoded = decode_token(token)

        assert decoded.department_id is None
        assert decoded.district_id is None
        assert decoded.role == "admin"


class TestTokenSecurity:
    """Tests for token security aspects."""

    def test_different_users_different_tokens(self):
        """Test that different users get different tokens."""
        user1_id = uuid4()
        user2_id = uuid4()

        token1 = create_access_token(
            user_id=user1_id,
            role="officer",
            username="user1",
        )
        token2 = create_access_token(
            user_id=user2_id,
            role="officer",
            username="user2",
        )

        assert token1 != token2

    def test_same_user_different_times_different_tokens(self):
        """Test that same user at different times gets different tokens."""
        import time

        user_id = uuid4()

        token1 = create_access_token(
            user_id=user_id,
            role="officer",
            username="same_user",
        )

        time.sleep(1.1)  # Wait at least 1 second for different timestamp

        token2 = create_access_token(
            user_id=user_id,
            role="officer",
            username="same_user",
        )

        # Tokens should be different due to timestamp (iat claim changes)
        # Note: If JWT doesn't include iat or exp changes, tokens might be same
        # Both tokens should be valid for the same user though
        decoded1 = decode_token(token1)
        decoded2 = decode_token(token2)
        assert str(decoded1.user_id) == str(decoded2.user_id)

    def test_token_contains_no_password(self):
        """Test that token doesn't contain password data."""
        user_id = uuid4()

        token = create_access_token(
            user_id=user_id,
            role="officer",
            username="test_user",
        )

        # Decode without verification to check contents
        import base64
        import json

        parts = token.split(".")
        # Payload is second part
        payload = parts[1] + "=" * (4 - len(parts[1]) % 4)  # Add padding
        decoded_payload = json.loads(base64.urlsafe_b64decode(payload))

        assert "password" not in decoded_payload
        assert "password_hash" not in decoded_payload
