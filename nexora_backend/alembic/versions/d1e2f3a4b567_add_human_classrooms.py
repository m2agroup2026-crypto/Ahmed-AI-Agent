"""Human classrooms, original assessments and metadata-only book catalog.

Revision ID: d1e2f3a4b567
Revises: c9d0e1f234a5
"""
from alembic import op
import sqlalchemy as sa

revision = "d1e2f3a4b567"
down_revision = "c9d0e1f234a5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("tutor_classrooms",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("invite_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("archived", sa.Boolean(), nullable=False))
    op.create_index("ix_tutor_classrooms_teacher_id", "tutor_classrooms", ["teacher_id"])
    op.create_table("tutor_classroom_enrollments",
        sa.Column("classroom_id", sa.String(36), sa.ForeignKey("tutor_classrooms.id"), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True))
    op.create_table("tutor_classroom_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("classroom_id", sa.String(36), sa.ForeignKey("tutor_classrooms.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("lesson", sa.Text(), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("provenance", sa.String(80), nullable=False))
    op.create_index("ix_tutor_classroom_assignments_classroom_id", "tutor_classroom_assignments", ["classroom_id"])
    op.create_table("tutor_classroom_exam_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("assignment_id", sa.String(36), sa.ForeignKey("tutor_classroom_assignments.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("answers", sa.JSON(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.UniqueConstraint("assignment_id", "student_id", name="uq_classroom_attempt"))
    op.create_index("ix_tutor_classroom_exam_attempts_assignment_id", "tutor_classroom_exam_attempts", ["assignment_id"])
    op.create_index("ix_tutor_classroom_exam_attempts_student_id", "tutor_classroom_exam_attempts", ["student_id"])
    op.create_table("tutor_external_books",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("metadata_record", sa.JSON(), nullable=False))
    op.create_index("ix_tutor_external_books_teacher_id", "tutor_external_books", ["teacher_id"])


def downgrade():
    for name in ("tutor_external_books", "tutor_classroom_exam_attempts", "tutor_classroom_assignments",
                 "tutor_classroom_enrollments", "tutor_classrooms"):
        op.drop_table(name)
