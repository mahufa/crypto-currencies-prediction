from datetime import datetime

import pandas as pd

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from db_manager import DatabaseManager
from db_schema import metadata, timestamps


class QuantDataCache:
    """Caches quantitative data from an API into the database after checking the latest timestamp."""
    __last_timestamps: dict = {}

    def __init__(self, table_name : str):
        self.__table_name = table_name

    def __call__(self, f):
        """Decorator that fetches, processes, and stores new data before returning it."""
        def wrapper(*args, **kwargs):
            coin_id = kwargs.get('coin_id')
            currency_symbol = kwargs.get('currency_symbol')
            if coin_id is None or currency_symbol is None:
                raise ValueError("Both 'coin_id' and 'currency_symbol' must be provided.")

            with DatabaseManager().get_connection() as con:

                if self.__last_timestamps.get(self.__table_name) is None:
                    self.__last_timestamps[self.__table_name] = self.last_timestamp(con)

                days = self.days_to_query(self.__last_timestamps[self.__table_name])

                new_data = f(*args, **kwargs, days=days)

                self.insert_data(con, api_data=new_data, coin_id=coin_id, currency_symbol=currency_symbol)

                return pd.read_sql(self.__table_name, con)

        return wrapper

    def last_timestamp(self, connection):
        """Returns the latest timestamp in the specified table.

        If no timestamp is found, returns None.
        Raises a ValueError if the table does not exist in the metadata or if it lacks a 'timestamp_id' column.
        """
        table = metadata.tables.get(self.__table_name)

        if table is None:
            raise ValueError(f"Table {self.__table_name} does not exist in metadata.")

        if 'timestamp_id' not in table.c:
            raise ValueError(f"Column 'timestamp_id' does not exist in table {self.__table_name}.")

        joined = timestamps.join(table, timestamps.c.id == table.c.timestamp_id)
        query = select(func.max(timestamps.c.timestamp)).select_from(joined)

        return connection.execute(query).scalar()

    @staticmethod
    def days_to_query(last_timestamp):
        """Returns the number of days since the last recorded timestamp.

        If no timestamp is found, defaults to 365 days.
        """
        if last_timestamp is None:
            return 365

        date = datetime.fromtimestamp(last_timestamp).date()
        return (datetime.now().date() - date).days

    @staticmethod
    def create_timestamp_input_df(timestamps_col: pd.Series, *, coin_id: str, currency_symbol: str):
        """Creates a DataFrame formatted for insertion into the 'timestamps' table."""
        res_df = pd.DataFrame()
        res_df['timestamp'] = timestamps_col
        res_df['coin_id'] = coin_id
        res_df['currency_symbol'] = currency_symbol
        return res_df

    @staticmethod
    def timestamps_with_ids(connection, *, coin_id: str, currency_symbol: str, row_num: int):
        """Fetches the latest timestamps and their corresponding IDs as a DataFrame."""
        query = select([timestamps.c.id, timestamps.c.timestamp]). \
            where(timestamps.c.coin_id == coin_id). \
            where(timestamps.c.currency_symbol == currency_symbol). \
            order_by(timestamps.c.timestamp.desc()). \
            limit(row_num)

        return pd.DataFrame(connection.execute(query).fetchall(), columns=['timestamp_id', 'timestamp'])

    @staticmethod
    def merge_timestamp_ids_into_data(*, api_data: pd.DataFrame, timestamps_with_ids: pd.DataFrame):
        """Merges API data with timestamp IDs for insertion into the appropriate table."""
        res = api_data.merge(timestamps_with_ids, on='timestamp', how='left')
        res.drop(columns=['timestamp'], inplace=True)
        return res

    def insert_data(self, connection, *, api_data: pd.DataFrame, coin_id: str, currency_symbol: str):
        """Inserts data into the appropriate table.

        If an error occurs, performs a rollback and raises an SQLAlchemyError.
        """
        ts_input = self.create_timestamp_input_df(api_data['timestamp'],
                                                  coin_id=coin_id, currency_symbol=currency_symbol, )

        try:
            ts_input.to_sql("timestamps", con=connection, if_exists='append',
                            index=False, method='multi', chunksize=1000)

            ts_with_ids = self.timestamps_with_ids(connection, coin_id=coin_id,
                                                   currency_symbol=currency_symbol, row_num=len(ts_input))

            prepared_input = self.merge_timestamp_ids_into_data(api_data=api_data, timestamps_with_ids=ts_with_ids)
            prepared_input.to_sql(self.__table_name, con=connection, if_exists='append',
                                  index=False, method='multi', chunksize=1000)

            connection.commit()

        except SQLAlchemyError as e:
            connection.rollback()
            raise SQLAlchemyError(f"Connection error when inserting data into table {self.__table_name}: {e}")