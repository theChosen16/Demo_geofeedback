# =============================================================================
# GeoFeedback Chile - Plataforma de Inteligencia Territorial
# Copyright (c) 2025 Alejandro Hernández Aguirre
# TODOS LOS DERECHOS RESERVADOS / ALL RIGHTS RESERVED
# 
# Este código es propiedad exclusiva del autor y se proporciona únicamente
# con fines de demostración técnica. Prohibido copiar, modificar o distribuir.
# =============================================================================

import os
import re
import datetime
import json
import time
import hashlib
import hmac
import threading
import concurrent.futures
import logging
import sys
from collections import defaultdict
import redis
from flask import Flask, jsonify, request, redirect, Response
from flask_cors import CORS
import ee
from gee_config import init_gee
import database # [NEW] Database module

try:
    from google import genai
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        gemini_model_name = 'gemini-3.5-flash'  # Gemini 3.5 Flash - google.dev
        gemini_available = True
        print("Gemini AI (gemini-3.5-flash) inicializado correctamente.")
    else:
        gemini_available = False
        print("WARNING: GEMINI_API_KEY no configurada.")
except ImportError:
    gemini_available = False
    gemini_client = None
    print("WARNING: google-genai no instalado.")


def call_gemini_with_retry(prompt, max_retries=2, timeout=30):
    """Llama a Gemini con reintentos y timeout real usando concurrent.futures.

    El parámetro `timeout` se aplica como wall-clock limit sobre cada intento.
    Sin esto un worker de Gunicorn puede bloquearse indefinidamente ante una
    respuesta lenta de la API.
    """
    if not gemini_available or not gemini_client:
        return None

    for attempt in range(max_retries):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    gemini_client.models.generate_content,
                    model=gemini_model_name,
                    contents=prompt,
                )
                response = future.result(timeout=timeout)
            return response.text
        except concurrent.futures.TimeoutError:
            print(f"Gemini intento {attempt + 1}/{max_retries}: timeout ({timeout}s)")
        except Exception as e:
            print(f"Gemini intento {attempt + 1}/{max_retries}: {e}")
        if attempt < max_retries - 1:
            time.sleep(1)
    return None

app = Flask(__name__)

# Apply SECRET_KEY from Config so Flask sessions are properly signed.
# Config raises RuntimeError if SECRET_KEY is absent in production.
from config import Config as _AppConfig
app.config['SECRET_KEY'] = _AppConfig.SECRET_KEY

# Limit request body size to 64 KB to prevent DoS via oversized payloads
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024

# CORS: restrict to known origins — NO wildcard default in production.
# Reads ALLOWED_ORIGINS first; falls back to legacy CORS_ORIGINS for
# deployments that documented the old variable name.
ALLOWED_ORIGINS = (
    os.environ.get('ALLOWED_ORIGINS', '') or
    os.environ.get('CORS_ORIGINS', '')
)
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == '*':
    import warnings
    warnings.warn("ALLOWED_ORIGINS no configurado. CORS abierto — solo aceptable en desarrollo local.")
    CORS(app)
else:
    CORS(app, origins=[o.strip() for o in ALLOWED_ORIGINS.split(',')])


# ============================================================================
# Security Headers
# ============================================================================
@app.after_request
def set_security_headers(response):
    """Aplica headers de seguridad HTTP en todas las respuestas."""
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(self), camera=(), microphone=()'
    # HSTS solo en producción (Railway provee HTTPS)
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # CSP: permite Google Maps, fonts, Earth Engine
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        # 'unsafe-eval' intentionally omitted: Chart.js v4 and the Google Maps
        # JS loader do not require it. 'unsafe-inline' is still needed because
        # the template relies on inline <script> blocks and inline event
        # handlers (onclick/onkeypress); removing it requires a template refactor.
        "script-src 'self' 'unsafe-inline' blob: https://maps.googleapis.com https://*.gstatic.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
        "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob: https://*.googleapis.com https://*.gstatic.com https://earthengine.googleapis.com https://*.google.com; "
        "connect-src 'self' data: https://*.googleapis.com https://*.gstatic.com https://earthengine.googleapis.com https://api.resend.com; "
        "worker-src 'self' blob:; "
        "frame-src 'self' https://*.google.com https://*.googleapis.com https://*.gstatic.com"
    )
    return response


@app.route('/favicon.ico')
def favicon():
    return Response(status=204)


@app.route('/robots.txt')
def robots_txt():
    return Response("User-agent: *\nAllow: /\n", mimetype='text/plain')


# ============================================================================
# Structured JSON Logging & Redis Orchestration 
# ============================================================================
logger = logging.getLogger('geofeedback')
logger.setLevel(logging.INFO)
# Configurar formato nativo para mejor integración con Loki
formatter = logging.Formatter('%(message)s')
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(ch)

def log_event(event_type, **kwargs):
    """Genera logs en formato JSON para Grafana/Loki Stack."""
    log_data = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "event": event_type,
        "environment": os.environ.get('RAILWAY_ENVIRONMENT', 'local'),
        **kwargs
    }
    logger.info(json.dumps(log_data))

