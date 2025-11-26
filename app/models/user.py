"""User model for citizens and officials."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID as UUID_Type

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.department import Department
    from app.models.district import District
    from app.models.grievance import Grievance


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """User account for citizens and government officials.

    Supports both citizen users (who submit grievances) and official users
    (officers, supervisors, admins) who process grievances.

    Authentication is via username/password for officials and
    mobile number + OTP for citizens.
    """

    __tablename__ = "users"

    # Authentication fields (required for officials)
    username: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,  # Nullable for citizens who use phone auth
        index=True,
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,  # Nullable for citizens
    )

    # Contact information
    mobile_number: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # Role and status
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="citizen",
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Assignment (for officers and supervisors)
    department_id: Mapped[UUID_Type | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    district_id: Mapped[UUID_Type | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Activity tracking
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    department: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="users",
        lazy="selectin",
    )
    district: Mapped["District | None"] = relationship(
        "District",
        back_populates="users",
        lazy="selectin",
    )
    grievances: Mapped[list["Grievance"]] = relationship(
        "Grievance",
        back_populates="citizen",
        foreign_keys="Grievance.citizen_id",
        lazy="selectin",
    )
    assigned_grievances: Mapped[list["Grievance"]] = relationship(
        "Grievance",
        back_populates="assigned_officer",
        foreign_keys="Grievance.assigned_officer_id",
        lazy="selectin",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        lazy="selectin",
    )

    __table_args__ = (
        # Composite indexes for common query patterns
        Index('idx_users_username_active', 'username', 'is_active'),  # Login queries
        Index('idx_users_role_mobile', 'role', 'mobile_number'),
        Index('idx_users_email_role', 'email', 'role'),
        Index('idx_users_role_department', 'role', 'department_id'),
        Index('idx_users_role_district', 'role', 'district_id'),
        Index('idx_users_active_role', 'is_active', 'role'),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(username={self.username}, name={self.full_name}, role={self.role})>"
