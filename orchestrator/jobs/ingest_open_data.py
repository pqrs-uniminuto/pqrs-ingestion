import os
import pandas as pd
from urllib.parse import quote_plus
from dotenv import load_dotenv
from dagster import job, op, get_dagster_logger
from sqlalchemy import create_engine
from connectors.open_data_client import OpenDataClient

# Force codificación UTF-8
os.environ["PGCLIENTENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

# Cargar variables de entorno desde el archivo .env local/contenedor
load_dotenv()

# Endpoint por defecto
SOCRATA_ENDPOINT = os.getenv(
    "SOCRATA_ENDPOINT",
    "https://www.datos.gov.co/resource/e88e-ctba.json"
)


def get_postgres_engine():
    """Genera el motor SQLAlchemy dando prioridad a DATABASE_URL del .env."""
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        user = os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres"))
        raw_password = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "postgrespassword"))
        password = quote_plus(raw_password)
        # El host por defecto apunta al container_name global en la red compartida
        host = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "pqrs_postgres_dwh"))
        port = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432"))
        db = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "pqrs_db"))

        db_url = f"postgresql://{user}:{password}@{host}:{port}/{db}?client_encoding=utf8"

    return create_engine(
        db_url,
        connect_args={"client_encoding": "utf8"},
        pool_pre_ping=True
    )


@op
def fetch_raw_data() -> pd.DataFrame:
    """Extrae registros desde la API de Socrata / Datos Abiertos Colombia."""
    logger = get_dagster_logger()
    logger.info(f"Iniciando extracción desde el endpoint Socrata: {SOCRATA_ENDPOINT}")

    try:
        client = OpenDataClient(SOCRATA_ENDPOINT)
        df = client.fetch_records(limit=3000)

        if df.empty:
            logger.warning("La API respondió pero no se obtuvieron registros (DataFrame vacío).")
        else:
            logger.info(
                f"Extracción exitosa. Registros obtenidos: {len(df)} | Columnas detectadas: {list(df.columns)}"
            )

        return df
    except Exception as e:
        logger.error(f"Error al consultar la API Socrata: {e}", exc_info=True)
        raise e


@op
def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza y mapea el DataFrame extraído a la estructura canónica del DWH."""
    logger = get_dagster_logger()
    logger.info("Iniciando fase de limpieza y transformación de los datos...")

    if df.empty:
        logger.warning("El DataFrame de entrada está vacío. Se omitirá la transformación.")
        return pd.DataFrame(columns=['entity_source', 'ticket_id', 'category', 'subject', 'description'])

    df_clean = pd.DataFrame()

    # 1. Mapeo a esquema canónico usando pandas Series
    df_clean['entity_source'] = "Aeropuerto Matecaña"
    df_clean['ticket_id'] = df['radicado'] if 'radicado' in df.columns else None

    if 'tipo' in df.columns:
        df_clean['category'] = df['tipo'].fillna('Otros')
    else:
        df_clean['category'] = 'Otros'

    if 'asunto' in df.columns:
        df_clean['subject'] = df['asunto'].fillna('')
    else:
        df_clean['subject'] = ''

    if 'detalle' in df.columns:
        df_clean['description'] = df['detalle'].fillna(df_clean['subject'])
    elif 'asunto' in df.columns:
        df_clean['description'] = df['asunto'].fillna('Sin descripción')
    else:
        df_clean['description'] = 'Sin descripción'

    registros_iniciales = len(df_clean)

    # 2. Filtrado de registros vacíos
    df_clean = df_clean[df_clean['description'].astype(str).str.strip() != '']

    # 3. Casteo explícito a string
    for col in ['entity_source', 'ticket_id', 'category', 'subject', 'description']:
        df_clean[col] = df_clean[col].astype(str)

    registros_filtrados = len(df_clean)
    descartados = registros_iniciales - registros_filtrados

    logger.info(
        f"Transformación completada: {registros_filtrados} registros válidos preparados. "
        f"Registros descartados: {descartados}."
    )

    return df_clean


@op
def load_to_dwh(df: pd.DataFrame):
    """Carga los datos transformados en la tabla raw_pqrs de PostgreSQL."""
    logger = get_dagster_logger()

    if df.empty:
        logger.warning("No hay registros para cargar en el DWH.")
        return

    logger.info(f"Conectando al DWH para cargar {len(df)} registros en 'raw_pqrs'...")

    engine = get_postgres_engine()

    try:
        df.to_sql(
            name="raw_pqrs",
            con=engine,
            if_exists="append",
            index=False,
            chunksize=500,
            method="multi"
        )
        logger.info("Carga completada exitosamente en PostgreSQL.")
    except Exception as e:
        logger.error(f"Error al escribir registros en PostgreSQL: {e}", exc_info=True)
        raise e


@job
def ingest_open_data_job():
    """Job principal de Dagster para orquestar la ingesta de Datos Abiertos."""
    raw_df = fetch_raw_data()
    clean_df = clean_and_transform(raw_df)
    load_to_dwh(clean_df)