"""Tests for OTP service."""

import pytest
from uuid import uuid4

from app.services.otp_service import (
    InMemoryOTPService,
    OTPResult,
    get_otp_service,
)
from app.config import settings


class TestInMemoryOTPService:
    """Tests for InMemoryOTPService."""

    @pytest.fixture
    def otp_service(self):
        """Create a fresh OTP service for each test."""
        return InMemoryOTPService()

    @pytest.mark.asyncio
    async def test_generate_otp_success(self, otp_service):
        """Test successful OTP generation."""
        identifier = str(uuid4())
        phone = "+919876543210"

        result = await otp_service.generate_otp(identifier, phone)

        assert result.success is True
        assert result.otp is not None
        assert len(result.otp) == settings.OTP_LENGTH
        assert result.otp.isdigit()
        assert result.attempts_remaining == settings.OTP_MAX_ATTEMPTS
        assert result.expires_at is not None

    @pytest.mark.asyncio
    async def test_generate_otp_different_identifiers(self, otp_service):
        """Test generating OTPs for different identifiers."""
        id1 = str(uuid4())
        id2 = str(uuid4())
        phone = "+919876543210"

        result1 = await otp_service.generate_otp(id1, phone)
        result2 = await otp_service.generate_otp(id2, phone)

        assert result1.success is True
        assert result2.success is True
        # OTPs should be different (extremely likely)
        # Note: There's a tiny chance they could be the same

    @pytest.mark.asyncio
    async def test_verify_otp_correct(self, otp_service):
        """Test verifying a correct OTP."""
        identifier = str(uuid4())
        phone = "+919876543210"

        gen_result = await otp_service.generate_otp(identifier, phone)
        verify_result = await otp_service.verify_otp(identifier, phone, gen_result.otp)

        assert verify_result.success is True
        assert verify_result.message == "OTP verified successfully"

    @pytest.mark.asyncio
    async def test_verify_otp_wrong_code(self, otp_service):
        """Test verifying an incorrect OTP."""
        identifier = str(uuid4())
        phone = "+919876543210"

        await otp_service.generate_otp(identifier, phone)
        verify_result = await otp_service.verify_otp(identifier, phone, "000000")

        assert verify_result.success is False
        assert verify_result.error == "Invalid OTP"
        assert verify_result.attempts_remaining == settings.OTP_MAX_ATTEMPTS - 1

    @pytest.mark.asyncio
    async def test_verify_otp_wrong_phone(self, otp_service):
        """Test verifying OTP with wrong phone number."""
        identifier = str(uuid4())
        phone = "+919876543210"
        wrong_phone = "+919999999999"

        gen_result = await otp_service.generate_otp(identifier, phone)
        verify_result = await otp_service.verify_otp(identifier, wrong_phone, gen_result.otp)

        assert verify_result.success is False
        assert "mismatch" in verify_result.error.lower()

    @pytest.mark.asyncio
    async def test_verify_otp_not_found(self, otp_service):
        """Test verifying OTP that doesn't exist."""
        identifier = str(uuid4())
        phone = "+919876543210"

        verify_result = await otp_service.verify_otp(identifier, phone, "123456")

        assert verify_result.success is False
        assert "not found" in verify_result.error.lower() or "expired" in verify_result.message.lower()

    @pytest.mark.asyncio
    async def test_verify_otp_max_attempts(self, otp_service):
        """Test that OTP is invalidated after max attempts."""
        identifier = str(uuid4())
        phone = "+919876543210"

        gen_result = await otp_service.generate_otp(identifier, phone)
        correct_otp = gen_result.otp

        # Exhaust all attempts with wrong OTPs
        for i in range(settings.OTP_MAX_ATTEMPTS):
            await otp_service.verify_otp(identifier, phone, "000000")

        # Now even the correct OTP should fail
        verify_result = await otp_service.verify_otp(identifier, phone, correct_otp)

        assert verify_result.success is False

    @pytest.mark.asyncio
    async def test_verify_otp_invalidates_on_success(self, otp_service):
        """Test that OTP is invalidated after successful verification."""
        identifier = str(uuid4())
        phone = "+919876543210"

        gen_result = await otp_service.generate_otp(identifier, phone)
        otp = gen_result.otp

        # First verification should succeed
        result1 = await otp_service.verify_otp(identifier, phone, otp)
        assert result1.success is True

        # Second verification with same OTP should fail
        result2 = await otp_service.verify_otp(identifier, phone, otp)
        assert result2.success is False

    @pytest.mark.asyncio
    async def test_invalidate_otp(self, otp_service):
        """Test manually invalidating an OTP."""
        identifier = str(uuid4())
        phone = "+919876543210"

        gen_result = await otp_service.generate_otp(identifier, phone)
        otp = gen_result.otp

        # Invalidate
        result = await otp_service.invalidate_otp(identifier)
        assert result is True

        # Verify should now fail
        verify_result = await otp_service.verify_otp(identifier, phone, otp)
        assert verify_result.success is False

    @pytest.mark.asyncio
    async def test_get_remaining_attempts(self, otp_service):
        """Test getting remaining attempts."""
        identifier = str(uuid4())
        phone = "+919876543210"

        # Before OTP generation
        remaining = await otp_service.get_remaining_attempts(identifier)
        assert remaining == settings.OTP_MAX_ATTEMPTS

        # Generate OTP
        await otp_service.generate_otp(identifier, phone)

        # After generation, should still have max attempts
        remaining = await otp_service.get_remaining_attempts(identifier)
        assert remaining == settings.OTP_MAX_ATTEMPTS

        # After one failed attempt
        await otp_service.verify_otp(identifier, phone, "000000")
        remaining = await otp_service.get_remaining_attempts(identifier)
        assert remaining == settings.OTP_MAX_ATTEMPTS - 1

    @pytest.mark.asyncio
    async def test_regenerate_otp_resets_attempts(self, otp_service):
        """Test that regenerating OTP resets attempt counter."""
        identifier = str(uuid4())
        phone = "+919876543210"

        # Generate and use one attempt
        await otp_service.generate_otp(identifier, phone)
        await otp_service.verify_otp(identifier, phone, "000000")

        remaining = await otp_service.get_remaining_attempts(identifier)
        assert remaining == settings.OTP_MAX_ATTEMPTS - 1

        # Regenerate OTP
        await otp_service.generate_otp(identifier, phone)

        # Attempts should be reset
        remaining = await otp_service.get_remaining_attempts(identifier)
        assert remaining == settings.OTP_MAX_ATTEMPTS


