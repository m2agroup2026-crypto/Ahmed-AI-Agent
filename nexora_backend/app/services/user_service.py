from sqlalchemy.orm import Session

from app.models.user import User
from app.security.password import hash_password
from app.schemas.user import UserCreate


def create_user(
    db: Session,
    user_data: UserCreate
):

    hashed_password = hash_password(
        user_data.password
    )

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