# Attempt to connect to Redis
REDIS_URL = os.environ.get('REDIS_URL')
redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()
        log_event('redis_init', status='connected')
    except Exception as e:
        log_event('redis_init', status='failed', error=str(e))
        redis_client = None

class RateLimiter:
    """Hybrid Rate Limiter: Redis-first, fallback to Thread-safe In-Memory."""
    def __init__(self, key_prefix, max_requests=10, window_seconds=60):
        self.prefix = key_prefix
        self.max_requests = max_requests
        self.window = window_seconds
        
        # In-Memory Fallback
        self._requests = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 300

    def _cleanup_old_entries(self, now):
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._last_cleanup = now
        stale_keys = [k for k, v in self._requests.items() if not v or now - v[-1] > self.window]
        for k in stale_keys:
            del self._requests[k]

    def is_allowed(self, client_ip):
        # Redis Primary Approach
        if redis_client:
            redis_key = f"rate_limit:{self.prefix}:{client_ip}"
            try:
                # Transacción Atómica
                pipe = redis_client.pipeline()
                pipe.incr(redis_key)
                pipe.expire(redis_key, self.window, nx=True) # set expire solo si no tiene uno
                results = pipe.execute()
                request_count = results[0]
                
                if request_count > self.max_requests:
                    log_event('rate_limit_exceeded', ip=client_ip, prefix=self.prefix, backend='redis')
                    return False
                return True
            except Exception as e:
                # Fallback to local memory if Redis crashes
                log_event('redis_error', error=str(e), action='fallback_to_memory')
        
        # Memory Standard Approach
        now = time.time()
        with self._lock:
            self._cleanup_old_entries(now)
            self._requests[client_ip] = [t for t in self._requests[client_ip] if now - t < self.window]
            if len(self._requests[client_ip]) >= self.max_requests:
                log_event('rate_limit_exceeded', ip=client_ip, prefix=self.prefix, backend='memory')
                return False
            self._requests[client_ip].append(now)
            return True

# 10 analyses per minute, 5 contact submissions per minute
analysis_limiter = RateLimiter(key_prefix='analyze', max_requests=10, window_seconds=60)
contact_limiter = RateLimiter(key_prefix='contact', max_requests=5, window_seconds=60)


def get_client_ip():
    """Get real client IP from a single trusted upstream proxy (Railway LB).

    Railway's load balancer appends the actual client IP as the last entry in
    X-Forwarded-For.  We always take that rightmost value so a client cannot
    spoof earlier entries to bypass rate limiting.  X-Real-IP is intentionally
    ignored because it is trivially forgeable by any HTTP client.
    """
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        # Rightmost entry is appended by the trusted Railway LB
        ips = [ip.strip() for ip in forwarded.split(',')]
        return ips[-1] if ips[-1] else request.remote_addr or '127.0.0.1'
    return request.remote_addr or '127.0.0.1'

# Inicializar Google Earth Engine
gee_initialized = init_gee()
_ANALYTICS_BOOTSTRAP_LOCK = threading.Lock()
_ANALYTICS_BOOTSTRAP_RETRY_SECONDS = 30
_ANALYTICS_BOOTSTRAP_ENABLED = os.environ.get(
    "ENABLE_ANALYTICS_BOOTSTRAP",
    "true" if os.environ.get("RAILWAY_ENVIRONMENT") else "false"
).lower() == "true"
_analytics_bootstrap_state = {
    "ready": False,
    "last_attempt": 0.0
}


def ensure_analytics_bootstrap_once(force=False):
    """Try to create analytics tables once per retry window before handling traffic."""
    if _analytics_bootstrap_state["ready"]:
        return True

    now = time.time()
    if not force and (now - _analytics_bootstrap_state["last_attempt"]) < _ANALYTICS_BOOTSTRAP_RETRY_SECONDS:
        return False

    with _ANALYTICS_BOOTSTRAP_LOCK:
        if _analytics_bootstrap_state["ready"]:
            return True

        now = time.time()
        if not force and (now - _analytics_bootstrap_state["last_attempt"]) < _ANALYTICS_BOOTSTRAP_RETRY_SECONDS:
            return False

        _analytics_bootstrap_state["last_attempt"] = now
        ready = database.ensure_analytics_ready()
        if ready:
            _analytics_bootstrap_state["ready"] = True
            log_event("analytics_bootstrap", status="ready")
        else:
            log_event("analytics_bootstrap", status="deferred")

        return _analytics_bootstrap_state["ready"]


@app.before_request
def bootstrap_analytics_before_traffic():
    if _ANALYTICS_BOOTSTRAP_ENABLED and not _analytics_bootstrap_state["ready"]:
        ensure_analytics_bootstrap_once()

def get_sentinel2_image(roi):
    """Obtiene la imagen Sentinel-2 más reciente y libre de nubes para la ROI."""
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=180) # 6 meses
    
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .sort('system:time_start', False))
            
    # Verificar si hay imágenes (evita error 500 si la colección está vacía)
    try:
        if col.size().getInfo() == 0:
            return None
    except Exception as e:
        print(f"Error checking collection size: {e}")
        return None
        
    return col.first()

