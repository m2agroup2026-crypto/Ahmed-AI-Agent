import os


class Settings:

    PROJECT_NAME = "AQLITH AI"

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

    AZURE_FOUNDRY_ENDPOINT = os.getenv(
        "AZURE_FOUNDRY_ENDPOINT",
        "https://nexora-foundry-dev.services.ai.azure.com/openai/v1"
    )

    AZURE_FOUNDRY_DEPLOYMENT = os.getenv(
        "AZURE_FOUNDRY_DEPLOYMENT",
        "gpt-5-mini"
    )


settings = Settings()
