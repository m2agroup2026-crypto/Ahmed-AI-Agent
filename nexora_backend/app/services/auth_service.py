from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.security.password import verify_password
from app.security.jwt import create_access_token


def login_user(
    db: Session,
    email: str,
    password: str
):

    user = db.query(User).filter(
        User.email == email
    ).first()


    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


    if not verify_password(
        password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


    access_token = create_access_token(
        {
            "user_id": user.id,
            "email": user.email
        }
    )


    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
