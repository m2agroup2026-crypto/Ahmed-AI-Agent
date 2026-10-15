from datetime import datetime, UTC, timedelta
import logging
from math import isfinite

from jose import JWTError, jwt

from app.config.settings import settings


ACCESS_TOKEN_EXPIRE_MINUTES = 60
logger = logging.getLogger(__name__)


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
            options={
                "require_exp": True,
                "verify_exp": True,
                "verify_signature": True,
            },
        )

        # NumericDate must be a number, not a boolean or a numeric string.
        expires_at = payload.get("exp")
        if (
            isinstance(expires_at, bool)
            or not isinstance(expires_at, (int, float))
            or (isinstance(expires_at, float) and not isfinite(expires_at))
        ):
            return None

        return payload

    except JWTError:
        logger.warning("JWT validation failed")
        return None

    except Exception:
        logger.error("JWT validation failed unexpectedly")
        return None
