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
├── .env                         # Variables de entorno locales
├── .gitignore                   # Exclusiones de control de versiones Git
├── docker-compose.yml           # Orquestación con PostgreSQL, FastAPI y Dagster
├── Dockerfile                   # Construcción de imagen ligera optimizada (Python 3.12-slim)
├── main.py                      # Punto de entrada principal (Servidor FastAPI)
├── README.md                    # Documentación y guía del proyecto
└── requirements.txt             # Dependencias del proyecto Python
```

##  Requisitos Previos

- **Python 3.12 (recomendado para desarrollo local)
- **Docker** y **Docker Compose** (opcional, para despliegue contenerizado)
- **PostgreSQL** (para almacenamiento, opcional)

##  Instalación y Configuración

## 📥 Clonación y Preparación del Proyecto

Sigue estos pasos para obtener el código fuente y preparar el entorno de trabajo:

```bash
# 1. Clonar el repositorio desde GitHub / GitLab
git clone [https://github.com/tu-usuario/pqrs-ingestion.git](https://github.com/tu-usuario/pqrs-ingestion.git)

# 2. Navegar al directorio raíz del proyecto
cd pqrs-ingestion

# 3. Crear el archivo de configuración .env a partir de la plantilla
cp .env.template .env   # En Linux / macOS
copy .env.template .env # En Windows (PowerShell / CMD)
```

### Variables de Entorno (.env)
Crea un archivo .env en la raíz del proyecto:

```text
# ==============================================================================
# 1. PUERTOS Y SERVICIOS (PODMAN / DOCKER COMPOSE)
# ==============================================================================
INGESTION_API_PORT=8000
DAGSTER_PORT=3000

# ==============================================================================
# 2. FUENTES DE DATOS (EXCEL & SOCRATA API)
# ==============================================================================
EXCEL_PATH=data/pqrs_ingest.xlsx
SHEET_NAME=0
REQUIRED_COLUMNS=fecha_recepcion,tipo_pqrs,nombre_solicitante
SOCRATA_ENDPOINT=[https://www.datos.gov.co/resource/e88e-ctba.json](https://www.datos.gov.co/resource/e88e-ctba.json)

# ==============================================================================
# 3. CONEXIÓN A BASE DE DATOS (POSTGRESQL DWH)
# ==============================================================================
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgrespassword
POSTGRES_HOST=pqrs_postgres_dwh
POSTGRES_PORT=5438
POSTGRES_DB=pqrs_db

# Cadena de conexión canónica compartida para SQLAlchemy / Psycopg2
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}?client_encoding=utf8

# ==============================================================================
# 4. CONFIGURACIÓN DE DAGSTER & ENTORNO
# ==============================================================================
DAGSTER_HOME=/app

# ==============================================================================
# 5. COMPATIBILIDAD Y CODIFICACIÓN (WINDOWS / PODMAN)
# ==============================================================================
PYTHONLEGACYWINDOWSSTDIO=1
PGCLIENTENCODING=utf-8
PYTHONUTF8=1
```

🚀 Despliegue con Podman / Docker Compose (Recomendado)

El entorno contenedorizado despliega 3 servicios coordinados (pqrs_postgres_dwh, 
pqrs_ingestion_api y pqrs_dagster_webserver) conectados mediante la red compartida externa pqrs_red_compartida.

1. Crear la Red Compartida 
Asegúrate de que la red compartida externa exista antes de iniciar los servicios:
```Bash
podman network create pqrs_red_compartida
```

2. Levantar los Servicios

Construye e inicia los contenedores en segundo plano:
```Bash
podman-compose up -d --build
```


3. Verificar Contenedores Activos

Comprueba que los 3 contenedores estén arriba y en sus respectivos puertos:

```Bash
podman ps
```

Deberías ver una salida similar a:

| Nombre del Contenedor | Puerto Interno | Puerto Expuesto (Host) | Servicio |
| :--- | :--- | :--- | :--- |
| **`pqrs_postgres_dwh`** | 5432 | **5438** | PostgreSQL DWH |
| **`pqrs_ingestion_api`** | 8000 | **8000** | FastAPI UI / REST |
| **`pqrs_dagster_webserver`** | 3000 | **3000** | Dagster Webserver |


4. Detener o Limpiar el Entorno
5. 
Detener manteniendo los datos: podman-compose down

Limpieza completa de Pods colgados: podman pod rm -f pod_pqrs-ingestion

🏃 Ejecución Local (Sin Contenedores)
Si prefieres ejecutar el código directamente en tu máquina local:


# 1. Crear e iniciar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar el servidor web de FastAPI
uvicorn main:app --reload --port 8000

# 4. Iniciar la interfaz web de Dagster (en otra terminal)
dagster dev -f main.py

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
