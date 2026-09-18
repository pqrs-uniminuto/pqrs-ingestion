FROM python:3.12-slim

# Banderas de optimización de Python y pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Instalar únicamente la librería de sistema para PostgreSQL (sin herramientas de compilación)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar dependencias aprovechando la caché de capas de Docker/Podman
COPY requirements.txt .

# La bandera --only-binary=:all: prohíbe compilar código C desde cero
RUN pip install --only-binary=:all: -r requirements.txt

# 3. Copiar el código fuente al final (evita re-instalar paquetes si cambia solo el código)
COPY . /app

EXPOSE 8000 3000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]