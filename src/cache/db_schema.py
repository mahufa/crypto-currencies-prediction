from sqlalchemy import Table, Column, Integer, Float, String, MetaData

metadata = MetaData()

historical_data = Table('historical_data', metadata,
                        Column('coin_id', String(50), primary_key=True),
                        Column('currency_symbol', String(5), primary_key=True),
                        Column('timestamp', Integer, primary_key=True),
                        Column('total_volume', Integer),
                        Column('market_cap', Integer),
                        Column('price', Float))

ohlc_data = Table('ohlc_data', metadata,
                  Column('coin_id', String(50), primary_key=True),
                  Column('currency_symbol', String(5), primary_key=True),
                  Column('timestamp', Integer, primary_key=True),
                  Column('open', Float),
                  Column('high', Float),
                  Column('low', Float),
                  Column('close', Float))

last_timestamps = Table('last_timestamps', metadata,
                        Column('table_name', String(30), primary_key=True),
                        Column('coin_id', String(50), primary_key=True),
                        Column('currency_symbol', String(5), primary_key=True),
                        Column('timestamp', Integer))