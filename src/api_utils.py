from datetime import datetime, timedelta

import pandas as pd
import requests

from cache import QuantDataCache
from frames import TimeSeriesFrame

PRECISION = 2

def _fetch_data(url, params=None):
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()


def get_currencies():
    """ Returns Series with all available currencies, else if status code = 4xx or 5xx raises HTTPError. """
    url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
    data = _fetch_data(url)

    return pd.Series(data) if data else pd.Series()


def get_coins():
    """ Returns DataFrame with all available coin IDs, symbols and names.

     If status code = 4xx or 5xx raises HTTPError. """
    url = "https://api.coingecko.com/api/v3/coins/list"
    data = _fetch_data(url)

    return pd.DataFrame(data) if data else pd.DataFrame()


def get_sorted_by_mkt_cap(n=10, currency_symbol="usd"):
    """ Returns DataFrame with n (max. 250) coins IDs, symbols, names, market capitalization and current prices,
     where coins have the biggest market capitalization.

     If status code = 4xx or 5xx raises HTTPError. """
    if not isinstance(n, int):
        raise TypeError("n must be an integer")

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": currency_symbol,
              "per_page": n,
              "precision": PRECISION}
    data = _fetch_data(url, params)

    return pd.DataFrame(data)[['id', 'symbol', 'name', 'market_cap', 'current_price']] if data else pd.DataFrame()


@QuantDataCache('historical_data')
def get_historical_data(*, coin_id='bitcoin', currency_symbol='usd', starting_timestamp=None):
    """ Returns QuantDataFrame with historical prices, market capitalization and 24h volume from day mathing
    starting_timestamp, or if it's None, from last year.

     If status code = 4xx or 5xx raises HTTPError. """
    if starting_timestamp is None:
        starting_timestamp = (datetime.now() - timedelta(days=365)).timestamp()
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {'vs_currency': currency_symbol,
              'precision': PRECISION,
              'from': starting_timestamp,
              'to': datetime.now().timestamp()}
    data = _fetch_data(url, params)

    if not data:
        return TimeSeriesFrame(None, coin_id, currency_symbol)

    return TimeSeriesFrame({
        'timestamp': [ts for ts, _ in data['prices']],
        'price': [price for _, price in data['prices']],
        'market_cap': [cap for _, cap in data['market_caps']],
        'total_volume': [vol for _, vol in data['total_volumes']]},
        coin_id,
        currency_symbol)


@QuantDataCache("ohlc_data")
def get_ohlc_data(*, coin_id='bitcoin', currency_symbol="usd", starting_timestamp=None):
    """ Returns QuantDataFrame with OHLC (Open, High, Low, Close) data for usage in candlestick chart from day mathing
    starting_timestamp, or if it's None, from last year.

    If status code = 4xx or 5xx raises HTTPError. """
    if starting_timestamp is None:
        days = 365
    else:
        date = datetime.fromtimestamp(starting_timestamp / 1000).date()
        days = (datetime.now().date() - date).days

    if days:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        params = {"vs_currency": currency_symbol,
                  "precision": PRECISION,
                  "days": days}
        data = _fetch_data(url, params)

        if not data:
            return TimeSeriesFrame(None, coin_id, currency_symbol)

        timestamps, opens, highs, lows, closes = zip(*data)
        return TimeSeriesFrame({
            'timestamp': timestamps,
            'open':     opens,
            'high':     highs,
            'low':      lows,
            'close':    closes},
            coin_id,
            currency_symbol)