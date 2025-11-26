"""Pydantic schemas for Empathy Engine API."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

import bleach
from pydantic import BaseModel, Field, field_validator


class DistressLevel(str, Enum):
    """Distress level classification."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    NORMAL = "NORMAL"


class Language(str, Enum):
    """Supported languages."""

    TELUGU = "te"
    ENGLISH = "en"
    HINDI = "hi"


# =============================================================================
# Request Schemas
# =============================================================================


class DistressAnalysisRequest(BaseModel):
    """Request to analyze grievance text for distress signals."""

    text: str = Field(..., min_length=10, max_length=5000)
    language: Language
    grievance_id: str = Field(
        ...,
        pattern=r"^PGRS-\d{4}-[A-Z]{2,3}-\d{5}$",
        description="Grievance ID format: PGRS-YYYY-XX(X)-NNNNN where XX(X) is 2-3 letter district code",
    )
    department: str = Field(..., min_length=2, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    base_sla_days: int = Field(..., ge=1, le=90)

    @field_validator("text")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        """Sanitize input text to prevent XSS."""
        return bleach.clean(v, tags=[], strip=True)


class EmpathyTemplateCreate(BaseModel):
    """Request to create a new empathy template."""

    template_key: str = Field(..., pattern=r"^[a-z_]+$", max_length=50)
    distress_level: DistressLevel
    category: Optional[str] = Field(None, max_length=50)
    language: Language
    template_text: str = Field(..., min_length=10)
    placeholders: Dict[str, bool] = Field(default_factory=dict)


class DistressKeywordCreate(BaseModel):
    """Request to create a new distress keyword."""

    keyword: str = Field(..., max_length=100)
    language: Language
    distress_level: DistressLevel
    weight: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.00"), le=Decimal("2.00"))


# =============================================================================
# Response Schemas
# =============================================================================


class DistressAnalysisResult(BaseModel):
    """Result of distress analysis."""

    grievance_id: str
    distress_score: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("10.00"))
    distress_level: DistressLevel
    detected_keywords: List[str]
    recommended_sla_hours: int
    adjusted_sla_days: int
    empathy_template_key: str
    empathy_response: str

    class Config:
        json_encoders = {Decimal: lambda v: float(v)}


class GrievanceSentimentResponse(BaseModel):
    """Stored sentiment analysis for a grievance."""

    grievance_id: str
    distress_score: Optional[Decimal]
    distress_level: DistressLevel
    detected_keywords: List[str]
    empathy_template_used: Optional[str]
    original_sla_days: int
    adjusted_sla_days: int
    analyzed_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: float(v)}


class EmpathyTemplateResponse(BaseModel):
    """Empathy template details."""

    id: int
    template_key: str
    distress_level: DistressLevel
    category: Optional[str]
    language: Language
    template_text: str
    placeholders: Dict[str, bool]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DistressKeywordResponse(BaseModel):
    """Distress keyword details."""

    id: int
    keyword: str
    language: Language
    distress_level: DistressLevel
    weight: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {Decimal: lambda v: float(v)}


# =============================================================================
# Query Parameter Schemas
# =============================================================================


class TemplateListParams(BaseModel):
    """Query parameters for listing templates."""

    distress_level: Optional[DistressLevel] = None
    language: Optional[Language] = None
    category: Optional[str] = None


class KeywordListParams(BaseModel):
    """Query parameters for listing keywords."""

    language: Optional[Language] = None
    distress_level: Optional[DistressLevel] = None
