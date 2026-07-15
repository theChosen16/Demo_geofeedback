import math
import datetime
import logging
import ee
from celery.signals import worker_process_init
from sqlmodel import Session
from geoalchemy2.elements import WKTElement

from app.tasks.celery_app import celery_app
from app.core.gee import init_gee
from app.db.session import engine
from app.db.models import ApiUsageLog

logger = logging.getLogger(__name__)

# Registrar la inicialización de Earth Engine al iniciar el worker process de Celery.
@worker_process_init.connect
def configure_gee_workers(*args, **kwargs):
    logger.info("Worker process inicializado: conectando a Google Earth Engine...")
    success = init_gee()
    if success:
        logger.info("Conexión a GEE exitosa en el worker.")
    else:
        logger.error("Falla crítica: No se pudo conectar a GEE en el worker.")


def get_sentinel2_image(roi):
    """Obtiene la imagen Sentinel-2 más reciente y libre de nubes para la ROI."""
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=180) # 6 meses
    
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .sort('system:time_start', False))
            
    try:
        # Check size of collection safely
        if col.size().getInfo() == 0:
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
def process_gee_analysis(self, lat: float, lng: float, radius: int, approach: str, location_name: str):
    """
    Tarea asíncrona de Celery para realizar análisis territorial usando Google Earth Engine.
    Guarda los logs en la base de datos de PostGIS e informa el estado.
    """
    logger.info(f"Iniciando tarea {self.request.id}: {approach} en ({lat}, {lng}), radio={radius}m")
    
    # Asegurar que Earth Engine esté inicializado
    # (Por lo general ya lo está gracias a worker_process_init, pero proveemos fallback)
    try:
        ee.Initialize()
    except Exception:
        logger.warning("GEE no inicializado en el hilo actual. Reintentando...")
        init_gee()

    try:
        point = ee.Geometry.Point([lng, lat])
        roi = point.buffer(radius)
        
        # Datos Base
        srtm = ee.Image('CGIAR/SRTM90_V4')
        elevation = srtm.select('elevation')
        slope = ee.Terrain.slope(elevation)
        
        s2_image = get_sentinel2_image(roi)
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
        
        # Lógica por Enfoque (Migrada exactamente del legacy app.py)
        if approach == 'mining':
            stats = s2_indices.select(['NDVI', 'NDWI']).addBands(slope).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            results = {
                "Vegetación Circundante (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Índice de Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Pendiente Promedio (°)": f"{stats.get('slope', 0):.1f}"
            }
            
        elif approach == 'agriculture':
            stats = s2_indices.select(['NDVI', 'NDMI']).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            results = {
                "Vigor Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Humedad Vegetación (NDMI)": f"{stats.get('NDMI', 0):.2f}",
                "Estado": "Saludable" if stats.get('NDVI', 0) > 0.4 else "Atención Requerida"
            }
            
        elif approach == 'energy':
            stats = srtm.select('elevation').addBands(slope).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=90, maxPixels=1e9
            ).getInfo()
            avg_slope = stats.get('slope', 0)
            results = {
                "Elevación Promedio (msnm)": f"{stats.get('elevation', 0):.0f}",
                "Pendiente Promedio (°)": f"{avg_slope:.1f}",
                "Aptitud Solar (Topografía)": "Alta" if avg_slope < 10 else "Media" if avg_slope < 20 else "Baja"
            }

        elif approach == 'real-estate':
            stats = s2_indices.select(['NDWI']).addBands(slope).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            avg_slope = stats.get('slope', 0)
            results = {
                "Pendiente Terreno (°)": f"{avg_slope:.1f}",
                "Índice Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Constructibilidad (Topo)": "Óptima" if avg_slope < 5 else "Buena" if avg_slope < 15 else "Compleja"
            }
            
        elif approach == 'flood-risk':
            stats = s2_indices.select(['NDWI']).addBands(elevation).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=30, maxPixels=1e9
            ).getInfo()
            results = {
                "NDWI Promedio": f"{stats.get('NDWI', 0):.2f}", 
                "Elevación Media": f"{stats.get('elevation', 0):.0f} m"
            }

        elif approach == 'water-management':
            stats = s2_indices.select(['NDWI', 'NDMI']).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            results = {
                "Cuerpos de Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}", 
                "Humedad Suelo/Veg (NDMI)": f"{stats.get('NDMI', 0):.2f}"
            }

        elif approach == 'environmental':
            stats = s2_indices.select(['NDVI']).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            results = {
                "Cobertura Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}"
            }
             
        elif approach == 'land-planning':
            stats = slope.reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=90, maxPixels=1e9
            ).getInfo()
            results = {
                "Pendiente Promedio": f"{stats.get('slope', 0):.1f}°"
            }

        elif approach == 'fire-risk':
            stats = s2_indices.select(['NDVI', 'NDMI']).addBands(slope).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            
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

        # Generar Visualización (Map ID) - Recortado a la ROI
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

        map_id_dict = vis_image.getMapId(vis_params)
        tile_url = map_id_dict['tile_fetcher'].url_format
        area_m2 = int(math.pi * radius * radius)

        # Obtener fecha de la imagen
        try:
            image_date = ee.Date(s2_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
        except Exception as e:
            logger.error(f"Error getting image date from GEE: {e}")
            image_date = datetime.datetime.now().strftime("%Y-%m-%d")

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

        # Retornar el resultado que el API de FastAPI leerá al completar la tarea
        return {
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
                "terrain": "SRTM v4",
                "date": image_date,
                "buffer_radius_m": radius
            }
        }

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
