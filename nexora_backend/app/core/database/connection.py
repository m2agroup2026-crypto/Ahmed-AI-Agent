from .config import database_config


def get_database_url():

    return (
        "postgresql://"
        f"{database_config.USER}:"
        f"{database_config.PASSWORD}@"
        f"{database_config.HOST}:"
        f"{database_config.PORT}/"
        f"{database_config.NAME}"
    )
