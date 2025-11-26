"""Empathy Engine models for distress detection and compassionate responses."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EmpathyTemplate(Base):
    """Pre-written empathetic response templates.

    Templates are selected based on distress level, category, and language.
    They contain placeholders that are filled with grievance-specific data.
    """

    __tablename__ = "empathy_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_key: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    distress_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
    template_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    placeholders: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
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

    __table_args__ = (
        CheckConstraint(
            "distress_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'NORMAL')",
            name="ck_empathy_templates_distress_level",
        ),
        CheckConstraint(
            "language IN ('te', 'en', 'hi')",
            name="ck_empathy_templates_language",
        ),
        Index(
            "idx_empathy_templates_lookup",
            "distress_level",
            "category",
            "language",
            postgresql_where=text("is_active = TRUE"),
        ),
    )

    def __repr__(self) -> str:
        return f"<EmpathyTemplate(key={self.template_key}, level={self.distress_level}, lang={self.language})>"


class DistressKeyword(Base):
    """Keywords used to detect distress levels in grievance text.

    Each keyword has a weight that affects how much it contributes to the
    overall distress score. Higher-level keywords (CRITICAL) have higher
    base scores.
    """

    __tablename__ = "distress_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
    )
    distress_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        server_default="1.00",
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

    __table_args__ = (
        CheckConstraint(
            "distress_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'NORMAL')",
            name="ck_distress_keywords_level",
        ),
        CheckConstraint(
            "language IN ('te', 'en', 'hi')",
            name="ck_distress_keywords_language",
        ),
        CheckConstraint(
            "weight >= 0.00 AND weight <= 2.00",
            name="ck_distress_keywords_weight",
        ),
        Index(
            "idx_distress_keywords_lookup",
            "language",
            "keyword",
            postgresql_where=text("is_active = TRUE"),
        ),
    )

    def __repr__(self) -> str:
        return f"<DistressKeyword(keyword={self.keyword}, level={self.distress_level}, lang={self.language})>"


class GrievanceSentiment(Base):
    """Stores distress analysis results for each grievance.

    Links to the grievance via grievance_id (the public PGRS-* ID).
    Records the analysis results including detected keywords and SLA adjustments.
    """

    __tablename__ = "grievance_sentiment"

    grievance_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("grievances.grievance_id", ondelete="CASCADE"),
        primary_key=True,
    )
    distress_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 2),
        nullable=True,
    )
    distress_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    detected_keywords: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
    )
    empathy_template_used: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    original_sla_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    adjusted_sla_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (
        CheckConstraint(
            "distress_score >= 0.00 AND distress_score <= 10.00",
            name="ck_grievance_sentiment_score",
        ),
        CheckConstraint(
            "distress_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'NORMAL')",
            name="ck_grievance_sentiment_level",
        ),
        Index(
            "idx_grievance_sentiment_level",
            "distress_level",
            "analyzed_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<GrievanceSentiment(grievance_id={self.grievance_id}, level={self.distress_level}, score={self.distress_score})>"
