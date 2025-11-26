# ============================================================================
# Dockerfile para API Flask - GeoFeedback Papudo
# Despliegue en Railway.app
# ============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="GeoFeedback Chile"
LABEL description="API REST para consultas de riesgo de inundación en Papudo"
LABEL version="1.0.0"

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
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar código de la aplicación
COPY app.py config.py ./
COPY templates/ ./templates/
COPY static/ ./static/

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puerto (Railway usa $PORT dinámicamente)
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/v1/health')"

# Comando de inicio con Gunicorn
# Usa $PORT de Railway, o 5000 como fallback para desarrollo local
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --timeout 120 --access-logfile - --error-logfile - app:app"]
