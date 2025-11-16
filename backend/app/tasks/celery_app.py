import os
from celery import Celery
from app.core.config import settings

# Obtener URL de Redis de la configuración.
# Para evitar colisiones en Redis, podemos añadir /1 para usar la DB 1 de Redis para Celery.
redis_url = settings.REDIS_URL or "redis://localhost:6379/0"

if settings.REDIS_URL and not redis_url.endswith("/0") and not redis_url.endswith("/1") and not redis_url.endswith("/2"):
    # Si viene de Railway inyectada directamente (ej. redis://...:port), forzar DB 1
    # para no mezclar con la DB de caché/rate limit (que usará DB 0 por defecto)
    if "?" in redis_url:
        base, query = redis_url.split("?", 1)
        redis_url = f"{base}/1?{query}"
    else:
        redis_url = f"{redis_url}/1"

# Inicializar Celery
celery_app = Celery(
    "geofeedback_tasks",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks.worker"]  # Importar el módulo del worker para registrar las tareas
)

# Configuraciones adicionales
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,          # Permite al frontend saber si la tarea inició
    task_time_limit=300,             # Límite de tiempo estricto: 5 minutos
    task_soft_time_limit=240,        # Límite suave: 4 minutos (emite excepción)
)
