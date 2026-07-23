import json
import math
import time
import datetime
import logging
import concurrent.futures
import ee
from celery.signals import worker_process_init
from sqlmodel import Session
from geoalchemy2.elements import WKTElement

from app.tasks.celery_app import celery_app
from app.core.gee import init_gee
from app.core.security import log_event, redis_client
from app.db.session import engine
from app.db.models import ApiUsageLog, UserAnalysis

logger = logging.getLogger(__name__)

# Executor persistente para llamadas a GEE con timeout wall-clock
_GEE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10)

# TTL de la cache de resultados de análisis: Sentinel-2 revisita cada ~5 días,
# así que un resultado sigue siendo representativo durante medio día.
ANALYSIS_CACHE_TTL_SECONDS = 12 * 60 * 60# Incluida en la cache key (ver build_analysis_cache_key en analyze.py). Incrementar esta
# versión cuando cambie la lógica de negocio que produce el resultado cacheado (fórmulas,
# umbrales, paleta de cada enfoque más abajo) para invalidar de inmediato lo ya cacheado en
# vez de esperar hasta 12h a que expire por TTL y quedar sirviendo resultados con lógica vieja.
ANALYSIS_LOGIC_VERSION = "v3"

# Misma idea que ANALYSIS_LOGIC_VERSION pero para la cache de process_timeseries (ver
# build_timeseries_cache_key en analyze.py).
TIMESERIES_LOGIC_VERSION = "v2"


def cache_analysis_result(cache_key: str, result: dict) -> None:
    """Guarda el resultado exitoso de un análisis en Redis (best-effort, nunca falla la tarea)."""
    if not redis_client or not cache_key:
        return
    try:
        redis_client.setex(cache_key, ANALYSIS_CACHE_TTL_SECONDS, json.dumps(result))
    except Exception as e:
        logger.warning(f"Error escribiendo cache de análisis ({cache_key}): {e}")


def persist_user_analysis(
    user_id: int,
    task_id: str,
    lat: float,
    lng: float,
    radius: int,
    approach: str,
    location_name: str,
    analysis_result: dict,
) -> None:
    """
    Guarda una copia de un análisis exitoso en el historial del usuario logeado
    (tabla user_analyses), tanto si vino de un cálculo GEE fresco (process_gee_analysis)
    como de un cache-hit (POST /analyze responde sin encolar tarea). Best-effort: nunca
    debe romper el flujo principal de análisis si la escritura falla.
    """
    if not user_id:
        return
    try:
        with Session(engine) as session:
            row = UserAnalysis(
                user_id=user_id,
                task_id=task_id,
                location_name=location_name[:255],
                lat=lat,
                lng=lng,
                radius=radius,
                approach=approach,
                coordinates=WKTElement(f"POINT({lng} {lat})", srid=4326),
                indices=analysis_result.get("data"),
                chart_data=analysis_result.get("chart_data"),
                map_layer_url=(analysis_result.get("map_layer") or {}).get("url"),
                image_date=(analysis_result.get("meta") or {}).get("date"),
            )
            session.add(row)
            session.commit()
    except Exception as e:
        logger.error(f"Error guardando historial de usuario (task {task_id}, user {user_id}): {e}")


def submit_gee_getinfo(ee_object):
    """Encola una llamada getInfo() de Earth Engine en el executor sin bloquear el hilo actual."""
    return _GEE_EXECUTOR.submit(ee_object.getInfo)


def resolve_with_timeout(future, timeout=30, op_name="GEE operation"):
    """Espera el resultado de un Future ya encolado (getInfo, getMapId, etc.) con límite de tiempo wall-clock."""
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError as e:
        logger.error(f"Operación GEE ({op_name}) excedió el timeout de {timeout}s")
        raise TimeoutError(f"Google Earth Engine operation '{op_name}' timed out after {timeout} seconds") from e


def get_info_with_timeout(ee_object, timeout=30):
    """Ejecuta getInfo() de Earth Engine en un hilo con límite de tiempo wall-clock."""
    return resolve_with_timeout(submit_gee_getinfo(ee_object), timeout=timeout, op_name="getInfo")

