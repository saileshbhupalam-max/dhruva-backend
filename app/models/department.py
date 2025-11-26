"""Department model for government departments."""

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.grievance import Grievance
    from app.models.user import User


class Department(Base, UUIDMixin, TimestampMixin):
    """Government department handling grievances.

    Each department has a default SLA (Service Level Agreement) in days
    that determines the expected resolution time for grievances assigned
    to that department.
    """

    __tablename__ = "departments"

    dept_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    dept_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    name_telugu: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sla_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7,  # Default 7-day SLA
    )

    # Relationships
    grievances: Mapped[list["Grievance"]] = relationship(
        "Grievance",
        back_populates="department",
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="department",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Department(code={self.dept_code}, name={self.dept_name}, sla={self.sla_days}d)>"
