"""Declare curriculum, unit and lesson content languages without guessing legacy data.

Revision ID: c9d0e1f234a5
Revises: b8c9d0e1f234
"""

from alembic import op
import sqlalchemy as sa

revision = "c9d0e1f234a5"
down_revision = "b8c9d0e1f234"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tutor_curriculum_versions") as batch:
        batch.add_column(sa.Column("content_language", sa.String(16), nullable=True))
    with op.batch_alter_table("tutor_curriculum_units") as batch:
        batch.add_column(sa.Column("content_language", sa.String(16), nullable=True))
    with op.batch_alter_table("tutor_curriculum_lessons") as batch:
        batch.add_column(sa.Column("content_language", sa.String(16), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tutor_curriculum_units") as batch:
        batch.drop_column("content_language")
    with op.batch_alter_table("tutor_curriculum_lessons") as batch:
        batch.drop_column("content_language")
    with op.batch_alter_table("tutor_curriculum_versions") as batch:
        batch.drop_column("content_language")
