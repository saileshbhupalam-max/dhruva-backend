"""Tests for SMS service."""

import pytest

from app.services.sms_service import (
    MockSMSService,
    SMSResult,
    get_sms_service,
)


class TestSMSResult:
    """Tests for SMSResult class."""

    def test_successful_result(self):
        """Test creating a successful SMS result."""
        result = SMSResult(
            success=True,
            message_sid="SM12345",
            to_phone="+919876543210",
            status="sent",
        )

        assert result.success is True
        assert result.message_sid == "SM12345"
        assert result.to_phone == "+919876543210"
        assert result.status == "sent"
        assert result.error is None

    def test_failed_result(self):
        """Test creating a failed SMS result."""
        result = SMSResult(
            success=False,
            to_phone="+919876543210",
            error="Network error",
            retry_count=3,
        )

        assert result.success is False
        assert result.error == "Network error"
        assert result.retry_count == 3

    def test_to_dict(self):
        """Test SMSResult to_dict method."""
        result = SMSResult(
            success=True,
            message_sid="SM12345",
            to_phone="+919876543210",
            status="sent",
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["message_sid"] == "SM12345"
        assert d["to_phone"] == "+919876543210"
        assert d["status"] == "sent"


class TestMockSMSService:
    """Tests for MockSMSService."""

    @pytest.fixture
    def sms_service(self):
        """Create a fresh SMS service for each test."""
        return MockSMSService()

    @pytest.mark.asyncio
    async def test_send_sms_success(self, sms_service):
        """Test successful SMS sending."""
        result = await sms_service.send_sms(
            to_phone="+919876543210",
            message="Test message",
        )

        assert result.success is True
        assert result.message_sid is not None
        assert result.to_phone == "+919876543210"
        assert result.status == "sent"

    @pytest.mark.asyncio
    async def test_send_sms_records_message(self, sms_service):
        """Test that sent messages are recorded."""
        await sms_service.send_sms(
            to_phone="+919876543210",
            message="Test message 1",
        )
        await sms_service.send_sms(
            to_phone="+919999999999",
            message="Test message 2",
        )

        assert len(sms_service.sent_messages) == 2
        assert sms_service.sent_messages[0]["to"] == "+919876543210"
        assert sms_service.sent_messages[1]["message"] == "Test message 2"

    @pytest.mark.asyncio
    async def test_send_sms_failure_mode(self):
        """Test SMS sending in failure mode."""
        service = MockSMSService(should_fail=True)

        result = await service.send_sms(
            to_phone="+919876543210",
            message="Test message",
        )

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_send_otp(self, sms_service):
        """Test OTP sending."""
        result = await sms_service.send_otp(
            to_phone="+919876543210",
            otp="123456",
        )

        assert result.success is True
        assert "123456" in sms_service.sent_messages[-1]["message"]

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, sms_service):
        """Test health check when service is healthy."""
        health = await sms_service.health_check()

        assert health["status"] == "healthy"
        assert health["mock"] is True

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self):
        """Test health check when service is unhealthy."""
        service = MockSMSService(should_fail=True)
        health = await service.health_check()

        assert health["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_get_last_message(self, sms_service):
        """Test getting the last sent message."""
        # No messages yet
        assert sms_service.get_last_message() is None

        # Send a message
        await sms_service.send_sms(
            to_phone="+919876543210",
            message="Last message",
        )

        last = sms_service.get_last_message()
        assert last is not None
        assert last["message"] == "Last message"

    @pytest.mark.asyncio
    async def test_clear_messages(self, sms_service):
        """Test clearing sent messages."""
        await sms_service.send_sms(
            to_phone="+919876543210",
            message="Message 1",
        )
        await sms_service.send_sms(
            to_phone="+919876543210",
            message="Message 2",
        )

        assert len(sms_service.sent_messages) == 2

        sms_service.clear_messages()

        assert len(sms_service.sent_messages) == 0

    @pytest.mark.asyncio
    async def test_call_count(self, sms_service):
        """Test that call count is tracked."""
        assert sms_service.call_count == 0

        await sms_service.send_sms("+919876543210", "Message 1")
        assert sms_service.call_count == 1

        await sms_service.send_sms("+919876543210", "Message 2")
        assert sms_service.call_count == 2


class TestGetSMSService:
    """Tests for get_sms_service function."""

    def test_get_sms_service_returns_instance(self):
        """Test that get_sms_service returns a service instance."""
        service = get_sms_service()
        assert service is not None
