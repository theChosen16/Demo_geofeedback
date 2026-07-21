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
ANALYSIS_CACHE_TTL_SECONDS = 12 * 60 * 60

# Incluida en la cache key (ver build_analysis_cache_key en analyze.py). Incrementar esta
# versión cuando cambie la lógica de negocio que produce el resultado cacheado (fórmulas,
# umbrales, paleta de cada enfoque más abajo) para invalidar de inmediato lo ya cacheado en
# vez de esperar hasta 12h a que expire por TTL y quedar sirviendo resultados con lógica vieja.
ANALYSIS_LOGIC_VERSION = "v1"

# Misma idea que ANALYSIS_LOGIC_VERSION pero para la cache de process_timeseries (ver
# build_timeseries_cache_key en analyze.py).
TIMESERIES_LOGIC_VERSION = "v1"


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
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError:
            end_date = datetime.datetime.now()
    else:
        end_date = datetime.datetime.now()
        
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
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .sort('system:time_start', False))
            
    try:
        # Check size of collection safely
        if get_info_with_timeout(col.size(), timeout=15) == 0:
            return None
    except Exception as e:
        logger.error(f"Error checking GEE collection size: {e}")
        return None
        
    return col.first()


def calculate_indices(image):
    """Calcula índices espectrales comunes."""
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI') # McFeeters
    ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI')
    return image.addBands([ndvi, ndwi, ndmi])


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
    # (Por lo general ya lo está gracias a worker_process_init, pero proveemos fallback)
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

        # Datos Base
        glo30_col = ee.ImageCollection('COPERNICUS/DEM/GLO30_2024_1')
        elevation = glo30_col.select('DEM').mosaic().setDefaultProjection(glo30_col.first().projection()).rename('elevation')
        slope = ee.Terrain.slope(elevation)

        t_check = time.monotonic()
        s2_image = get_sentinel2_image(roi, start_date_str=start_date, end_date_str=end_date)
        timings['collection_check_s'] = round(time.monotonic() - t_check, 2)
        if not s2_image:
            # Guardar log de advertencia en la base de datos
            with Session(engine) as session:
                log = ApiUsageLog(
                    endpoint="/api/v1/analyze",
                    location_name=location_name[:255],
                    coordinates=WKTElement(f"POINT({lng} {lat})", srid=4326),
                    approach=approach,
                    status="warning_no_images"
                )
                session.add(log)
                session.commit()

            return {
                "status": "warning", 
                "message": "No se encontraron imágenes satelitales libres de nubes en los últimos 6 meses para esta ubicación. Intenta con otra zona o espera a mejores condiciones climáticas.",
                "retry": False
            }
            
        s2_indices = calculate_indices(s2_image)
        mean_reducer = ee.Reducer.mean()
        results = {}

        # Determinar la imagen y escala para la reducción de región según el enfoque
        stats_image = None
        scale = 20

        if approach == 'mining':
            stats_image = s2_indices.select(['NDVI', 'NDWI']).addBands(slope)
            scale = 20
        elif approach == 'agriculture':
            stats_image = s2_indices.select(['NDVI', 'NDMI'])
            scale = 20
        elif approach == 'energy':
            stats_image = elevation.addBands(slope)
            scale = 30
        elif approach == 'real-estate':
            stats_image = s2_indices.select(['NDWI']).addBands(slope)
            scale = 20
        elif approach == 'flood-risk':
            stats_image = s2_indices.select(['NDWI']).addBands(elevation)
            scale = 30
        elif approach == 'water-management':
            stats_image = s2_indices.select(['NDWI', 'NDMI'])
            scale = 20
        elif approach == 'environmental':
            stats_image = s2_indices.select(['NDVI'])
            scale = 20
        elif approach == 'land-planning':
            stats_image = slope
            scale = 30
        elif approach == 'fire-risk':
            stats_image = s2_indices.select(['NDVI', 'NDMI']).addBands(slope)
            scale = 20

        # Determinar la imagen y parámetros de Visualización (Map ID) según el enfoque - Recortado a la ROI
        # (Se construye aquí, antes de la reducción, porque no depende de sus resultados y así puede
        # lanzarse a GEE en paralelo con reduceRegion/fecha en vez de esperar a que ambos terminen.)
        vis_params = {}
        vis_image = None

        if approach in ['mining', 'agriculture', 'environmental', 'water-management']:
            vis_image = s2_indices.select('NDVI').clip(roi)
            vis_params = {'min': -0.2, 'max': 0.8, 'palette': ['red', 'yellow', 'green']}
            if approach == 'water-management' or approach == 'flood-risk':
                 vis_image = s2_indices.select('NDWI').clip(roi)
                 vis_params = {'min': -0.5, 'max': 0.5, 'palette': ['white', 'blue']}
        elif approach in ['energy', 'real-estate', 'land-planning']:
            vis_image = slope.clip(roi)
            vis_params = {'min': 0, 'max': 45, 'palette': ['green', 'yellow', 'red']}
        elif approach == 'fire-risk':
            ndvi_risk = s2_indices.select('NDVI').multiply(-1).add(0.6)
            ndmi_risk = s2_indices.select('NDMI').multiply(-1).add(0.4)
            slope_norm = slope.divide(45)

            risk_composite = ndvi_risk.add(ndmi_risk).add(slope_norm).divide(3).clip(roi)
            vis_image = risk_composite
            vis_params = {'min': 0, 'max': 1, 'palette': ['#22c55e', '#84cc16', '#eab308', '#f97316', '#dc2626']}
        else:
            vis_image = s2_indices.select('NDVI').clip(roi)
            vis_params = {'min': 0, 'max': 1, 'palette': ['white', 'green']}

        # Stats primero, en solitario: si reduceRegion falla, la excepción debe propagarse
        # (comportamiento sin cambios) porque sin estos datos el análisis no tiene ningún valor.
        # Se resuelve ANTES de someter fecha/mapa a propósito: si se sometieran los 3 a la vez y
        # stats fallara, las otras 2 llamadas a GEE ya habrían salido igual (gastando cuota/latencia
        # y ocupando hilos del _GEE_EXECUTOR) para un resultado que de todas formas se descarta.
        t_sub = time.monotonic()
        if stats_image is not None:
            stats = resolve_with_timeout(
                submit_gee_getinfo(stats_image.reduceRegion(
                    reducer=mean_reducer,
                    geometry=roi,
                    scale=scale,
                    maxPixels=1e9
                )),
                timeout=30, op_name="reduceRegion"
            )
        else:
            stats = {}
        timings['gee_stats_s'] = round(time.monotonic() - t_sub, 2)

        # Una vez que sabemos que stats tuvo éxito, fecha y capa de mapa sí se lanzan juntas en
        # paralelo (ninguna depende de la otra, y ambas son mucho más rápidas que reduceRegion).
        t_parallel = time.monotonic()
        date_future = submit_gee_getinfo(ee.Date(s2_image.get('system:time_start')).format('YYYY-MM-dd'))
        map_future = _GEE_EXECUTOR.submit(vis_image.getMapId, vis_params)

        # Fecha: si falla, se usa la fecha de hoy como fallback (comportamiento sin cambios); no
        # invalida el análisis porque el dato principal (stats) ya se obtuvo.
        try:
            image_date = resolve_with_timeout(date_future, timeout=15, op_name="image date")
        except Exception as e:
            logger.error(f"Error getting image date from GEE: {e}")
            image_date = datetime.datetime.now().strftime("%Y-%m-%d")
        timings['gee_date_s'] = round(time.monotonic() - t_parallel, 2)

        # Capa de mapa: si falla se propaga (comportamiento sin cambios), el frontend necesita la capa.
        t_sub = time.monotonic()
        map_id_dict = resolve_with_timeout(map_future, timeout=30, op_name="getMapId")
        tile_url = map_id_dict['tile_fetcher'].url_format
        timings['gee_mapid_s'] = round(time.monotonic() - t_sub, 2)

        timings['gee_parallel_wall_s'] = round(time.monotonic() - t_parallel, 2)

        # Mapear resultados según el enfoque
        if approach == 'mining':
            results = {
                "Vegetación Circundante (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Índice de Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Pendiente Promedio (°)": f"{stats.get('slope', 0):.1f}"
            }
        elif approach == 'agriculture':
            results = {
                "Vigor Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Humedad Vegetación (NDMI)": f"{stats.get('NDMI', 0):.2f}",
                "Estado": "Saludable" if stats.get('NDVI', 0) > 0.4 else "Atención Requerida"
            }
        elif approach == 'energy':
            avg_slope = stats.get('slope', 0)
            results = {
                "Elevación Promedio (msnm)": f"{stats.get('elevation', 0):.0f}",
                "Pendiente Promedio (°)": f"{avg_slope:.1f}",
                "Aptitud Solar (Topografía)": "Alta" if avg_slope < 10 else "Media" if avg_slope < 20 else "Baja"
            }
        elif approach == 'real-estate':
            avg_slope = stats.get('slope', 0)
            results = {
                "Pendiente Terreno (°)": f"{avg_slope:.1f}",
                "Índice Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Constructibilidad (Topo)": "Óptima" if avg_slope < 5 else "Buena" if avg_slope < 15 else "Compleja"
            }
        elif approach == 'flood-risk':
            results = {
                "NDWI Promedio": f"{stats.get('NDWI', 0):.2f}", 
                "Elevación Media": f"{stats.get('elevation', 0):.0f} m"
            }
        elif approach == 'water-management':
            results = {
                "Cuerpos de Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}", 
                "Humedad Suelo/Veg (NDMI)": f"{stats.get('NDMI', 0):.2f}"
            }
        elif approach == 'environmental':
            results = {
                "Cobertura Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}"
            }
        elif approach == 'land-planning':
            results = {
                "Pendiente Promedio": f"{stats.get('slope', 0):.1f}°"
            }
        elif approach == 'fire-risk':
            ndvi = stats.get('NDVI', 0)
            ndmi = stats.get('NDMI', 0)
            avg_slope = stats.get('slope', 0)
            
            # Cálculo de índice de riesgo (0-100)
            risk_vegetation = max(0, (0.6 - ndvi) / 0.6 * 40)
            risk_moisture = max(0, (0.4 - ndmi) / 0.4 * 40)
            risk_slope = min(avg_slope / 45 * 20, 20)
            
            risk_index = min(int(risk_vegetation + risk_moisture + risk_slope), 100)
            
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
                "Índice de Riesgo": f"{risk_index}/100",
                "Nivel de Riesgo": risk_level,
                "Vegetación (NDVI)": f"{ndvi:.2f}",
                "Humedad (NDMI)": f"{ndmi:.2f}",
                "Pendiente (°)": f"{avg_slope:.1f}"
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

        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=35)

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
