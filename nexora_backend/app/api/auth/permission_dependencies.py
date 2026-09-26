from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.api.auth.dependencies import get_current_user
from app.models.user import User
from app.services.permission_service import has_permission


def require_permission(permission_name: str):

    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):

        allowed = has_permission(
            db,
            current_user.id,
            permission_name,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return True

    return permission_checker