def calculate_indices(image):
    """Calcula índices espectrales comunes."""
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI') # McFeeters
    ndmi = image.normalizedDifference(['B8', 'B11']).rename('NDMI')
    return image.addBands([ndvi, ndwi, ndmi])

# Enfoques válidos (whitelist)
VALID_APPROACHES = {
    'mining', 'agriculture', 'energy', 'real-estate',
    'flood-risk', 'water-management', 'environmental',
    'land-planning', 'fire-risk'
}
MAX_RADIUS = 50000

@app.route('/api/v1/analyze', methods=['POST'])
def analyze_territory():
    if not analysis_limiter.is_allowed(get_client_ip()):
        return jsonify({"status": "error", "message": "Demasiadas solicitudes. Intenta en un minuto."}), 429

    if not gee_initialized:
        return jsonify({"status": "error", "message": "GEE no está inicializado"}), 500
    
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Body JSON requerido"}), 400

    try:
        lat = float(data.get('lat', 0))
        lng = float(data.get('lng', 0))
        radius = min(int(data.get('radius', 1000)), MAX_RADIUS)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "lat, lng y radius deben ser numéricos"}), 400

    approach = str(data.get('approach', '')).strip()
    location_name = str(data.get('location', 'Unknown'))[:200]

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return jsonify({"status": "error", "message": "Coordenadas fuera de rango válido"}), 400
    if lat == 0 and lng == 0:
        return jsonify({"status": "error", "message": "Coordenadas requeridas"}), 400
    if approach not in VALID_APPROACHES:
        return jsonify({"status": "error", "message": f"Enfoque no válido"}), 400
    if radius < 100:
        radius = 100

    client_ip = get_client_ip()
    log_event('api_call', endpoint='/analyze', ip=client_ip, approach=approach, radius=radius,
              coords={'lat': lat, 'lng': lng})

    try:
        point = ee.Geometry.Point([lng, lat])
        roi = point.buffer(radius)
        
        # Datos Base
        srtm = ee.Image('CGIAR/SRTM90_V4')
        elevation = srtm.select('elevation')
        slope = ee.Terrain.slope(elevation)
        
        s2_image = get_sentinel2_image(roi)
        if not s2_image:
            return jsonify({
                "status": "warning", 
                "message": "No se encontraron imágenes satelitales libres de nubes en los últimos 6 meses para esta ubicación. Intenta con otra zona o espera a mejores condiciones climáticas.",
                "retry": False
            }), 200
            
        s2_indices = calculate_indices(s2_image)
        
        # Reducers
        mean_reducer = ee.Reducer.mean()
        
        results = {}
        
        # Lógica por Enfoque
        if approach == 'mining':
            # Minería: Vegetación (Impacto), Agua (Relaves), Pendiente (Estabilidad)
            stats = s2_indices.select(['NDVI', 'NDWI']).addBands(slope).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            results = {
                "Vegetación Circundante (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Índice de Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Pendiente Promedio (°)": f"{stats.get('slope', 0):.1f}"
            }
            
        elif approach == 'agriculture':
            # Agro: Salud Cultivo (NDVI), Estrés Hídrico (NDMI)
            stats = s2_indices.select(['NDVI', 'NDMI']).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            results = {
                "Vigor Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}",
                "Humedad Vegetación (NDMI)": f"{stats.get('NDMI', 0):.2f}",
                "Estado": "Saludable" if stats.get('NDVI', 0) > 0.4 else "Atención Requerida"
            }
            
        elif approach == 'energy':
            # Energía: Pendiente (Solar/Eólica), Elevación
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
            # Inmobiliario: Pendiente (Constructibilidad), Riesgo Inundación (NDWI proxy)
            stats = s2_indices.select(['NDWI']).addBands(slope).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            avg_slope = stats.get('slope', 0)
            results = {
                "Pendiente Terreno (°)": f"{avg_slope:.1f}",
                "Índice Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}",
                "Constructibilidad (Topo)": "Óptima" if avg_slope < 5 else "Buena" if avg_slope < 15 else "Compleja"
            }
            
        # Enfoques Originales (Mantenidos/Mejorados)
        # Enfoques Originales (Mantenidos/Mejorados)
        elif approach == 'flood-risk':
             stats = s2_indices.select(['NDWI']).addBands(elevation).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=30, maxPixels=1e9
            ).getInfo()
             results = {"NDWI Promedio": f"{stats.get('NDWI', 0):.2f}", "Elevación Media": f"{stats.get('elevation', 0):.0f} m"}

        elif approach == 'water-management':
             stats = s2_indices.select(['NDWI', 'NDMI']).reduceRegion(
                 reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
             ).getInfo()
             results = {"Cuerpos de Agua (NDWI)": f"{stats.get('NDWI', 0):.2f}", "Humedad Suelo/Veg (NDMI)": f"{stats.get('NDMI', 0):.2f}"}

        elif approach == 'environmental':
             stats = s2_indices.select(['NDVI']).reduceRegion(
                 reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
             ).getInfo()
             results = {"Cobertura Vegetal (NDVI)": f"{stats.get('NDVI', 0):.2f}"}
             
        elif approach == 'land-planning':
             stats = slope.reduceRegion(
                 reducer=mean_reducer, geometry=roi, scale=90, maxPixels=1e9
             ).getInfo()
             results = {"Pendiente Promedio": f"{stats.get('slope', 0):.1f}°"}

        elif approach == 'fire-risk':
            # Riesgo de Incendio: NDVI (vegetación seca), NDMI (humedad baja), Pendiente (dificulta combate)
            stats = s2_indices.select(['NDVI', 'NDMI']).addBands(slope).reduceRegion(
                reducer=mean_reducer, geometry=roi, scale=20, maxPixels=1e9
            ).getInfo()
            
            ndvi = stats.get('NDVI', 0)
            ndmi = stats.get('NDMI', 0)
            avg_slope = stats.get('slope', 0)
            
            # Cálculo de índice de riesgo (0-100)
            # NDVI bajo = más riesgo (vegetación seca)
            # NDMI bajo = más riesgo (baja humedad)
            # Pendiente alta = más riesgo (dificulta combate)
            risk_vegetation = max(0, (0.6 - ndvi) / 0.6 * 40)  # 40 pts max
            risk_moisture = max(0, (0.4 - ndmi) / 0.4 * 40)    # 40 pts max
            risk_slope = min(avg_slope / 45 * 20, 20)          # 20 pts max
            
            risk_index = min(int(risk_vegetation + risk_moisture + risk_slope), 100)
            
            # Clasificación de riesgo
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

        # Generar Visualización (Map ID) - CLIPPED to ROI
        vis_params = {}
        vis_image = None
        
        if approach in ['mining', 'agriculture', 'environmental', 'water-management']:
            # Visualizar NDVI/NDWI
            vis_image = s2_indices.select('NDVI').clip(roi)
            vis_params = {'min': -0.2, 'max': 0.8, 'palette': ['red', 'yellow', 'green']}
            if approach == 'water-management' or approach == 'flood-risk':
                 vis_image = s2_indices.select('NDWI').clip(roi)
                 vis_params = {'min': -0.5, 'max': 0.5, 'palette': ['white', 'blue']}
        elif approach in ['energy', 'real-estate', 'land-planning']:
            # Visualizar Pendiente
            vis_image = slope.clip(roi)
            vis_params = {'min': 0, 'max': 45, 'palette': ['green', 'yellow', 'red']}
        elif approach == 'fire-risk':
            # Visualizar riesgo compuesto: bajo NDVI + bajo NDMI + alta pendiente = más riesgo
            # Crear imagen compuesta de riesgo
            ndvi_risk = s2_indices.select('NDVI').multiply(-1).add(0.6)  # Invertir: menos verde = más riesgo
            ndmi_risk = s2_indices.select('NDMI').multiply(-1).add(0.4)  # Invertir: menos humedad = más riesgo
            slope_norm = slope.divide(45)  # Normalizar pendiente
            
            risk_composite = ndvi_risk.add(ndmi_risk).add(slope_norm).divide(3).clip(roi)
            vis_image = risk_composite
            vis_params = {'min': 0, 'max': 1, 'palette': ['#22c55e', '#84cc16', '#eab308', '#f97316', '#dc2626']}
        else:
            vis_image = s2_indices.select('NDVI').clip(roi)  # Fallback
            vis_params = {'min': 0, 'max': 1, 'palette': ['white', 'green']}

        map_id_dict = vis_image.getMapId(vis_params)
        tile_url = map_id_dict['tile_fetcher'].url_format
        
        # Calculate analysis area dynamically (area = π * r²)
        import math
        area_m2 = int(math.pi * radius * radius)

        # Get actual image date from Sentinel-2 metadata
        try:
            image_date = ee.Date(s2_image.get('system:time_start')).format('YYYY-MM-dd').getInfo()
        except Exception as e:
            print(f"Error getting image date from GEE: {e}")
            image_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # [NEW] Log analysis to database
        try:
            database.log_analysis(
                endpoint='/api/v1/analyze',
                location_name=location_name,
                lat=lat,
                lng=lng,
                approach=approach,
                status='success'
            )
        except Exception as e:
            print(f"Error logging analysis: {e}")

        return jsonify({
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
        })

    except Exception as e:
        print(f"Error en análisis GEE: {e}")
        return jsonify({"status": "error", "message": "Error interno en el análisis. Por favor intenta de nuevo."}), 500


