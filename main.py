import os
import logging
from dagster import Definitions
from orchestrator.jobs.ingest_open_data import ingest_open_data_job
from orchestrator.schedules import ingest_open_data_schedule

# Forzar codificación UTF-8 en cliente de PostgreSQL para Windows
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "1"
os.environ["PGCLIENTENCODING"] = "utf-8"

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

# DEFINICIÓN CORRECTA DE COMPONENTES
defs = Definitions(
    jobs=[ingest_open_data_job],            # <- Solo objetos JobDefinition aquí
    schedules=[ingest_open_data_schedule],  # <- Solo objetos ScheduleDefinition aquí
)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info(" PROCESANDO INGESTA DE PQRS - API DATOS ABIERTOS")
    logger.info("=" * 60)

    logger.info("Ejecutando 'ingest_open_data_job' en proceso local...")
    result = ingest_open_data_job.execute_in_process()

    if result.success:
        logger.info("¡Procesamiento e ingesta desde API completado exitosamente!")
        logger.info(f" Run ID: {result.run_id}")
    else:
        logger.error("Error durante el procesamiento de la ingesta de Datos Abiertos.")