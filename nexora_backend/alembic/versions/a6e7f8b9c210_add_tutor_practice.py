"""add source-grounded tutor practice

Revision ID: a6e7f8b9c210
Revises: 9f4a2c7d1e10
Create Date: 2026-09-26 20:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6e7f8b9c210"
down_revision: Union[str, Sequence[str], None] = "9f4a2c7d1e10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tutor_curriculum_questions",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("lesson_id", sa.String(length=128), nullable=False),
        sa.Column("skill_code", sa.String(length=128), nullable=True),
        sa.Column("question_type", sa.String(length=32), nullable=False),
        sa.Column("prompt_ar", sa.Text(), nullable=False),
        sa.Column("prompt_en", sa.Text(), nullable=False),
        sa.Column("choices_ar", sa.JSON(), nullable=False),
        sa.Column("choices_en", sa.JSON(), nullable=False),
        sa.Column("accepted_answers", sa.JSON(), nullable=False),
        sa.Column("explanation_ar", sa.Text(), nullable=False),
        sa.Column("explanation_en", sa.Text(), nullable=False),
        sa.Column("source_locator", sa.String(length=255), nullable=False),
        sa.Column("source_checksum", sa.String(length=128), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["tutor_curriculum_lessons.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tutor_curriculum_questions_lesson_id",
        "tutor_curriculum_questions",
        ["lesson_id"],
    )
    op.create_index(
        "ix_tutor_curriculum_questions_skill_code",
        "tutor_curriculum_questions",
        ["skill_code"],
    )
    op.create_table(
        "tutor_assessment_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.String(length=128), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("submitted_answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["tutor_curriculum_questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["tutor_learning_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tutor_assessment_attempts_user_id",
        "tutor_assessment_attempts",
        ["user_id"],
    )
    op.create_index(
        "ix_tutor_assessment_attempts_question_id",
        "tutor_assessment_attempts",
        ["question_id"],
    )
    op.create_index(
        "ix_tutor_assessment_attempts_session_id",
        "tutor_assessment_attempts",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tutor_assessment_attempts_session_id",
        table_name="tutor_assessment_attempts",
    )
    op.drop_index(
        "ix_tutor_assessment_attempts_question_id",
        table_name="tutor_assessment_attempts",
    )
    op.drop_index(
        "ix_tutor_assessment_attempts_user_id",
        table_name="tutor_assessment_attempts",
    )
    op.drop_table("tutor_assessment_attempts")
    op.drop_index(
        "ix_tutor_curriculum_questions_skill_code",
        table_name="tutor_curriculum_questions",
    )
    op.drop_index(
        "ix_tutor_curriculum_questions_lesson_id",
        table_name="tutor_curriculum_questions",
    )
    op.drop_table("tutor_curriculum_questions")
