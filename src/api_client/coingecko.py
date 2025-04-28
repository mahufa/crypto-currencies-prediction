from datetime import datetime, timedelta

import pandas as pd
from http_client import get_json
from cache import DataCache
from frames import make_time_series_frame

PRECISION = 2
DEFAULT_DAYS = 30
DEFAULT_CURRENCY = "usd"


def _days_for_free_api(days: int) -> int:
    limits = (1, 7, 14, 30, 90, 180)
    return next((limit for limit in limits if days <= limit), 365)


def get_currencies() -> pd.Series:
    """ Returns Series with all available currencies, else if status code = 4xx or 5xx raises HTTPError. """
    url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
    data = get_json(url)

    return pd.Series(data) if data else pd.Series()


def get_coins() -> pd.DataFrame:
    """ Returns DataFrame with all available coin IDs, symbols and names.

    Frame columns:
        'id' | 'symbol' | 'name'

     If status code = 4xx or 5xx raises HTTPError. """
    url = "https://api.coingecko.com/api/v3/coins/list"
    data = get_json(url)

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
              "precision": PRECISION}
    data = get_json(url, params)

    return pd.DataFrame(data)[['id', 'symbol', 'name', 'market_cap', 'current_price']] if data else pd.DataFrame()


@DataCache('historical_data', 5)
def get_historical_data(coin_id: str = 'bitcoin',
                        currency_symbol: str = DEFAULT_CURRENCY,
                        starting_timestamp: int | float = None
                        ) -> pd.DataFrame:
    """ Returns DataFrame with historical data from day mathing
    starting_timestamp, or if it's None, from range of DEFAULT_DAYS.

    Frame columns:
        'timestamp' | 'price' | 'market_cap' | 'total_volume'

     If status code = 4xx or 5xx raises HTTPError. """
    if starting_timestamp is None:
        starting_timestamp = (datetime.now() - timedelta(days=DEFAULT_DAYS)).timestamp() * 1000
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {'vs_currency': currency_symbol,
              'precision': PRECISION,
              'from': starting_timestamp/1000,
              'to': datetime.now().timestamp()}
    data = get_json(url, params)

    if not data:
        return make_time_series_frame([], coin_id, currency_symbol)

    return make_time_series_frame(
        {
            'timestamp': [ts for ts, _ in data['prices']],
            'price': [price for _, price in data['prices']],
            'market_cap': [cap for _, cap in data['market_caps']],
            'total_volume': [vol for _, vol in data['total_volumes']]
        },
        coin_id,
        currency_symbol)


@DataCache("ohlc_data", 5)
def get_ohlc_data(coin_id: str = 'bitcoin',
                  currency_symbol: str = DEFAULT_CURRENCY,
                  starting_timestamp: int | float=None
                  ) -> pd.DataFrame:
    """ Returns DataFrame with OHLC data from day mathing
    starting_timestamp, or if it's None, from range of DEFAULT_DAYS.

    Frame columns:
        timestamp | open | high | low | close

    If status code = 4xx or 5xx raises HTTPError. """
    if starting_timestamp is None:
        days = DEFAULT_DAYS
    else:
        date = datetime.fromtimestamp(starting_timestamp / 1000).date()
        days = (datetime.now().date() - date).days

    adjusted_days = _days_for_free_api(days)

    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {"vs_currency": currency_symbol,
              "precision": PRECISION,
              "days": adjusted_days}
    data = get_json(url, params)

    if not data:
        return make_time_series_frame([], coin_id, currency_symbol)

    timestamps, opens, highs, lows, closes = zip(*data)

    return make_time_series_frame(
        {
            'timestamp': timestamps,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes
        },
        coin_id,
        currency_symbol)
