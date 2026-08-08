from dagster import ScheduleDefinition, DefaultScheduleStatus
from orchestrator.jobs.ingest_open_data import ingest_open_data_job

ingest_open_data_schedule = ScheduleDefinition(
    job=ingest_open_data_job,
    cron_schedule="54 23 * * *",
    execution_timezone="America/Bogota",
    default_status=DefaultScheduleStatus.RUNNING,  # <-- Activa el schedule por defecto
    description="Ejecuta la ingesta de Datos Abiertos a las 10:50 PM"
)