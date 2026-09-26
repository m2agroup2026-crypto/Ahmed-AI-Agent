from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class LearnerProfile(Base):
    """Tutor preferences and learning context for one authenticated user."""

    __tablename__ = "tutor_learner_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    grade_level: Mapped[str] = mapped_column(String(64), nullable=False)
    locale: Mapped[str] = mapped_column(String(16), default="ar-EG", nullable=False)
    subject_codes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    learning_preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LearningSession(Base):
    """A durable Tutor interaction session."""

    __tablename__ = "tutor_learning_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_code: Mapped[str] = mapped_column(String(32), nullable=False)
    curriculum_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    messages: Mapped[list["LearningMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="LearningMessage.created_at"
    )


class LearningMessage(Base):
    """A learner or tutor message stored in a learning session."""

    __tablename__ = "tutor_learning_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_learning_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    lesson_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped[LearningSession] = relationship(back_populates="messages")
