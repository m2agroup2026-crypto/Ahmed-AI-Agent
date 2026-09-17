import os


class Settings:

    PROJECT_NAME = "NEXORA AI"

    VERSION = "0.1.0"

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./nexora.db"
    )

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "NEXORA_DEVELOPMENT_SECRET"
    )

    ALGORITHM = "HS256"


settings = Settings()
