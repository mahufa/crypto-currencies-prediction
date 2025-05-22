from datetime import datetime
from typing import Any

import requests

from cache import CacheManager
from config import DEFAULT_DAYS, PRICE_PRECISION
from project_utils import days_since_dt, days_for_free_api


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
        days = cache.days_to_call(starting_dt)
        if days != 0:
            params = {"vs_currency": currency_symbol,
                      "precision": PRICE_PRECISION,
                      "days": days}

            data = get(url, params)
            normal_data = cache.normalize_data(data)
            cache.upsert(normal_data)

        return cache.fetch_local()