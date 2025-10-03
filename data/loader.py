import os
import pandas as pd

class DataHandler:
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self._data_cache = None

    def load_data(self):
        if self._data_cache is None:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(f"Fichier non trouvé : {self.data_path}")
            self._data_cache = pd.read_pickle(self.data_path)
        return self._data_cache

    def get(self, symbol: str, price = None, start: str = None, end: str = None) -> pd.DataFrame:
        if price == None:
            df = self.load_data()[symbol]
        else:
            df = self.load_data()[symbol][price]
        if start or end:
            df = df.loc[start:end]
        return df

    def get_multiple(self, symbols: list, price = ['Open', 'High', 'Low', 'Close', 'Volume'], start: str = None, end: str = None) -> dict:
        return {s: self.get(s, price, start, end) for s in symbols}
    
    def get_multiple_df(self, symbols: list, price, start: str = None, end: str = None) -> pd.DataFrame:
        data = self.load_data()
        adj_close_df = data.loc[start:end, pd.IndexSlice[symbols, price]]
        adj_close_df.columns = adj_close_df.columns.droplevel(1)
        
        return adj_close_df

