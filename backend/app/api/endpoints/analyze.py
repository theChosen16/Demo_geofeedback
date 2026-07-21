import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from celery.result import AsyncResult
from sqlmodel import Session, select
import datetime

from app.core.auth import get_optional_user
from app.core.security import verify_rate_limit, analysis_limiter, status_limiter, redis_client
from app.db.session import get_session
from app.db.models import User, UserAnalysis
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


def build_analysis_cache_key(approach: str, radius: int, lat: float, lng: float, start_date: str = None, end_date: str = None) -> str:
    """
    Genera la clave de cache para un análisis dado.

    Se redondea lat/lng a 4 decimales (~11m de precisión) para que selecciones
    casi idénticas del mapa (mismo punto, distinto redondeo de float) compartan
    cache. Sentinel-2 revisita cada ~5 días, así que un resultado sigue siendo
    válido durante todo el TTL de la cache. Incluye ANALYSIS_LOGIC_VERSION para que
    un cambio en las fórmulas/umbrales de worker.py invalide la cache de inmediato en
    vez de esperar hasta 12h a que expire por TTL (ver comentario junto a esa constante).
    """
    key = f"analysis:{ANALYSIS_LOGIC_VERSION}:{approach}:{radius}:{round(lat, 4)}:{round(lng, 4)}"
    if start_date and end_date:
        key += f":{start_date}:{end_date}"
    return key


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
    start_date: Optional[str] = Field(None, description="Fecha de inicio (YYYY-MM-DD) para análisis histórico")
    end_date: Optional[str] = Field(None, description="Fecha de término (YYYY-MM-DD) para análisis histórico")


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

    cache_key = build_analysis_cache_key(
        data.approach, data.radius, data.lat, data.lng, data.start_date, data.end_date
    )

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
        user_id=user.id if user else None,
        start_date=data.start_date,
        end_date=data.end_date
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


