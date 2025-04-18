import pandas as pd


def make_time_series_frame(data, coin_id: str, currency_symbol: str):
    df = pd.DataFrame(data)
    df.attrs['coin_id'] = coin_id
    df.attrs['currency_symbol'] = currency_symbol
    return df