# Registrar la inicialización de Earth Engine al iniciar el worker process de Celery.
@worker_process_init.connect
def configure_gee_workers(*args, **kwargs):
    logger.info("Worker process inicializado: conectando a Google Earth Engine...")
    success = init_gee()
    if success:
        logger.info("Conexión a GEE exitosa en el worker.")
    else:
        logger.error("Falla crítica: No se pudo conectar a GEE en el worker.")


def get_sentinel2_image(roi, start_date_str=None, end_date_str=None):
    """Obtiene la imagen Sentinel-2 más reciente y libre de nubes para la ROI."""
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d") + datetime.timedelta(days=1)
        except ValueError:
            end_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    else:
        end_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        except ValueError:
            start_date = end_date - datetime.timedelta(days=180)
    else:
        start_date = end_date - datetime.timedelta(days=180) # 6 meses
    
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
            .sort('system:time_start', False))
            
    return col.first()


def calculate_indices(image):
    """Calcula índices espectrales avanzados para análisis territoriales."""
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI') # McFeeters
    mndwi = image.normalizedDifference(['B3', 'B11']).rename('MNDWI') # Xu Modified NDWI
    ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI')
    nbr = image.normalizedDifference(['B8', 'B12']).rename('NBR') # Normalized Burn Ratio
    ndbi = image.normalizedDifference(['B11', 'B8']).rename('NDBI') # Normalized Difference Built-up Index
    
    # SAVI: Soil Adjusted Vegetation Index (L = 0.5)
    savi = image.expression(
        '((NIR - RED) / (NIR + RED + 0.5)) * 1.5',
        {'NIR': image.select('B8'), 'RED': image.select('B4')}
    ).rename('SAVI')
    
    # EVI: Enhanced Vegetation Index
    evi = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6.0 * RED - 7.5 * BLUE + 1.0))',
        {'NIR': image.select('B8'), 'RED': image.select('B4'), 'BLUE': image.select('B2')}
    ).rename('EVI')
    
    # BSI: Bare Soil Index
    bsi = image.expression(
        '((SWIR1 + RED) - (NIR + BLUE)) / ((SWIR1 + RED) + (NIR + BLUE))',
        {
            'SWIR1': image.select('B11'),
            'RED': image.select('B4'),
            'NIR': image.select('B8'),
            'BLUE': image.select('B2')
        }
    ).rename('BSI')
    
    # NDRE: Normalized Difference Red Edge
    ndre = image.normalizedDifference(['B8', 'B5']).rename('NDRE')

    return image.addBands([ndvi, ndwi, mndwi, ndmi, nbr, ndbi, savi, evi, bsi, ndre])


