# ============================================================================
# Dockerfile - API Flask GeoFeedback Papudo
# Optimizado para Railway Free Tier (512MB RAM)
# ============================================================================

FROM python:3.11-slim AS base

# Variables inmutables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ============================================================================
# LAYER 1: Dependencias del sistema (raramente cambia)
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================================
# LAYER 2: Dependencias Python (cambia solo con requirements.txt)
# ============================================================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# ============================================================================
# LAYER 3: Código de aplicación (cambia frecuentemente)
# ============================================================================
# CRÍTICO: Copiar TODO el directorio para evitar archivos faltantes
COPY . .

# ============================================================================
# SEGURIDAD: Usuario no-root
# ============================================================================
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ============================================================================
# HEALTH CHECK: Usando curl (más robusto)
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/api/v1/health || exit 1

# ============================================================================
# COMANDO: Optimizado para Railway Free Tier
# - workers=2: Máximo para 512MB RAM (~150MB cada uno + overhead)
# - threads=2: Mejor concurrencia sin aumentar RAM
# - timeout=120: Para queries PostGIS pesadas
# - preload: Comparte memoria entre workers
# ============================================================================
CMD ["sh", "-c", "gunicorn \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 2 \
    --threads 2 \
    --timeout 120 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app"]
