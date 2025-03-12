from sqlalchemy import create_engine

from db_schema import metadata

class DatabaseManager:
    _instance = None

    def __new__(cls, db_url="sqlite:///crypto.db"):
        """Returns a single instance of the DatabaseManager class (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__engine = create_engine(db_url)
            metadata.create_all(cls._instance.__engine)
        return cls._instance

    def get_engine(self):
        """Returns the SQLAlchemy engine."""
        return self.__engine

    def get_connection(self):
        """Returns a new database connection."""
        return self.__engine.connect()