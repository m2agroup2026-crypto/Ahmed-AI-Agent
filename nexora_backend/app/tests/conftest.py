"""Shared test database bootstrap for legacy and product API tests."""

import pytest

from app.database.base import Base
from app.database.connection import SessionLocal, engine
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def bootstrap_default_database():
    """Provide the minimal seeded identity expected by legacy AI tests."""

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
