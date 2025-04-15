from datetime import datetime

import pandas as pd


class TimeSeriesFrame(pd.DataFrame):
    """Wrapper over pandas.DataFrame containing coin_id and currency_symbol.
    The constructor creates datetime from timestamp from the given data and sets it as the index.

    Returns an empty frame with coin_id and currency_symbol if the given data is None.

    Raises a ValueError if the given data structure doesn't contain a timestamp."""
    def __init__(self, data,  coin_id: str, currency_symbol: str):
        if not data:
            super().__init__(data)
        elif 'timestamp' not in data:
            raise ValueError("Data should contain timestamp.")
        else:
            super().__init__(data, index=[datetime.fromtimestamp(ts/1000) for ts in data['timestamp']])
            self.index.name = 'datetime'

        self._coin_id = coin_id
        self._currency_symbol = currency_symbol

    @property
    def coin_id(self):
        return self._coin_id

    @property
    def currency_symbol(self):
        return self._currency_symbol