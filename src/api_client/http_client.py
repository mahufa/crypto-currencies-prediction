from datetime import datetime
from typing import Any

import requests

from cache import CacheManager
from config import DEFAULT_DAYS
from project_utils import utc_from_cached_ts, days_since_dt, days_for_free_api


def get_json(url: str, params: dict[str, any] = None):
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()


def get(url: str,
        params: dict[str, any] = None,
        coin_id: str = None,
        starting_dt: datetime = None,
        table_name: str = None) -> dict | Any | None:
    if not table_name:
        get_json(url, params)

    with CacheManager(coin_id, params.get('vs_currency'), table_name) as cache:
        local_data = cache.fetch_local()

        if not local_data:
            normalized_new_data = cache.normalize_data(get_json(url, params))
            cache.upsert(normalized_new_data)

            return normalized_new_data

        last_cached_ts = cache.last_ts()
        last_cached_dt = utc_from_cached_ts(last_cached_ts)
        if not starting_dt:
            days_from_last_cached = (days_for_free_api(days_since_dt(last_cached_dt))
                                     if table_name == 'ohlc_data'
                                     else days_since_dt(last_cached_dt))
            days = days_from_last_cached if days_from_last_cached < DEFAULT_DAYS else DEFAULT_DAYS
        elif starting_dt < last_cached_dt:
            days = (days_for_free_api(days_since_dt(last_cached_dt)) if table_name == 'ohlc_data'
                    else days_since_dt(last_cached_dt))
        params['days'] = days

        normalized_new_data = cache.normalize_data(get_json(url, params))
        cache.upsert(normalized_new_data)

        print()
        return local_data + normalized_new_data
