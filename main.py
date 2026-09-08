import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from routes.upload_routes import router as upload_router

os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "1"
os.environ["PGCLIENTENCODING"] = "utf-8"

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT
)
logger = logging.getLogger("pqrs.ingestion")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Gestiona el inicio y apagado elegante (graceful shutdown) del servicio."""
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO SERVICIO DE INGESTA DE PQRS")
    logger.info("=" * 60)

    # Aquí se pueden verificar conexiones a DB o cargar recursos al iniciar

    yield  # La aplicación FastAPI corre y atiende peticiones en este punto

    logger.info("=" * 60)
    logger.info("🛑 APAGANDO SERVICIO DE INGESTA DE PQRS")
    logger.info("=" * 60)


app = FastAPI(
    title="PQRS Ingestion Service",
    description="Microservicio desacoplado para la ingesta dinámica de fuentes PQRS.",
    version="1.0.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory="templates")

app.include_router(upload_router)

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def root_view(request: Request):
    """Renderiza la pantalla amigable de ingesta de datos en Jinja2."""
    logger.info("Cargando formulario web de carga e ingesta...")
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Endpoint de monitoreo para comprobar el estado de salud del servicio."""
    return {"status": "healthy", "service": "pqrs-ingestion"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando servidor Uvicorn en modo de desarrollo local...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )