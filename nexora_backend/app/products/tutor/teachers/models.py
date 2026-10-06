from datetime import UTC, datetime, time
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class TeacherProfile(Base):
    """Human teacher profile linked to one authenticated NEXORA user."""

    __tablename__ = "tutor_teacher_profiles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    bio: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    languages: Mapped[str] = mapped_column(
        String(255),
        default="ar",
        nullable=False,
    )

    experience_years: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    verification_status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        index=True,
        nullable=False,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    subjects: Mapped[list["TeacherSubject"]] = relationship(
        back_populates="teacher",
        cascade="all, delete-orphan",
    )

    availability: Mapped[list["TeacherAvailability"]] = relationship(
        back_populates="teacher",
        cascade="all, delete-orphan",
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="teacher",
    )


class TeacherSubject(Base):
    """Subject and grade combination that a teacher can teach."""

    __tablename__ = "tutor_teacher_subjects"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "subject_code",
            "grade_level",
            name="uq_tutor_teacher_subject_grade",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    teacher_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_teacher_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    subject_code: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
    )

    grade_level: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    teacher: Mapped["TeacherProfile"] = relationship(
        back_populates="subjects",
    )


class TeacherAvailability(Base):
    """Recurring weekly availability window for a human teacher."""

    __tablename__ = "tutor_teacher_availability"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "day_of_week",
            "start_time",
            "end_time",
            name="uq_tutor_teacher_availability_window",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    teacher_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_teacher_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    day_of_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    teacher: Mapped["TeacherProfile"] = relationship(
        back_populates="availability",
    )


class Booking(Base):
    """Booking between a learner account and a human teacher."""

    __tablename__ = "tutor_teacher_bookings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    teacher_id: Mapped[str] = mapped_column(
        ForeignKey("tutor_teacher_profiles.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    learner_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    subject_code: Mapped[str] = mapped_column(
        String(32),
        index=True,
        nullable=False,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        index=True,
        nullable=False,
    )

    meeting_url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    teacher: Mapped["TeacherProfile"] = relationship(
        back_populates="bookings",
    )
