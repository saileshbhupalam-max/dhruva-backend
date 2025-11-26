"""Verification model for data integrity checks."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUID_Type

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.grievance import Grievance


class Verification(Base, UUIDMixin):
    """Data integrity verification record."""

    __tablename__ = "verifications"

    grievance_id: Mapped[UUID_Type] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    verification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    verification_details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    grievance: Mapped["Grievance"] = relationship(
        "Grievance",
        back_populates="verifications",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Verification(type={self.verification_type}, status={self.status}, verified={self.verified})>"
