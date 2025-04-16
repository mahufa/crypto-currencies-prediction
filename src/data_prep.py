import pandas as pd


def set_date_index(ts_frame):
    ts_frame.timestamp = pd.to_datetime(ts_frame.timestamp, unit='ms').dt.floor('s')
    ts_frame.set_index('timestamp', inplace=True)
    ts_frame.index.name = 'datetime'
    return ts_frame

