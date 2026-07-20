import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, status
from pydantic import BaseModel, Field
from celery.result import AsyncResult

from app.core.auth import get_optional_user
from app.core.security import verify_rate_limit, analysis_limiter, status_limiter, redis_client
from app.db.models import User
from app.tasks.worker import (
    process_gee_analysis,
    process_timeseries,
    persist_user_analysis,
    ANALYSIS_LOGIC_VERSION,
    TIMESERIES_LOGIC_VERSION,
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter()


def build_analysis_cache_key(approach: str, radius: int, lat: float, lng: float) -> str:
    """
    Genera la clave de cache para un análisis dado.

    Se redondea lat/lng a 4 decimales (~11m de precisión) para que selecciones
    casi idénticas del mapa (mismo punto, distinto redondeo de float) compartan
    cache. Sentinel-2 revisita cada ~5 días, así que un resultado sigue siendo
    válido durante todo el TTL de la cache. Incluye ANALYSIS_LOGIC_VERSION para que
    un cambio en las fórmulas/umbrales de worker.py invalide la cache de inmediato en
    vez de esperar hasta 12h a que expire por TTL (ver comentario junto a esa constante).
    """
    return f"analysis:{ANALYSIS_LOGIC_VERSION}:{approach}:{radius}:{round(lat, 4)}:{round(lng, 4)}"


def build_timeseries_cache_key(radius: int, lat: float, lng: float) -> str:
    """
    Clave de cache para la serie temporal del Pulso Territorial. A diferencia de
    build_analysis_cache_key, NO incluye el "approach": los mismos NDVI/NDWI/NDMI se
    calculan igual sin importar qué enfoque haya elegido el usuario, así que dos
    análisis de la misma ubicación+radio con distinto enfoque comparten esta cache.
    """
    return f"timeseries:{TIMESERIES_LOGIC_VERSION}:{radius}:{round(lat, 4)}:{round(lng, 4)}"


def resolve_timeseries(radius: int, lat: float, lng: float) -> tuple:
    """
    Devuelve (timeseries_task_id, timeseries_result): si hay cache-hit, task_id es None y
    result trae el chart_data directo (sin encolar nada). Si no, se encola process_timeseries
    y se devuelve su task_id para que el frontend lo sondee con el mismo endpoint de status
    que usa el análisis principal (GET /analyze/status/{task_id}).
    """
    cache_key = build_timeseries_cache_key(radius, lat, lng)

    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return None, json.loads(cached)
        except Exception as e:
            logger.warning(f"Error leyendo cache de serie temporal ({cache_key}): {e}")

    task = process_timeseries.delay(lat=lat, lng=lng, radius=radius, cache_key=cache_key)
    return task.id, None

# Enfoques válidos (whitelist)
VALID_APPROACHES = {
    'mining', 'agriculture', 'energy', 'real-estate',
    'flood-risk', 'water-management', 'environmental',
    'land-planning', 'fire-risk'
}

class AnalyzeRequest(BaseModel):
    lat: float = Field(..., description="Latitud (-90 a 90)", ge=-90, le=90)
    lng: float = Field(..., description="Longitud (-180 a 180)", ge=-180, le=180)
    radius: int = Field(1000, description="Radio del buffer en metros (100 a 50000)", ge=100, le=50000)
    approach: str = Field(..., description="Enfoque de análisis satelital")
    location: str = Field("Unknown", description="Nombre legible del lugar seleccionado", max_length=200)


@router.post("/analyze", dependencies=[Depends(verify_rate_limit(analysis_limiter))])
def trigger_analysis(data: AnalyzeRequest, user: Optional[User] = Depends(get_optional_user)):
    """
    Inicia un análisis satelital con Google Earth Engine.
    El procesamiento se ejecuta de forma asíncrona en Celery.
    Retorna el ID de la tarea para consultar el estado.
    Si el usuario está logeado, el resultado también se guarda en su historial personal.
    """
    if data.lat == 0 and data.lng == 0:
        raise HTTPException(status_code=400, detail="Coordenadas requeridas")

    if data.approach not in VALID_APPROACHES:
        raise HTTPException(status_code=400, detail="Enfoque no válido")

    cache_key = build_analysis_cache_key(data.approach, data.radius, data.lat, data.lng)

    # El Pulso Territorial (evolución mensual de índices) es contenido premium para usuarios
    # logeados: se encola/cachea en paralelo al análisis principal para no retrasarlo.
    timeseries_task_id, timeseries_result = (
        resolve_timeseries(data.radius, data.lat, data.lng) if user else (None, None)
    )

    # Cache hit: devolver el resultado ya calculado sin encolar ni esperar a GEE.
    # Sentinel-2 solo revisita cada ~5 días, así que reanalizar el mismo punto+enfoque
    # dentro del TTL siempre da el mismo resultado.
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                cached_result = json.loads(cached)
                cached_task_id = f"cached-{uuid.uuid4()}"
                # El worker nunca corre en un cache-hit, así que si hay un usuario logeado
                # hay que guardar la copia de su historial personal aquí mismo.
                if user:
                    persist_user_analysis(
                        user.id, cached_task_id, data.lat, data.lng, data.radius,
                        data.approach, data.location, cached_result
                    )
                return {
                    "status": "complete",
                    "task_id": cached_task_id,
                    "result": cached_result,
                    "timeseries_task_id": timeseries_task_id,
                    "timeseries_result": timeseries_result,
                    "message": "Resultado obtenido desde cache (análisis reciente de esta zona)."
                }
        except Exception as e:
            logger.warning(f"Error leyendo cache de análisis ({cache_key}): {e}")

    # Encolar la tarea en Celery
    task = process_gee_analysis.delay(
        lat=data.lat,
        lng=data.lng,
        radius=data.radius,
        approach=data.approach,
        location_name=data.location,
        cache_key=cache_key,
        user_id=user.id if user else None
    )

    return {
        "status": "queued",
        "task_id": task.id,
        "timeseries_task_id": timeseries_task_id,
        "timeseries_result": timeseries_result,
        "message": "Análisis encolado correctamente. Consulta el estado utilizando el ID de tarea."
    }


@router.get("/analyze/status/{task_id}", dependencies=[Depends(verify_rate_limit(status_limiter))])
def get_analysis_status(task_id: str):
    """
    Consulta el estado de una tarea de análisis satelital encolada.
    """
    # Consultar el estado de la tarea en Redis
    result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "state": result.state
    }
    
    if result.state == "SUCCESS":
        response["status"] = "success"
        response["result"] = result.result
    elif result.state == "FAILURE":
        response["status"] = "failed"
        response["error"] = str(result.info or "Error interno en el worker.")
    elif result.state == "STARTED":
        response["status"] = "running"
        response["message"] = "El análisis está siendo procesado por Google Earth Engine..."
    else:
        response["status"] = "queued"
        response["message"] = "La tarea está encolada esperando un worker disponible..."
        
    return response
