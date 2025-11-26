"""Grievance schemas for API validation"""

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID


class Language(str, Enum):
    """Supported languages"""
    TELUGU = "te"
    ENGLISH = "en"
    HINDI = "hi"


class Channel(str, Enum):
    """Grievance submission channels"""
    WEB = "web"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    VOICE = "voice"


class GrievanceStatus(str, Enum):
    """Grievance status values"""
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"
    REJECTED = "rejected"


class Priority(str, Enum):
    """Grievance priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"


class JobStatus(str, Enum):
    """Async job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VerificationMethod(str, Enum):
    """Verification methods"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    CALL = "call"
    EMAIL = "email"


class CitizenResponse(str, Enum):
    """Citizen verification response"""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


class AuditAction(str, Enum):
    """Audit log actions"""
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    REOPENED = "REOPENED"


class AttachmentType(str, Enum):
    """Attachment types"""
    BEFORE = "before"
    AFTER = "after"
    EVIDENCE = "evidence"
    DOCUMENT = "document"


class GrievanceCreateRequest(BaseModel):
    """Request schema for creating a new grievance"""
    citizen_name: str = Field(..., min_length=2, max_length=100, description="Citizen full name")
    citizen_phone: str = Field(..., pattern=r'^\+91[6-9]\d{9}$', description="Citizen phone (+91XXXXXXXXXX)")
    citizen_email: Optional[EmailStr] = Field(None, description="Citizen email (optional)")
    citizen_address: str = Field(..., min_length=10, max_length=500, description="Full address")
    district_code: str = Field(..., pattern=r'^[0-9]{2}$', description="District code (01-13)")
    grievance_text: str = Field(..., min_length=20, max_length=5000, description="Detailed grievance")
    language: Language = Field(..., description="Language code")
    department_id: Optional[UUID] = Field(None, description="Department UUID (optional, auto-assigned if not provided)")
    subject: Optional[str] = Field(None, max_length=500, description="Brief subject (optional)")
    channel: Channel = Field(..., description="Submission channel")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="GPS longitude")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @field_validator('grievance_text')
    @classmethod
    def validate_grievance_text_not_empty(cls, v: str) -> str:
        """Ensure grievance text is not empty after stripping whitespace"""
        if not v or v.strip() == "":
            raise ValueError("Grievance text cannot be empty")
        return v.strip()

    @field_validator('district_code')
    @classmethod
    def validate_district_code_range(cls, v: str) -> str:
        """Validate district code is in valid range 01-13 (Andhra Pradesh districts)"""
        if not v:
            raise ValueError("District code is required")
        try:
            district_num = int(v)
            if not (1 <= district_num <= 13):
                raise ValueError(f"District code must be between 01 and 13, got {v}")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"District code must be numeric, got {v}")
            raise
        return v

    @field_validator('department_id')
    @classmethod
    def validate_department_id(cls, v: Optional[UUID]) -> Optional[UUID]:
        """Validate department ID is a valid UUID if provided"""
        # UUID validation is automatic via type hint
        return v

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "citizen_name": "Rajesh Kumar",
                "citizen_phone": "+919876543210",
                "citizen_email": "rajesh@example.com",
                "citizen_address": "Plot 123, MG Road, Vijayawada, Krishna District",
                "district_code": "05",
                "grievance_text": "Government hospital doctors are not available. My mother has been sick for 3 days but no treatment.",
                "language": "te",
                "channel": "web",
                "latitude": 16.5062,
                "longitude": 80.6480
            }
        }
    )


class GrievanceUpdateRequest(BaseModel):
    """Request schema for updating a grievance"""
    status: Optional[GrievanceStatus] = None
    assigned_officer_id: Optional[str] = Field(None, description="Officer UUID to assign")
    department_id: Optional[UUID] = Field(None, description="For manual department reassignment (supervisor only)")
    resolution_text: Optional[str] = Field(None, min_length=20, max_length=5000)
    resolution_notes: Optional[str] = Field(None, max_length=2000)

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "status": "in_progress",
                "resolution_notes": "Inspected site. Scheduling repair work."
            }
        }
    )


class GrievanceResponse(BaseModel):
    """Response schema for grievance (basic)"""
    id: str = Field(..., description="Grievance UUID")
    grievance_id: str = Field(..., pattern=r'^PGRS-\d{4}-\d{2}-\d{5}$', description="Public grievance ID")
    citizen_name: str
    citizen_phone: str
    citizen_email: Optional[str] = None
    citizen_address: str
    status: GrievanceStatus
    priority: Priority
    department: Optional[Dict[str, Any]] = None
    district: Dict[str, Any]
    assigned_officer: Optional[Dict[str, Any]] = None
    sla_days: int
    due_date: datetime
    grievance_text: str
    language: Language
    channel: Channel
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "grievance_id": "PGRS-2025-05-00001",
                "citizen_name": "Rajesh Kumar",
                "citizen_phone": "+919876543210",
                "status": "submitted",
                "priority": "high",
                "district": {"id": 5, "code": "05", "name": "Krishna"},
                "sla_days": 7,
                "due_date": "2025-12-01T10:30:00Z",
                "created_at": "2025-11-24T10:30:00Z"
            }
        }
    )


class AttachmentResponse(BaseModel):
    """Attachment metadata"""
    id: str = Field(..., description="Attachment UUID")
    file_name: str
    file_type: str = Field(..., description="MIME type")
    file_size_bytes: int
    file_url: str = Field(..., description="URL to download file")
    attachment_type: Optional[AttachmentType] = None
    uploaded_at: datetime

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "file_name": "evidence.jpg",
                "file_type": "image/jpeg",
                "file_size_bytes": 1024000,
                "file_url": "https://storage.dhruva.ap.gov.in/attachments/550e8400.jpg",
                "attachment_type": "evidence",
                "uploaded_at": "2025-11-24T10:30:00Z"
            }
        }
    )


class AuditLogResponse(BaseModel):
    """Audit log entry"""
    id: str = Field(..., description="Audit log UUID")
    action: AuditAction
    actor: Optional[Dict[str, Any]] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "action": "ASSIGNED",
                "actor": {"id": "...", "username": "supervisor_krishna"},
                "old_value": None,
                "new_value": {"assigned_officer_id": "..."},
                "reason": "Assigned to officer for investigation",
                "created_at": "2025-11-24T10:30:00Z"
            }
        }
    )


class VerificationResponse(BaseModel):
    """Verification response"""
    id: str = Field(..., description="Verification UUID")
    verification_method: VerificationMethod
    phone_number: Optional[str] = None
    message_sent_at: datetime
    citizen_response: CitizenResponse
    citizen_rating: Optional[int] = Field(None, ge=1, le=5)
    response_received_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "verification_method": "whatsapp",
                "phone_number": "+919876543210",
                "message_sent_at": "2025-11-24T10:30:00Z",
                "citizen_response": "approved",
                "citizen_rating": 5,
                "response_received_at": "2025-11-24T11:00:00Z"
            }
        }
    )


class GrievanceDetailResponse(GrievanceResponse):
    """Response schema for grievance (detailed with relationships)"""
    attachments: List[AttachmentResponse] = []
    audit_logs: List[AuditLogResponse] = []
    verifications: List[VerificationResponse] = []


class GrievanceListResponse(BaseModel):
    """Response schema for paginated grievance list"""
    data: List[GrievanceResponse]
    pagination: Dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "grievance_id": "PGRS-2025-05-00001",
                        "status": "submitted"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 50,
                    "total_items": 1234,
                    "total_pages": 25
                }
            }
        }
    )


class GrievancePublicResponse(BaseModel):
    """Public grievance response (no PII)"""
    grievance_id: str = Field(..., pattern=r'^PGRS-\d{4}-\d{2}-\d{5}$')
    status: GrievanceStatus
    submitted_at: datetime
    estimated_resolution_date: Optional[datetime] = None
    department: Dict[str, Any]
    district: Dict[str, Any]
    status_history: List[Dict[str, Any]]

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "grievance_id": "PGRS-2025-05-00001",
                "status": "in_progress",
                "submitted_at": "2025-11-24T10:30:00Z",
                "estimated_resolution_date": "2025-12-01T10:30:00Z",
                "department": {
                    "code": "HLTH",
                    "name": "Health Department",
                    "name_telugu": "ఆరోగ్య శాఖ"
                },
                "district": {
                    "code": "05",
                    "name": "Krishna"
                },
                "status_history": [
                    {
                        "status": "SUBMITTED",
                        "timestamp": "2025-11-24T10:30:00Z",
                        "message": "Grievance submitted successfully"
                    }
                ]
            }
        }
    )


class BulkUpdateRequest(BaseModel):
    """Bulk update request"""
    grievance_ids: List[str] = Field(..., min_length=1, max_length=100, description="List of grievance IDs (max 100)")
    updates: Dict[str, Any] = Field(..., description="Fields to update")

    @field_validator('grievance_ids')
    @classmethod
    def validate_grievance_ids(cls, v: List[str]) -> List[str]:
        for gid in v:
            if not gid.startswith("PGRS-"):
                raise ValueError(f"Invalid grievance ID format: {gid}")
        return v

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "grievance_ids": [
                    "PGRS-2025-05-00001",
                    "PGRS-2025-05-00002"
                ],
                "updates": {
                    "assigned_officer_id": "550e8400-e29b-41d4-a716-446655440000",
                    "audit_reason": "Reassigned due to officer leave"
                }
            }
        }
    )


class BulkUpdateResponse(BaseModel):
    """Bulk update response"""
    message: str
    updated_count: int
    failed_count: int
    results: List[Dict[str, Any]]

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "message": "Successfully updated 2 of 2 grievances",
                "updated_count": 2,
                "failed_count": 0,
                "results": [
                    {"grievance_id": "PGRS-2025-05-00001", "status": "success"},
                    {"grievance_id": "PGRS-2025-05-00002", "status": "success"}
                ]
            }
        }
    )


class OTPResponse(BaseModel):
    """OTP request response"""
    message: str = Field(..., description="Confirmation message with masked phone")
    expires_in_seconds: int = Field(..., description="OTP validity period (300 seconds)")
    retry_allowed_in_seconds: int = Field(..., description="Seconds before next OTP request")
    remaining_attempts: int = Field(..., ge=0, le=3, description="OTP requests remaining")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "message": "OTP sent to +91****3210",
                "expires_in_seconds": 300,
                "retry_allowed_in_seconds": 0,
                "remaining_attempts": 3
            }
        }
    )


class OTPErrorResponse(BaseModel):
    """OTP verification error"""
    error: str
    message: str
    remaining_attempts: int = Field(..., ge=0, le=3)
    status_code: int

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "error": "Unauthorized",
                "message": "Invalid OTP",
                "remaining_attempts": 2,
                "status_code": 401
            }
        }
    )


class JobStatusResponse(BaseModel):
    """Async job status"""
    job_id: str = Field(..., description="Job UUID")
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = Field(None, description="Job result")
    error: Optional[str] = Field(None, description="Error message if failed")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "created_at": "2025-11-24T10:30:00Z",
                "completed_at": "2025-11-24T10:30:15Z",
                "result": {
                    "grievance_id": "PGRS-2025-05-00001"
                }
            }
        }
    )
