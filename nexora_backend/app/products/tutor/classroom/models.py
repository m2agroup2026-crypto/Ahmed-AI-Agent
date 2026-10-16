from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def new_id():
    return str(uuid4())


def now():
    return datetime.now(UTC)


class Classroom(Base):
    __tablename__ = "tutor_classrooms"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    invite_hash: Mapped[str] = mapped_column(String(64), unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)


class Enrollment(Base):
    __tablename__ = "tutor_classroom_enrollments"
    classroom_id: Mapped[str] = mapped_column(ForeignKey("tutor_classrooms.id"), primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)


class Assignment(Base):
    __tablename__ = "tutor_classroom_assignments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    classroom_id: Mapped[str] = mapped_column(ForeignKey("tutor_classrooms.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    lesson: Mapped[str] = mapped_column(Text)
    questions: Mapped[list] = mapped_column(JSON)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    provenance: Mapped[str] = mapped_column(String(80), default="teacher_original_author_declared")


class ExamAttempt(Base):
    __tablename__ = "tutor_classroom_exam_attempts"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_classroom_attempt"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    assignment_id: Mapped[str] = mapped_column(ForeignKey("tutor_classroom_assignments.id"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ExternalBook(Base):
    """Metadata only. A license declaration never enables content import."""
    __tablename__ = "tutor_external_books"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    metadata_record: Mapped[dict] = mapped_column(JSON)
