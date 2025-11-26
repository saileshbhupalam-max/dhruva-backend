"""Authentication and user schemas"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    OFFICER = "officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class LoginRequest(BaseModel):
    """Login request payload"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "officer_vijayawada",
                "password": "password123"
            }
        }
    )

    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=8, description="Password")


class DistrictResponse(BaseModel):
    """District information"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440005",
                "code": "05",
                "name": "Krishna"
            }
        }
    )

    id: str = Field(..., description="District UUID")
    code: str = Field(..., pattern=r'^[0-9]{2}$')
    name: str


class DepartmentResponse(BaseModel):
    """Department information"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "code": "HLTH",
                "name": "Health Department",
                "name_telugu": "ఆరోగ్య శాఖ",
                "sla_days": 7
            }
        }
    )

    id: str = Field(..., description="Department UUID")
    code: str
    name: str
    name_telugu: Optional[str] = None
    description: Optional[str] = None
    sla_days: int = Field(..., description="Default SLA in days")


class UserResponse(BaseModel):
    """User information response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "officer_vijayawada",
                "email": "officer.vijayawada@dhruva.ap.gov.in",
                "full_name": "Ramesh Kumar",
                "phone": "+919876543211",
                "role": "officer",
                "department": {
                    "id": 1,
                    "code": "REV",
                    "name": "Revenue Department",
                    "sla_days": 30
                },
                "district": {
                    "id": 5,
                    "code": "05",
                    "name": "Krishna"
                },
                "is_active": True
            }
        }
    )

    id: str = Field(..., description="User UUID")
    username: str
    email: EmailStr
    full_name: str
    phone: str = Field(..., pattern=r'^\+91[6-9]\d{9}$')
    role: UserRole
    department: Optional[DepartmentResponse] = None
    district: Optional[DistrictResponse] = None
    is_active: bool
    last_login_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    """Login response with JWT token"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "officer_vijayawada",
                    "role": "officer"
                }
            }
        }
    )

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    user: UserResponse
