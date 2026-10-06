import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./nexora.db",
)


engine_kwargs = {
    "pool_pre_ping": True,
}


# SQLite configuration for local development.
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
    }

# PostgreSQL configuration.
# Azure Database for PostgreSQL requires secure TLS/SSL connections.
elif DATABASE_URL.startswith("postgresql"):
    engine_kwargs["connect_args"] = {
        "sslmode": "require",
    }


engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
