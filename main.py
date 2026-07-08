# main.py - Mantener como está
import os
from dagster import Definitions, RunConfig
from orchestrator.jobs.ingest_excel import ingest_csv_job  # ← Así debe quedar
from orchestrator.schedules import ingest_csv_schedule
from orchestrator.sensors import csv_file_sensor


class Config:
    CSV_PATH = os.getenv("CSV_PATH", "reporte_exportacion_flores_validado.csv")
    DELIMITER = os.getenv("CSV_DELIMITER", ",")  # Volvemos a fijar la coma
    ENCODING = os.getenv("CSV_ENCODING", "latin-1")

    REQUIRED_COLUMNS = os.getenv(
        "REQUIRED_COLUMNS",
        "fecha_pedido,tipo_flor,cantidad_tallos,total_venta_usd,ciudad_destino"
    ).split(",")


defs = Definitions(
    jobs=[ingest_csv_job],
    schedules=[ingest_csv_schedule],
    sensors=[csv_file_sensor],
)

if __name__ == "__main__":
    print(" Procesando archivo de exportación de flores")
    print(f" Archivo: {Config.CSV_PATH}")

    if not os.path.exists(Config.CSV_PATH):
        print(f" Archivo no encontrado: {Config.CSV_PATH}")
        print("   Coloca el archivo CSV en la raíz del proyecto")
        exit(1)

    # Configuración de ejecución adaptada para desarrollo local
    run_config = {
        "ops": {
            "extract_csv": {
                "config": {
                    "file_path": Config.CSV_PATH,
                    "delimiter": Config.DELIMITER,
                    "encoding": Config.ENCODING,
                    "required_columns": Config.REQUIRED_COLUMNS
                }
            }
        }
    }

    # Reemplazo de execute_job por la función nativa del objeto job pasando el diccionario de configuración
    result = ingest_csv_job.execute_in_process(run_config=run_config)

    if result.success:
        print("\n ¡Procesamiento completado exitosamente!")
        print(f" Run ID: {result.run_id}")
    else:
        print("\n Error en el procesamiento")
