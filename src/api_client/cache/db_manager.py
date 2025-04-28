from sqlalchemy import create_engine

from api_client.cache.db_schema import metadata

class CacheManager:
    _instance = None

    def __new__(cls, db_url="sqlite:///cache.db"):
        """Returns a single instance of the CacheManager class."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine = create_engine(db_url)
            metadata.create_all(cls._instance._engine)
        return cls._instance

    def get_connection(self):
        """Returns a new database connection."""
        return self._engine.connect()