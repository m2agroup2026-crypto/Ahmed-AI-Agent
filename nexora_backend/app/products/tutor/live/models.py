from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.products.tutor.classroom.models import new_id, now


class LiveSession(Base):
    __tablename__ = "tutor_live_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    classroom_id: Mapped[str] = mapped_column(ForeignKey("tutor_classrooms.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    provider: Mapped[str] = mapped_column(String(32))
    provider_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="scheduled")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recording_notice: Mapped[bool] = mapped_column(Boolean, default=False)
    notice_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LiveParticipant(Base):
    __tablename__ = "tutor_live_participants"
    session_id: Mapped[str] = mapped_column(ForeignKey("tutor_live_sessions.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(16))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hand_raised: Mapped[bool] = mapped_column(Boolean, default=False)
    can_speak: Mapped[bool] = mapped_column(Boolean, default=False)


class LiveGrant(Base):
    __tablename__ = "tutor_live_grants"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("tutor_live_sessions.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LiveConsent(Base):
    __tablename__ = "tutor_live_consents"
    session_id: Mapped[str] = mapped_column(ForeignKey("tutor_live_sessions.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    notice_version: Mapped[int] = mapped_column(Integer)
    accepted: Mapped[bool] = mapped_column(Boolean)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LiveRecording(Base):
    __tablename__ = "tutor_live_recordings"
    session_id: Mapped[str] = mapped_column(ForeignKey("tutor_live_sessions.id"), primary_key=True)
    state: Mapped[str] = mapped_column(String(24), default="not_started")
    provider_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)


class LiveAuditEvent(Base):
    __tablename__ = "tutor_live_audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("tutor_live_sessions.id"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
