import inspect

import pandas as pd

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from db_manager import DatabaseManager
from db_schema import metadata, timestamps
from quant_data_frame import QuantDataFrame


class QuantDataCache:
    """Caches quantitative data from an API into the database after checking the latest timestamp."""

    def __init__(self, table_name : str):
        self._table = metadata.tables.get(table_name)

        if self._table is None:
            raise ValueError(f"Table {table_name} does not exist in metadata.")
        if 'timestamp_id' not in self._table.c:
            raise ValueError(f"Column 'timestamp_id' does not exist in table {table_name}.")

        self._table_name = table_name

    def __call__(self, f):
        """Decorator that fetches, processes, and stores new data before returning it."""
        def wrapper(*args, **kwargs):
            sig = inspect.signature(f)
            bound_args = sig.bind_partial(*args, **kwargs)
            bound_args.apply_defaults()

            coin_id = bound_args.arguments.get('coin_id')
            if coin_id is None:
                raise ValueError("'coin_id' must be provided.")
            currency_symbol = bound_args.arguments.get('currency_symbol')

            with DatabaseManager().get_connection() as con:
                local_data = self.get_local(con, coin_id, currency_symbol)

                if not local_data.empty:
                    kwargs['starting_timestamp'] = local_data['timestamp'].max()

                new_data = f(*args, **kwargs)
                if new_data.empty:
                    return local_data

                try:
                    self.to_ts_table(con, new_data)
                    ts_with_ids = self.get_ts_ids(con, new_data)
                    self.to_quant_data_table(con, new_data, ts_with_ids)
                    con.commit()

                except SQLAlchemyError as e:
                    con.rollback()
                    raise SQLAlchemyError(f"Failed to insert new data into {self._table_name}: {e}.")

                return pd.concat([local_data, new_data])

        return wrapper

    def get_local(self, connection, coin_id: str, currency_symbol: str):
        joined = timestamps.join(self._table, timestamps.c.id == self._table.c.timestamp_id)
        query = (select(timestamps.c.timestamp, *[col for col in self._table.c if col.name != 'timestamp_id'])
                 .select_from(joined)
                 .where(timestamps.c.coin_id == coin_id)
                 .where(timestamps.c.currency_symbol == currency_symbol))

        return QuantDataFrame(connection.execute(query).fetchall(), coin_id, currency_symbol)

    def to_ts_table(self, connection, new_data: QuantDataFrame):
        """Inserts data into timestamps table."""
        coin_id = new_data.get_coin_id()
        currency_symbol = new_data.get_currency_symbol()

        query = (select(timestamps.c.timestamp).
                 where(timestamps.c.coin_id == coin_id).
                 where(timestamps.c.currency_symbol == currency_symbol).
                 where(timestamps.c.timestamp >= new_data['timestamp'].min()))

        locally_stored_ts = pd.Series([row[0] for row in connection.execute(query).fetchall()])

        df_to_insert = new_data.loc[~new_data['timestamp'].isin(locally_stored_ts), ['timestamp']].copy()
        df_to_insert['coin_id'] = coin_id
        df_to_insert['currency_symbol'] = currency_symbol

        df_to_insert.to_sql('timestamps', connection, if_exists='append', index=False)

    @staticmethod
    def get_ts_ids(connection, new_data: QuantDataFrame):
        """Fetches filtered timestamps and their corresponding IDs as a DataFrame."""
        coin_id = new_data.get_coin_id()
        currency_symbol = new_data.get_currency_symbol()

        query = (select(timestamps.c.id, timestamps.c.timestamp).
                 where(timestamps.c.coin_id == coin_id).
                 where(timestamps.c.currency_symbol == currency_symbol).
                 where(timestamps.c.timestamp.in_(new_data['timestamp'].tolist())))

        return QuantDataFrame(connection.execute(query).fetchall(), coin_id, currency_symbol)

    def to_quant_data_table(self, connection, new_data: QuantDataFrame, ts_with_ids: QuantDataFrame):
        """Merges new data with ids from the timestamp table and inserts into the appropriate table."""
        df_to_insert = new_data.merge(ts_with_ids, on='timestamp', how='left').copy()
        df_to_insert.drop(columns=['timestamp'], inplace=True)
        df_to_insert.rename(columns={'id': 'timestamp_id'}, inplace=True)


        df_to_insert.to_sql(self._table_name, con=connection, if_exists='append',
                                  index=False, method='multi', chunksize=1000)