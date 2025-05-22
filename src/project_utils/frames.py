import pandas as pd


def make_time_series_frame(data: any, coin_id: str, currency_symbol: str) -> pd.DataFrame:
    df = pd.DataFrame(data)
    df.attrs['coin_id'] = coin_id
    df.attrs['currency_symbol'] = currency_symbol
    return df

def get_frame_attr(time_series_frame: pd.DataFrame) -> tuple[str,str]:
    return time_series_frame.attrs['coin_id'], time_series_frame.attrs['currency_symbol']