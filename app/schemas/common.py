"""Common Pydantic schemas used across multiple endpoints"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum


class HealthStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Basic health check response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-24T10:30:00Z",
                "version": "1.0.0"
            }
        }
    )

    status: HealthStatus
    timestamp: datetime
    version: str = Field(default="1.0.0", description="API version")


class DatabaseHealthResponse(BaseModel):
    """Database health check response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "latency_ms": 45.23,
                "connection_pool_size": 10,
                "connections_in_use": 3,
                "database_url": "localhost/dhruva_pgrs"
            }
        }
    )

    status: HealthStatus
    latency_ms: float = Field(..., description="Database query latency in milliseconds")
    connection_pool_size: int = Field(..., description="Total connections in pool")
    connections_in_use: int = Field(..., description="Currently active connections")
    database_url: str = Field(..., description="Masked database URL (no password)")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Validation Error",
                "message": "Invalid phone number format",
                "status_code": 400,
                "details": {
                    "field": "citizen_phone",
                    "code": "INVALID_PHONE_FORMAT"
                }
            }
        }
    )

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    retry_after: Optional[int] = Field(None, description="Seconds until retry allowed (for rate limits)")


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "citizen_phone",
                "message": "Invalid phone format. Use +91XXXXXXXXXX",
                "code": "INVALID_PHONE_FORMAT"
            }
        }
    )

    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")


class PaginationResponse(BaseModel):
    """Pagination metadata"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 50,
                "total_items": 1234,
                "total_pages": 25,
                "has_next": True,
                "has_previous": False
            }
        }
    )

    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether next page exists")
    has_previous: bool = Field(..., description="Whether previous page exists")
