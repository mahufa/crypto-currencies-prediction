from datetime import datetime
from typing import Any

import requests

from cache import CacheManager
from config import PRICE_PRECISION
from project_utils.time import days_to_call


def get(url: str, params: dict[str, any] = None) -> dict:
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()


def get_time_series(url: str,
                    coin_id: str,
                    currency_symbol: str,
                    starting_dt: datetime | None,
                    table_name: str) -> dict | Any | None:

    with (CacheManager(coin_id, currency_symbol, table_name) as cache):
        days = days_to_call(starting_dt,
                            cache.last_dt(),
                            is_ohlc = table_name=='ohlc_data')
        if days != 0:
            params = {"vs_currency": currency_symbol,
                      "precision": PRICE_PRECISION,
                      "days": days}

            raw_data = get(url, params)
            cache.upsert(raw_data)

        return cache.fetch_local()