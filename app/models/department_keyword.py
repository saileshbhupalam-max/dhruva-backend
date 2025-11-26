"""Department keyword model for NLP-based routing."""

from typing import TYPE_CHECKING, Any, List
from uuid import UUID as UUID_Type

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.department import Department


class DepartmentKeyword(Base, UUIDMixin, TimestampMixin):
    """Keywords for automatic department routing.

    Stores bilingual (Telugu + English) keywords extracted from PGRS BOOK
    for 30 departments. Used for NLP-based grievance classification.
    """

    __tablename__ = "department_keywords"

    department_id: Mapped[UUID_Type] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_english: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    subject_telugu: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    keyword_english: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    keyword_telugu: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    sub_subjects: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    weight: Mapped[float] = mapped_column(
        nullable=False,
        default=1.0,
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationship
    department: Mapped["Department"] = relationship(
        "Department",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<DepartmentKeyword(dept={self.department_id}, keyword_en={self.keyword_english}, keyword_te={self.keyword_telugu})>"
