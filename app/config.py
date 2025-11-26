"""Application configuration using Pydantic Settings."""

import os
from typing import Any, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be overridden via environment variables or .env file.
    """

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Application Configuration
    APP_NAME: str = os.getenv("APP_NAME", "DHRUVA-PGRS")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    API_V1_PREFIX: str = "/api/v1"

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/dhruva_pgrs",
    )
    TEST_DATABASE_URL: str = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/dhruva_pgrs_test",
    )

    @field_validator('DATABASE_URL', 'TEST_DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate and transform DATABASE_URL to use asyncpg driver"""
        if v is None:
            return v

        # Transform Railway's postgresql:// to postgresql+asyncpg://
        if v.startswith('postgresql://'):
            v = v.replace('postgresql://', 'postgresql+asyncpg://', 1)

        if not v.startswith('postgresql+asyncpg://'):
            raise ValueError(
                'DATABASE_URL must use asyncpg driver. '
                'Format: postgresql+asyncpg://user:password@host:port/database\n'
                f'Got: {v[:30]}...'
            )
        return v

    # Database Pool Configuration
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

    # Redis Configuration (for rate limiting, OTP storage, caching)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_OTP_DB: int = int(os.getenv("REDIS_OTP_DB", "1"))
    REDIS_RATE_LIMIT_DB: int = int(os.getenv("REDIS_RATE_LIMIT_DB", "2"))
    REDIS_CACHE_DB: int = int(os.getenv("REDIS_CACHE_DB", "3"))

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "dev-secret-key-change-in-production-must-be-at-least-32-chars"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )

    # Password Hashing Configuration
    PASSWORD_HASH_ROUNDS: int = int(os.getenv("PASSWORD_HASH_ROUNDS", "12"))

    # CORS Configuration - all as strings, parsed in properties
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:5177,http://localhost:5178,http://localhost:5179,http://127.0.0.1:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "GET,POST,PATCH,DELETE,OPTIONS"
    CORS_ALLOW_HEADERS: str = "Authorization,Content-Type,Idempotency-Key,X-Request-ID"

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def cors_methods_list(self) -> List[str]:
        """Get CORS methods as a list."""
        return [method.strip() for method in self.CORS_ALLOW_METHODS.split(",")]

    @property
    def cors_headers_list(self) -> List[str]:
        """Get CORS headers as a list."""
        return [header.strip() for header in self.CORS_ALLOW_HEADERS.split(",")]

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_DEFAULT_REQUESTS: int = int(
        os.getenv("RATE_LIMIT_DEFAULT_REQUESTS", "100")
    )
    RATE_LIMIT_DEFAULT_WINDOW: int = int(
        os.getenv("RATE_LIMIT_DEFAULT_WINDOW", "60")
    )  # seconds
    RATE_LIMIT_GRIEVANCE_SUBMIT: int = int(
        os.getenv("RATE_LIMIT_GRIEVANCE_SUBMIT", "10")
    )  # per hour
    RATE_LIMIT_OTP_REQUEST: int = int(
        os.getenv("RATE_LIMIT_OTP_REQUEST", "3")
    )  # per 5 minutes

    # OTP Configuration
    OTP_EXPIRY_SECONDS: int = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))  # 5 minutes
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "3"))
    OTP_LENGTH: int = int(os.getenv("OTP_LENGTH", "6"))

    # NLP Service Configuration (IndicBERT)
    NLP_SERVICE_URL: str = os.getenv(
        "NLP_SERVICE_URL",
        "http://localhost:8001"
    )
    NLP_SERVICE_TIMEOUT: int = int(os.getenv("NLP_SERVICE_TIMEOUT", "5"))  # seconds
    NLP_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("NLP_CONFIDENCE_THRESHOLD", "0.70")
    )
    NLP_ENABLED: bool = os.getenv("NLP_ENABLED", "true").lower() == "true"

    # Twilio SMS/WhatsApp Configuration
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    SMS_ENABLED: bool = os.getenv("SMS_ENABLED", "false").lower() == "true"
    WHATSAPP_ENABLED: bool = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"

    # File Storage Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    ALLOWED_FILE_TYPES: List[str] = os.getenv(
        "ALLOWED_FILE_TYPES",
        "image/jpeg,image/png,image/gif,application/pdf"
    ).split(",")
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")  # local, s3

    # S3 Configuration (for future use)
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    S3_REGION: str = os.getenv("S3_REGION", "ap-south-1")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Idempotency Configuration
    IDEMPOTENCY_KEY_TTL: int = int(
        os.getenv("IDEMPOTENCY_KEY_TTL", "3600")
    )  # 1 hour

    # Cache Configuration
    CACHE_REFERENCE_DATA_TTL: int = int(
        os.getenv("CACHE_REFERENCE_DATA_TTL", "86400")
    )  # 24 hours

    # Celery Configuration
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Citizen Empowerment Configuration
    EMPOWERMENT_ENABLED: bool = os.getenv("DHRUVA_EMPOWERMENT_ENABLED", "true").lower() == "true"
    EMPOWERMENT_MAX_ASK_LATER: int = int(os.getenv("DHRUVA_EMPOWERMENT_MAX_ASK_LATER", "2"))
    EMPOWERMENT_ASK_LATER_DELAY_HOURS: int = int(
        os.getenv("DHRUVA_EMPOWERMENT_ASK_LATER_DELAY_HOURS", "24")
    )

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # Allow extra fields from .env
    }

    def get_database_url(self, test: bool = False) -> str:
        """Get appropriate database URL based on environment."""
        if test or self.ENVIRONMENT == "testing":
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL

    def get_pool_config(self) -> dict[str, Any]:
        """Get database pool configuration."""
        return {
            "pool_size": self.DATABASE_POOL_SIZE,
            "max_overflow": self.DATABASE_MAX_OVERFLOW,
            "pool_timeout": self.DATABASE_POOL_TIMEOUT,
            "pool_recycle": self.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,  # Verify connections before using
        }

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()
