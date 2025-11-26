"""Pydantic schemas for Citizen Empowerment System (Task 3C).

This module contains request/response schemas for:
- Opt-in handling
- Rights information retrieval
- Level-up requests
- Knowledge base management
- Proactive triggers
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class OptInChoice(str, Enum):
    """Citizen's response to opt-in prompt."""

    YES = "YES"
    NO = "NO"
    LATER = "LATER"


class TriggerType(str, Enum):
    """Types of proactive triggers."""

    SLA_50_PERCENT = "SLA_50_PERCENT"
    SLA_APPROACHING = "SLA_APPROACHING"
    NO_UPDATE_7_DAYS = "NO_UPDATE_7_DAYS"
    MANUAL = "MANUAL"


class InteractionType(str, Enum):
    """Types of empowerment interactions."""

    OPT_IN_PROMPT = "OPT_IN_PROMPT"
    OPT_IN_YES = "OPT_IN_YES"
    OPT_IN_NO = "OPT_IN_NO"
    OPT_IN_LATER = "OPT_IN_LATER"
    RIGHTS_SENT = "RIGHTS_SENT"
    LEVEL_UP_REQUEST = "LEVEL_UP_REQUEST"
    PROACTIVE_TRIGGER = "PROACTIVE_TRIGGER"


class Language(str, Enum):
    """Supported languages."""

    TELUGU = "te"
    ENGLISH = "en"


# ============================================
# Request Schemas
# ============================================


class OptInRequest(BaseModel):
    """Request for handling citizen opt-in decision."""

    citizen_phone: str = Field(..., pattern=r"^[0-9]{10}$", description="10-digit phone number")
    grievance_id: str = Field(..., description="Grievance ID")
    response: OptInChoice = Field(..., description="Citizen's opt-in choice")
    preferred_language: Language = Field(
        default=Language.TELUGU, description="Preferred language"
    )

    @field_validator("citizen_phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number is 10 digits."""
        if len(v) != 10 or not v.isdigit():
            raise ValueError("Phone must be 10 digits")
        return v


class LevelUpRequest(BaseModel):
    """Request to move to next disclosure level."""

    citizen_phone: str = Field(..., pattern=r"^[0-9]{10}$", description="10-digit phone number")


class RightEntryCreate(BaseModel):
    """Request to create a new rights entry."""

    department: str = Field(..., max_length=50, description="Department name")
    category: str = Field(..., max_length=100, description="Category name")
    disclosure_level: int = Field(..., ge=1, le=4, description="Disclosure level 1-4")
    right_title: str = Field(..., max_length=200, description="Title of the right")
    right_description_en: str = Field(..., description="English description")
    right_description_te: str = Field(..., description="Telugu description")
    legal_reference: Optional[str] = Field(
        None, max_length=200, description="Legal reference"
    )
    helpful_contact: Optional[str] = Field(
        None, max_length=100, description="Helpful contact info"
    )
    priority_order: int = Field(default=1, ge=1, description="Priority order")


class TriggerRequest(BaseModel):
    """Request to manually trigger empowerment message."""

    trigger_type: TriggerType = Field(..., description="Type of trigger")


# ============================================
# Response Schemas
# ============================================


class RightInfo(BaseModel):
    """Individual right information."""

    id: int
    title: str
    description: str
    legal_reference: Optional[str] = None
    helpful_contact: Optional[str] = None

    model_config = {"from_attributes": True}


class EmpowermentResponse(BaseModel):
    """Response with rights information."""

    grievance_id: str
    disclosure_level: int
    rights: List[RightInfo]
    has_more_levels: bool
    message_text: str


class OptInResponse(BaseModel):
    """Response to opt-in request."""

    success: bool
    message: str
    rights_sent: bool
    empowerment_response: Optional[EmpowermentResponse] = None


class RightEntryResponse(BaseModel):
    """Response with rights entry details."""

    id: int
    department: str
    category: str
    disclosure_level: int
    right_title: str
    right_description_en: str
    right_description_te: str
    legal_reference: Optional[str] = None
    helpful_contact: Optional[str] = None
    priority_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TriggerResponse(BaseModel):
    """Response to trigger request."""

    success: bool
    message_sent: bool
    reason: Optional[str] = None


class PreferenceResponse(BaseModel):
    """Response with citizen preferences."""

    citizen_phone: str
    opted_in: bool
    opted_out: bool
    ask_later: bool
    ask_later_count: int
    last_ask_later_at: Optional[datetime] = None
    preferred_language: str
    max_disclosure_level: int
    total_info_requests: int

    model_config = {"from_attributes": True}


class InteractionLogResponse(BaseModel):
    """Response with interaction log entry."""

    id: int
    grievance_id: Optional[str]
    citizen_phone: str
    interaction_type: str
    disclosure_level: Optional[int]
    rights_sent: Optional[List[int]]
    trigger_reason: Optional[str]
    citizen_response: Optional[str]
    message_sent: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProactiveTriggerConfigResponse(BaseModel):
    """Response with trigger configuration."""

    id: int
    trigger_type: str
    enabled: bool
    threshold_value: int
    message_template_en: str
    message_template_te: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================
# List Response Schemas
# ============================================


class RightsListResponse(BaseModel):
    """Response with list of rights entries."""

    total: int
    items: List[RightEntryResponse]


class InteractionsListResponse(BaseModel):
    """Response with list of interactions."""

    total: int
    items: List[InteractionLogResponse]
