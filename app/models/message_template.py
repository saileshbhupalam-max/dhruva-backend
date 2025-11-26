"""Message template model for Telugu communication."""

from typing import Any, List

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class MessageTemplate(Base, UUIDMixin, TimestampMixin):
    """Telugu message templates for citizen communication.

    Stores 54 official PGRS templates for SMS/WhatsApp notifications
    with bilingual support and variable substitution.
    """

    __tablename__ = "message_templates"

    template_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    status: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    text_telugu: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    text_english: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    contains_department: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    extracted_departments: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    extracted_keywords: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    officer_designations: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    character_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    variables: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<MessageTemplate(id={self.template_id}, category={self.category}, chars={self.character_count})>"
