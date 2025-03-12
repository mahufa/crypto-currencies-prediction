import pandas as pd
import requests

from db_manager import QuantDataCache


def fetch_data(url, params=None):
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()


def get_currencies():
    """ Returns Series with all available currencies, else if status code = 4xx or 5xx raises HTTPError. """
    url = "https://api.coingecko.com/api/v3/simple/supported_vs_currencies"
    data = fetch_data(url)

    return pd.Series(data) if data else pd.Series()


def get_coins():
    """ Returns DataFrame with all available coin IDs, symbols and names,
     else if status code = 4xx or 5xx raises HTTPError. """
    url = "https://api.coingecko.com/api/v3/coins/list"
    data = fetch_data(url)

    return pd.DataFrame(data) if data else pd.DataFrame()


def get_sorted_by_mkt_cap(n=10, currency_symbol="usd", precision=4):
    """ Returns DataFrame with n (max. 250) coins IDs, symbols, names, market capitalization and current prices,
     where coins have the biggest market capitalization, else if status code = 4xx or 5xx raises HTTPError. """
    if not isinstance(n, int):
        raise TypeError("n must be an integer")

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": currency_symbol,
              "per_page": n,
              "precision": precision}
    data = fetch_data(url, params)

    return pd.DataFrame(data)[['id', 'symbol', 'name', 'market_cap', 'current_price']] if data else pd.DataFrame()


@QuantDataCache("historical_data")
def get_historical_data(coin_id, currency_symbol="usd", precision=4, days=30):
    """ Returns DataFrame with historical prices, market capitalization and 24h volume from last days,
     else if status code = 4xx or 5xx raises HTTPError. """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": currency_symbol,
              "precision": precision,
              "days": days}
    data = fetch_data(url, params)

    if not data:
        return pd.DataFrame()

    return pd.DataFrame({
        "timestamp": [ts for ts, _ in data["prices"]],
        "prices": [price for _, price in data["prices"]],
        "market_caps": [cap for _, cap in data["market_caps"]],
        "total_volumes": [vol for _, vol in data["total_volumes"]]})


@QuantDataCache("ohlc_data")
def get_ohlc_data(coin_id, currency_symbol="usd", precision=4, days=30):
    """ Returns DataFrame with OHLC (Open, High, Low, Close) data for usage in candlestick chart from last days,
     else if status code = 4xx or 5xx raises HTTPError. """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {"vs_currency": currency_symbol,
              "precision": precision,
              "days": days}
    data = fetch_data(url, params)

    if data:
        df = pd.DataFrame(data)
        df.columns = ['timestamp', 'open', 'high', 'low', 'close']

        return df

    return pd.DataFrame()
