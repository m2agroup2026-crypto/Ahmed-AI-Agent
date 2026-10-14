"""Isolated test bootstrap; refuse persistent databases before app imports."""

import os
import secrets

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Dialect


def require_isolated_database_url(url: str) -> None:
    if url not in {"sqlite://", "sqlite:///:memory:"}:
        raise pytest.UsageError(
            "Tests require disposable in-memory SQLite; persistent databases are forbidden."
        )


# Validate before importing the application's engine or any test module.
require_isolated_database_url(os.environ.get("DATABASE_URL", "sqlite://"))
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)


@event.listens_for(Dialect, "do_connect")
def refuse_persistent_test_connection(dialect, connection_record, args, kwargs):
    """Also block test-created engines before they open any existing database."""
    if dialect.name != "sqlite" or not args or args[0] != ":memory:":
        raise pytest.UsageError(
            "Test database connection blocked: only in-memory SQLite is permitted."
        )

from app.database.base import Base
from app.database.connection import SessionLocal, engine
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def bootstrap_isolated_database():
    """Seed legacy identity only in this process's disposable test database."""

    require_isolated_database_url(engine.url.render_as_string(hide_password=True))
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "SUPER_ADMIN").first()
        if role is None:
            role = Role(name="SUPER_ADMIN")
            db.add(role)
            db.flush()

        user = db.query(User).filter(User.id == 1).first()
        if user is None:
            user = User(
                id=1,
                name="Test Administrator",
                email="test-admin@example.com",
                password_hash="test",
                role_id=role.id,
            )
            db.add(user)
        elif user.role_id is None:
            user.role_id = role.id

        for permission_name in ("users.manage", "dashboard.manage"):
            permission = (
                db.query(Permission).filter(Permission.name == permission_name).first()
            )
            if permission is None:
                permission = Permission(name=permission_name)
                db.add(permission)
                db.flush()
            relation = (
                db.query(RolePermission)
                .filter(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
                .first()
            )
            if relation is None:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

        db.commit()
    finally:
        db.close()

    yield