@celery_app.task(name="app.tasks.worker.process_gee_analysis", bind=True)
def process_gee_analysis(
    self, lat: float, lng: float, radius: int, approach: str, location_name: str,
    cache_key: str = None, user_id: int = None, start_date: str = None, end_date: str = None
):
    """
    Tarea asíncrona de Celery para realizar análisis territorial usando Google Earth Engine.
    Guarda los logs en la base de datos de PostGIS e informa el estado.
    Si `cache_key` viene dado, el resultado exitoso se guarda en Redis con ese key
    para que futuras solicitudes idénticas se respondan sin volver a golpear GEE.
    Si `user_id` viene dado (usuario logeado), el resultado exitoso también se guarda
    en su historial personal (tabla user_analyses).
    """
    logger.info(f"Iniciando tarea {self.request.id}: {approach} en ({lat}, {lng}), radio={radius}m")
    
    # Asegurar que Earth Engine esté inicializado
    try:
        ee.Initialize()
    except Exception:
        logger.warning("GEE no inicializado en el hilo actual. Reintentando...")
        init_gee()

    timings = {}
    t_task_start = time.monotonic()

    try:
        point = ee.Geometry.Point([lng, lat])
        roi = point.buffer(radius)

        # Datos Base (Demografía / Topografía DEM GLO-30)
        glo30_col = ee.ImageCollection('COPERNICUS/DEM/GLO30_2024_1')
        elevation = glo30_col.select('DEM').mosaic().setDefaultProjection(glo30_col.first().projection()).rename('elevation')
        slope = ee.Terrain.slope(elevation).rename('slope')
        aspect = ee.Terrain.aspect(elevation).rename('aspect')

        s2_image = get_sentinel2_image(roi, start_date_str=start_date, end_date_str=end_date)
        s2_indices = calculate_indices(s2_image)
        mean_reducer = ee.Reducer.mean()
        results = {}

        # Determinar la imagen y escala para la reducción de región según el enfoque
        stats_image = None
        scale = 20

        if approach == 'mining':
            stats_image = s2_indices.select(['NDVI', 'NDWI', 'BSI', 'NDBI']).addBands([slope])
            scale = 20
        elif approach == 'agriculture':
            stats_image = s2_indices.select(['NDVI', 'NDMI', 'SAVI', 'NDRE', 'BSI'])
            scale = 20
        elif approach == 'energy':
            stats_image = elevation.addBands([slope, aspect]).addBands(s2_indices.select(['NDBI']))
            scale = 30
        elif approach == 'real-estate':
            stats_image = s2_indices.select(['NDBI', 'MNDWI']).addBands([elevation, slope])
            scale = 20
        elif approach == 'flood-risk':
            stats_image = s2_indices.select(['MNDWI', 'NDWI', 'NDBI']).addBands([elevation, slope])
            scale = 30
        elif approach == 'water-management':
            stats_image = s2_indices.select(['NDWI', 'MNDWI', 'NDMI', 'NDVI'])
            scale = 20
        elif approach == 'environmental':
            stats_image = s2_indices.select(['EVI', 'NDVI', 'NDMI', 'BSI'])
            scale = 20
        elif approach == 'land-planning':
            stats_image = s2_indices.select(['NDBI', 'BSI', 'NDVI']).addBands([elevation, slope])
            scale = 30
        elif approach == 'fire-risk':
            stats_image = s2_indices.select(['NBR', 'NDMI', 'NDVI']).addBands([slope])
            scale = 20

        # Determinar la imagen y parámetros de Visualización (Map ID) según el enfoque - Recortado a la ROI
        vis_params = {}
        vis_image = None

        if approach == 'mining':
            vis_image = s2_indices.select('BSI').clip(roi)
            vis_params = {'min': -0.3, 'max': 0.5, 'palette': ['#16a34a', '#eab308', '#d97706', '#dc2626']}
        elif approach == 'agriculture':
            vis_image = s2_indices.select('NDVI').clip(roi)
            vis_params = {'min': -0.2, 'max': 0.8, 'palette': ['#dc2626', '#eab308', '#22c55e', '#15803d']}
        elif approach == 'energy':
            vis_image = slope.clip(roi)
            vis_params = {'min': 0, 'max': 45, 'palette': ['#22c55e', '#eab308', '#dc2626']}
        elif approach == 'real-estate':
            vis_image = s2_indices.select('NDBI').clip(roi)
            vis_params = {'min': -0.5, 'max': 0.5, 'palette': ['#3b82f6', '#f8fafc', '#f97316', '#dc2626']}
        elif approach == 'fire-risk':
            vis_image = s2_indices.select('NBR').clip(roi)
            vis_params = {'min': -0.5, 'max': 0.8, 'palette': ['#dc2626', '#ea580c', '#eab308', '#22c55e']}
        elif approach == 'flood-risk':
            vis_image = s2_indices.select('MNDWI').clip(roi)
            vis_params = {'min': -0.5, 'max': 0.5, 'palette': ['#f8fafc', '#38bdf8', '#1d4ed8']}
        elif approach == 'water-management':
            vis_image = s2_indices.select('NDWI').clip(roi)
            vis_params = {'min': -0.5, 'max': 0.5, 'palette': ['#ffffff', '#0284c7', '#0369a1', '#0c4a6e']}
        elif approach == 'environmental':
            vis_image = s2_indices.select('EVI').clip(roi)
            vis_params = {'min': -0.2, 'max': 0.8, 'palette': ['#a16207', '#eab308', '#22c55e', '#14532d']}
        elif approach == 'land-planning':
            vis_image = s2_indices.select('NDBI').clip(roi)
            vis_params = {'min': -0.5, 'max': 0.5, 'palette': ['#16a34a', '#eab308', '#9333ea']}
        else:
            vis_image = s2_indices.select('NDVI').clip(roi)
            vis_params = {'min': 0, 'max': 1, 'palette': ['white', 'green']}

        # Encolar las 3 operaciones de GEE en paralelo
        t_parallel = time.monotonic()

        stats_future = (
            submit_gee_getinfo(
                stats_image.reduceRegion(
                    reducer=mean_reducer,
                    geometry=roi,
                    scale=scale,
                    maxPixels=1e9
                )
            )
            if stats_image is not None
            else None
        )

        date_future = submit_gee_getinfo(ee.Date(s2_image.get('system:time_start')).format('YYYY-MM-dd'))
        map_future = _GEE_EXECUTOR.submit(vis_image.getMapId, vis_params)

        # Resolver estadísticas de reducción espectral
        if stats_future is not None:
            try:
                stats = resolve_with_timeout(stats_future, timeout=30, op_name="reduceRegion")
            except Exception as e:
                if "empty" in str(e).lower() or "collection" in str(e).lower():
                    logger.warning(f"No hay imágenes Sentinel-2 disponibles para la ROI: {e}")
                    return {
                        "status": "warning",
                        "message": "No se encontraron imágenes satelitales libres de nubes en los últimos 6 meses para esta ubicación.",
                        "retry": False
                    }
                raise e
        else:
            stats = {}
        timings['gee_stats_s'] = round(time.monotonic() - t_parallel, 2)

        # Resolver fecha de la imagen
        try:
            image_date = resolve_with_timeout(date_future, timeout=15, op_name="image date")
        except Exception as e:
            logger.error(f"Error getting image date from GEE: {e}")
            image_date = "Fecha de captura no disponible"

        # Resolver capa de mapa
        map_id_dict = resolve_with_timeout(map_future, timeout=30, op_name="getMapId")
        tile_url = map_id_dict['tile_fetcher'].url_format
        timings['gee_total_parallel_s'] = round(time.monotonic() - t_parallel, 2)

        timings['gee_parallel_wall_s'] = round(time.monotonic() - t_parallel, 2)

        # Mapear resultados según el enfoque e índices correspondientes
        if approach == 'mining':
            results = {
                "Vegetación Circundante (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Índice de Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Exposición Suelo Desnudo (BSI)": f"{stats.get('BSI', 0):.2f}",
                "Huella Suelo Construido (NDBI)": f"{stats.get('NDBI', 0):.2f}",
                "Pendiente Promedio (°)": f"{stats.get('slope', 0):.1f}"
            }
        elif approach == 'agriculture':
            results = {
                "Vigor Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Humedad Canopia (NDMI)": f"{stats.get('NDMI', 0):.2f}",
                "Ajuste Suelo (SAVI)": f"{stats.get('SAVI', 0):.2f}",
                "Clorofila / Borde Rojo (NDRE)": f"{stats.get('NDRE', 0):.2f}",
                "Exposición Suelo (BSI)": f"{stats.get('BSI', 0):.2f}",
                "Estado Cultivos": "Excelente" if stats.get('NDVI', 0) > 0.6 else "Saludable" if stats.get('NDVI', 0) > 0.35 else "Atención Requerida"
            }
        elif approach == 'energy':
            avg_slope = stats.get('slope', 0)
            avg_aspect = stats.get('aspect', 0)
            results = {
                "Elevación Promedio (msnm)": f"{stats.get('elevation', 0):.0f}",
                "Pendiente Promedio (°)": f"{avg_slope:.1f}",
                "Orientación Sol/Ladera (°)": f"{avg_aspect:.0f}°",
                "Huella Superficial (NDBI)": f"{stats.get('NDBI', 0):.2f}",
                "Aptitud Solar (Topografía)": "Alta" if avg_slope < 10 else "Media" if avg_slope < 20 else "Baja"
            }
        elif approach == 'real-estate':
            avg_slope = stats.get('slope', 0)
            results = {
                "Huella Construida (NDBI)": f"{stats.get('NDBI', 0):.2f}",
                "Pendiente Terreno (°)": f"{avg_slope:.1f}",
                "Elevación Media (msnm)": f"{stats.get('elevation', 0):.0f}",
                "Índice Agua Urbano (MNDWI)": f"{stats.get('MNDWI', 0):.2f}",
                "Constructibilidad": "Óptima" if avg_slope < 5 else "Buena" if avg_slope < 15 else "Compleja"
            }
        elif approach == 'fire-risk':
            nbr = stats.get('NBR', 0)
            ndmi = stats.get('NDMI', 0)
            ndvi = stats.get('NDVI', 0)
            avg_slope = stats.get('slope', 0)
            
            # Cálculo de índice de riesgo compuesto de incendio (0-100)
            risk_vegetation = max(0, (0.6 - ndvi) / 0.6 * 30)
            risk_moisture = max(0, (0.5 - ndmi) / 0.5 * 40)
            risk_burn = max(0, (0.4 - nbr) / 0.4 * 20)
            risk_slope = min(avg_slope / 45 * 10, 10)
            
            risk_index = min(int(risk_vegetation + risk_moisture + risk_burn + risk_slope), 100)
            
            if risk_index < 20:
                risk_level = "Bajo"
            elif risk_index < 40:
                risk_level = "Moderado"
            elif risk_index < 60:
                risk_level = "Alto"
            elif risk_index < 80:
                risk_level = "Muy Alto"
            else:
                risk_level = "Extremo"
            
            results = {
                "Índice de Riesgo Incendio": f"{risk_index}/100",
                "Nivel de Riesgo": risk_level,
                "Severidad/Quema (NBR)": f"{nbr:.2f}",
                "Humedad Vegetal (NDMI)": f"{ndmi:.2f}",
                "Vegetación (NDVI)": f"{ndvi:.2f}",
                "Pendiente (°)": f"{avg_slope:.1f}"
            }
        elif approach == 'flood-risk':
            results = {
                "Agua Modificado Urbano (MNDWI)": f"{stats.get('MNDWI', 0):.2f}",
                "Cuerpos de Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Huella Suelo Construido (NDBI)": f"{stats.get('NDBI', 0):.2f}",
                "Elevación Media (msnm)": f"{stats.get('elevation', 0):.0f}",
                "Pendiente Terreno (°)": f"{stats.get('slope', 0):.1f}"
            }
        elif approach == 'water-management':
            results = {
                "Agua Superficial (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Agua Urbano/Modificado (MNDWI)": f"{stats.get('MNDWI', 0):.2f}",
                "Humedad Suelo/Veg (NDMI)": f"{stats.get('NDMI', 0):.2f}",
                "Cobertura Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}"
            }
        elif approach == 'environmental':
            results = {
                "Índice Vegetación Mejorado (EVI)": f"{stats.get('EVI', 0):.2f}",
                "Cobertura Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Estrés Hídrico (NDMI)": f"{stats.get('NDMI', 0):.2f}",
                "Exposición Suelo (BSI)": f"{stats.get('BSI', 0):.2f}"
            }
        elif approach == 'land-planning':
            results = {
                "Pendiente Promedio (°)": f"{stats.get('slope', 0):.1f}",
                "Suelo Construido (NDBI)": f"{stats.get('NDBI', 0):.2f}",
                "Suelo Desnudo (BSI)": f"{stats.get('BSI', 0):.2f}",
                "Cobertura Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Elevación Media (msnm)": f"{stats.get('elevation', 0):.0f}"
            }

        area_m2 = int(math.pi * radius * radius)

        timings['total_s'] = round(time.monotonic() - t_task_start, 2)
        log_event(
            'analysis_timing',
            task_id=self.request.id,
            approach=approach,
            **timings
        )

        # Guardar log en la base de datos de PostGIS
        with Session(engine) as session:
            log = ApiUsageLog(
                endpoint="/api/v1/analyze",
                location_name=location_name[:255],
                coordinates=WKTElement(f"POINT({lng} {lat})", srid=4326),
                approach=approach,
                status="success"
            )
            session.add(log)
            session.commit()

        # Resultado que el API de FastAPI leerá al completar la tarea
        analysis_result = {
            "status": "success",
            "approach": approach,
            "data": results,
            "area_m2": area_m2,
            "map_layer": {
                "url": tile_url,
                "attribution": "Google Earth Engine"
            },
            "meta": {
                "satellite": "Sentinel-2 MSI (Level-2A)",
                "terrain": "Copernicus DEM GLO-30",
                "date": image_date,
                "buffer_radius_m": radius,
                "timings": timings
            }
        }

        cache_analysis_result(cache_key, analysis_result)
        persist_user_analysis(user_id, self.request.id, lat, lng, radius, approach, location_name, analysis_result)

        return analysis_result

    except Exception as e:
        logger.error(f"Error en análisis GEE asíncrono: {e}", exc_info=True)
        # Registrar fallo en la BD
        try:
            with Session(engine) as session:
                log = ApiUsageLog(
                    endpoint="/api/v1/analyze",
                    location_name=location_name[:255],
                    coordinates=WKTElement(f"POINT({lng} {lat})", srid=4326),
                    approach=approach,
                    status="failed"
                )
                session.add(log)
                session.commit()
        except Exception as db_err:
            logger.error(f"Error logging failed task to database: {db_err}")

        # Lanzar excepción para marcar la tarea de Celery como fallida
        raise e


