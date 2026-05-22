# ============================================================================
# Dockerfile - GeoFeedback Chile (Root Deployment)
# Optimizado para Railway Free Tier (512MB RAM)
# ============================================================================

FROM python:3.11-slim AS base

# Variables inmutables de entorno
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
# LAYER 2: Dependencias de Python
# ============================================================================
# Copiar requirements.txt desde el subdirectorio api
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ============================================================================
# LAYER 3: Código de aplicación
# ============================================================================
# Copiar el código del backend principal de la carpeta api a /app
COPY api/ .

# Copiar scripts adicionales por si se necesitan ejecutar tareas de soporte
COPY scripts/ ./scripts/

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
# COMANDO: Optimizado para Railway Free Tier (512MB)
# ============================================================================
CMD ["sh", "-c", "gunicorn \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --preload \
    --access-logfile /dev/stdout \
    --error-logfile /dev/stdout \
    --log-level info \
    app:app"]
