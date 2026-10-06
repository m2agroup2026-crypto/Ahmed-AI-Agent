"""add source-aware tutor curriculum content

Revision ID: 9f4a2c7d1e10
Revises: 700d90f036fa
Create Date: 2026-09-26 20:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f4a2c7d1e10"
down_revision: Union[str, Sequence[str], None] = "700d90f036fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tutor_curriculum_sources",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name_ar", sa.String(length=255), nullable=False),
        sa.Column("name_en", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=False),
        sa.Column("license_status", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tutor_curriculum_versions",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("title_ar", sa.String(length=255), nullable=False),
        sa.Column("title_en", sa.String(length=255), nullable=False),
        sa.Column("stage", sa.String(length=64), nullable=False),
        sa.Column("grade_level", sa.String(length=64), nullable=False),
        sa.Column("academic_year", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["tutor_curriculum_sources.id"]),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_index(
        "ix_tutor_curriculum_versions_source_id",
        "tutor_curriculum_versions",
        ["source_id"],
    )
    op.create_table(
        "tutor_curriculum_skills",
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("curriculum_version", sa.String(length=64), nullable=False),
        sa.Column("subject_code", sa.String(length=32), nullable=False),
        sa.Column("title_ar", sa.String(length=255), nullable=False),
        sa.Column("title_en", sa.String(length=255), nullable=False),
        sa.Column("description_ar", sa.Text(), nullable=False),
        sa.Column("description_en", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["curriculum_version"], ["tutor_curriculum_versions.code"]
        ),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_index(
        "ix_tutor_curriculum_skills_curriculum_version",
        "tutor_curriculum_skills",
        ["curriculum_version"],
    )
    op.create_table(
        "tutor_curriculum_lessons",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("curriculum_version", sa.String(length=64), nullable=False),
        sa.Column("subject_code", sa.String(length=32), nullable=False),
        sa.Column("title_ar", sa.String(length=255), nullable=False),
        sa.Column("title_en", sa.String(length=255), nullable=False),
        sa.Column("summary_ar", sa.Text(), nullable=False),
        sa.Column("summary_en", sa.Text(), nullable=False),
        sa.Column("content_ar", sa.Text(), nullable=False),
        sa.Column("content_en", sa.Text(), nullable=False),
        sa.Column("skill_codes", sa.JSON(), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=False),
        sa.Column("source_locator", sa.String(length=255), nullable=False),
        sa.Column("source_checksum", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["curriculum_version"], ["tutor_curriculum_versions.code"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tutor_curriculum_lessons_curriculum_version",
        "tutor_curriculum_lessons",
        ["curriculum_version"],
    )
    op.create_index(
        "ix_tutor_curriculum_lessons_subject_code",
        "tutor_curriculum_lessons",
        ["subject_code"],
    )
    op.create_table(
        "tutor_curriculum_content_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.String(length=128), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("content_ar", sa.Text(), nullable=False),
        sa.Column("content_en", sa.Text(), nullable=False),
        sa.Column("source_locator", sa.String(length=255), nullable=False),
        sa.Column("content_checksum", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["tutor_curriculum_lessons.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("lesson_id", "ordinal", name="uq_tutor_lesson_chunk"),
    )
    op.create_index(
        "ix_tutor_curriculum_content_chunks_id",
        "tutor_curriculum_content_chunks",
        ["id"],
    )
    op.create_index(
        "ix_tutor_curriculum_content_chunks_lesson_id",
        "tutor_curriculum_content_chunks",
        ["lesson_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tutor_curriculum_content_chunks_lesson_id",
        table_name="tutor_curriculum_content_chunks",
    )
    op.drop_index(
        "ix_tutor_curriculum_content_chunks_id",
        table_name="tutor_curriculum_content_chunks",
    )
    op.drop_table("tutor_curriculum_content_chunks")
    op.drop_index(
        "ix_tutor_curriculum_lessons_subject_code",
        table_name="tutor_curriculum_lessons",
    )
    op.drop_index(
        "ix_tutor_curriculum_lessons_curriculum_version",
        table_name="tutor_curriculum_lessons",
    )
    op.drop_table("tutor_curriculum_lessons")
    op.drop_index(
        "ix_tutor_curriculum_skills_curriculum_version",
        table_name="tutor_curriculum_skills",
    )
    op.drop_table("tutor_curriculum_skills")
    op.drop_index(
        "ix_tutor_curriculum_versions_source_id",
        table_name="tutor_curriculum_versions",
    )
    op.drop_table("tutor_curriculum_versions")
    op.drop_table("tutor_curriculum_sources")