@celery_app.task(name="app.tasks.worker.process_timeseries", bind=True)
def process_timeseries(self, lat: float, lng: float, radius: int, cache_key: str = None):
    """
    Tarea asíncrona de Celery: calcula la evolución mensual de los índices satelitales
    (NDVI/NDWI/NDMI) de una ubicación para el panel "Pulso Territorial" (contenido premium
    para usuarios logeados, ver plan de Julio 2026). Se encola en paralelo al análisis
    principal (process_gee_analysis) para no retrasar la respuesta ya visible al usuario.

    A diferencia del análisis principal, el resultado NO depende del "approach": los mismos
    tres índices se calculan siempre igual, así que una sola serie temporal por
    ubicación+radio puede reutilizarse sin importar qué enfoque haya elegido el usuario.
    """
    try:
        ee.Initialize()
    except Exception:
        logger.warning("GEE no inicializado en el hilo actual. Reintentando...")
        init_gee()

    try:
        point = ee.Geometry.Point([lng, lat])
        roi = point.buffer(radius)

        end_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        start_date = end_date - datetime.timedelta(days=60)

        col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(roi)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60))
                .sort('system:time_start'))

        def extract_indices(image):
            indices = calculate_indices(image)
            stats = indices.select(['NDVI', 'NDWI', 'NDMI']).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=20,
                maxPixels=1e9
            )
            return ee.Feature(None, {
                'date': ee.Date(image.get('system:time_start')).format('YYYY-MM-dd'),
                'clouds': image.get('CLOUDY_PIXEL_PERCENTAGE'),
                'ndvi': stats.get('NDVI'),
                'ndwi': stats.get('NDWI'),
                'ndmi': stats.get('NDMI'),
            })

        # Un solo getInfo() para TODA la colección (mismo patrón de batching de A2 en
        # process_gee_analysis): construir N features (una por pasada satelital) y evaluarlas
        # en una única llamada, en vez de una llamada por imagen.
        feature_collection = ee.FeatureCollection(col.map(extract_indices))
        fc_info = get_info_with_timeout(feature_collection, timeout=60)

        chart_data = []
        for feature in fc_info.get('features', []):
            props = feature.get('properties', {}) or {}
            # Pasadas donde la ROI específica quedó totalmente cubierta por nubes/no-data
            # (aunque el CLOUDY_PIXEL_PERCENTAGE global de la imagen esté bajo el umbral)
            # devuelven None en reduceRegion; se descartan en vez de graficar un cero falso.
            if props.get('ndvi') is None:
                continue
            chart_data.append({
                'date': props.get('date'),
                'ndvi': round(props.get('ndvi', 0), 4),
                'ndwi': round(props.get('ndwi', 0), 4),
                'ndmi': round(props.get('ndmi', 0), 4),
                'clouds': round(props.get('clouds', 0), 1) if props.get('clouds') is not None else None,
            })

        result = {"status": "success", "chart_data": chart_data}
        cache_analysis_result(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"Error en cálculo de serie temporal: {e}", exc_info=True)
        raise e
