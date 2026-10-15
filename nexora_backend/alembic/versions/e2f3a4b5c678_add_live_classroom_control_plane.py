"""Provider-neutral live session metadata; no Azure resources or content.

Revision ID: e2f3a4b5c678
Revises: d1e2f3a4b567
"""
from alembic import op
import sqlalchemy as sa

revision = "e2f3a4b5c678"
down_revision = "d1e2f3a4b567"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("tutor_live_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("classroom_id", sa.String(36), sa.ForeignKey("tutor_classrooms.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_reference", sa.Text(), nullable=True),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recording_notice", sa.Boolean(), nullable=False),
        sa.Column("notice_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_tutor_live_sessions_classroom_id", "tutor_live_sessions", ["classroom_id"])
    op.create_table("tutor_live_participants",
        sa.Column("session_id", sa.String(36), sa.ForeignKey("tutor_live_sessions.id"), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hand_raised", sa.Boolean(), nullable=False),
        sa.Column("can_speak", sa.Boolean(), nullable=False))
    op.create_table("tutor_live_grants",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("tutor_live_sessions.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_tutor_live_grants_session_id", "tutor_live_grants", ["session_id"])
    op.create_table("tutor_live_consents",
        sa.Column("session_id", sa.String(36), sa.ForeignKey("tutor_live_sessions.id"), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("notice_version", sa.Integer(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("tutor_live_recordings",
        sa.Column("session_id", sa.String(36), sa.ForeignKey("tutor_live_sessions.id"), primary_key=True),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("provider_reference", sa.Text(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("encrypted", sa.Boolean(), nullable=False))
    op.create_table("tutor_live_audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("tutor_live_sessions.id"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_tutor_live_audit_events_session_id", "tutor_live_audit_events", ["session_id"])


def downgrade():
    for name in ("tutor_live_audit_events", "tutor_live_recordings", "tutor_live_consents",
                 "tutor_live_grants", "tutor_live_participants", "tutor_live_sessions"):
        op.drop_table(name)