# ============================================================================
# AI INTERPRETATION AND CHAT ENDPOINTS
# ============================================================================

@app.route('/api/v1/interpret', methods=['POST'])
def interpret_analysis():
    """Generate AI interpretation of analysis results."""
    if not analysis_limiter.is_allowed(get_client_ip()):
        return jsonify({"status": "error", "message": "Demasiadas solicitudes. Intenta en un minuto."}), 429

    if not gemini_available:
        return jsonify({"status": "error", "message": "Gemini AI no disponible"}), 503
    
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Body JSON requerido"}), 400
        results = data.get('results', {})
        # Validate results: must be a dict, bounded size to prevent prompt stuffing
        if not isinstance(results, dict) or len(results) > 20:
            return jsonify({"status": "error", "message": "Datos de resultados inválidos"}), 400
        approach = str(data.get('approach', '')).strip()
        location = str(data.get('location', 'ubicación seleccionada'))[:200]
        meta_date = str(data.get('meta_date', 'Desconocida'))[:30]
        
        approach_names = {
            'mining': 'Minería Sostenible',
            'agriculture': 'Agroindustria Inteligente',
            'energy': 'Energías Renovables',
            'real-estate': 'Desarrollo Inmobiliario',
            'flood-risk': 'Riesgo de Inundación',
            'water-management': 'Gestión Hídrica',
            'environmental': 'Calidad Ambiental',
            'land-planning': 'Planificación Territorial'
        }
        
        # System prompt for expert personality
        system_prompt = f"""PERSONALIDAD Y ROL:
Eres GeoBot, el asistente experto de GeoFeedback Chile. Eres un especialista en análisis geoespacial, teledetección satelital e índices ambientales. Tu rol es explicar datos técnicos de forma clara y accesible para cualquier usuario, sin perder rigor científico.

ESTILO DE COMUNICACIÓN:
- Usa un tono profesional pero cercano y amigable
- Evita tecnicismos innecesarios, pero cuando los uses explícalos brevemente
- Sé conciso y ve directo al punto
- Usa emojis moderadamente para hacer el contenido más visual (🌱 🌊 ⛰️ 📊 ⚠️ ✅)
- NO uses formato markdown como ### o ** porque no se renderiza bien
- Usa saltos de línea para separar secciones

INFORMACIÓN METODOLÓGICA (OBLIGATORIO MENCIONAR):
- Muestra explícitamente el nombre del satélite (Sentinel-2) y la fecha de la imagen analizada.
- OBLIGATORIO: Usa única y exclusivamente la fecha real de la imagen satelital proporcionada en el contexto de los datos ({meta_date}), NO inventes, simules ni alucines ninguna otra fecha bajo ninguna circunstancia. Si la fecha es "Desconocida" o nula, indícalo tal cual, pero jamás inventes fechas falsas (como 12 de marzo de 2024).
- Explica que los índices se calculan procesando bandas espectrales de luz no visible.
- Indica que los resultados presentados son el promedio de la respuesta satelital en toda la zona (promedio de índices según el área de análisis en km²).
- IMPORTANTE: Reitera que esta demo usa imágenes de archivo reciente (no tiempo real) debido a los límites de la licencia gratuita de GEE. El monitoreo en vivo es comercial.

ESTRUCTURA DE RESPUESTA:
Organiza tu respuesta en estas secciones claramente separadas:
1. RESUMEN (2-3 líneas con el hallazgo principal, incluye Satélite y Fecha)
2. QUÉ SIGNIFICAN LOS DATOS (explica métricas, procesamiento espectral y promedio por área)
3. IMPLICACIONES PRÁCTICAS (qué significa esto para el usuario)
4. RECOMENDACIONES (3-5 acciones concretas)
"""
        
        prompt = f"""{system_prompt}

DATOS A INTERPRETAR:
Tipo de análisis: {approach_names.get(approach, approach)}
Ubicación: {location}
Fecha de la imagen satelital analizada: {meta_date}

Resultados del análisis satelital:
{json.dumps(results, indent=2, ensure_ascii=False)}

Genera una interpretación profesional de estos datos siguiendo la estructura indicada. Máximo 250 palabras."""

        response_text = call_gemini_with_retry(prompt, timeout=45)
        
        if not response_text:
            return jsonify({
                "status": "error",
                "message": "No se pudo generar la interpretación. El servicio de IA está temporalmente no disponible. Por favor intenta de nuevo."
            }), 503
        
        return jsonify({
            "status": "success",
            "interpretation": response_text,
            "model": gemini_model_name
        })
        
    except Exception as e:
        print(f"Error en interpretación AI: {e}")
        return jsonify({"status": "error", "message": "Error temporal en el servicio de IA. Por favor intenta de nuevo."}), 503


