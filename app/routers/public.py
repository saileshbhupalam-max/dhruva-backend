"""Public Tracking Router.

Provides public grievance tracking endpoints with OTP verification:
- POST /public/grievances/{id}/request-otp - Request OTP for tracking
- GET /public/grievances/{id} - View grievance status with OTP
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.connection import get_db_session
from app.models.grievance import Grievance
from app.services.otp_service import get_otp_service
from app.services.sms_service import get_sms_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public")


# Request/Response Models


class OTPRequestBody(BaseModel):
    """OTP request body for phone verification."""

    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Phone number (E.164 format preferred: +919876543210)",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove spaces and dashes
        cleaned = v.replace(" ", "").replace("-", "")

        # Ensure numeric after optional +
        if cleaned.startswith("+"):
            if not cleaned[1:].isdigit():
                raise ValueError("Phone number must contain only digits after +")
        else:
            if not cleaned.isdigit():
                raise ValueError("Phone number must contain only digits")

        return cleaned


class OTPRequestResponse(BaseModel):
    """Response for OTP request."""

    success: bool = Field(..., description="Whether OTP was sent successfully")
    message: str = Field(..., description="Status message")
    expires_in_seconds: Optional[int] = Field(
        None,
        description="OTP expiry time in seconds",
    )
    masked_phone: Optional[str] = Field(
        None,
        description="Masked phone number for confirmation",
    )


class OTPVerifyRequest(BaseModel):
    """OTP verification in query parameters."""

    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit OTP code",
    )
    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Phone number used to request OTP",
    )

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        """Validate OTP format."""
        if not v.isdigit():
            raise ValueError("OTP must contain only digits")
        return v


class PublicGrievanceResponse(BaseModel):
    """Public-facing grievance response (limited fields)."""

    id: str = Field(..., description="Grievance UUID")
    grievance_id: str = Field(..., description="Public grievance ID (PGRS-YYYY-DD-NNNNN)")
    status: str = Field(..., description="Current status")
    subject: Optional[str] = Field(None, description="Grievance subject")
    department: Optional[Dict[str, Any]] = Field(
        None,
        description="Assigned department",
    )
    district: Optional[Dict[str, Any]] = Field(
        None,
        description="District information",
    )
    created_at: datetime = Field(..., description="Submission timestamp")
    due_date: Optional[datetime] = Field(None, description="SLA due date")
    resolution_summary: Optional[str] = Field(
        None,
        description="Brief resolution summary (if resolved)",
    )
    timeline: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Status change timeline",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "grievance_id": "PGRS-2024-05-00001",
                "status": "in_progress",
                "subject": "Road repair needed",
                "department": {
                    "name": "Roads & Buildings",
                    "code": "RB",
                },
                "district": {
                    "name": "Krishna",
                    "code": "05",
                },
                "created_at": "2024-01-15T10:30:00Z",
                "due_date": "2024-01-22T10:30:00Z",
                "timeline": [
                    {
                        "status": "submitted",
                        "timestamp": "2024-01-15T10:30:00Z",
                    },
                    {
                        "status": "assigned",
                        "timestamp": "2024-01-15T11:00:00Z",
                    },
                    {
                        "status": "in_progress",
                        "timestamp": "2024-01-16T09:00:00Z",
                    },
                ],
            }
        }


# Helper Functions


def _mask_phone(phone: str) -> str:
    """Mask phone number for display.

    Args:
        phone: Full phone number

    Returns:
        Masked phone with only last 4 digits visible
    """
    if len(phone) <= 4:
        return "****"

    # Show country code if present, mask middle, show last 4
    if phone.startswith("+"):
        # +91 9876 543210 -> +91 **** 3210
        return f"{phone[:3]} **** {phone[-4:]}"
    else:
        # 9876543210 -> **** 3210
        return f"**** {phone[-4:]}"


def _build_timeline(grievance: Grievance) -> List[Dict[str, Any]]:
    """Build status change timeline from grievance.

    Args:
        grievance: Grievance model instance

    Returns:
        List of timeline events
    """
    timeline: List[Dict[str, Any]] = []

    # Always have submitted event
    timeline.append({
        "status": "submitted",
        "timestamp": grievance.created_at.isoformat() if grievance.created_at else None,
        "description": "Grievance submitted",
    })

    # Add assigned event if officer assigned
    if grievance.assigned_at:
        timeline.append({
            "status": "assigned",
            "timestamp": grievance.assigned_at.isoformat(),
            "description": "Assigned to officer",
        })

    # Add in_progress if status indicates
    if grievance.status in ["in_progress", "resolved", "closed"]:
        # Estimate based on assigned_at or halfway to resolution
        in_progress_at = grievance.assigned_at or grievance.created_at
        if in_progress_at:
            timeline.append({
                "status": "in_progress",
                "timestamp": in_progress_at.isoformat(),
                "description": "Investigation in progress",
            })

    # Add resolved event
    if grievance.resolved_at:
        timeline.append({
            "status": "resolved",
            "timestamp": grievance.resolved_at.isoformat(),
            "description": "Resolution provided",
        })

    # Add verified event
    if grievance.verified_at:
        timeline.append({
            "status": "verified",
            "timestamp": grievance.verified_at.isoformat(),
            "description": "Resolution verified",
        })

    # Add closed event
    if grievance.closed_at:
        timeline.append({
            "status": "closed",
            "timestamp": grievance.closed_at.isoformat(),
            "description": "Grievance closed",
        })

    return timeline


# Endpoints


@router.post(
    "/grievances/{grievance_id}/request-otp",
    response_model=OTPRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request OTP for grievance tracking",
    description="Request an OTP to view grievance status. OTP is sent to the registered phone number.",
)
async def request_tracking_otp(
    grievance_id: UUID,
    body: OTPRequestBody,
    db: AsyncSession = Depends(get_db_session),
) -> OTPRequestResponse:
    """Request OTP for grievance tracking.

    Validates that the provided phone matches the grievance record,
    generates an OTP, and sends it via SMS.

    Args:
        grievance_id: Grievance UUID
        body: Request body with phone number
        db: Database session

    Returns:
        OTPRequestResponse with status

    Raises:
        HTTPException 404: Grievance not found
        HTTPException 400: Phone number doesn't match
        HTTPException 429: Rate limit exceeded
        HTTPException 500: SMS sending failed
    """
    # Find grievance
    stmt = select(Grievance).where(
        Grievance.id == grievance_id,
        Grievance.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found",
        )

    # Normalize phone numbers for comparison
    stored_phone = (grievance.citizen_phone or "").replace(" ", "").replace("-", "")
    provided_phone = body.phone.replace(" ", "").replace("-", "")

    # Remove +91 prefix for comparison if present
    if stored_phone.startswith("+91"):
        stored_phone = stored_phone[3:]
    if provided_phone.startswith("+91"):
        provided_phone = provided_phone[3:]

    # Also handle 0 prefix
    if stored_phone.startswith("0"):
        stored_phone = stored_phone[1:]
    if provided_phone.startswith("0"):
        provided_phone = provided_phone[1:]

    # Verify phone matches
    if stored_phone != provided_phone:
        logger.warning(
            f"OTP request phone mismatch for grievance {grievance_id}: "
            f"stored={_mask_phone(grievance.citizen_phone or '')} vs provided={_mask_phone(body.phone)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number does not match our records",
        )

    # Generate OTP
    otp_service = get_otp_service()
    otp_result = await otp_service.generate_otp(
        identifier=str(grievance_id),
        phone=body.phone,
    )

    if not otp_result.success:
        logger.error(f"Failed to generate OTP for grievance {grievance_id}: {otp_result.error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OTP. Please try again.",
        )

    # Send OTP via SMS
    sms_service = get_sms_service()
    assert otp_result.otp is not None  # generate_otp always sets otp on success
    sms_result = await sms_service.send_otp(
        to_phone=body.phone,
        otp=otp_result.otp,
    )

    if not sms_result.success:
        # Log failure but don't reveal to user
        logger.error(
            f"Failed to send OTP SMS for grievance {grievance_id}: {sms_result.error}"
        )
        # In development, still return success for testing
        if settings.ENVIRONMENT == "development":
            logger.warning(f"DEV MODE: OTP for {grievance_id} is {otp_result.otp}")

    logger.info(f"OTP requested for grievance {grievance_id}")

    return OTPRequestResponse(
        success=True,
        message="OTP sent to your registered phone number",
        expires_in_seconds=settings.OTP_EXPIRY_SECONDS,
        masked_phone=_mask_phone(body.phone),
    )


@router.get(
    "/grievances/{grievance_id}",
    response_model=PublicGrievanceResponse,
    summary="View grievance status with OTP",
    description="View grievance status after OTP verification. Requires valid OTP.",
)
async def get_grievance_public(
    grievance_id: UUID,
    otp: str = Query(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit OTP code",
    ),
    phone: str = Query(
        ...,
        min_length=10,
        max_length=15,
        description="Phone number used for OTP request",
    ),
    db: AsyncSession = Depends(get_db_session),
) -> PublicGrievanceResponse:
    """Get grievance status with OTP verification.

    Verifies the OTP and returns grievance status if valid.

    Args:
        grievance_id: Grievance UUID
        otp: OTP code for verification
        phone: Phone number used during OTP request
        db: Database session

    Returns:
        PublicGrievanceResponse with limited grievance info

    Raises:
        HTTPException 404: Grievance not found
        HTTPException 401: Invalid or expired OTP
        HTTPException 429: Max OTP attempts exceeded
    """
    # Verify OTP first
    otp_service = get_otp_service()
    verify_result = await otp_service.verify_otp(
        identifier=str(grievance_id),
        phone=phone,
        otp=otp,
    )

    if not verify_result.success:
        if "expired" in (verify_result.error or "").lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OTP has expired. Please request a new OTP.",
            )
        elif "max attempts" in (verify_result.error or "").lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Maximum verification attempts exceeded. Please request a new OTP.",
            )
        else:
            attempts_msg = ""
            if verify_result.attempts_remaining is not None:
                attempts_msg = f" {verify_result.attempts_remaining} attempts remaining."
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid OTP.{attempts_msg}",
            )

    # OTP verified - fetch grievance with relationships
    stmt = (
        select(Grievance)
        .options(
            selectinload(Grievance.department),
            selectinload(Grievance.district),
        )
        .where(
            Grievance.id == grievance_id,
            Grievance.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found",
        )

    logger.info(f"Public grievance view: {grievance_id}")

    # Build response with limited fields
    return PublicGrievanceResponse(
        id=str(grievance.id),
        grievance_id=grievance.grievance_id,
        status=grievance.status,
        subject=grievance.subject,
        department=(
            {
                "name": grievance.department.dept_name,
                "code": grievance.department.dept_code,
                "name_telugu": grievance.department.name_telugu,
            }
            if grievance.department
            else None
        ),
        district=(
            {
                "name": grievance.district.district_name,
                "code": grievance.district.district_code,
            }
            if grievance.district
            else None
        ),
        created_at=grievance.created_at,
        due_date=grievance.due_date,
        resolution_summary=(
            grievance.resolution_text[:200] + "..."
            if grievance.resolution_text and len(grievance.resolution_text) > 200
            else grievance.resolution_text
        ),
        timeline=_build_timeline(grievance),
    )


@router.get(
    "/grievances/track/{public_grievance_id}",
    response_model=Dict[str, Any],
    summary="Look up grievance by public ID",
    description="Find grievance by public ID (PGRS-YYYY-DD-NNNNN). Use this before requesting OTP.",
)
async def lookup_by_public_id(
    public_grievance_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Look up grievance by public ID.

    Returns grievance UUID and masked phone for OTP request.

    Args:
        public_grievance_id: Public grievance ID (e.g., PGRS-2024-05-00001)
        db: Database session

    Returns:
        Dict with id (UUID) and masked_phone

    Raises:
        HTTPException 404: Grievance not found
    """
    stmt = select(Grievance).where(
        Grievance.grievance_id == public_grievance_id,
        Grievance.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    grievance = result.scalar_one_or_none()

    if grievance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found. Please check the grievance ID.",
        )

    return {
        "id": str(grievance.id),
        "grievance_id": grievance.grievance_id,
        "masked_phone": _mask_phone(grievance.citizen_phone or ""),
        "message": "Please request OTP to view grievance details",
    }
