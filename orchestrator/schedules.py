from dagster import ScheduleDefinition
from orchestrator.jobs.ingest_excel import ingest_csv_job

# Schedule para ejecutar cada hora
ingest_csv_schedule = ScheduleDefinition(
    job=ingest_csv_job,
    cron_schedule="0 * * * *",
    description="Ejecuta la ingesta del CSV de exportación de flores cada hora"
)