@app.route('/api/v1/chat', methods=['POST'])
def chat_with_assistant():
    """Chat with GeoFeedback AI assistant."""
    if not analysis_limiter.is_allowed(get_client_ip()):
        return jsonify({"status": "error", "message": "Demasiadas solicitudes. Intenta en un minuto."}), 429

    if not gemini_available:
        return jsonify({"status": "error", "message": "Gemini AI no disponible"}), 503
    
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Body JSON requerido"}), 400
        message = str(data.get('message', ''))[:500]
        context = data.get('context', {})
        if not isinstance(context, dict):
            context = {}
        history = data.get('history', [])
        if not isinstance(history, list):
            history = []
        meta_date = str(context.get('meta_date', 'Desconocida'))[:30] if context else 'Desconocida'

        chat_history = ""
        for msg in history[:20]:  # Cap history to 20 messages to prevent prompt stuffing
            role = str(msg.get('role', 'user'))[:10]
            text = str(msg.get('text', ''))[:500]  # Cap each message length
            chat_history += f"{role}: {text}\n"

        log_event('api_call', endpoint='/chat', ip=get_client_ip(), message_length=len(message))
        
        # GeoBot system personality
        system_prompt = f"""Eres GeoBot, el asistente experto de GeoFeedback Chile. 
Eres un especialista en análisis geoespacial, teledetección satelital e índices ambientales.
Tu rol es responder preguntas de forma clara, útil y accesible.

REGLAS:
- Responde siempre en español
- Sé conciso (máximo 100 palabras para respuestas simples)
- Usa emojis moderadamente para hacer el contenido más visual
- NO uses formato markdown como ### o ** porque no se renderiza
- Si no tienes datos de análisis, indica que el usuario debe primero realizar un análisis

CONTEXTO CLAVE:
- Esta es una DEMO. Usa imágenes Sentinel-2 recientes, no tiempo real.
- OBLIGATORIO: Si hablas de la fecha de la imagen del análisis, debes usar obligatoriamente la fecha real provista en el contexto: {meta_date}. NO inventes, simules ni alucines ninguna otra fecha bajo ninguna circunstancia.
- El monitoreo en TIEMPO REAL es exclusivo de la versión COMERCIAL.
- Metodología: Los datos son promedios calculados mediante procesamiento de bandas espectrales sobre el área circular seleccionada (km²).
- Debes mencionar el satélite Sentinel-2 y la fecha cuando hables de análisis.
"""
        
        prompt = f"""{system_prompt}

CONTEXTO DEL ANÁLISIS ACTUAL:
{json.dumps(context, indent=2, ensure_ascii=False) if context else "No hay análisis activo aún."}

HISTORIAL DE CONVERSACIÓN:
{chat_history if chat_history else "Inicio de conversación."}

PREGUNTA DEL USUARIO: {message}

Responde de forma útil y amigable:"""

        response_text = call_gemini_with_retry(prompt, timeout=30)
        
        if not response_text:
            return jsonify({
                "status": "error",
                "message": "El servicio de IA está temporalmente ocupado. Por favor intenta de nuevo en unos segundos.",
                "retry": True
            }), 503
        
        return jsonify({
            "status": "success",
            "response": response_text,
            "model": gemini_model_name
        })
        
    except Exception as e:
        log_event('chat_error', error=str(e))
        return jsonify({
            "status": "error", 
            "message": "Error de conexión temporal. Por favor intenta de nuevo.",
            "retry": True
        }), 503


