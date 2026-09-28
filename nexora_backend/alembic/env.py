import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.database.config import database_config

from app.database.base import Base
from app.models import User, Role, Permission, RolePermission
from app.billing.models import (
    Plan,
    Subscription,
    CreditTransaction,
    UsageRecord,
    Wallet,
)
from app.products.tutor import (
    AssessmentAttempt,
    CurriculumContentChunk,
    CurriculumLesson,
    CurriculumQuestion,
    CurriculumSkill,
    CurriculumSource,
    CurriculumVersion,
    LearnerProfile,
    LearningMessage,
    LearningSession,
)


# Alembic Config object.
config = context.config

NEXORA_DATABASE_URL = (
    f"postgresql://{database_config.USER}:"
    f"{database_config.PASSWORD}@"
    f"{database_config.HOST}:"
    f"{database_config.PORT}/"
    f"{database_config.NAME}"
)

config.set_main_option(
    "sqlalchemy.url",
    NEXORA_DATABASE_URL,
)


# Configure Python logging from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Use Azure/PostgreSQL DATABASE_URL when available.
# Fall back to the URL configured in alembic.ini for local development.
database_url = os.getenv("DATABASE_URL")

if database_url:
    config.set_main_option(
        "sqlalchemy.url",
        database_url.replace("%", "%%"),
    )


# SQLAlchemy metadata used by Alembic migrations.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
