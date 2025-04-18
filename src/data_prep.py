import pandas as pd


def set_date_index(ts_frame : pd.DataFrame):
    ts_frame.timestamp = pd.to_datetime(ts_frame.timestamp, unit='ms').dt.floor('s')
    ts_frame = ts_frame.set_index('timestamp')
    ts_frame.index.name = 'datetime'
    return ts_frame

def resample_data(ts_frame: pd.DataFrame, freq="1D") -> pd.DataFrame:
    return ts_frame.resample(freq).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'total_volume': 'sum'
    })