def send_email_resend(name, company, email, message):
    """Envía email usando Resend API (HTTP-based, funciona en Railway)."""
    import urllib.request
    import urllib.error
    import json
    
    resend_api_key = os.environ.get('RESEND_API_KEY')
    # Dominio verificado en Resend: geofeedback.cl
    from_email = "GeoFeedback <contacto@geofeedback.cl>"
    destination_email = os.environ.get('RESEND_TO_EMAIL', 'GeoFeedback.cl@gmail.com')
    
    if not resend_api_key:
        return False, "RESEND_API_KEY no configurado"
    
    try:
        email_data = {
            "from": from_email,
            "to": [destination_email],
            "reply_to": email,
            "subject": f"[GeoFeedback Web] Nuevo contacto de {name}",
            "text": f"Nombre: {name}\nEmpresa: {company}\nEmail: {email}\n\nMensaje: {message}"
        }
        
        req = urllib.request.Request(
            'https://api.resend.com/emails',
            data=json.dumps(email_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {resend_api_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as res:
            if res.status in [200, 201]:
                log_event('contact_email_sent', status='success', destination=destination_email)
                return True, "Enviado"
            else:
                log_event('contact_email_error', status_code=res.status)
                return False, "Error API"
            
    except Exception as e:
        log_event('contact_system_error', error=str(e))
        return False, str(e)

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_FIELD_LIMITS = {'name': 100, 'company': 100, 'email': 254, 'message': 2000}


@app.route('/api/v1/contact', methods=['POST'])
def contact_form():
    """Handle contact form submissions - SYNC version."""
    if not contact_limiter.is_allowed(get_client_ip()):
        return jsonify({"status": "error", "message": "Demasiadas solicitudes. Intenta en un minuto."}), 429

    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Body JSON requerido"}), 400
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()

        if not name or not email or not message:
            return jsonify({"status": "error", "message": "Campos requeridos incompletos"}), 400

        # Field length limits — prevent oversized payloads reaching Resend API
        for field, value in [('name', name), ('company', company), ('email', email), ('message', message)]:
            if len(value) > _FIELD_LIMITS[field]:
                return jsonify({"status": "error", "message": f"Campo '{field}' demasiado largo"}), 400

        # Basic email format validation
        if not _EMAIL_RE.match(email):
            return jsonify({"status": "error", "message": "Formato de email inválido"}), 400

        log_event('contact_received', ip=get_client_ip(), has_name=bool(name))
        
        success, error_detail = send_email_resend(name, company, email, message)
        
        if success:
            return jsonify({"status": "success", "message": "Mensaje enviado correctamente"})
        else:
            return jsonify({"status": "error", "message": "Error al enviar el mensaje por API"}), 500
        
    except Exception as e:
        log_event('contact_system_error', error=str(e))
        return jsonify({"status": "error", "message": "Falla interna del sistema"}), 500



# Fallback simple HTML for template loading errors
LANDING_ERROR_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Error Interno - GeoFeedback Chile</title>
    <style>
        body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #fafaf8; color: #2c3e2d; text-align: center; padding: 50px; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 4px solid #2d5a4a; }
        h1 { color: #2d5a4a; margin-bottom: 20px; }
        p { color: #5a6b5c; line-height: 1.6; }
        .btn { display: inline-block; background: #2d5a4a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin-top: 20px; font-weight: 500; }
        .btn:hover { background: #3d7a5f; }
    </style>
</head>
<body>
    <div class="container">
        <h1>GeoFeedback Chile</h1>
        <p>Lo sentimos, no se pudo cargar la plantilla de la interfaz correctamente. Esto puede deberse a tareas de mantenimiento o a un error de configuración del servidor.</p>
        <p><small>Por favor, contacta al soporte técnico en <a href="mailto:contacto@geofeedback.cl" style="color: #2d5a4a;">contacto@geofeedback.cl</a></small></p>
        <a href="/" class="btn">Reintentar Cargar</a>
    </div>
</body>
</html>
'''

@app.route('/')
def landing():
    # SECURITY: GOOGLE_MAPS_API_KEY is necessarily exposed to the browser (it is
    # used by the Maps/Air Quality/Solar JS APIs). It is NOT a secret, but it
    # MUST be locked down in the Google Cloud Console with an HTTP-referrer
    # restriction (e.g. *.geofeedback.cl) and limited to the specific APIs in
    # use, otherwise a third party can scrape it from the page and run up the
    # billing account. There is no server-side fix for this — it is a GCP config.
    google_maps_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    if not google_maps_key:
        print("WARNING: GOOGLE_MAPS_API_KEY not found in environment variables.")
    else:
        print(f"INFO: GOOGLE_MAPS_API_KEY found (length: {len(google_maps_key)})")
    
    try:
        # Log visit
        try:
            user_agent = request.headers.get('User-Agent')
            ip = get_client_ip()
            ip_hash = hashlib.sha256(ip.encode()).hexdigest() if ip else None
            database.log_visit(page='/', user_agent=user_agent, ip_hash=ip_hash)
        except Exception as e:
            print(f"Error logging visit: {e}")

        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            html = f.read()
        return html.replace('GOOGLE_MAPS_KEY_PLACEHOLDER', google_maps_key)
    except Exception as e:
        print(f"Error template: {e}")
        return LANDING_ERROR_HTML

@app.route('/api/v1/health')
def health():
    return jsonify({"status": "healthy", "service": "GeoFeedback API", "version": "1.0.0"})


@app.route('/api/v1/observability')
def observability():
    """System health endpoint.

    Full details (component breakdown, analytics schema state) are gated behind
    a shared secret presented in the ``X-Observability-Token`` header and
    compared in constant time.  This prevents external callers from
    fingerprinting which subsystems are unavailable before mounting a targeted
    attack.

    NOTE: gating on ``RAILWAY_ENVIRONMENT`` (the previous approach) was
    ineffective — Railway sets that variable process-wide in production, so the
    breakdown was exposed to *every* caller.  When ``OBSERVABILITY_TOKEN`` is
    unset the endpoint fails safe and returns only the aggregated status and
    public stats to everyone.
    """
    snapshot = database.get_observability_snapshot()

    # Read the expected token per-request (not at import time) so deployments
    # can rotate it and tests can patch the environment.
    expected_token = os.environ.get('OBSERVABILITY_TOKEN')
    provided_token = request.headers.get('X-Observability-Token', '')
    is_internal = bool(expected_token) and hmac.compare_digest(provided_token, expected_token)

    critical_checks = {
        "database": bool(snapshot["database"]["connected"]),
        "analytics": bool(snapshot["analytics"]["ready"]),
        "google_earth_engine": bool(gee_initialized),
        # Avoid confirming presence/absence of specific API keys to external callers
        "google_maps_key": bool(os.environ.get('GOOGLE_MAPS_API_KEY')),
    }
    optional_checks = {
        "gemini": bool(gemini_available),
        "redis": bool(redis_client),
    }
    overall_status = "healthy" if all(critical_checks.values()) else "degraded"

    payload = {
        "status": overall_status,
        "service": "GeoFeedback API",
        "version": "1.0.0",
        "checked_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "public_stats": snapshot["public_stats"],
    }

    # Expose internal component detail only to callers with a valid token
    if is_internal:
        payload["critical_checks"] = critical_checks
        payload["optional_checks"] = optional_checks
        payload["analytics"] = snapshot["analytics"]

    status_code = 200 if overall_status == "healthy" else 503
    return jsonify(payload), status_code

@app.route('/api/v1/stats')
def stats():
    try:
        public_stats = database.get_public_stats()
        return jsonify(public_stats)
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({"visits": 0, "analyses": 0})

@app.route('/api')
@app.route('/api/')
def api_redirect():
    return redirect('/api/docs', code=302)

@app.route('/contact')
@app.route('/contact/')
def contact_redirect():
    return redirect('/#contacto', code=302)

@app.route('/api/v1/infrastructure')
def infrastructure():
    return jsonify({"features": [{"type": "school", "name": "Escuela Papudo", "lat": -32.5127, "lng": -71.4469}]})

@app.route('/api/v1/risk-zones')
def risk_zones():
    return jsonify({"zones": [{"level": "high", "area_ha": 45.2, "description": "Quebrada El Frances"}]})

@app.route('/api/docs')
def api_docs():
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <title>GeoFeedback API Documentation</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #f8fafc; color: #1f2937; line-height: 1.6; }
        .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
        header { background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: white; padding: 3rem 2rem; margin-bottom: 2rem; }
        header h1 { font-size: 2rem; margin-bottom: 0.5rem; }
        header p { opacity: 0.8; }
        .section { background: white; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .section h2 { color: #1e3a5f; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
        .endpoint { background: #f8fafc; border-radius: 8px; padding: 1.25rem; margin: 1rem 0; border-left: 4px solid #10b981; }
        .method { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: 600; font-size: 0.8rem; margin-right: 0.5rem; }
        .get { background: #10b981; color: white; }
        .post { background: #3b82f6; color: white; }
        code { background: #e5e7eb; padding: 0.2rem 0.5rem; border-radius: 4px; font-family: monospace; }
        .endpoint-path { font-weight: 600; color: #1e3a5f; }
        .endpoint-desc { color: #6b7280; margin-top: 0.5rem; font-size: 0.95rem; }
        .api-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem; }
        .api-item { background: #f0fdf4; padding: 1rem; border-radius: 8px; text-align: center; }
        .api-item i { font-size: 1.5rem; color: #10b981; margin-bottom: 0.5rem; display: block; }
        .back-link { display: inline-flex; align-items: center; gap: 0.5rem; color: #1e3a5f; text-decoration: none; margin-top: 2rem; }
        .back-link:hover { color: #10b981; }
        .note { background: #fef3c7; border: 1px solid #f59e0b; padding: 1rem; border-radius: 8px; margin-top: 1rem; }
        .note strong { color: #92400e; }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <header>
        <div class="container">
            <h1><i class="fas fa-code"></i> GeoFeedback API v1</h1>
            <p>Documentacion de la API de inteligencia territorial</p>
        </div>
    </header>
    
    <div class="container">
        <div class="section">
            <h2><i class="fas fa-plug"></i> APIs Integradas</h2>
            <p>GeoFeedback integra multiples APIs de Google Cloud Platform:</p>
            <div class="api-list">
                <div class="api-item"><i class="fas fa-map"></i>Maps JavaScript API</div>
                <div class="api-item"><i class="fas fa-mountain"></i>Elevation API</div>
                <div class="api-item"><i class="fas fa-wind"></i>Air Quality API</div>
                <div class="api-item"><i class="fas fa-sun"></i>Solar API</div>
                <div class="api-item"><i class="fas fa-map-marker-alt"></i>Geocoding API</div>
                <div class="api-item"><i class="fas fa-satellite"></i>Earth Engine</div>
            </div>
        </div>
        
        <div class="section">
            <h2><i class="fas fa-server"></i> Endpoints Publicos</h2>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/v1/health</span>
                <p class="endpoint-desc">Verifica el estado del servicio y componentes.</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/v1/stats</span>
                <p class="endpoint-desc">Estadísticas de uso: Visitas totales y Análisis realizados.</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/v1/analyze</span>
                <p class="endpoint-desc">Ejecuta analisis geoespacial con Google Earth Engine. Retorna índices y mapa.</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/v1/interpret</span>
                <p class="endpoint-desc">Genera interpretacion con IA (Gemini) de los resultados.</p>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/v1/chat</span>
                <p class="endpoint-desc">Chatbot asistente para consultas sobre los datos.</p>
            </div>
            
            <div class="note">
                <strong><i class="fas fa-info-circle"></i> Nota:</strong> 
                Esta documentación cubre los endpoints públicos principales de la Demo.
            </div>
        </div>
        
        <div class="section">
            <h2><i class="fas fa-envelope"></i> Contacto</h2>
            <p>Para consultas sobre la API o integraciones comerciales:</p>
            <p style="margin-top: 1rem;"><strong>Email:</strong> <a href="mailto:GeoFeedback.cl@gmail.com">GeoFeedback.cl@gmail.com</a></p>
        </div>
        
        <a href="/" class="back-link"><i class="fas fa-arrow-left"></i> Volver al inicio</a>
    </div>
</body>
</html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
