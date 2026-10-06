import os


class DatabaseConfig:

    HOST = os.getenv(
        "NEXORA_DB_HOST",
        "nexora-tutor-db-dev.postgres.database.azure.com",
    )

    NAME = os.getenv(
        "NEXORA_DB_NAME",
        "nexora_core_dev",
    )

    USER = os.getenv(
        "NEXORA_DB_USER",
        "nexoraadmin",
    )

    PASSWORD = os.getenv(
        "NEXORA_DB_PASSWORD",
        "",
    )

    PORT = os.getenv(
        "NEXORA_DB_PORT",
        "5432",
    )


database_config = DatabaseConfig()
