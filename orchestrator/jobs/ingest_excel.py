# jobs/ingest_csv.py (en la carpeta jobs/)
from dagster import job, op
import pandas as pd
import os
from connectors.excel_reader import read_csv


@op(
    config_schema={
        "file_path": str,
        "delimiter": str,
        "encoding": str,
        "required_columns": list,
    }
)
def extract_csv(context) -> pd.DataFrame:
    config = context.op_config

    context.log.info(f" Leyendo archivo: {config['file_path']}")

    df = read_csv(
        file_path=config['file_path'],
        delimiter=config.get('delimiter', ','),
        encoding=config.get('encoding', 'utf-8'),
        required_columns=config.get('required_columns', [])
    )

    context.log.info(f" Extraídas {len(df)} filas")
    context.log.info(f" Columnas: {list(df.columns)}")

    return df


@op
def validate_records(context, df: pd.DataFrame) -> pd.DataFrame:
    from validators.business_rules import validate_exportacion_flores

    records = df.to_dict('records')
    valid_records = []
    errors_count = 0

    for idx, rec in enumerate(records):
        try:
            validated = validate_exportacion_flores(rec)
            valid_records.append(validated)
        except Exception as e:
            errors_count += 1
            context.log.warning(f" ** Fila {idx} inválida: {e} **")

    context.log.info(f" {len(valid_records)} registros válidos de {len(records)}")
    context.log.info(f" {errors_count} registros inválidos")

    return pd.DataFrame(valid_records)


@op
def load_to_database(context, df: pd.DataFrame):
    if df.empty:
        context.log.warning(" No hay datos para cargar")
        return

    from sqlalchemy import create_engine

    db_url = os.getenv("DATABASE_URL", "sqlite:///flores.db")  # Usar SQLite por defecto
    engine = create_engine(db_url)

    df.to_sql('exportaciones_flores', engine, if_exists='append', index=False)
    context.log.info(f" Cargados {len(df)} registros a la base de datos")


@job
def ingest_csv_job():
    df = extract_csv()
    valid_df = validate_records(df)
    load_to_database(valid_df)