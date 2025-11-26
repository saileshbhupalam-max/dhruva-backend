"""Lapse case model for audit training data."""

from typing import TYPE_CHECKING, Any, List
from uuid import UUID as UUID_Type

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.district import District


class LapseCase(Base, UUIDMixin, TimestampMixin):
    """Lapse case from audit reports for ML training.

    Stores 2,298 labeled Guntur cases + multi-district audit data
    with 13 lapse categories for improper redressal prediction.
    """

    __tablename__ = "lapse_cases"

    district_id: Mapped[UUID_Type | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[UUID_Type | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    lapse_category: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    lapse_category_telugu: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    lapse_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,  # "behavioral" or "procedural"
    )
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",  # "critical", "high", "medium", "low"
    )
    officer_designation: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    improper_percentage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    total_cases_audited: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    examples: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    source_audit: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,  # "guntur", "ananthapur", "constituency_pre_audit", etc.
    )
    audit_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    mandal: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    district: Mapped["District | None"] = relationship(
        "District",
        lazy="selectin",
    )
    department: Mapped["Department | None"] = relationship(
        "Department",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<LapseCase(category={self.lapse_category}, type={self.lapse_type}, severity={self.severity}, source={self.source_audit})>"