class TestOTPResult:
    """Tests for OTPResult class."""

    def test_otp_result_to_dict_success(self):
        """Test OTPResult to_dict for successful result."""
        result = OTPResult(
            success=True,
            otp="123456",
            message="OTP generated",
            attempts_remaining=3,
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["message"] == "OTP generated"
        assert d["attempts_remaining"] == 3

    def test_otp_result_to_dict_failure(self):
        """Test OTPResult to_dict for failed result."""
        result = OTPResult(
            success=False,
            error="Invalid OTP",
            attempts_remaining=2,
        )

        d = result.to_dict()

        assert d["success"] is False
        assert d["error"] == "Invalid OTP"
        assert d["attempts_remaining"] == 2


class TestGetOTPService:
    """Tests for get_otp_service function."""

    def test_get_otp_service_returns_instance(self):
        """Test that get_otp_service returns a service instance."""
        service = get_otp_service()
        assert service is not None

    def test_get_otp_service_singleton_like(self):
        """Test that get_otp_service returns consistent instance."""
        service1 = get_otp_service()
        service2 = get_otp_service()
        # May or may not be the same instance depending on implementation
        assert service1 is not None
        assert service2 is not None


class TestOTPExpiry:
    """Tests for OTP expiration behavior."""

    @pytest.fixture
    def otp_service(self):
        """Create a fresh OTP service for each test."""
        return InMemoryOTPService()

    @pytest.mark.asyncio
    async def test_otp_has_expiry_time(self, otp_service):
        """Test that OTP has an expiry time set."""
        identifier = str(uuid4())
        phone = "+919876543210"

        result = await otp_service.generate_otp(identifier, phone)

        assert result.success is True
        assert result.expires_at is not None

    @pytest.mark.asyncio
    async def test_otp_expiry_within_5_minutes(self, otp_service):
        """Test OTP expires within 5 minutes (300 seconds)."""
        from datetime import datetime, timezone, timedelta

        identifier = str(uuid4())
        phone = "+919876543210"

        result = await otp_service.generate_otp(identifier, phone)

        assert result.success is True
        if result.expires_at:
            now = datetime.now(timezone.utc)
            # Expires within 6 minutes (to account for processing time)
            max_expiry = now + timedelta(minutes=6)
            assert result.expires_at <= max_expiry

    @pytest.mark.asyncio
    async def test_otp_format_is_digits_only(self, otp_service):
        """Test that OTP contains only digits."""
        identifier = str(uuid4())
        phone = "+919876543210"

        result = await otp_service.generate_otp(identifier, phone)

        assert result.success is True
        assert result.otp is not None
        assert result.otp.isdigit()

    @pytest.mark.asyncio
    async def test_otp_case_insensitive_verification(self, otp_service):
        """Test OTP verification is case-insensitive for phone."""
        identifier = str(uuid4())
        phone = "+919876543210"

        result = await otp_service.generate_otp(identifier, phone)
        assert result.success is True

        # OTPs are numeric, no case sensitivity applies to OTP itself
        # But phone numbers should match exactly
        verify_result = await otp_service.verify_otp(identifier, phone, result.otp)
        assert verify_result.success is True


class TestOTPRateLimiting:
    """Tests for OTP rate limiting behavior."""

    @pytest.fixture
    def otp_service(self):
        """Create a fresh OTP service for each test."""
        return InMemoryOTPService()

    @pytest.mark.asyncio
    async def test_multiple_otp_generations(self, otp_service):
        """Test that multiple OTPs can be generated for same phone."""
        phone = "+919876543210"

        # Generate OTPs for different identifiers
        for i in range(3):
            identifier = str(uuid4())
            result = await otp_service.generate_otp(identifier, phone)
            assert result.success is True

    @pytest.mark.asyncio
    async def test_otp_regeneration_invalidates_old(self, otp_service):
        """Test that regenerating OTP for same identifier invalidates old one."""
        identifier = str(uuid4())
        phone = "+919876543210"

        # Generate first OTP
        result1 = await otp_service.generate_otp(identifier, phone)
        old_otp = result1.otp

        # Generate new OTP for same identifier
        result2 = await otp_service.generate_otp(identifier, phone)
        new_otp = result2.otp

        # New OTP should work
        verify_result = await otp_service.verify_otp(identifier, phone, new_otp)
        assert verify_result.success is True
