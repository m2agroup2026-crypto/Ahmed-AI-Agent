from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Float,
    DateTime,
    JSON,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.database.base import Base


class LearningProfile(Base):

    __tablename__ = "learning_profiles"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
    )


    learning_state: Mapped[str] = mapped_column(
        String(100),
        default="new",
    )


    confidence_level: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )


    preferred_strategy: Mapped[str] = mapped_column(
        String(100),
        default="adaptive",
    )


    emotion_state: Mapped[str] = mapped_column(
        String(100),
        default="neutral",
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )



class MasteryRecord(Base):

    __tablename__ = "mastery_records"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
    )


    score: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )


    level: Mapped[str] = mapped_column(
        String(50),
        default="explorer",
    )


    knowledge: Mapped[float] = mapped_column(
        Float,
        default=0,
    )


    problem_solving: Mapped[float] = mapped_column(
        Float,
        default=0,
    )


    creativity: Mapped[float] = mapped_column(
        Float,
        default=0,
    )


    curiosity: Mapped[float] = mapped_column(
        Float,
        default=0,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )



class StudentWallet(Base):

    __tablename__ = "student_wallets"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
        unique=True,
    )


    xp_points: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )


    creator_tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )


    discount_points: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )



class LearningEvent(Base):

    __tablename__ = "learning_events"


    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )


    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
    )


    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )


    payload: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
