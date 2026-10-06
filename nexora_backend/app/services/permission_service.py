from sqlalchemy.orm import Session

from app.models.user import User
from app.models.permission import Permission


def has_permission(
    db: Session,
    user_id: int,
    permission_name: str,
) -> bool:

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        return False

    if not user.is_active:
        return False

    if not user.role_id:
        return False

    permission = (
        db.query(Permission)
        .join(Permission.role_permissions)
        .filter(Permission.name == permission_name)
        .first()
    )

    if not permission:
        return False

    return any(
        role_permission.role_id == user.role_id
        for role_permission in permission.role_permissions
    )
