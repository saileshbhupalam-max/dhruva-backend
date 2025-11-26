"""Grievance model for citizen complaints."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID as UUID_Type

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attachment import Attachment
    from app.models.audit_log import AuditLog
    from app.models.department import Department
    from app.models.district import District
    from app.models.user import User
    from app.models.verification import Verification


class Grievance(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Citizen grievance/complaint record.

    This is the central entity of the PGRS system. Each grievance represents
    a citizen's complaint that needs to be addressed by government departments.

    The grievance lifecycle:
    submitted -> assigned -> in_progress -> resolved -> verified -> closed

    Supports multiple submission channels (web, mobile, whatsapp, sms, voice)
    and languages (te=Telugu, en=English, hi=Hindi).
    """

    __tablename__ = "grievances"

    # Public-facing grievance ID (format: PGRS-YYYY-DD-NNNNN)
    grievance_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    # Citizen Information (inline for public submissions without login)
    citizen_id: Mapped[UUID_Type | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # Nullable for anonymous submissions
        index=True,
    )
    citizen_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    citizen_phone: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
    )
    citizen_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    citizen_address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Location references
    district_id: Mapped[UUID_Type] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[UUID_Type | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=True,  # Nullable until NLP classification or manual assignment
        index=True,
    )

    # Grievance content
    subject: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,  # Auto-generated from grievance_text if not provided
    )
    grievance_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    grievance_text_original: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,  # Original text before any translation
    )

    # Language and channel
    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="te",  # Default Telugu
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="web",
        index=True,
    )

    # Status and priority
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="submitted",
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
        index=True,
    )

    # Officer assignment
    assigned_officer_id: Mapped[UUID_Type | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # SLA tracking
    sla_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,
    )
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Resolution
    resolution_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,  # Internal notes, not visible to citizen
    )

    # Smart Resolution Engine fields (3B)
    officer_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,  # Officer remarks for signal detection
    )
    contact_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,  # Number of times officer tried to contact citizen
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,  # Category string for resolution template matching
        index=True,
    )

    # Timestamps
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Location (GPS coordinates)
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    location_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Extra data (JSONB for extensibility)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
    )

    # Relationships
    citizen: Mapped["User | None"] = relationship(
        "User",
        back_populates="grievances",
        foreign_keys=[citizen_id],
        lazy="selectin",
    )
    assigned_officer: Mapped["User | None"] = relationship(
        "User",
        back_populates="assigned_grievances",
        foreign_keys=[assigned_officer_id],
        lazy="selectin",
    )
    district: Mapped["District"] = relationship(
        "District",
        back_populates="grievances",
        lazy="selectin",
    )
    department: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="grievances",
        lazy="selectin",
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment",
        back_populates="grievance",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="grievance",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    verifications: Mapped[list["Verification"]] = relationship(
        "Verification",
        back_populates="grievance",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Composite indexes for common query patterns
        Index(
            'idx_grievances_district_status',
            'district_id', 'status',
            postgresql_where=text("deleted_at IS NULL")
        ),
        Index(
            'idx_grievances_department_created',
            'department_id', 'created_at',
        ),
        Index(
            'idx_grievances_officer_status',
            'assigned_officer_id', 'status',
            postgresql_where=text("deleted_at IS NULL")
        ),
        Index(
            'idx_grievances_citizen_phone',
            'citizen_phone', 'created_at',
        ),
        Index(
            'idx_grievances_status_due_date',
            'status', 'due_date',
            postgresql_where=text("deleted_at IS NULL")
        ),
        Index(
            'idx_grievances_channel_language',
            'channel', 'language',
        ),
        # Timestamp validation constraints
        CheckConstraint(
            'resolved_at IS NULL OR resolved_at >= submitted_at',
            name='check_resolved_at_valid'
        ),
        CheckConstraint(
            'verified_at IS NULL OR verified_at >= resolved_at',
            name='check_verified_at_valid'
        ),
        CheckConstraint(
            'closed_at IS NULL OR closed_at >= submitted_at',
            name='check_closed_at_valid'
        ),
        CheckConstraint(
            "status IN ('submitted', 'assigned', 'in_progress', 'resolved', 'verified', 'closed', 'rejected')",
            name='check_status_valid'
        ),
        CheckConstraint(
            "priority IN ('critical', 'high', 'normal')",
            name='check_priority_valid'
        ),
        CheckConstraint(
            "language IN ('te', 'en', 'hi')",
            name='check_language_valid'
        ),
        CheckConstraint(
            "channel IN ('web', 'mobile', 'whatsapp', 'sms', 'voice')",
            name='check_channel_valid'
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
            name='check_latitude_valid'
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
            name='check_longitude_valid'
        ),
        CheckConstraint(
            "char_length(grievance_text) >= 20",
            name='check_grievance_text_min_length'
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Grievance(id={self.grievance_id}, status={self.status}, priority={self.priority})>"
