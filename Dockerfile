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

# Healthcheck apuntando a la API de FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/api/v1/health || exit 1

# Comando por defecto para levantar FastAPI
CMD ["sh", "-c", "gunicorn \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --preload \
    --access-logfile /dev/stdout \
    --error-logfile /dev/stdout \
    --log-level info \
    app.main:app"]
