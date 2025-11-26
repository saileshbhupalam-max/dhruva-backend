"""Audio clip model for transcribed voice messages."""

from typing import Any, List

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class AudioClip(Base, UUIDMixin, TimestampMixin):
    """Transcribed audio clip from PGRS voice messages.

    Stores metadata and transcriptions of Telugu audio files used for
    voice message classification and keyword extraction.
    """

    __tablename__ = "audio_clips"

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    source_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    duration_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    transcription_telugu: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    transcription_english: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    language_detected: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="te",
    )
    contains_department_name: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )
    departments_mentioned: Mapped[List[Any]] = mapped_column(
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
    transcription_length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="success",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<AudioClip(file={self.filename}, duration={self.duration_seconds}s, confidence={self.confidence:.2f})>"
