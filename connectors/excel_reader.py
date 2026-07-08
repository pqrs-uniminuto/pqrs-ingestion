import pandas as pd
from typing import Optional, Union
from pathlib import Path

def read_csv(
        file_path: str,
        delimiter: str = ',',
        encoding: str = 'utf-8',
        required_columns: Optional[list] = None,
        **kwargs
) -> pd.DataFrame:
    """
    Lee un archivo CSV y lo retorna como DataFrame con normalización de columnas.
    """
    # 1. Verificar que el archivo existe
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    # Configuración adaptativa del separador
    if delimiter is None:
        engine = 'python'
        sep = None
    else:
        engine = kwargs.pop('engine', 'c' if delimiter != 'None' else 'python')
        sep = delimiter

    # 2. Leer CSV con pandas
    df = pd.read_csv(file_path, sep=sep, encoding=encoding, engine=engine, **kwargs)

    # 3. Validar que no esté vacío
    if df.empty:
        raise ValueError("El archivo CSV está vacío")

    # ----------------------------------------------------------------
    # NUEVA NORMALIZACIÓN CRÍTICA: Elimina espacios y pasa a minúsculas
    # ----------------------------------------------------------------
    df.columns = df.columns.str.strip().str.lower()

    # 4. Validar columnas requeridas (también normalizadas para comparar)
    if required_columns:
        req_clean = [col.strip().lower() for col in required_columns]
        missing = set(req_clean) - set(df.columns)
        if missing:
            # Imprime las columnas reales exactas leídas para que puedas auditarlas en consola
            print(f"\n🔍 [DEBUG EXCEL_READER] Columnas leídas del archivo: {list(df.columns)}")
            raise ValueError(f"Columnas faltantes: {missing}")

    return df
