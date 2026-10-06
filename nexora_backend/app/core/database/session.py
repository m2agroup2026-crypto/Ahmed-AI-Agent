from .connection import get_database_url


class DatabaseSessionManager:


    def __init__(self):

        self.database_url = (
            get_database_url()
        )


    def info(self):

        return {
            "database": "nexora_core_dev",
            "engine": "postgresql",
            "url_configured": bool(
                self.database_url
            ),
        }


database_session = DatabaseSessionManager()
