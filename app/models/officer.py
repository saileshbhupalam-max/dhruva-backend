"""Officer model for performance tracking."""

from typing import TYPE_CHECKING
from uuid import UUID as UUID_Type

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.department import Department


class Officer(Base, UUIDMixin, TimestampMixin):
    """Officer performance metrics for grievance handling.

    Tracks 490 officers across 34 departments with workload and
    improper redressal metrics for ML-based prediction.
    """

    __tablename__ = "officers"

    department_id: Mapped[UUID_Type] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    designation: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
    received: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    viewed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    pending: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    redressed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    improper_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    workload: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    viewed_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    throughput: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    dept_context: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationship
    department: Mapped["Department"] = relationship(
        "Department",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Officer(designation={self.designation}, dept={self.department_id}, improper={self.improper_rate:.2%})>"
