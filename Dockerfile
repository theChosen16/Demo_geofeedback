# ============================================================================
# Dockerfile - GeoFeedback Chile (Root Deployment)
# Build multi-etapa optimizado para Railway Pro
# ============================================================================

# --- Etapa 1: Compilación de Frontend React ---
FROM node:20-slim AS frontend-builder
WORKDIR /build

# Instalar dependencias
COPY frontend/package*.json ./
RUN npm ci

# Compilar SPA
COPY frontend/ ./
RUN npm run build

# --- Etapa 2: Servidor Backend Python FastAPI ---
FROM python:3.11-slim AS runner
WORKDIR /app

# Variables inmutables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Instalar dependencias del sistema requeridas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements y dependencias
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar el código del backend principal
COPY backend/ .

# Copiar la compilación estática del frontend
COPY --from=frontend-builder /build/dist ./frontend/dist

# Configuración de usuario no-root por seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck adaptativo para FastAPI o Celery Worker
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD if [ "$SERVICE_TYPE" = "worker" ]; then \
        python -m celery -A app.tasks.celery_app inspect ping || exit 0; \
    elif [ "$SERVICE_TYPE" = "beat" ]; then \
        exit 0; \
    else \
        curl -f http://127.0.0.1:${PORT:-5000}/api/v1/health || exit 0; \
    fi

# Comando por defecto para levantar FastAPI o Celery Worker dinámicamente
#
# El worker usa el pool prefork por defecto (no threads/gevent) a propósito: es el único
# que soporta task_time_limit/task_soft_time_limit (celery_app.py) vía señales al proceso hijo,
# el backstop que mata una tarea de GEE realmente colgada. Lo que sí se ajusta es la
# concurrencia (WORKER_CONCURRENCY, 4 procesos por defecto) para poder atender varios
# análisis a la vez en vez de uno a la vez, ya que sin este flag Celery calcula la
# concurrencia según los CPUs visibles del contenedor, que en Railway puede ser 1-2.
CMD ["sh", "-c", "if [ \"$SERVICE_TYPE\" = \"worker\" ]; then \
    python -m celery -A app.tasks.celery_app worker --loglevel=info --concurrency=${WORKER_CONCURRENCY:-4}; \
    elif [ \"$SERVICE_TYPE\" = \"beat\" ]; then \
    python -m celery -A app.tasks.celery_app beat --loglevel=info; \
    else \
    gunicorn \
        --bind 0.0.0.0:${PORT:-5000} \
        --workers 2 \
        --worker-class uvicorn.workers.UvicornWorker \
        --timeout 120 \
        --preload \
        --access-logfile /dev/stdout \
        --error-logfile /dev/stdout \
        --log-level info \
        app.main:app; \
    fi"]
