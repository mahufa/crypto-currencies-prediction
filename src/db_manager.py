from sqlalchemy import (Table, Column, Integer, Float, String, ForeignKey, UniqueConstraint, MetaData,create_engine)

metadata = MetaData()

# tables
coins = Table('coin', metadata,
                Column('id', String(50), primary_key=True),
                Column('symbol', String(10), unique=True),
                Column('name', String(50), unique=True))

currencies = Table('currency', metadata,
                Column('symbol', String(5), primary_key=True))

timestamps = Table('timestamp', metadata,
                Column('id', Integer, primary_key=True, autoincrement=True),
                Column('coin_id', String(50), ForeignKey('coin.id')),
                Column('currency_symbol', String(5), ForeignKey('currency.symbol')),
                Column('timestamp', Integer),
                UniqueConstraint('coin_id', 'currency_symbol', 'timestamp', name='uq_timestamp_entry'))

ohlc_data = Table('ohlc_data', metadata,
                Column('id', Integer,ForeignKey('timestamp.id'), primary_key=True),
                Column('open', Float),
                Column('high', Float),
                Column('low', Float),
                Column('close', Float))

historical_data = Table('historical_data', metadata,
                Column('id', Integer, ForeignKey('timestamp.id'), primary_key=True),
                Column('total_volume', Integer),
                Column('market_cap', Integer),
                Column('price', Float))

class DatabaseManager:
    def __init__(self, db_url="sqlite:///crypto.db"):
        self.engine = create_engine(db_url)
        metadata.create_all(self.engine)

    def get_engine(self):
        return self.engine

    def get_connection(self):
        return self.engine.connect()