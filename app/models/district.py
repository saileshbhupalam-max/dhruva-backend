"""District model for administrative divisions."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.grievance import Grievance
    from app.models.user import User
    from app.models.verifier_profile import VerifierProfile


class District(Base, UUIDMixin, TimestampMixin):
    """Administrative district in Andhra Pradesh.

    Andhra Pradesh has 13 districts, each with a unique code (01-13).
    Districts are used for geographic assignment of grievances
    and officer jurisdictions.
    """

    __tablename__ = "districts"

    district_code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
    )
    district_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Relationships
    grievances: Mapped[list["Grievance"]] = relationship(
        "Grievance",
        back_populates="district",
        lazy="selectin",
    )
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="district",
        lazy="selectin",
    )
    verifier_profiles: Mapped[list["VerifierProfile"]] = relationship(
        "VerifierProfile",
        back_populates="district",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<District(code={self.district_code}, name={self.district_name})>"
