from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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


class CurriculumSource(Base):
    """A registered source from which Tutor curriculum can be imported."""

    __tablename__ = "tutor_curriculum_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    license_status: Mapped[str] = mapped_column(
        String(32), default="pending_review", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    versions: Mapped[list["CurriculumVersion"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class CurriculumVersion(Base):
    """Versioned curriculum metadata; a version is never silently overwritten."""

    __tablename__ = "tutor_curriculum_versions"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_curriculum_sources.id"), index=True, nullable=False
    )
    title_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    grade_level: Mapped[str] = mapped_column(String(64), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    source: Mapped[CurriculumSource] = relationship(back_populates="versions")
    lessons: Mapped[list["CurriculumLesson"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class CurriculumSkill(Base):
    """A skill node used to adapt explanations and measure mastery later."""

    __tablename__ = "tutor_curriculum_skills"

    code: Mapped[str] = mapped_column(String(128), primary_key=True)
    curriculum_version: Mapped[str] = mapped_column(
        ForeignKey("tutor_curriculum_versions.code"), index=True, nullable=False
    )
    subject_code: Mapped[str] = mapped_column(String(32), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    description_ar: Mapped[str] = mapped_column(Text, nullable=False)
    description_en: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class CurriculumLesson(Base):
    """A reviewed lesson with provenance and source-aware content."""

    __tablename__ = "tutor_curriculum_lessons"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    curriculum_version: Mapped[str] = mapped_column(
        ForeignKey("tutor_curriculum_versions.code"), index=True, nullable=False
    )
    subject_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    title_ar: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[str] = mapped_column(String(255), nullable=False)
    summary_ar: Mapped[str] = mapped_column(Text, nullable=False)
    summary_en: Mapped[str] = mapped_column(Text, nullable=False)
    content_ar: Mapped[str] = mapped_column(Text, nullable=False)
    content_en: Mapped[str] = mapped_column(Text, nullable=False)
    skill_codes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    source_locator: Mapped[str] = mapped_column(String(255), nullable=False)
    source_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    version: Mapped[CurriculumVersion] = relationship(back_populates="lessons")


class CurriculumContentChunk(Base):
    """Searchable lesson chunk with exact source location."""

    __tablename__ = "tutor_curriculum_content_chunks"
    __table_args__ = (UniqueConstraint("lesson_id", "ordinal", name="uq_tutor_lesson_chunk"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_curriculum_lessons.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    content_ar: Mapped[str] = mapped_column(Text, nullable=False)
    content_en: Mapped[str] = mapped_column(Text, nullable=False)
    source_locator: Mapped[str] = mapped_column(String(255), nullable=False)
    content_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CurriculumQuestion(Base):
    """A validated practice question attached to one reviewed lesson."""

    __tablename__ = "tutor_curriculum_questions"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_curriculum_lessons.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill_code: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    question_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_ar: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_en: Mapped[str] = mapped_column(Text, nullable=False)
    choices_ar: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    choices_en: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    accepted_answers: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    explanation_ar: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_en: Mapped[str] = mapped_column(Text, nullable=False)
    source_locator: Mapped[str] = mapped_column(String(255), nullable=False)
    source_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    lesson: Mapped[CurriculumLesson] = relationship()


class AssessmentAttempt(Base):
    """An immutable answer event; mastery is derived from these events."""

    __tablename__ = "tutor_assessment_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_curriculum_questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("tutor_learning_sessions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    submitted_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    locale: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


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
