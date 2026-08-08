import requests
import pandas as pd

class OpenDataClient:
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url

    def fetch_records(self, limit: int = 2000) -> pd.DataFrame:
        params = {"$limit": limit}
        response = requests.get(self.endpoint_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)