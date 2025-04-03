import pandas as pd


class TimeSeriesFrame(pd.DataFrame):
    """Wrapper over pandas.DataFrame containing coin_id and currency_symbol.
    The constructor extracts timestamp from the given data and sets it as the index.

    Returns an empty frame with coin_id and currency_symbol if the given data is None.

    Raises a ValueError if the given data structure doesn't contain a timestamp."""
    def __init__(self, data,  coin_id: str, currency_symbol: str):
        if not data:
            super().__init__(data)
        elif 'timestamp' not in data:
            raise ValueError("Data should contain timestamp.")
        else:
            ts_column = data.pop('timestamp')
            super().__init__(data, index=ts_column)
            self.index.name = 'timestamp'

        self._coin_id = coin_id
        self._currency_symbol = currency_symbol

    def get_coin_id(self):
        return self._coin_id

    def get_currency_symbol(self):
        return self._currency_symbol