"""External services module.

This module contains interfaces and implementations for external service integrations:
- NLP Service: Department classification using IndicBERT
- SMS Service: OTP and notifications via Twilio
- WhatsApp Service: Messages via Twilio WhatsApp
- Storage Service: File upload handling
- Rate Limiter: Redis-based rate limiting
- OTP Service: OTP generation and verification
"""

from app.services.nlp_service import INLPService, IndicBERTNLPService, MockNLPService
from app.services.sms_service import ISMSService, TwilioSMSService, MockSMSService
from app.services.whatsapp_service import (
    IWhatsAppService,
    TwilioWhatsAppService,
    MockWhatsAppService,
)
from app.services.storage_service import IStorageService, LocalStorageService
from app.services.rate_limiter import IRateLimiter, RedisRateLimiter, InMemoryRateLimiter
from app.services.otp_service import IOTPService, RedisOTPService, InMemoryOTPService

__all__ = [
    # NLP
    "INLPService",
    "IndicBERTNLPService",
    "MockNLPService",
    # SMS
    "ISMSService",
    "TwilioSMSService",
    "MockSMSService",
    # WhatsApp
    "IWhatsAppService",
    "TwilioWhatsAppService",
    "MockWhatsAppService",
    # Storage
    "IStorageService",
    "LocalStorageService",
    # Rate Limiter
    "IRateLimiter",
    "RedisRateLimiter",
    "InMemoryRateLimiter",
    # OTP
    "IOTPService",
    "RedisOTPService",
    "InMemoryOTPService",
]
