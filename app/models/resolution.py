"""Smart Resolution Engine models for root cause analysis and resolution templates."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RootCauseAnalysis(Base):
    """Stores root cause analysis results for grievances.

    Each time a grievance is analyzed for root cause, a record is created
    with the detected cause, confidence score, and detection signals.
    """

    __tablename__ = "root_cause_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("grievances.grievance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    detected_root_cause: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )
    detection_signals: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
    intervention_applied: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    intervention_result: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="PENDING",
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    analyzed_by: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "confidence_score >= 0.00 AND confidence_score <= 1.00",
            name="ck_root_cause_confidence",
        ),
        CheckConstraint(
            "detected_root_cause IN ('WRONG_DEPARTMENT', 'MISSING_INFORMATION', "
            "'DUPLICATE_CASE', 'OUTSIDE_JURISDICTION', 'NEEDS_FIELD_VISIT', "
            "'EXTERNAL_DEPENDENCY', 'CITIZEN_UNREACHABLE', 'POLICY_LIMITATION', "
            "'RESOURCE_CONSTRAINT', 'OFFICER_OVERLOAD')",
            name="ck_root_cause_type",
        ),
        CheckConstraint(
            "intervention_result IN ('SUCCESS', 'PARTIAL', 'FAILED', 'PENDING')",
            name="ck_intervention_result",
        ),
        Index("idx_root_cause_type", "detected_root_cause"),
        Index("idx_root_cause_result", "intervention_result"),
    )

    def __repr__(self) -> str:
        return (
            f"<RootCauseAnalysis(grievance={self.grievance_id}, "
            f"cause={self.detected_root_cause}, score={self.confidence_score})>"
        )


class ResolutionTemplate(Base):
    """Pre-built resolution workflows for common root causes.

    Templates contain action steps that can be executed to resolve
    grievances. Success rates are tracked and updated over time.
    """

    __tablename__ = "resolution_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    department: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    root_cause: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    template_title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    template_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    action_steps: Mapped[List[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
    )
    success_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        server_default="0.00",
    )
    avg_resolution_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    similar_cases_resolved: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    applications: Mapped[List["TemplateApplication"]] = relationship(
        "TemplateApplication",
        back_populates="template",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "success_rate >= 0.00 AND success_rate <= 100.00",
            name="ck_templates_success_rate",
        ),
        Index(
            "idx_resolution_templates_lookup",
            "department",
            "category",
            "root_cause",
            postgresql_where=text("is_active = TRUE"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ResolutionTemplate(key={self.template_key}, "
            f"dept={self.department}, success_rate={self.success_rate}%)>"
        )


class InterventionQuestion(Base):
    """Clarification questions for specific root causes.

    Questions are presented to citizens to gather missing information
    needed for resolution. Supports multiple languages and response types.
    """

    __tablename__ = "intervention_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    root_cause: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    department: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    question_text_en: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_text_te: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
    )
    response_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    response_options: Mapped[List[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    responses: Mapped[List["ClarificationResponse"]] = relationship(
        "ClarificationResponse",
        back_populates="question",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "response_type IN ('TEXT', 'SINGLE_CHOICE', 'MULTIPLE_CHOICE', "
            "'PHOTO', 'DATE', 'NUMBER')",
            name="ck_questions_response_type",
        ),
        Index(
            "idx_intervention_questions_lookup",
            "root_cause",
            "department",
            "category",
            postgresql_where=text("is_active = TRUE"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<InterventionQuestion(id={self.id}, "
            f"root_cause={self.root_cause}, order={self.question_order})>"
        )


class ClarificationResponse(Base):
    """Citizen responses to clarification questions.

    Stores answers from citizens in various formats (text, choice,
    photo URL, number, date) based on the question type.
    """

    __tablename__ = "clarification_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("grievances.grievance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("intervention_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    response_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    response_choice: Mapped[List[str] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    response_photo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    response_number: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    response_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    responded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationships
    question: Mapped["InterventionQuestion"] = relationship(
        "InterventionQuestion",
        back_populates="responses",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<ClarificationResponse(grievance={self.grievance_id}, "
            f"question={self.question_id})>"
        )


class TemplateApplication(Base):
    """Records of resolution template applications.

    Tracks when templates are applied to grievances, by whom,
    and the outcome. Used to calculate template success rates.
    """

    __tablename__ = "template_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("grievances.grievance_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resolution_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    applied_by: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    result: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="PENDING",
    )
    result_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    template: Mapped["ResolutionTemplate"] = relationship(
        "ResolutionTemplate",
        back_populates="applications",
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "result IN ('SUCCESS', 'PARTIAL', 'FAILED', 'PENDING')",
            name="ck_template_app_result",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<TemplateApplication(grievance={self.grievance_id}, "
            f"template={self.template_id}, result={self.result})>"
        )
