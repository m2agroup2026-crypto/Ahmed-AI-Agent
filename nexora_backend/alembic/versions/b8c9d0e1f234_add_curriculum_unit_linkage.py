"""Add optional curriculum units without relabeling existing lesson data.

Revision ID: b8c9d0e1f234
Revises: a6e7f8b9c210
"""

from alembic import op
import sqlalchemy as sa

revision = "b8c9d0e1f234"
down_revision = "a6e7f8b9c210"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tutor_curriculum_units",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("curriculum_version", sa.String(64), sa.ForeignKey("tutor_curriculum_versions.code"), nullable=False),
        sa.Column("subject_code", sa.String(32), nullable=False),
        sa.Column("title_ar", sa.String(255), nullable=False),
        sa.Column("title_en", sa.String(255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_tutor_curriculum_units_curriculum_version", "tutor_curriculum_units", ["curriculum_version"])
    with op.batch_alter_table("tutor_curriculum_lessons") as batch:
        batch.add_column(sa.Column("unit_id", sa.String(128), nullable=True))
        batch.add_column(sa.Column("position", sa.Integer(), nullable=False, server_default="0"))
        batch.create_foreign_key("fk_tutor_lesson_unit", "tutor_curriculum_units", ["unit_id"], ["id"])
        batch.create_index("ix_tutor_curriculum_lessons_unit_id", ["unit_id"])


def downgrade() -> None:
    with op.batch_alter_table("tutor_curriculum_lessons") as batch:
        batch.drop_index("ix_tutor_curriculum_lessons_unit_id")
        batch.drop_constraint("fk_tutor_lesson_unit", type_="foreignkey")
        batch.drop_column("unit_id")
        batch.drop_column("position")
    op.drop_index("ix_tutor_curriculum_units_curriculum_version", table_name="tutor_curriculum_units")
    op.drop_table("tutor_curriculum_units")
