import inspect
from datetime import datetime, timedelta

import pandas as pd

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db_manager import DatabaseManager
from db_schema import metadata, timestamps, staging
from frames import make_time_series_frame


def _n_min_ago_timestamp(n: int) -> float:
    """Returns the timestamp of the moment that was n minutes ago in the format used in API calls."""
    return (datetime.now() - timedelta(minutes=n)).timestamp() * 1000


class DataCache:
    """Caches quantitative data from an API into the database after checking the latest timestamp.

    Skips API call if the latest timestamp is more than DEF_MIN minutes old."""

    def __init__(self, table_name: str, min_interval: int):
        self._table = metadata.tables.get(table_name)

        if self._table is None:
            raise ValueError(f"Table {table_name} does not exist in metadata.")
        if 'timestamp_id' not in self._table.c:
            raise ValueError(f"Column 'timestamp_id' does not exist in table {table_name}.")

        self._table_name = table_name
        self._min_interval = min_interval
        self._last_called_ts: int | None = None

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            coin_id, currency_symbol = self._default_or_custom_coin_and_curr(f, *args, **kwargs)

            with DatabaseManager().get_connection() as con:
                local_data = self.get_local(con, coin_id, currency_symbol)

                if not local_data.empty:
                    self._last_called_ts = self._last_called_ts or local_data.timestamp.max()

                    if self._last_called_ts > _n_min_ago_timestamp(n=self._min_interval):
                        return local_data

                    kwargs['starting_timestamp'] = self._last_called_ts

                new_data = f(*args, **kwargs)
                if new_data.empty:
                    return local_data

                self.to_db(con, new_data)

                return pd.concat([local_data, new_data])

        return wrapper

    @staticmethod
    def _default_or_custom_coin_and_curr(f, *args, **kwargs) -> tuple[str, str]:
        """Inspects the decorated function signature to get actual coin_id and currency_symbol."""
        sig = inspect.signature(f)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()

        coin_id = bound_args.arguments.get('coin_id')
        if coin_id is None:
            raise ValueError("'coin_id' must be provided.")

        currency_symbol = bound_args.arguments.get('currency_symbol')
        if currency_symbol is None:
            raise ValueError("'currency_symbol' must be provided.")

        return coin_id, currency_symbol

    def get_local(self, connection, coin_id: str, currency_symbol: str) -> pd.DataFrame:
        joined = timestamps.join(self._table, timestamps.c.id == self._table.c.timestamp_id)
        query = (select(timestamps.c.timestamp, *[col for col in self._table.c if col.name != 'timestamp_id'])
                 .select_from(joined)
                 .where(timestamps.c.coin_id == coin_id)
                 .where(timestamps.c.currency_symbol == currency_symbol))

        result = connection.execute(query)

        col_names = result.keys()
        columns = zip(*result.fetchall())

        loc = {col_name: column for col_name, column in zip(col_names, columns)}

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

    def to_db(self, connection, new_data: pd.DataFrame):
        try:
            self.to_ts_table(connection, new_data)
            self.to_time_series_table(connection, new_data)
            connection.commit()

        except SQLAlchemyError as e:
            connection.rollback()
            raise RuntimeError(f"Failed to insert new data into {self._table_name}.") from e
