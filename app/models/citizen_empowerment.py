"""SQLAlchemy models for Citizen Empowerment System (Task 3C).

This module contains the database models for:
- RightsKnowledgeBase: Rights information by department/category/level
- CitizenEmpowermentPreference: Citizen opt-in/out preferences
- EmpowermentInteraction: Log of all empowerment interactions
- ProactiveTriggerConfig: Configuration for proactive triggers
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RightsKnowledgeBase(Base):
    """Rights knowledge base for progressive disclosure.

    Stores rights information organized by:
    - Department (e.g., Pension, Revenue, Civil Supplies)
    - Category (e.g., Pension Delay, Ration Card, Land Survey)
    - Disclosure Level (1-4, from basic to detailed)

    Level 1: Basic rights (3 key points, 8th-grade language)
    Level 2: Officer details, office timings
    Level 3: Legal provisions, appeal process
    Level 4: Similar resolved cases, success tips
    """

    __tablename__ = "rights_knowledge_base"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    disclosure_level: Mapped[int] = mapped_column(Integer, nullable=False)
    right_title: Mapped[str] = mapped_column(String(200), nullable=False)
    right_description_en: Mapped[str] = mapped_column(Text, nullable=False)
    right_description_te: Mapped[str] = mapped_column(Text, nullable=False)
    legal_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    helpful_contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority_order: Mapped[int] = mapped_column(Integer, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "disclosure_level >= 1 AND disclosure_level <= 4",
            name="ck_rights_disclosure_level",
        ),
        Index(
            "idx_rights_lookup",
            "department",
            "category",
            "disclosure_level",
            postgresql_where="is_active = TRUE",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RightsKnowledgeBase(id={self.id}, "
            f"department={self.department}, "
            f"category={self.category}, "
            f"level={self.disclosure_level})>"
        )


class CitizenEmpowermentPreference(Base):
    """Citizen empowerment preferences for opt-in tracking.

    Tracks:
    - Opt-in/out status
    - Ask-later tracking with retry count
    - Preferred language
    - Maximum disclosure level reached
    """

    __tablename__ = "citizen_empowerment_preferences"

    citizen_phone: Mapped[str] = mapped_column(String(15), primary_key=True)
    opted_in: Mapped[bool] = mapped_column(Boolean, server_default="false")
    opted_out: Mapped[bool] = mapped_column(Boolean, server_default="false")
    ask_later: Mapped[bool] = mapped_column(Boolean, server_default="false")
    ask_later_count: Mapped[int] = mapped_column(Integer, server_default="0")
    last_ask_later_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    preferred_language: Mapped[str] = mapped_column(String(5), server_default="te")
    max_disclosure_level: Mapped[int] = mapped_column(Integer, server_default="1")
    opted_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_info_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_info_requests: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<CitizenEmpowermentPreference(phone={self.citizen_phone}, "
            f"opted_in={self.opted_in}, "
            f"level={self.max_disclosure_level})>"
        )


class EmpowermentInteraction(Base):
    """Log of empowerment interactions with citizens.

    Tracks all interactions including:
    - Opt-in prompts sent
    - Opt-in responses (YES/NO/LATER)
    - Rights information sent
    - Level-up requests
    - Proactive triggers
    """

    __tablename__ = "empowerment_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("grievances.grievance_id", ondelete="SET NULL"),
        nullable=True,
    )
    citizen_phone: Mapped[str] = mapped_column(String(15), nullable=False)
    interaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    disclosure_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rights_sent: Mapped[Optional[List[Any]]] = mapped_column(JSONB, nullable=True)
    trigger_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    citizen_response: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    message_sent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "interaction_type IN ('OPT_IN_PROMPT', 'OPT_IN_YES', 'OPT_IN_NO', "
            "'OPT_IN_LATER', 'RIGHTS_SENT', 'LEVEL_UP_REQUEST', 'PROACTIVE_TRIGGER')",
            name="ck_interaction_type",
        ),
        Index("idx_interactions_phone", "citizen_phone"),
        Index("idx_interactions_grievance", "grievance_id"),
        Index("idx_interactions_type", "interaction_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmpowermentInteraction(id={self.id}, "
            f"type={self.interaction_type}, "
            f"grievance={self.grievance_id})>"
        )


class ProactiveTriggerConfig(Base):
    """Configuration for proactive empowerment triggers.

    Defines trigger conditions and message templates for:
    - SLA_50_PERCENT: Case at 50% of SLA time
    - SLA_APPROACHING: Case at 80% of SLA time
    - NO_UPDATE_7_DAYS: No update in 7 days
    """

    __tablename__ = "proactive_trigger_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger_type: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, server_default="true")
    threshold_value: Mapped[int] = mapped_column(Integer, nullable=False)
    message_template_en: Mapped[str] = mapped_column(Text, nullable=False)
    message_template_te: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<ProactiveTriggerConfig(type={self.trigger_type}, "
            f"enabled={self.enabled})>"
        )
