from fastapi import APIRouter, Request, Depends, HTTPException, status
from pydantic import BaseModel, Field
from celery.result import AsyncResult

from app.core.security import verify_rate_limit, analysis_limiter
from app.tasks.worker import process_gee_analysis
from app.tasks.celery_app import celery_app

router = APIRouter()

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
async def trigger_analysis(data: AnalyzeRequest):
    """
    Inicia un análisis satelital con Google Earth Engine.
    El procesamiento se ejecuta de forma asíncrona en Celery.
    Retorna el ID de la tarea para consultar el estado.
    """
    if data.lat == 0 and data.lng == 0:
        raise HTTPException(status_code=400, detail="Coordenadas requeridas")
        
    if data.approach not in VALID_APPROACHES:
        raise HTTPException(status_code=400, detail="Enfoque no válido")

    # Encolar la tarea en Celery
    task = process_gee_analysis.delay(
        lat=data.lat,
        lng=data.lng,
        radius=data.radius,
        approach=data.approach,
        location_name=data.location
    )

    return {
        "status": "queued",
        "task_id": task.id,
        "message": "Análisis encolado correctamente. Consulta el estado utilizando el ID de tarea."
    }


@router.get("/analyze/status/{task_id}")
async def get_analysis_status(task_id: str):
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
