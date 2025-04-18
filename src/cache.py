import inspect
from datetime import datetime, timedelta

import pandas as pd

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db_manager import DatabaseManager
from db_schema import metadata, timestamps, staging
from frames import make_time_series_frame


class DataCache:
    """Caches quantitative data from an API into the database after checking the latest timestamp.

    Skips API call if the latest timestamp is more than 5 minutes old."""

    def __init__(self, table_name : str):
        self._table = metadata.tables.get(table_name)

        if self._table is None:
            raise ValueError(f"Table {table_name} does not exist in metadata.")
        if 'timestamp_id' not in self._table.c:
            raise ValueError(f"Column 'timestamp_id' does not exist in table {table_name}.")

        self._table_name = table_name
        self._last_call_ts = None

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
                    self._last_call_ts = self._last_call_ts or local_data.timestamp.max()

                    if self._last_call_ts > (datetime.now() - timedelta(minutes=5)).timestamp():
                        return local_data

                    kwargs['starting_timestamp'] = self._last_call_ts

                new_data = f(*args, **kwargs)
                if new_data.empty:
                    return local_data

                try:
                    self.to_ts_table(con, new_data)
                    self.to_time_series_table(con, new_data)
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

        result = connection.execute(query)

        col_names = result.keys()
        columns =  zip(*result.fetchall())

        loc  = {col_name: column for col_name, column in zip(col_names, columns)}

        return make_time_series_frame(loc, coin_id, currency_symbol)

    @staticmethod
    def to_ts_table(connection, new_data: pd.DataFrame):
        """Inserts data into the timestamps table."""
        coin_id = new_data.attrs['coin_id']
        currency_symbol = new_data.attrs['currency_symbol']

        df_to_insert = pd.DataFrame()
        df_to_insert['timestamp'] = new_data.timestamp
        df_to_insert['coin_id'] = coin_id
        df_to_insert['currency_symbol'] = currency_symbol
        stmt = timestamps.insert().prefix_with('OR IGNORE')

        connection.execute(stmt, df_to_insert.to_dict(orient='records'))

    def to_time_series_table(self, connection, new_data: pd.DataFrame):
        """Merges new data with ids from the timestamp table and inserts into the appropriate table."""
        stmt = staging.insert().prefix_with('OR REPLACE')
        connection.execute(stmt, new_data.to_dict(orient='records'))

        sel_to_insert = (select(timestamps.c.id,
                                *[col for col in staging.c if col.name in map(lambda c: c.name, self._table.c)]).
                         select_from(timestamps.join(staging, timestamps.c.timestamp == staging.c.timestamp)))

        stmt = (self._table.insert().prefix_with('OR REPLACE').
                from_select(names=[col for col in self._table.c], select=sel_to_insert))

        connection.execute(stmt)
        connection.execute(staging.delete())