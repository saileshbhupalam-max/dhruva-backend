"""SMS Service for sending OTP and notifications via Twilio.

Provides SMS sending capability with retry logic and graceful degradation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class SMSResult:
    """Result of SMS send operation."""

    def __init__(
        self,
        success: bool,
        message_sid: Optional[str] = None,
        to_phone: Optional[str] = None,
        status: Optional[str] = None,
        error: Optional[str] = None,
        retry_count: int = 0,
    ):
        self.success = success
        self.message_sid = message_sid
        self.to_phone = to_phone
        self.status = status
        self.error = error
        self.retry_count = retry_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message_sid": self.message_sid,
            "to_phone": self.to_phone,
            "status": self.status,
            "error": self.error,
            "retry_count": self.retry_count,
        }


class ISMSService(ABC):
    """Interface for SMS sending service.

    All implementations must provide the send_sms method.
    """

    @abstractmethod
    async def send_sms(
        self,
        to_phone: str,
        message: str,
        retry_count: int = 3,
    ) -> SMSResult:
        """Send an SMS message.

        Args:
            to_phone: Recipient phone number (E.164 format: +919876543210)
            message: SMS message content
            retry_count: Number of retry attempts on failure

        Returns:
            SMSResult with status and message_sid
        """
        pass

    @abstractmethod
    async def send_otp(
        self,
        to_phone: str,
        otp: str,
    ) -> SMSResult:
        """Send OTP SMS.

        Args:
            to_phone: Recipient phone number
            otp: OTP code to send

        Returns:
            SMSResult
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if SMS service is healthy.

        Returns:
            Dict with status and details
        """
        pass


class TwilioSMSService(ISMSService):
    """Production SMS service using Twilio.

    Sends SMS via Twilio API with retry logic.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.from_number = from_number or settings.TWILIO_PHONE_NUMBER
        self._client = None

    def _get_client(self) -> Any:
        """Get or create Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client

                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.error("Twilio library not installed")
                raise RuntimeError("Twilio library not installed")
        return self._client

    async def send_sms(
        self,
        to_phone: str,
        message: str,
        retry_count: int = 3,
    ) -> SMSResult:
        """Send SMS via Twilio with retry logic.

        Args:
            to_phone: Recipient phone (E.164 format)
            message: Message content
            retry_count: Retry attempts

        Returns:
            SMSResult
        """
        if not settings.SMS_ENABLED:
            return SMSResult(
                success=False,
                to_phone=to_phone,
                error="SMS service disabled",
            )

        if not self.account_sid or not self.auth_token:
            return SMSResult(
                success=False,
                to_phone=to_phone,
                error="Twilio credentials not configured",
            )

        import asyncio

        last_error = None
        for attempt in range(retry_count):
            try:
                client = self._get_client()

                # Twilio is synchronous, run in executor
                loop = asyncio.get_event_loop()
                message_obj = await loop.run_in_executor(
                    None,
                    lambda: client.messages.create(
                        body=message,
                        from_=self.from_number,
                        to=to_phone,
                    ),
                )

                return SMSResult(
                    success=True,
                    message_sid=message_obj.sid,
                    to_phone=to_phone,
                    status=message_obj.status,
                    retry_count=attempt,
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"SMS send attempt {attempt + 1}/{retry_count} failed: {e}"
                )

                if attempt < retry_count - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    await asyncio.sleep(2**attempt)

        return SMSResult(
            success=False,
            to_phone=to_phone,
            error=last_error,
            retry_count=retry_count,
        )

    async def send_otp(
        self,
        to_phone: str,
        otp: str,
    ) -> SMSResult:
        """Send OTP via SMS.

        Args:
            to_phone: Recipient phone number
            otp: OTP code

        Returns:
            SMSResult
        """
        message = (
            f"Your Dhruva PGRS verification OTP is: {otp}. "
            f"Valid for {settings.OTP_EXPIRY_SECONDS // 60} minutes. "
            f"Do not share this code with anyone."
        )
        return await self.send_sms(to_phone, message)

    async def health_check(self) -> Dict[str, Any]:
        """Check Twilio service health."""
        if not settings.SMS_ENABLED:
            return {
                "status": "disabled",
                "enabled": False,
            }

        if not self.account_sid or not self.auth_token:
            return {
                "status": "not_configured",
                "enabled": True,
                "error": "Twilio credentials missing",
            }

        try:
            import asyncio

            client = self._get_client()
            loop = asyncio.get_event_loop()

            # Fetch account info as health check
            account = await loop.run_in_executor(
                None,
                lambda: client.api.accounts(self.account_sid).fetch(),
            )

            return {
                "status": "healthy",
                "enabled": True,
                "account_status": account.status,
                "from_number": self.from_number,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "enabled": True,
                "error": str(e),
            }


class MockSMSService(ISMSService):
    """Mock SMS service for testing.

    Records sent messages without actually sending them.
    """

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent_messages: List[Dict[str, str]] = []
        self.call_count = 0

    async def send_sms(
        self,
        to_phone: str,
        message: str,
        retry_count: int = 3,
    ) -> SMSResult:
        """Mock SMS send."""
        self.call_count += 1

        if self.should_fail:
            return SMSResult(
                success=False,
                to_phone=to_phone,
                error="Mock failure",
            )

        self.sent_messages.append({
            "to": to_phone,
            "message": message,
        })

        return SMSResult(
            success=True,
            message_sid=f"MOCK_SID_{self.call_count}",
            to_phone=to_phone,
            status="sent",
        )

    async def send_otp(
        self,
        to_phone: str,
        otp: str,
    ) -> SMSResult:
        """Mock OTP send."""
        message = f"Your OTP is: {otp}"
        return await self.send_sms(to_phone, message)

    async def health_check(self) -> Dict[str, Any]:
        """Return mock health status."""
        return {
            "status": "healthy" if not self.should_fail else "unhealthy",
            "mock": True,
            "messages_sent": len(self.sent_messages),
        }

    def get_last_message(self) -> Optional[Dict[str, str]]:
        """Get the last sent message."""
        return self.sent_messages[-1] if self.sent_messages else None

    def clear_messages(self) -> None:
        """Clear sent messages."""
        self.sent_messages.clear()


# Singleton instance
_sms_service: Optional[ISMSService] = None


def get_sms_service() -> ISMSService:
    """Get SMS service instance.

    Returns:
        ISMSService instance
    """
    global _sms_service

    if _sms_service is None:
        if settings.SMS_ENABLED:
            _sms_service = TwilioSMSService()
        else:
            _sms_service = MockSMSService()

    return _sms_service
