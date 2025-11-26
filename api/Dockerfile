# ============================================================================
# Dockerfile para API Flask - GeoFeedback Papudo
# OPTIMIZADO para Railway Free Tier (512MB RAM)
# ============================================================================

FROM python:3.11-slim

LABEL maintainer="GeoFeedback Chile"
LABEL description="API REST para consultas de riesgo de inundación en Papudo"
LABEL version="1.0.2"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema (para psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación (NO templates ni static para ahorrar RAM)
COPY app.py config.py ./

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puerto (Railway usa $PORT dinámicamente)
EXPOSE 5000

# Health check optimizado (sin requests library)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/api/v1/health || exit 1

# ============================================================================
# COMANDO CRÍTICO OPTIMIZADO PARA RAILWAY FREE TIER (512MB)
# ============================================================================
# Cambios desde versión anterior:
#   - workers 2 → 1 (reduce memoria ~50% adicional)
#   - Removido --threads y gthread (overhead innecesario)
#   - Agregado --max-requests 500 (recicla workers más frecuente)
#   - --log-level warning (menos overhead I/O)
# Resultado esperado: ~80-120MB RAM total
# ============================================================================

CMD ["sh", "-c", "gunicorn \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 1 \
    --timeout 120 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level warning \
    app:app"]
