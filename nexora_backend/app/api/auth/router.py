from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.user_service import create_user
from app.services.auth_service import login_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.get("/health")
def auth_health():

    return {
        "service": "NEXORA Authentication",
        "status": "ready"
    }


@router.post("/register", response_model=UserResponse)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):

    return create_user(
        db,
        user_data
    )


@router.post("/login", response_model=TokenResponse)
def login(
    user_data: LoginRequest,
    db: Session = Depends(get_db)
):

    return login_user(
        db,
        user_data.email,
        user_data.password
    )


from app.api.auth.dependencies import get_current_user_id
from app.services.current_user_service import get_user_by_id


@router.get("/me")
def current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    user = get_user_by_id(
        db,
        user_id
    )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_active": user.is_active
    }


from app.api.auth.permission_dependencies import require_permission


@router.get("/admin-test")
def admin_test(
    allowed: bool = Depends(
        require_permission("dashboard.manage")
    )
):

    return {
        "message": "NEXORA protected endpoint",
        "permission": "dashboard.manage",
        "access": "granted"
    }
