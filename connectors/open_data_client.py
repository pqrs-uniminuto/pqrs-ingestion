import io
import logging
from typing import Optional
import pandas as pd
import requests

logger = logging.getLogger("pqrs.ingestion.connectors")


class OpenDataClient:
    """
    Cliente orquestador para obtener DataFrames desde distintas fuentes:
    - Archivos subidos en memoria (CSV, Excel, JSON, Parquet).
    - Endpoints de API REST / Datos Abiertos (Socrata, JSON directos).
    """

    @staticmethod
    def fetch_from_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
        """
        Lee bytes de un archivo subido y los convierte en un DataFrame de pandas.
        Maneja automáticamente codificaciones de caracteres (UTF-8, Latin-1, ISO-8859-1).
        """
        ext = filename.split(".")[-1].lower() if "." in filename else ""

        if ext == "csv":
            # Probar distintos encodings comunes en entornos Windows y América Latina
            encodings_to_try = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]
            last_exception = None

            for encoding in encodings_to_try:
                try:
                    stream = io.BytesIO(file_bytes)
                    df = pd.read_csv(stream, encoding=encoding)
                    logger.info(f"Archivo '{filename}' leído exitosamente con encoding='{encoding}'.")
                    return df
                except (UnicodeDecodeError, Exception) as e:
                    last_exception = e
                    continue

            raise ValueError(
                f"No se pudo decodificar el archivo CSV '{filename}'. "
                f"Error original: {str(last_exception)}"
            )

        elif ext in ["xlsx", "xls"]:
            stream = io.BytesIO(file_bytes)
            engine = "openpyxl" if ext == "xlsx" else "xlrd"
            return pd.read_excel(stream, engine=engine)

        elif ext == "json":
            stream = io.BytesIO(file_bytes)
            return pd.read_json(stream)

        elif ext == "parquet":
            stream = io.BytesIO(file_bytes)
            return pd.read_parquet(stream)

        else:
            raise ValueError(
                f"Formato de archivo no soportado: '.{ext}'. "
                f"Formatos permitidos: .csv, .xlsx, .xls, .json, .parquet"
            )

    @staticmethod
    def fetch_from_api(url: str, limit: int = 50000) -> pd.DataFrame:
        """
        Obtiene datos desde una URL de API REST o Socrata / Datos Abiertos.
        """
        logger.info(f"Consultando API remota: {url}")

        # Si la URL es de Socrata (Datos Abiertos Colombia, etc.)
        if "$limit" not in url and "socrata" in url.lower():
            delimiter = "&" if "?" in url else "?"
            url = f"{url}{delimiter}$limit={limit}"

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # En caso de respuestas envueltas en llaves como {"data": [...]}
            if "data" in data and isinstance(data["data"], list):
                df = pd.DataFrame(data["data"])
            elif "results" in data and isinstance(data["results"], list):
                df = pd.DataFrame(data["results"])
            else:
                df = pd.DataFrame([data])
        else:
            raise ValueError("El formato de respuesta de la API no se pudo transformar en tabla.")

        return df