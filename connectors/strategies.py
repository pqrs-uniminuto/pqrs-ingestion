from abc import ABC, abstractmethod
import json
import pandas as pd
import requests

class BaseIngestionStrategy(ABC):
    """Interfaz abstracta para la lectura de cualquier fuente de datos."""
    @abstractmethod
    def read(self, source_path_or_url: str, **kwargs) -> pd.DataFrame:
        pass

class CsvIngestionStrategy(BaseIngestionStrategy):
    """Estrategia para archivos CSV / TSV."""
    def read(self, source_path_or_url: str, **kwargs) -> pd.DataFrame:
        encoding = kwargs.get("encoding", "utf-8")
        sep = kwargs.get("sep", None)
        return pd.read_csv(source_path_or_url, sep=sep, encoding=encoding, engine="python")

class ExcelIngestionStrategy(BaseIngestionStrategy):
    """Estrategia para archivos Excel (.xlsx, .xls)."""
    def read(self, source_path_or_url: str, **kwargs) -> pd.DataFrame:
        sheet_name = kwargs.get("sheet_name", 0)
        return pd.read_excel(source_path_or_url, sheet_name=sheet_name)

class JsonApiIngestionStrategy(BaseIngestionStrategy):
    """Estrategia para archivos JSON locales o Endpoints de APIs REST / Socrata."""
    def read(self, source_path_or_url: str, **kwargs) -> pd.DataFrame:
        if source_path_or_url.startswith("http"):
            response = requests.get(source_path_or_url, timeout=30)
            response.raise_for_status()
            data = response.json()
        else:
            with open(source_path_or_url, "r", encoding="utf-8") as f:
                data = json.load(f)

        return self._normalize_json_payload(data)

    def _normalize_json_payload(self, data: list | dict) -> pd.DataFrame:
        if isinstance(data, list):
            return pd.json_normalize(data)
        if isinstance(data, dict):
            for key in ["data", "results", "items", "records"]:
                if key in data and isinstance(data[key], list):
                    return pd.json_normalize(data[key])
            return pd.json_normalize([data])
        raise ValueError("El contenido JSON recibido no tiene un formato tabular válido.")