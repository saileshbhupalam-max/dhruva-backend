"""Pydantic schemas for Smart Resolution Engine API."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

import bleach
from pydantic import BaseModel, Field, field_validator, ConfigDict


class RootCause(str, Enum):
    """Root cause classification for stuck grievances."""

    WRONG_DEPARTMENT = "WRONG_DEPARTMENT"
    MISSING_INFORMATION = "MISSING_INFORMATION"
    DUPLICATE_CASE = "DUPLICATE_CASE"
    OUTSIDE_JURISDICTION = "OUTSIDE_JURISDICTION"
    NEEDS_FIELD_VISIT = "NEEDS_FIELD_VISIT"
    EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"
    CITIZEN_UNREACHABLE = "CITIZEN_UNREACHABLE"
    POLICY_LIMITATION = "POLICY_LIMITATION"
    RESOURCE_CONSTRAINT = "RESOURCE_CONSTRAINT"
    OFFICER_OVERLOAD = "OFFICER_OVERLOAD"


class InterventionResult(str, Enum):
    """Result of applying an intervention or template."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    PENDING = "PENDING"


class ResponseType(str, Enum):
    """Types of responses for clarification questions."""

    TEXT = "TEXT"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    PHOTO = "PHOTO"
    DATE = "DATE"
    NUMBER = "NUMBER"


# =============================================================================
# Internal Data Structures
# =============================================================================


class ActionStep(BaseModel):
    """A single step in a resolution template."""

    step: int
    action: str
    description: str


class ActionExecuted(BaseModel):
    """Result of executing a single action step."""

    action: str
    status: str
    details: Optional[str] = None


# =============================================================================
# Request Schemas
# =============================================================================


class ApplyTemplateRequest(BaseModel):
    """Request to apply a resolution template."""

    template_key: str = Field(..., pattern=r"^[a-z_]+$", max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize notes to prevent XSS."""
        if v is not None:
            return bleach.clean(v, tags=[], strip=True)
        return v


class ClarificationAnswer(BaseModel):
    """A single answer to a clarification question."""

    question_id: int
    response_text: Optional[str] = None
    response_choice: Optional[List[str]] = None
    response_photo_url: Optional[str] = Field(None, max_length=500)
    response_number: Optional[Decimal] = None
    response_date: Optional[date] = None

    @field_validator("response_text")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text to prevent XSS."""
        if v is not None:
            return bleach.clean(v, tags=[], strip=True)
        return v


class ClarificationSubmission(BaseModel):
    """Request to submit clarification answers."""

    responses: List[ClarificationAnswer] = Field(..., min_length=1)


class UpdateApplicationResultRequest(BaseModel):
    """Request to update a template application result."""

    result: InterventionResult
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize notes to prevent XSS."""
        if v is not None:
            return bleach.clean(v, tags=[], strip=True)
        return v


# =============================================================================
# Response Schemas
# =============================================================================


class InterventionQuestionResponse(BaseModel):
    """A clarification question with its details."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question_text: str
    response_type: ResponseType
    response_options: Optional[List[str]] = None
    is_required: bool


class ResolutionTemplateResponse(BaseModel):
    """A resolution template with its success metrics."""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: lambda v: float(v)},
    )

    id: int
    template_key: str
    department: str
    category: str
    root_cause: Optional[RootCause]
    title: str
    description: str
    action_steps: List[ActionStep]
    success_rate: Decimal
    avg_resolution_hours: int
    similar_cases_resolved: int


class RootCauseAnalysisResult(BaseModel):
    """Result of analyzing a grievance for root cause."""

    model_config = ConfigDict(json_encoders={Decimal: lambda v: float(v)})

    grievance_id: str
    detected_root_cause: RootCause
    confidence_score: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("1.00"))
    detection_signals: List[str]
    recommended_intervention: str
    clarification_questions: List[InterventionQuestionResponse] = []
    suggested_templates: List[ResolutionTemplateResponse] = []


class TemplateApplicationResult(BaseModel):
    """Result of applying a resolution template."""

    success: bool
    application_id: int
    actions_executed: List[ActionExecuted]
    next_steps: List[str]


class ClarificationResult(BaseModel):
    """Result of submitting clarification answers."""

    success: bool
    responses_saved: int
    next_action: str


class RootCauseAnalysisResponse(BaseModel):
    """Stored root cause analysis for a grievance."""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: lambda v: float(v)},
    )

    id: int
    grievance_id: str
    detected_root_cause: RootCause
    confidence_score: Optional[Decimal]
    detection_signals: List[str]
    intervention_applied: Optional[str]
    intervention_result: InterventionResult
    analyzed_at: datetime
    resolved_at: Optional[datetime]
    analyzed_by: Optional[str]


class TemplateApplicationResponse(BaseModel):
    """Stored template application record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    grievance_id: str
    template_id: int
    applied_by: str
    applied_at: datetime
    result: InterventionResult
    result_updated_at: Optional[datetime]
    notes: Optional[str]


# =============================================================================
# Query Parameter Schemas
# =============================================================================


class TemplateListParams(BaseModel):
    """Query parameters for listing templates."""

    department: Optional[str] = None
    category: Optional[str] = None
    root_cause: Optional[RootCause] = None


class QuestionListParams(BaseModel):
    """Query parameters for listing questions."""

    department: Optional[str] = None
    category: Optional[str] = None
    language: str = Field(default="en", pattern=r"^(en|te)$")
