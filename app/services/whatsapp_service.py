"""WhatsApp Service for sending messages via Twilio WhatsApp API.

Provides WhatsApp messaging with fallback to SMS on failure.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from app.config import settings
from app.services.sms_service import SMSResult, get_sms_service

logger = logging.getLogger(__name__)


class WhatsAppResult:
    """Result of WhatsApp send operation."""

    def __init__(
        self,
        success: bool,
        message_sid: Optional[str] = None,
        to_phone: Optional[str] = None,
        status: Optional[str] = None,
        error: Optional[str] = None,
        fallback_to_sms: bool = False,
        sms_result: Optional[SMSResult] = None,
    ):
        self.success = success
        self.message_sid = message_sid
        self.to_phone = to_phone
        self.status = status
        self.error = error
        self.fallback_to_sms = fallback_to_sms
        self.sms_result = sms_result

    def to_dict(self) -> Dict[str, Union[bool, str, Dict[str, Any], None]]:
        """Convert to dictionary."""
        result: Dict[str, Union[bool, str, Dict[str, Any], None]] = {
            "success": self.success,
            "message_sid": self.message_sid,
            "to_phone": self.to_phone,
            "status": self.status,
            "error": self.error,
            "fallback_to_sms": self.fallback_to_sms,
        }
        if self.sms_result:
            result["sms_result"] = self.sms_result.to_dict()
        return result


class IWhatsAppService(ABC):
    """Interface for WhatsApp messaging service."""

    @abstractmethod
    async def send_message(
        self,
        to_phone: str,
        message: str,
        fallback_to_sms: bool = True,
    ) -> WhatsAppResult:
        """Send a WhatsApp message.

        Args:
            to_phone: Recipient phone (E.164 format)
            message: Message content
            fallback_to_sms: Whether to fallback to SMS on failure

        Returns:
            WhatsAppResult
        """
        pass

    @abstractmethod
    async def send_otp(
        self,
        to_phone: str,
        otp: str,
        fallback_to_sms: bool = True,
    ) -> WhatsAppResult:
        """Send OTP via WhatsApp.

        Args:
            to_phone: Recipient phone
            otp: OTP code
            fallback_to_sms: Whether to fallback to SMS

        Returns:
            WhatsAppResult
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check WhatsApp service health."""
        pass


class TwilioWhatsAppService(IWhatsAppService):
    """Production WhatsApp service using Twilio.

    Sends WhatsApp messages via Twilio API.
    Falls back to SMS if WhatsApp fails.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.from_number = from_number or settings.TWILIO_WHATSAPP_NUMBER
        self._client = None

    def _get_client(self) -> Any:
        """Get or create Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client

                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                raise RuntimeError("Twilio library not installed")
        return self._client

    async def send_message(
        self,
        to_phone: str,
        message: str,
        fallback_to_sms: bool = True,
    ) -> WhatsAppResult:
        """Send WhatsApp message with optional SMS fallback.

        Args:
            to_phone: Recipient phone (E.164 format)
            message: Message content
            fallback_to_sms: Fallback to SMS on failure

        Returns:
            WhatsAppResult
        """
        if not settings.WHATSAPP_ENABLED:
            # Try SMS fallback if enabled
            if fallback_to_sms and settings.SMS_ENABLED:
                sms_service = get_sms_service()
                sms_result = await sms_service.send_sms(to_phone, message)
                return WhatsAppResult(
                    success=sms_result.success,
                    to_phone=to_phone,
                    error="WhatsApp disabled, used SMS fallback",
                    fallback_to_sms=True,
                    sms_result=sms_result,
                )

            return WhatsAppResult(
                success=False,
                to_phone=to_phone,
                error="WhatsApp service disabled",
            )

        if not self.account_sid or not self.auth_token or not self.from_number:
            return WhatsAppResult(
                success=False,
                to_phone=to_phone,
                error="Twilio WhatsApp credentials not configured",
            )

        import asyncio

        try:
            client = self._get_client()

            # Format WhatsApp numbers
            wa_from = f"whatsapp:{self.from_number}"
            wa_to = f"whatsapp:{to_phone}"

            loop = asyncio.get_event_loop()
            message_obj = await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    body=message,
                    from_=wa_from,
                    to=wa_to,
                ),
            )

            return WhatsAppResult(
                success=True,
                message_sid=message_obj.sid,
                to_phone=to_phone,
                status=message_obj.status,
            )

        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")

            # Try SMS fallback
            if fallback_to_sms and settings.SMS_ENABLED:
                sms_service = get_sms_service()
                sms_result = await sms_service.send_sms(to_phone, message)
                return WhatsAppResult(
                    success=sms_result.success,
                    to_phone=to_phone,
                    error=f"WhatsApp failed: {e}, used SMS fallback",
                    fallback_to_sms=True,
                    sms_result=sms_result,
                )

            return WhatsAppResult(
                success=False,
                to_phone=to_phone,
                error=str(e),
            )

    async def send_otp(
        self,
        to_phone: str,
        otp: str,
        fallback_to_sms: bool = True,
    ) -> WhatsAppResult:
        """Send OTP via WhatsApp.

        Args:
            to_phone: Recipient phone
            otp: OTP code
            fallback_to_sms: Fallback to SMS

        Returns:
            WhatsAppResult
        """
        message = (
            f"🔐 *Dhruva PGRS Verification*\n\n"
            f"Your OTP is: *{otp}*\n\n"
            f"Valid for {settings.OTP_EXPIRY_SECONDS // 60} minutes.\n"
            f"Do not share this code with anyone."
        )
        return await self.send_message(to_phone, message, fallback_to_sms)

    async def health_check(self) -> Dict[str, Any]:
        """Check WhatsApp service health."""
        if not settings.WHATSAPP_ENABLED:
            return {
                "status": "disabled",
                "enabled": False,
            }

        if not self.from_number:
            return {
                "status": "not_configured",
                "enabled": True,
                "error": "WhatsApp number not configured",
            }

        try:
            # Just verify client can be created
            self._get_client()
            return {
                "status": "healthy",
                "enabled": True,
                "from_number": self.from_number,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "enabled": True,
                "error": str(e),
            }


class MockWhatsAppService(IWhatsAppService):
    """Mock WhatsApp service for testing."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent_messages: List[Dict[str, str]] = []
        self.call_count = 0

    async def send_message(
        self,
        to_phone: str,
        message: str,
        fallback_to_sms: bool = True,
    ) -> WhatsAppResult:
        """Mock WhatsApp send."""
        self.call_count += 1

        if self.should_fail:
            if fallback_to_sms:
                # Simulate SMS fallback
                return WhatsAppResult(
                    success=True,
                    to_phone=to_phone,
                    status="sms_fallback",
                    fallback_to_sms=True,
                )
            return WhatsAppResult(
                success=False,
                to_phone=to_phone,
                error="Mock failure",
            )

        self.sent_messages.append({
            "to": to_phone,
            "message": message,
            "channel": "whatsapp",
        })

        return WhatsAppResult(
            success=True,
            message_sid=f"MOCK_WA_SID_{self.call_count}",
            to_phone=to_phone,
            status="sent",
        )

    async def send_otp(
        self,
        to_phone: str,
        otp: str,
        fallback_to_sms: bool = True,
    ) -> WhatsAppResult:
        """Mock OTP send."""
        message = f"Your OTP is: {otp}"
        return await self.send_message(to_phone, message, fallback_to_sms)

    async def health_check(self) -> Dict[str, Any]:
        """Return mock health status."""
        return {
            "status": "healthy" if not self.should_fail else "unhealthy",
            "mock": True,
            "messages_sent": len(self.sent_messages),
        }


# Singleton instance
_whatsapp_service: Optional[IWhatsAppService] = None


def get_whatsapp_service() -> IWhatsAppService:
    """Get WhatsApp service instance.

    Returns:
        IWhatsAppService instance
    """
    global _whatsapp_service

    if _whatsapp_service is None:
        if settings.WHATSAPP_ENABLED:
            _whatsapp_service = TwilioWhatsAppService()
        else:
            _whatsapp_service = MockWhatsAppService()

    return _whatsapp_service
