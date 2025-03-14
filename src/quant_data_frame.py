import pandas as pd


class QuantDataFrame(pd.DataFrame):
    """Wrapper over pandas.DataFrame containing coin_id and currency_symbol."""
    def __init__(self, data,  coin_id: str, currency_symbol: str):
        super().__init__(data)
        self._coin_id = coin_id
        self._currency_symbol = currency_symbol

    def get_coin_id(self):
        return self._coin_id

    def get_currency_symbol(self):
        return self._currency_symbol