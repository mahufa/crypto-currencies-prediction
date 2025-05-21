from sqlalchemy import create_engine, Engine, Connection

from .db_schema import metadata

_engine: Engine | None = None


def get_engine(db_url="sqlite:///cache.db") -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(db_url)
        metadata.create_all(_engine)
    return _engine


def get_connection() -> Connection:
    return get_engine().connect()
