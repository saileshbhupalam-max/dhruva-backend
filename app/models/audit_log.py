"""Audit log model for tracking all changes."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUID_Type

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.grievance import Grievance
    from app.models.user import User


class AuditLog(Base, UUIDMixin):
    """Tamper-proof audit trail for all system actions."""

    __tablename__ = "audit_logs"

    grievance_id: Mapped[UUID_Type] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID_Type] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    previous_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    current_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        index=True,
    )

    # Relationships
    grievance: Mapped["Grievance"] = relationship(
        "Grievance",
        back_populates="audit_logs",
        lazy="selectin",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="audit_logs",
        lazy="selectin",
    )

    __table_args__ = (
        # Composite index for audit log queries by grievance and time
        Index(
            'idx_audit_logs_grievance_timestamp',
            'grievance_id', 'timestamp',
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog(action={self.action}, timestamp={self.timestamp}, hash={self.current_hash[:8]}...)>"
