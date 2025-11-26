"""Verifier Portal schemas for API validation."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class VerificationResult(str, Enum):
    """Verification result types."""

    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class Badge(str, Enum):
    """Verifier badge levels."""

    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    CHAMPION = "CHAMPION"


class LeaderboardPeriod(str, Enum):
    """Leaderboard time period."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


class QueueStatus(str, Enum):
    """Verification queue status filter."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"


# Request Schemas


class VerificationSubmitRequest(BaseModel):
    """Request schema for submitting verification result."""

    grievance_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Grievance ID to verify",
    )
    verifier_phone: str = Field(
        ...,
        pattern=r"^\+91[6-9]\d{9}$",
        description="Verifier phone number (+91XXXXXXXXXX)",
    )
    verification_result: VerificationResult = Field(
        ..., description="Verification result"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)",
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional verification notes",
    )
    location_lat: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="GPS latitude",
    )
    location_lng: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="GPS longitude",
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """Validate notes field."""
        if v is not None and len(v.strip()) == 0:
            return None
        return v


# Response Schemas


class GrievanceQueueItem(BaseModel):
    """Single grievance in verification queue."""

    grievance_id: str = Field(..., description="Grievance ID")
    subject: str = Field(..., description="Grievance subject")
    district_name: str = Field(..., description="District name")
    department_name: str = Field(..., description="Department name")
    resolved_at: datetime = Field(..., description="Resolution timestamp")
    days_since_resolution: int = Field(..., description="Days since resolution")
    priority: str = Field(..., description="Priority level")
    citizen_phone: str = Field(..., description="Citizen phone (masked)")

    model_config = {"from_attributes": True}


class VerificationQueueResponse(BaseModel):
    """Response for verification queue endpoint."""

    items: List[GrievanceQueueItem] = Field(
        ..., description="List of grievances awaiting verification"
    )
    total: int = Field(..., description="Total count of items")
    has_more: bool = Field(..., description="Whether more items are available")


class VerificationSubmitResponse(BaseModel):
    """Response after submitting verification."""

    success: bool = Field(..., description="Whether submission was successful")
    points_earned: int = Field(..., description="Points earned for this verification")
    total_points: int = Field(..., description="Verifier's total points")
    badge_earned: Optional[Badge] = Field(
        None, description="Badge earned (if level up occurred)"
    )

    model_config = {"from_attributes": True}


class VerifierStatsResponse(BaseModel):
    """Response for verifier statistics."""

    verifier_phone: str = Field(..., description="Verifier phone number")
    display_name: Optional[str] = Field(None, description="Display name")
    total_verifications: int = Field(..., description="Total verifications performed")
    verified_count: int = Field(..., description="Count of VERIFIED results")
    disputed_count: int = Field(..., description="Count of DISPUTED results")
    accuracy_rate: float = Field(..., description="Accuracy rate percentage")
    points: int = Field(..., description="Total points earned")
    rank: int = Field(..., description="Rank on leaderboard")
    badge: Badge = Field(..., description="Current badge level")
    badges_earned: List[str] = Field(..., description="All badges earned")
    streak_days: int = Field(..., description="Current streak in days")
    joined_at: datetime = Field(..., description="Profile creation timestamp")

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    """Single entry in leaderboard."""

    rank: int = Field(..., description="Rank position")
    verifier_phone: str = Field(..., description="Verifier phone (masked)")
    display_name: Optional[str] = Field(None, description="Display name")
    total_points: int = Field(..., description="Total points")
    total_verifications: int = Field(..., description="Total verifications")
    accuracy_rate: float = Field(..., description="Accuracy rate percentage")
    badge: Badge = Field(..., description="Current badge")
    district_name: Optional[str] = Field(None, description="District name")

    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    """Response for leaderboard endpoint."""

    period: LeaderboardPeriod = Field(..., description="Time period")
    period_start: Optional[datetime] = Field(None, description="Period start timestamp")
    period_end: Optional[datetime] = Field(None, description="Period end timestamp")
    leaders: List[LeaderboardEntry] = Field(..., description="Leaderboard entries")
    total_participants: int = Field(..., description="Total participants in period")

    model_config = {"from_attributes": True}
