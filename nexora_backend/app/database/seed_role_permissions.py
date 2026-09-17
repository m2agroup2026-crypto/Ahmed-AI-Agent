from app.database.connection import SessionLocal

from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission


def seed_role_permissions():

    db = SessionLocal()

    try:
        role = db.query(Role).filter(
            Role.name == "SUPER_ADMIN"
        ).first()

        if not role:
            raise Exception("SUPER_ADMIN role not found")

        permissions = db.query(Permission).all()

        for permission in permissions:

            exists = db.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id
            ).first()

            if not exists:
                db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id
                    )
                )

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_role_permissions()
