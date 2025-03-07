from sqlalchemy import (Table, Column, Integer, Float, String, ForeignKey, UniqueConstraint, MetaData,create_engine)

_metadata = MetaData()

# tables
coins = Table('coin', _metadata,
              Column('id', String(50), primary_key=True),
              Column('symbol', String(10), unique=True),
              Column('name', String(50), unique=True))

currencies = Table('currency', _metadata,
                   Column('symbol', String(5), primary_key=True))

timestamps = Table('timestamp', _metadata,
                   Column('id', Integer, primary_key=True, autoincrement=True),
                   Column('coin_id', String(50), ForeignKey('coin.id')),
                   Column('currency_symbol', String(5), ForeignKey('currency.symbol')),
                   Column('timestamp', Integer),
                   UniqueConstraint('coin_id', 'currency_symbol', 'timestamp', name='uq_timestamp_entry'))

ohlc_data = Table('ohlc_data', _metadata,
                  Column('id', Integer,ForeignKey('timestamp.id'), primary_key=True),
                  Column('open', Float),
                  Column('high', Float),
                  Column('low', Float),
                  Column('close', Float))

historical_data = Table('historical_data', _metadata,
                        Column('id', Integer, ForeignKey('timestamp.id'), primary_key=True),
                        Column('total_volume', Integer),
                        Column('market_cap', Integer),
                        Column('price', Float))

class DatabaseManager:
    _instance = None

    def __new__(cls, db_url="sqlite:///crypto.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.engine = create_engine(db_url)
            _metadata.create_all(cls._instance.engine)
        return cls._instance

    def get_engine(self):
        return self.engine

    def get_connection(self):
        return self.engine.connect()
