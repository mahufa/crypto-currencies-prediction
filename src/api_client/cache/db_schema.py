from sqlalchemy import Table, Column, Integer, Float, String, ForeignKey, UniqueConstraint, MetaData

metadata = MetaData()

# tables
coins = Table('coins', metadata,
              Column('id', String(50), primary_key=True),
              Column('symbol', String(10), unique=True),
              Column('name', String(50), unique=True))

currencies = Table('currencies', metadata,
                   Column('symbol', String(5), primary_key=True))

timestamps = Table('timestamps', metadata,
                   Column('id', Integer, primary_key=True, autoincrement=True),
                   Column('coin_id', String(50), ForeignKey('coins.id')),
                   Column('currency_symbol', String(5), ForeignKey('currencies.symbol')),
                   Column('timestamp', Integer),
                   UniqueConstraint('coin_id', 'currency_symbol', 'timestamp', name='uq_timestamp_entry'))

ohlc_data = Table('ohlc_data', metadata,
                  Column('timestamp_id', Integer, ForeignKey('timestamps.id'), primary_key=True),
                  Column('open', Float),
                  Column('high', Float),
                  Column('low', Float),
                  Column('close', Float))

historical_data = Table('historical_data', metadata,
                        Column('timestamp_id', Integer, ForeignKey('timestamps.id'), primary_key=True),
                        Column('total_volume', Integer),
                        Column('market_cap', Integer),
                        Column('price', Float))

staging = Table('staging', metadata,
                Column('timestamp', Integer, primary_key=True),
                Column('open', Float, nullable=True),
                Column('high', Float, nullable=True),
                Column('low', Float, nullable=True),
                Column('close', Float, nullable=True),
                Column('total_volume', Integer, nullable=True),
                Column('market_cap', Integer, nullable=True),
                Column('price', Float, nullable=True))