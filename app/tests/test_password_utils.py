"""Tests for password utility functions."""

import pytest

from app.utils.password import (
    hash_password,
    verify_password,
    needs_rehash,
)


class TestHashPassword:
    """Tests for hash_password function."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        result = hash_password("testpassword123")
        assert isinstance(result, str)

    def test_hash_password_returns_bcrypt_hash(self):
        """Test that the hash is a valid bcrypt hash."""
        result = hash_password("testpassword123")
        # Bcrypt hashes start with $2b$ or $2a$
        assert result.startswith("$2b$") or result.startswith("$2a$")

    def test_hash_password_different_for_same_input(self):
        """Test that hashing same password twice gives different hashes (salt)."""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2

    def test_hash_password_empty_string(self):
        """Test hashing an empty string."""
        result = hash_password("")
        assert isinstance(result, str)
        assert result.startswith("$2b$") or result.startswith("$2a$")

    def test_hash_password_long_password(self):
        """Test hashing a long password."""
        long_password = "a" * 100
        result = hash_password(long_password)
        assert isinstance(result, str)

    def test_hash_password_unicode(self):
        """Test hashing a password with unicode characters."""
        unicode_password = "పాస్‌వర్డ్123"  # Telugu + numbers
        result = hash_password(unicode_password)
        assert isinstance(result, str)

    def test_hash_password_special_characters(self):
        """Test hashing a password with special characters."""
        special_password = "p@$$w0rd!#$%^&*()"
        result = hash_password(special_password)
        assert isinstance(result, str)


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_verify_correct_password(self):
        """Test verifying a correct password."""
        password = "correctpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verifying an incorrect password."""
        password = "correctpassword123"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_verify_empty_password(self):
        """Test verifying an empty password."""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_verify_unicode_password(self):
        """Test verifying a unicode password."""
        password = "పాస్‌వర్డ్123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_verify_special_characters(self):
        """Test verifying a password with special characters."""
        password = "p@$$w0rd!#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "CaseSensitive123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("casesensitive123", hashed) is False
        assert verify_password("CASESENSITIVE123", hashed) is False

    def test_verify_whitespace_matters(self):
        """Test that whitespace in passwords matters."""
        password = "password with spaces"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("passwordwithspaces", hashed) is False
        assert verify_password(" password with spaces ", hashed) is False


class TestNeedsRehash:
    """Tests for needs_rehash function."""

    def test_fresh_hash_no_rehash(self):
        """Test that a freshly created hash doesn't need rehashing."""
        hashed = hash_password("testpassword")
        assert needs_rehash(hashed) is False

    def test_valid_bcrypt_hash_no_rehash(self):
        """Test that a valid bcrypt hash doesn't need rehashing."""
        # Create a valid hash with default settings
        hashed = hash_password("testpassword")
        assert needs_rehash(hashed) is False

    def test_invalid_hash_raises_exception(self):
        """Test that an invalid hash format raises exception."""
        # MD5 hash format (not bcrypt) - passlib raises UnknownHashError
        md5_hash = "5f4dcc3b5aa765d61d8327deb882cf99"
        with pytest.raises(Exception):
            needs_rehash(md5_hash)

    def test_empty_hash_raises_exception(self):
        """Test that an empty hash raises exception."""
        # Empty string is not a valid bcrypt hash
        with pytest.raises(Exception):
            needs_rehash("")


class TestPasswordIntegration:
    """Integration tests for password functions."""

    def test_full_password_flow(self):
        """Test the complete password flow: hash -> verify."""
        original_password = "MySecurePassword123!"

        # Hash the password
        hashed = hash_password(original_password)

        # Verify the password
        assert verify_password(original_password, hashed) is True

        # Check if rehash is needed
        assert needs_rehash(hashed) is False

    def test_multiple_passwords(self):
        """Test hashing and verifying multiple passwords."""
        passwords = [
            "simple",
            "Complex123!",
            "వినియోగదారు",  # Telugu
            "a" * 50,  # Well under bcrypt's 72-byte limit
            " ",  # Single space
        ]

        for password in passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True
            # Wrong password should fail
            assert verify_password(password + "x", hashed) is False

    def test_bcrypt_72_byte_limit(self):
        """Test that bcrypt truncates at 72 bytes (known behavior)."""
        # bcrypt only uses first 72 bytes - this is expected behavior
        base_password = "a" * 72
        hashed = hash_password(base_password)
        # Passwords beyond 72 bytes are truncated, so this verifies as True
        assert verify_password(base_password + "ignored", hashed) is True

    def test_password_hash_length(self):
        """Test that all password hashes have consistent length."""
        passwords = ["short", "medium length password", "a" * 100]
        hash_lengths = set()

        for password in passwords:
            hashed = hash_password(password)
            hash_lengths.add(len(hashed))

        # All bcrypt hashes should have the same length (60 characters)
        assert len(hash_lengths) == 1
        assert 60 in hash_lengths
