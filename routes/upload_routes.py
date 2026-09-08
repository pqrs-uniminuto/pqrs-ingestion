import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Importaciones del proyecto
from connectors.open_data_client import OpenDataClient
from repositories.dynamic_repository import DynamicDatabaseRepository

# Configuración de logs
logger = logging.getLogger("pqrs.ingestion.routes")

# Inicialización del Router y las Plantillas Jinja2
router = APIRouter(prefix="/upload", tags=["Ingestion Web UI"])
templates = Jinja2Templates(directory="templates")


def get_db_repository() -> DynamicDatabaseRepository:
    """Inyección de dependencia para obtener el repositorio de la base de datos."""
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:root@localhost:5432/pqrs_db?client_encoding=utf8"
    )
    return DynamicDatabaseRepository(db_url=db_url)


def get_open_data_client() -> OpenDataClient:
    """Inyección de dependencia para obtener el orquestador de lecturas de datos."""
    return OpenDataClient()


@router.get("", response_class=HTMLResponse)
async def render_upload_page(request: Request):
    """Renderiza la interfaz gráfica principal para la ingesta de PQRS."""
    return templates.TemplateResponse(
        request=request,
        name="upload.html"
    )


@router.post("", response_class=HTMLResponse)
async def handle_ingestion_upload(
        request: Request,
        ingest_mode: str = Form(...),  # 'file' o 'api'
        table_name: str = Form(...),
        file: Optional[UploadFile] = File(None),
        api_url: Optional[str] = Form(None),
        repository: DynamicDatabaseRepository = Depends(get_db_repository),
        client: OpenDataClient = Depends(get_open_data_client)
):
    """
    Controlador principal que procesa la ingesta desde un archivo subido
    o desde una API remota/Socrata y guarda los resultados en PostgreSQL.
    """
    try:
        # Validación básica del nombre de la tabla
        table_name_clean = table_name.strip()
        if not table_name_clean:
            raise ValueError("El nombre de la tabla de destino no puede estar vacío.")

        df = None
        source_type_label = ""

        # MODO 1: Ingesta desde Archivo Local (CSV, Excel, JSON)
        if ingest_mode == "file":
            if not file or not file.filename:
                raise ValueError("Debe seleccionar un archivo válido para cargar.")

            file_bytes = await file.read()
            if not file_bytes:
                raise ValueError("El archivo subido está vacío.")

            # Lectura dinámica a través del cliente orquestador
            df = client.fetch_from_file(file_bytes=file_bytes, filename=file.filename)
            source_type_label = f"FILE_{file.filename.split('.')[-1].upper()}"

        # MODO 2: Ingesta desde Endpoint API / Socrata
        elif ingest_mode == "api":
            if not api_url or not api_url.strip():
                raise ValueError("Debe proporcionar una URL de API válida.")

            # Lectura remota desde API REST o Socrata
            df = client.fetch_from_api(url=api_url.strip())
            source_type_label = "API_ENDPOINT"

        else:
            raise ValueError(f"Modo de ingesta no soportado: '{ingest_mode}'")

        # Validación del contenido leído
        if df is None or df.empty:
            raise ValueError("La fuente de datos procesada no contiene registros o no pudo ser leída.")

        # Guardar en PostgreSQL y actualizar data_sources_catalog
        created_table, text_col, cat_col = repository.save(
            df=df,
            table_name=table_name_clean,
            source_type=source_type_label
        )

        logger.info(
            f"Ingesta exitosa. Tabla creada: '{created_table}' ({len(df)} filas). "
            f"[Mapeo: Texto='{text_col}', Categoria='{cat_col}']"
        )

        # Respuesta de éxito renderizada en la plantilla Jinja2
        return templates.TemplateResponse(
            request=request,
            name="upload.html",
            context={
                "success": True,
                "message": f"¡Ingesta exitosa! Se guardaron {len(df)} registros en la tabla '{created_table}'.",
                "table_name": created_table,
                "row_count": len(df),
                "text_column": text_col,
                "category_column": cat_col,
                "columns": list(df.columns)
            }
        )

    except Exception as e:
        # Registro detallado del error en consola
        logger.error(f"Error crítico durante el proceso de ingesta: {str(e)}", exc_info=True)

        # Respuesta de error controlada para el usuario en la UI
        return templates.TemplateResponse(
            request=request,
            name="upload.html",
            context={
                "success": False,
                "error": f"Error durante la ingesta: {str(e)}"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )