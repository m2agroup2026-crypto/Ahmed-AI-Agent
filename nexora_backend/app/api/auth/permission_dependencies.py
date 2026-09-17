from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.api.auth.dependencies import get_current_user_id
from app.services.permission_service import has_permission


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_permission(permission_name: str):

    def permission_checker(
        user_id: int = Depends(get_current_user_id),
        db: Session = Depends(get_db)
    ):

        allowed = has_permission(
            db,
            user_id,
            permission_name
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )

        return True

    return permission_checker
