from dagster import sensor, RunRequest, SkipReason
import os
import hashlib
from pathlib import Path
from orchestrator.jobs.ingest_excel import ingest_csv_job

processed_files = {}


@sensor(job=ingest_csv_job)
def csv_file_sensor(context):
    csv_path = os.getenv("CSV_PATH", "reporte_exportacion_flores_validado.csv")

    if not Path(csv_path).exists():
        yield SkipReason(f"Archivo no encontrado: {csv_path}")
        return

    with open(csv_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    if processed_files.get(csv_path) == file_hash:
        yield SkipReason(f"El archivo {csv_path} no ha cambiado")
        return

    processed_files[csv_path] = file_hash

    yield RunRequest(
        run_key=f"csv_{Path(csv_path).stem}",
        run_config={
            "ops": {
                "extract_csv": {
                    "config": {
                        "file_path": csv_path,
                        "delimiter": os.getenv("CSV_DELIMITER", ","),
                        "encoding": os.getenv("CSV_ENCODING", "utf-8"),
                        "required_columns": os.getenv("REQUIRED_COLUMNS", "fecha,tipo_flor,cantidad,valor,pais").split(
                            ",")
                    }
                }
            }
        }
    )