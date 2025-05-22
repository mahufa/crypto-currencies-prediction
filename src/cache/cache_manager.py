from datetime import datetime

from sqlalchemy import select, func

from cache.db_manager import get_connection
from cache.db_schema import metadata, historical_data, ohlc_data
from cache.parsers import parse_historical, parse_ohlc
from config import DEFAULT_DAYS
from project_utils import utc_from_cached_ts, days_for_free_api, days_since_dt


class CacheManager:
    def __init__(self,  coin_id: str, currency_symbol: str, table_name: str):
        self.table = metadata.tables.get(table_name)
        if self.table is None:
            raise ValueError(f"Table {table_name} does not exist in metadata.")

        self.coin_id = coin_id
        self.currency_symbol = currency_symbol

    def __enter__(self):
        self.conn = get_connection()
        self.trans = self.conn.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.trans.rollback()
        else:
            self.trans.commit()
        self.conn.close()

    def last_dt(self) -> datetime | None:
        q = (select(func.max(self.table.c.timestamp))
             .select_from(self.table)
             .where(self.table.c.coin_id == self.coin_id)
             .where(self.table.c.currency_symbol == self.currency_symbol))
        last_ts = self.conn.execute(q).scalar()
        return utc_from_cached_ts(last_ts) if last_ts else None

    def fetch_local(self) -> list[dict]:
        q = (select(*[col for col in self.table.c if col.name not in ['coin_id', 'currency_symbol']])
                 .select_from(self.table)
                 .where(self.table.c.coin_id == self.coin_id)
                 .where(self.table.c.currency_symbol == self.currency_symbol))

        q_result =  self.conn.execute(q)

        cols = q_result.keys()
        rows = q_result.fetchall()
        return [{col : val for col, val in zip(cols, row)} for row in rows]

    def normalize_data(self, raw_data: dict | list) -> list[dict]:
        if self.table is historical_data:
            return parse_historical(raw_data)
        elif self.table is ohlc_data:
            return parse_ohlc(raw_data)
        else:
            raise RuntimeError(f"No parser for table {self.table.name!r}")

    def upsert(self, normalized_data: dict | list):
        data_to_upsert = [{'coin_id': self.coin_id,
                           'currency_symbol': self.currency_symbol,
                           **row} for row in normalized_data]

        stmt = self.table.insert().prefix_with('OR REPLACE')
        self.conn.execute(stmt, data_to_upsert)

    def days_to_call(self, starting_dt: datetime | None) -> int:
        last_cached_dt = self.last_dt()

        if (starting_dt and last_cached_dt
                or not starting_dt and last_cached_dt):
            return (days_for_free_api(days_since_dt(last_cached_dt) if self.table== ohlc_data
                                      else days_since_dt(last_cached_dt)))
        elif starting_dt and not last_cached_dt:
            return (days_for_free_api(days_since_dt(starting_dt) if self.table == ohlc_data
                                      else days_since_dt(last_cached_dt)))
        else:
            return (days_for_free_api(DEFAULT_DAYS) if self.table == ohlc_data
                    else DEFAULT_DAYS)
