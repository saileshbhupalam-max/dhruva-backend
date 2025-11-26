"""Verifier Activity model for verification action logging."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.verifier_profile import VerifierProfile


class VerifierActivity(Base):
    """Log of verification actions for streak tracking and analytics.

    Records each verification action performed by a community verifier,
    including the result, points earned, and any bonuses applied.
    """

    __tablename__ = "verifier_activities"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Foreign keys
    verifier_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("verifier_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grievance_id: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    # Verification details
    result: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    points_earned: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    bonus_applied: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Location data
    location_lat: Mapped[float | None] = mapped_column(
        Numeric(10, 8),
        nullable=True,
    )
    location_lng: Mapped[float | None] = mapped_column(
        Numeric(11, 8),
        nullable=True,
    )

    # Additional notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamp
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "result IN ('VERIFIED', 'DISPUTED', 'INCONCLUSIVE')",
            name="ck_activity_result",
        ),
    )

    # Relationships
    verifier: Mapped["VerifierProfile"] = relationship(
        "VerifierProfile",
        back_populates="activities",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<VerifierActivity(grievance_id={self.grievance_id}, result={self.result}, points={self.points_earned})>"
