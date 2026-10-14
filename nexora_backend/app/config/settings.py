import os
import hashlib


# Fingerprint only: never retain or retrieve the retired signing material.
_UNSAFE_KEY_DIGEST = "8db952e9b838962bdaf54d40c1ced85f90e0bdb9717e002fde656e9a312c9de7"


def _validate_signing_key(key: str | None) -> str:
    error = (
        "SECRET_KEY must be explicitly supplied as a strong signing key "
        "(at least 32 characters and 16 distinct characters, without whitespace)."
    )
    if not isinstance(key, str) or not key or not key.strip():
        raise RuntimeError(error)
    if hashlib.sha256(key.strip().encode()).hexdigest() == _UNSAFE_KEY_DIGEST:
        raise RuntimeError(error)
    if len(key) < 32 or len(set(key)) < 16 or any(char.isspace() for char in key):
        raise RuntimeError(error)
    return key



class Settings:

    PROJECT_NAME = "AQLITH AI"

    VERSION = "0.1.0"

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./nexora.db"
    )

    def __init__(self):
        self.SECRET_KEY = _validate_signing_key(os.getenv("SECRET_KEY"))

    ALGORITHM = "HS256"

    AZURE_FOUNDRY_ENDPOINT = os.getenv(
        "AZURE_FOUNDRY_ENDPOINT",
        "https://nexora-foundry-dev.services.ai.azure.com/openai/v1"
    )

    AZURE_FOUNDRY_DEPLOYMENT = os.getenv(
        "AZURE_FOUNDRY_DEPLOYMENT",
        "gpt-5-mini"
    )


settings = Settings()
