from app.database.connection import SessionLocal
from app.models.permission import Permission


PERMISSIONS = [
    "users.manage",
    "roles.manage",
    "permissions.manage",
    "dashboard.manage",
    "ai.manage",
]


def seed_permissions():

    db = SessionLocal()

    try:
        for permission_name in PERMISSIONS:

            exists = db.query(Permission).filter(
                Permission.name == permission_name
            ).first()

            if not exists:
                db.add(
                    Permission(
                        name=permission_name
                    )
                )

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_permissions()
