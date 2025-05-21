from datetime import datetime

import pandas as pd

from frames import make_time_series_frame
from project_utils import days_since_dt, days_for_free_api
from api_client.http_client import get
from config import DEFAULT_CURRENCY, PRICE_PRECISION, DEFAULT_COIN


def get_currencies() -> pd.Series:
    """ Returns Series with all available currencies, else if status code = 4xx or 5xx raises HTTPError. """
    url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
    data = get(url)

    return pd.Series(data) if data else pd.Series()


def get_coins() -> pd.DataFrame:
    """ Returns DataFrame with all available coin IDs, symbols and names.

    Frame columns:
        'id' | 'symbol' | 'name'

     If status code = 4xx or 5xx raises HTTPError. """
    url = "https://api.coingecko.com/api/v3/coins/list"
    data = get(url)

    return pd.DataFrame(data) if data else pd.DataFrame()


def get_sorted_by_mkt_cap(n: int=10, currency_symbol: str = DEFAULT_CURRENCY) -> pd.DataFrame:
    """ Returns DataFrame with n (max. 250) coins IDs, symbols, names, market capitalization and current prices,
     where coins have the biggest market capitalization.

     Frame columns:
        'id' | 'symbol' | 'name' | 'market_cap' | 'current_price'

     If status code = 4xx or 5xx raises HTTPError. """
    if not isinstance(n, int):
        raise TypeError("n must be an integer")

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": currency_symbol,
              "per_page": n,
              "precision": PRICE_PRECISION}
    data = get(url, params)

    return pd.DataFrame(data)[['id', 'symbol', 'name', 'market_cap', 'current_price']] \
        if data else pd.DataFrame()


def get_historical_data(coin_id: str = DEFAULT_COIN,
                        currency_symbol: str = DEFAULT_CURRENCY,
                        starting_dt: datetime = None
                        ) -> pd.DataFrame:
    """ Returns DataFrame with historical data from day mathing
    starting_dt, or if it's None, from range of DEFAULT_DAYS.

    Frame columns:
        'timestamp' | 'price' | 'market_cap' | 'total_volume'

     If status code = 4xx or 5xx raises HTTPError. """
    days = days_since_dt(starting_dt)

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {'vs_currency': currency_symbol,
              'precision': PRICE_PRECISION,
              'days': days}
    data = get(url, params, coin_id, starting_dt, 'historical_data')

    return make_time_series_frame(data, coin_id, currency_symbol)


def get_ohlc_data(coin_id: str = DEFAULT_COIN,
                  currency_symbol: str = DEFAULT_CURRENCY,
                  starting_dt: datetime=None
                  ) -> pd.DataFrame:
    """ Returns a DataFrame with OHLC data from the day matching
    starting_dt, or if it's None, from the range of DEFAULT_DAYS.

    Frame columns:
        timestamp | open | high | low | close

    If status code = 4xx or 5xx raises HTTPError. """
    days = days_since_dt(starting_dt)
    adjusted_days = days_for_free_api(days)

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {"vs_currency": currency_symbol,
              "precision": PRICE_PRECISION,
              "days": adjusted_days}
    data = get(url, params, coin_id, starting_dt, 'ohlc_data')
    return make_time_series_frame(data, coin_id, currency_symbol)