@router.get("/analyze/export/{task_id}", response_class=HTMLResponse)
def export_analysis_pdf(task_id: str, session: Session = Depends(get_session)):
    """
    Genera una página HTML optimizada para impresión (con window.print()) que
    sirve como reporte formal de exportación del análisis satelital.
    """
    # Intentar buscar el análisis en la base de datos
    analysis = session.exec(
        select(UserAnalysis).where(UserAnalysis.task_id == task_id)
    ).first()

    if not analysis:
        # Fallback: si no está en la base de datos, intentar leer de Celery/Redis
        result = AsyncResult(task_id, app=celery_app)
        if result.state == "SUCCESS":
            res_data = result.result
            
            # Armar un objeto temporal
            class TempAnalysis:
                pass
            analysis = TempAnalysis()
            analysis.task_id = task_id
            analysis.location_name = "Análisis Temporal"
            meta = res_data.get("meta", {})
            analysis.lat = 0.0
            analysis.lng = 0.0
            analysis.radius = meta.get("buffer_radius_m", 1000)
            analysis.approach = res_data.get("approach", "desconocido")
            analysis.indices = res_data.get("data", {})
            analysis.chart_data = None
            analysis.map_layer_url = (res_data.get("map_layer") or {}).get("url")
            analysis.image_date = meta.get("date")
            analysis.interpretation = "Interpretación no disponible en este reporte rápido. Inicia sesión para guardar tu historial completo con GeoBot."
        else:
            raise HTTPException(
                status_code=404,
                detail="Análisis no encontrado o no ha sido completado todavía."
            )

    # Formatear el enfoque para presentación
    approach_titles = {
        "mining": "Gestión de Relaves y Minería",
        "agriculture": "Agricultura de Precisión",
        "energy": "Energía y Viabilidad Solar",
        "real-estate": "Desarrollo Inmobiliario y Plusvalía",
        "flood-risk": "Riesgo de Inundación",
        "water-management": "Gestión Hídrica y Sequía",
        "environmental": "Conservación y Ecología",
        "land-planning": "Planificación Territorial",
        "fire-risk": "Riesgo de Incendio Forestal"
    }
    approach_title = approach_titles.get(analysis.approach, analysis.approach.capitalize())

    # Formatear los índices para presentación
    indices_rows = ""
    if analysis.indices:
        for key, val in analysis.indices.items():
            if isinstance(val, (int, float)):
                indices_rows += f"""
                <tr>
                    <td style="padding: 12px; border: 1px solid #e2e8f0; font-weight: bold; color: #334155;">{key}</td>
                    <td style="padding: 12px; border: 1px solid #e2e8f0; font-family: monospace; font-size: 15px;">{val:.4f}</td>
                </tr>
                """
    
    chart_section = ""
    if analysis.chart_data:
        chart_rows = ""
        for pt in analysis.chart_data:
            chart_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #e2e8f0;">{pt.get('date')}</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-family: monospace;">{pt.get('ndvi', 0):.4f}</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-family: monospace;">{pt.get('ndwi', 0):.4f}</td>
                <td style="padding: 8px; border: 1px solid #e2e8f0; font-family: monospace;">{pt.get('ndmi', 0):.4f}</td>
            </tr>
            """
        chart_section = f"""
        <div class="section-title">Evolución Histórica (Pulso Territorial)</div>
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px;">
            <thead>
                <tr style="background-color: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                    <th style="padding: 8px; border: 1px solid #e2e8f0; text-align: left; color: #475569;">Fecha</th>
                    <th style="padding: 8px; border: 1px solid #e2e8f0; text-align: left; color: #475569;">NDVI (Vegetación)</th>
                    <th style="padding: 8px; border: 1px solid #e2e8f0; text-align: left; color: #475569;">NDWI (Agua)</th>
                    <th style="padding: 8px; border: 1px solid #e2e8f0; text-align: left; color: #475569;">NDMI (Humedad)</th>
                </tr>
            </thead>
            <tbody>
                {chart_rows}
            </tbody>
        </table>
        """

    interpretation_html = ""
    if analysis.interpretation:
        interpretation_html = f"""
        <div class="section-title">Interpretación de GeoBot</div>
        <div class="geobot-text">
            {analysis.interpretation.replace(chr(10), '<br>')}
        </div>
        """

    map_html = ""
    if analysis.map_layer_url:
        map_html = f"""
        <div class="section-title">Capa Satelital</div>
        <p style="font-size: 14px; margin-top: 10px;">
            Sentinel-2 GEE MSI (Level-2A) del <strong>{analysis.image_date or 'Fecha de captura desconocida'}</strong>.<br>
            <span style="font-size: 12px; color: #64748b;">ID de la Tarea: {analysis.task_id}</span>
        </p>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte Territorial - GeoFeedback</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            @media print {{
                body {{
                    background: white !important;
                    color: black !important;
                    padding: 0 !important;
                }}
                .no-print {{
                    display: none !important;
                }}
            }}
            body {{
                font-family: 'Outfit', sans-serif;
                max-width: 800px;
                margin: auto;
                padding: 40px 20px;
                background-color: #fafafa;
                color: #2d3748;
            }}
            .report-card {{
                background-color: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
                border: 1px solid #e2e8f0;
            }}
            .header {{
                border-bottom: 4px solid #0f172a;
                padding-bottom: 20px;
                margin-bottom: 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .logo-title {{
                font-size: 26px;
                font-weight: 700;
                color: #0f172a;
            }}
            .logo-sub {{
                font-size: 14px;
                color: #64748b;
                margin-top: 2px;
            }}
            .meta-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}
            .meta-table td {{
                padding: 10px;
                border: 1px solid #e2e8f0;
                font-size: 14px;
            }}
            .meta-label {{
                font-weight: 600;
                color: #475569;
                background-color: #f8fafc;
                width: 30%;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: 600;
                margin-top: 35px;
                margin-bottom: 12px;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 6px;
                color: #0f172a;
            }}
            .geobot-text {{
                background-color: #f8fafc;
                padding: 20px;
                border-left: 5px solid #0f172a;
                border-radius: 4px;
                line-height: 1.6;
                font-size: 15px;
                color: #334155;
            }}
            .print-btn-container {{
                text-align: right;
                margin-bottom: 20px;
            }}
            .btn-print {{
                background-color: #0f172a;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 15px;
                font-weight: 600;
                border-radius: 8px;
                cursor: pointer;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
                transition: background-color 0.2s;
            }}
            .btn-print:hover {{
                background-color: #1e293b;
            }}
        </style>
    </head>
    <body>
        <div class="print-btn-container no-print">
            <button onclick="window.print()" class="btn-print">💾 Guardar como PDF / Imprimir</button>
        </div>
        <div class="report-card">
            <div class="header">
                <div>
                    <div class="logo-title">GeoFeedback</div>
                    <div class="logo-sub">Inteligencia y Diagnóstico Territorial Satelital</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 600; font-size: 14px;">Reporte Ejecutivo</div>
                    <div style="font-size: 12px; color: #64748b;">Generado: {datetime.datetime.now().strftime('%d-%m-%Y')}</div>
                </div>
            </div>
            
            <table class="meta-table">
                <tr>
                    <td class="meta-label">Ubicación</td>
                    <td>{analysis.location_name}</td>
                </tr>
                <tr>
                    <td class="meta-label">Coordenadas</td>
                    <td>{analysis.lat:.6f}, {analysis.lng:.6f}</td>
                </tr>
                <tr>
                    <td class="meta-label">Radio de Análisis</td>
                    <td>{analysis.radius} metros</td>
                </tr>
                <tr>
                    <td class="meta-label">Enfoque Metodológico</td>
                    <td>{approach_title}</td>
                </tr>
            </table>

            <div class="section-title">Valores Promedio de Índices Espectrales</div>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; font-size: 13px;">
                        <th style="padding: 12px; border: 1px solid #e2e8f0; text-align: left;">Índice Espectral</th>
                        <th style="padding: 12px; border: 1px solid #e2e8f0; text-align: left;">Valor Medio de la Zona</th>
                    </tr>
                </thead>
                <tbody>
                    {indices_rows or '<tr><td colspan="2" style="padding: 12px; text-align: center;">No hay índices calculados</td></tr>'}
                </tbody>
            </table>

            {interpretation_html}

            {chart_section}

            {map_html}
        </div>
        <script>
            window.onload = function() {{
                setTimeout(function() {{
                    window.print();
                }}, 500);
            }};
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
