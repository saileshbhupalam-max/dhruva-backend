"""Verifier Profile model for community verification gamification."""

from datetime import datetime
from typing import TYPE_CHECKING, List
from uuid import UUID as UUID_Type

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.district import District
    from app.models.verifier_activity import VerifierActivity


class VerifierProfile(Base):
    """Gamification profile for community verifiers.

    Tracks points, badges, streaks, and verification statistics for
    community members who participate in the verification process.
    """

    __tablename__ = "verifier_profiles"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Verifier identity
    phone: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    district_id: Mapped[UUID_Type | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Gamification metrics
    total_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_verifications: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    verified_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    disputed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    inconclusive_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    accuracy_rate: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0.0,
        server_default="0.0",
    )

    # Streak tracking
    current_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    longest_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_verification_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Badge system
    badge: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="BRONZE",
        server_default="BRONZE",
    )
    badges_json: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        onupdate=datetime.utcnow,
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "badge IN ('BRONZE', 'SILVER', 'GOLD', 'CHAMPION')",
            name="ck_verifier_badge",
        ),
    )

    # Relationships
    district: Mapped["District"] = relationship(
        "District",
        back_populates="verifier_profiles",
        lazy="selectin",
    )
    activities: Mapped[List["VerifierActivity"]] = relationship(
        "VerifierActivity",
        back_populates="verifier",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<VerifierProfile(phone={self.phone}, badge={self.badge}, points={self.total_points})>"
