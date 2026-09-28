from datetime import datetime, UTC, timedelta

from jose import JWTError, jwt

from app.config.settings import settings


ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.
    """

    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {
            "exp": expire,
        }
    )

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def verify_token(token: str) -> dict | None:
    """
    Decode and validate a JWT access token.

    Returns the decoded payload when the token is valid.
    Returns None when validation fails.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload

    except JWTError as exc:
        print(
            f"NEXORA JWT validation error: "
            f"{exc.__class__.__name__}: {exc}"
        )
        return None

    except Exception as exc:
        print(
            f"NEXORA JWT unexpected error: "
            f"{exc.__class__.__name__}: {exc}"
        )
        return None
