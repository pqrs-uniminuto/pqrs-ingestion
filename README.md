# 📥 PQRS - Servicio de Ingesta Dinámica de Datos

Microservicio desacoplado de **ingesta, normalización y almacenamiento dinámico** para solicitudes de PQRS (Peticiones, Quejas, Reclamos y Sugerencias). 

Soporta múltiples fuentes de entrada (archivos locales CSV/Excel/JSON y conectores a APIs REST/Socrata), automatiza la creación de tablas dinámicas en **PostgreSQL**, registra los esquemas en un catálogo centralizado y expone tanto una **Interfaz Web (FastAPI + Jinja2 + Tailwind CSS)** como capacidades de orquestación con **Dagster**.

---

## 🌟 Características Principales

- **Arquitectura Basada en Patrones de Diseño (SOLID):**
  - **Strategy Pattern & Registry:** Selección dinámica del lector según la fuente sin sentencias `if/elif` extensas.
  - **Dependency Inversion (DIP):** Inyección de dependencias limpias mediante FastAPI (`Depends`).
- **Soporte Multi-Formato & Fuentes Remotas:**
  - Archivos locales: `CSV`, `Excel (.xlsx, .xls)`, `JSON`.
  - Integración remota: URLs de `APIs REST` y datasets de datos abiertos (`Socrata`).
- **Persistencia Dinámica & Catálogo Centralizado:**
  - Crea tablas independientes saneadas en PostgreSQL por cada ingestión (`pqrs_custom_tbl`).
  - Actualiza automáticamente el catálogo de metadatos (`data_sources_catalog`).
- **Doble Interfaz de Operación:**
  - **Web UI:** Formulario interactivo responsivo (Jinja2 + Tailwind CSS).
  - **Dagster Engine:** Pipelines programables, sensores y ejecuciones orquestadas.

---

## 📂 Estructura del Proyecto

```text
pqrs-ingestion/
├── connectors/
│   ├── __init__.py
│   ├── api_b2b_client.py        # Cliente para integración con APIs B2B
│   ├── email_imap.py            # Módulo de lectura/ingesta vía correo IMAP
│   ├── excel_reader.py          # Lector especializado de archivos Excel
│   ├── open_data_client.py      # Cliente orquestador de lectura dinámico (Socrata/OpenData)
│   ├── registry.py              # Registro por diccionario de estrategias
│   └── strategies.py            # Patrón Strategy (Lectores CSV, Excel, JSON/API)
├── docs/                        # Documentación general del módulo
├── orchestrator/                # Definiciones de pipelines para Dagster
│   ├── jobs/                    # Jobs de procesamiento programado
│   ├── __init__.py
│   └── schedules.py             # Programaciones temporales (Schedules)
├── repositories/
│   ├── __init__.py
│   └── dynamic_repository.py    # Persistencia en Postgres y actualización del Catálogo
├── routes/
│   ├── __init__.py
│   └── upload_routes.py         # Endpoints de FastAPI y controlador de Vistas
├── templates/
│   └── upload.html              # Interfaz gráfica interactiva (Jinja2 + Tailwind CSS)
├── validators/                  # Validadores de esquemas y reglas de datos
├── venv/                        # Entorno virtual de Python
├── .env                         # Variables de entorno locales
├── .env.template                # Plantilla de variables de entorno
├── .gitignore                   # Exclusiones de control de versiones Git
├── docker-compose.yml           # Orquestación con PostgreSQL y Dagster
├── flores.db                    # Base de datos SQLite / fallback local
├── main.py                      # Punto de entrada principal (Servidor FastAPI)
├── README.md                    # Documentación y guía del proyecto
├── reporte_exportacion_flores_validado.csv # Dataset de prueba local
└── requirements.txt             # Dependencias del proyecto Python
```

##  Requisitos Previos

- **Python 3.10** o superior
- **Docker** y **Docker Compose** (opcional, para despliegue contenerizado)
- **PostgreSQL** (para almacenamiento, opcional)

##  Instalación y Configuración

### Variables de Entorno (.env)
Crea un archivo .env en la raíz del proyecto:

# Configuración del servidor FastAPI
PORT=8000
HOST=0.0.0.0

# Conexión a la Base de Datos PostgreSQL
DATABASE_URL=postgresql://pqrs_user:pqrs_pass@localhost:5432/pqrs_dwh

# Compatibilidad de codificación (Windows)
PYTHONLEGACYWINDOWSSTDIO=1
PGCLIENTENCODING=utf-8

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd pqrs-ingestion
```
# 2. Crear entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

# 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

# 4. Crear directorio para datos
```bash
mkdir -p data/incoming
mkdir -p data/processed
```

3. Opción B: Ejecución con Docker Compose
```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd pqrs-ingestion
```

# 2. Levantar todos los servicios
```bash
docker-compose up -d --build
```

# 3. Verificar que todo está funcionando
```bash
docker-compose ps
```
🏃 Ejecución

Desarrollo Local
```bash
# Iniciar la interfaz web de Dagster
dagster dev -f main.py
```

# Acceder a la UI en: http://localhost:3000
Ejecutar un Job específico
```bash
# Desde línea de comandos
python main.py
```
# O usando Dagster CLI
```bash
dagster job execute -f main.py -j ingest_excel_job
```
Con Docker
```bash
# Levantar servicios
docker-compose up -d
```
# Ver logs
```bash
docker-compose logs -f dagster
```

# Ejecutar job manualmente desde la UI
# Abrir http://localhost:3000 y ejecutar desde la interfaz

```bash

[ Formulario Upload (Jinja2/Tailwind) ]  ó  [ Solicitud HTTP / API REST ]
                         │
                         ▼
             [ FastAPI /upload_routes ]
                         │
                         ▼
        [ OpenDataClient + Strategy Registry ]
         ├── CsvIngestionStrategy
         ├── ExcelIngestionStrategy
         └── JsonApiIngestionStrategy
                         │
                         ▼
         [ DynamicDatabaseRepository ]
         ├── Crea tabla independiente: 'nombre_tabla_custom'
         └── Actualiza metadatos en: 'data_sources_catalog'
```

```
id,table_name,source_type,row_count,columns_schema,created_at
1,pqrs_bogota_2026,FILE_CSV,15420,"{""id"": ""int64"", ""descripcion"": ""object""}",2026-09-01 10:00:00
2,pqrs_api_socrata,API,8500,"{""ticket_id"": ""object"", ""estado"": ""object""}",2026-09-01 10:30:00
```

# Pruebas Unitarias e Integración

## Ejecutar suite de pruebas con Pytest
```text
pytest
```
## Generar reporte de cobertura de código
```bash
pytest --cov=. --cov-report=html
```

# Ejecucion sin contenedores
```bash
uvicorn main:app --reload --port 8000
```

## Visualizar pagina inicial
```text
http://localhost:8000/upload
```

![Pagina Inicial Pantalla](docs/pantalla_inicio.png)

## Base de datos

![Pagina Inicial Pantalla](docs/postgresql.png)
