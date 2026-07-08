 README.md
markdown
#  PQRS - Sistema de Ingesta de Datos

Sistema de ingesta automatizada de PQRS (Peticiones, Quejas, Reclamos y Sugerencias) utilizando **Dagster** como orquestador de workflows.

##  ¿Qué hace este proyecto?

Este sistema permite **ingestar, validar y procesar** archivos de PQRS desde múltiples fuentes:

-  **Archivos Excel** (local, URL, FTP)
- 🔌 **APIs B2B** (próximamente)
-  **Correos electrónicos** (próximamente)

Todo orquestado de manera automática y monitoreable a través de la interfaz web de Dagster.

##  Arquitectura
pqrs-ingestion/
├── main.py # Punto de entrada principal
├── orchestrator/
│ ├── jobs/ # Jobs de ingesta
│ │ └── ingest_excel.py # Job para archivos Excel
│ ├── schedules.py # Programaciones automáticas
│ └── sensors.py # Sensores para eventos
├── connectors/
│ └── excel_reader.py # Lector de Excel con principios SOLID
├── validators/
│ ├── schemas.py # Validación de esquemas con Pydantic
│ └── business_rules.py # Reglas de negocio
├── docker-compose.yml # Orquestación con Docker
├── Dockerfile # Imagen para contenerización
└── requirements.txt # Dependencias

text

##  Requisitos Previos

- **Python 3.10** o superior
- **Docker** y **Docker Compose** (opcional, para despliegue contenerizado)
- **PostgreSQL** (para almacenamiento, opcional)

##  Instalación

### Opción 1: Local (Desarrollo)

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

Opción 2: Con Docker (Producción)
```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd pqrs-ingestion
```

# 2. Levantar todos los servicios
```bash
docker-compose up -d
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
📊 Flujo de Trabajo
1. Ingesta de Excel
python
from connectors.excel_reader import read_excel

# Leer desde archivo local
df = read_excel('local', file_path='data/pqrs.xlsx')

# Leer desde URL
df = read_excel('url', url='https://ejemplo.com/pqrs.xlsx')

# Leer desde FTP
df = read_excel('ftp', 
                host='ftp.ejemplo.com',
                user='usuario',
                password='clave',
                file_path='/reportes/pqrs.xlsx')
2. Validación de Datos
python
from validators.schemas import PQRSRecord
from validators.business_rules import BusinessRules

# Validar cada registro
record = PQRSRecord(**data)
validation = BusinessRules.apply_rules(data)
3. Automatización con Dagster
Schedules: Ejecución automática cada hora

Sensors: Reacción a nuevos archivos

UI: Monitoreo y ejecución manual

⚙️ Configuración
Variables de Entorno (.env)
env
# Configuración de Excel
EXCEL_PATH=data/pqrs_ingest.xlsx
SHEET_NAME=0
REQUIRED_COLUMNS=fecha_recepcion,tipo_pqrs,nombre_solicitante

# Base de datos
DATABASE_URL=postgresql://user:pass@postgres:5432/pqrs_db

# FTP (si se usa)
FTP_HOST=ftp.ejemplo.com
FTP_USER=usuario
FTP_PASSWORD=clave
FTP_PATH=/reportes/pqrs.xlsx
Dagster Config
Editar main.py para configurar:

python
class Config:
    EXCEL_PATH = os.getenv("EXCEL_PATH", "data/pqrs_ingest.xlsx")
    REQUIRED_COLUMNS = os.getenv("REQUIRED_COLUMNS", "fecha_recepcion,tipo_pqrs,nombre_solicitante").split(",")
🧪 Pruebas
bash
# Ejecutar todas las pruebas
pytest tests/

# Ejecutar pruebas específicas
pytest tests/test_excel_reader.py

# Con cobertura
pytest --cov=connectors tests/
📊 Monitoreo
Dagster UI
Acceder a http://localhost:3000 para:

📋 Ver todos los jobs disponibles

▶️ Ejecutar jobs manualmente

📊 Ver logs y métricas

⏰ Gestionar schedules y sensors

🔍 Depurar errores

Logs
bash
# Ver logs en tiempo real
docker-compose logs -f dagster

# O desde la UI de Dagster
# Ir a "Runs" → Seleccionar ejecución → Ver logs
🔧 Solución de Problemas
Error: "Module not found"
bash
# Verificar que estás en el entorno correcto
which python
pip list | grep dagster

# Reinstalar dependencias
pip install -r requirements.txt --upgrade
Error: "Permission denied" en archivos
bash
# Dar permisos al directorio de datos
chmod -R 755 data/
Dagster no inicia
bash
# Verificar puerto disponible
lsof -i :3000  # En Linux/Mac
netstat -ano | findstr :3000  # En Windows

# Cambiar puerto en el comando
dagster dev -f main.py --port 3001
Error de conexión a PostgreSQL
bash
# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Reiniciar PostgreSQL
docker-compose restart postgres
🗄️ Estructura de Datos Esperada
Archivo Excel (PQRS)
Columna	Tipo	Descripción	Obligatorio
fecha_recepcion	datetime	Fecha de recepción
tipo_pqrs	string	Petición/Queja/Reclamo/Sugerencia
canal	string	Correo/Web/Presencial
nombre_solicitante	string	Nombre completo
email_solicitante	email	Correo electrónico
telefono_solicitante	string	Teléfono de contacto
descripcion	text	Descripción del caso
estado	string	Recibido/En proceso/Resuelto/Cerrado
fecha_resolucion	datetime	Fecha de resolución	
observaciones	text	Observaciones adicionales
🚀 Roadmap
Ingesta de archivos Excel

Validación de datos con Pydantic

Reglas de negocio

Orquestación con Dagster

Schedules y Sensors

Ingesta desde APIs B2B

Ingesta desde correos electrónicos

Dashboard de métricas

Alertas y notificaciones

UI personalizada

🤝 Contribuciones
Fork el proyecto

Crear una rama (git checkout -b feature/nueva-funcionalidad)

Commitear cambios (git commit -am 'Agrega nueva funcionalidad')

Push a la rama (git push origin feature/nueva-funcionalidad)

Crear un Pull Request

📄 Licencia
Este proyecto está bajo la licencia MIT