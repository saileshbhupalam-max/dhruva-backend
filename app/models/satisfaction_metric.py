"""Satisfaction metric model for call center feedback."""

from typing import TYPE_CHECKING
from uuid import UUID as UUID_Type

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.department import Department


class SatisfactionMetric(Base, UUIDMixin, TimestampMixin):
    """Call center (1100) satisfaction metrics by department.

    Stores 93,892 aggregated satisfaction records across 31 departments
    for risk scoring and department prioritization.
    """

    __tablename__ = "satisfaction_metrics"

    department_id: Mapped[UUID_Type] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_feedback: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    avg_satisfaction_5: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    pct_satisfied: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    dept_risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    rank: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    relative_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="call_center_1100",
    )

    # Relationship
    department: Mapped["Department"] = relationship(
        "Department",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<SatisfactionMetric(dept={self.department_id}, feedback={self.total_feedback}, satisfaction={self.avg_satisfaction_5:.2f})>"
