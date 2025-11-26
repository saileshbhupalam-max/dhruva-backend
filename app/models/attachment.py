"""Attachment model for grievance documents."""

from typing import TYPE_CHECKING
from uuid import UUID as UUID_Type

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.grievance import Grievance


class Attachment(Base, UUIDMixin, TimestampMixin):
    """File attachment for grievance (images, PDFs, documents)."""

    __tablename__ = "attachments"

    grievance_id: Mapped[UUID_Type] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grievances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Relationships
    grievance: Mapped["Grievance"] = relationship(
        "Grievance",
        back_populates="attachments",
        lazy="selectin",
    )

    __table_args__ = (
        # File size validation: 1 byte to 10 MB
        CheckConstraint(
            'file_size >= 1 AND file_size <= 10485760',
            name='check_file_size_valid'
        ),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Attachment(file={self.file_name}, type={self.file_type}, size={self.file_size})>"
