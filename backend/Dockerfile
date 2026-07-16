# ============================================================================
# Dockerfile - API FastAPI & Celery GeoFeedback
# Optimizado para Railway Pro (512MB-1GB RAM)
# ============================================================================

FROM python:3.11-slim AS base

# Variables inmutables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ============================================================================
# LAYER 1: Dependencias del sistema
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================================
# LAYER 2: Dependencias Python
# ============================================================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# LAYER 3: Código de aplicación
# ============================================================================
COPY . .

# ============================================================================
# SEGURIDAD: Usuario no-root
# ============================================================================
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ============================================================================
# HEALTH CHECK
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/api/v1/health || exit 1

# ============================================================================
# COMANDO DE INICIO (Por defecto levanta la API de FastAPI con Gunicorn)
# Nota: El servicio worker de Celery en Railway sobreescribirá este comando por:
# celery -A app.tasks.worker worker --loglevel=info
# ============================================================================
CMD ["sh", "-c", "gunicorn \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile /dev/stdout \
    --error-logfile /dev/stdout \
    --log-level info \
    app.main:app"]
