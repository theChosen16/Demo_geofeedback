# =============================================================================
# GeoFeedback Chile - Plataforma de Inteligencia Territorial
# Copyright (c) 2025 Alejandro Olivares Verdugo
# TODOS LOS DERECHOS RESERVADOS / ALL RIGHTS RESERVED
# 
# Este código es propiedad exclusiva del autor y se proporciona únicamente
# con fines de demostración técnica. Prohibido copiar, modificar o distribuir.
# =============================================================================

import os
import datetime
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import ee
from gee_config import init_gee

# Gemini AI Integration
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        gemini_available = True
        print("Gemini AI inicializado correctamente.")
    else:
        gemini_available = False
        print("WARNING: GEMINI_API_KEY no configurada.")
except ImportError:
    gemini_available = False
    print("WARNING: google-generativeai no instalado.")

app = Flask(__name__)
CORS(app)

# Inicializar Google Earth Engine
gee_initialized = init_gee()

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

@app.route('/api/v1/analyze', methods=['POST'])
def analyze_territory():
    if not gee_initialized:
        return jsonify({"status": "error", "message": "GEE no está inicializado"}), 500
    
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    approach = data.get('approach')
    radius = data.get('radius', 1000)  # Default 1km
    
    if not lat or not lng or not approach:
        return jsonify({"status": "error", "message": "Faltan parámetros"}), 400

    try:
        point = ee.Geometry.Point([lng, lat])
        roi = point.buffer(radius)  # Dynamic radius from frontend
        
        # Datos Base
        srtm = ee.Image('CGIAR/SRTM90_V4')
        elevation = srtm.select('elevation')
        slope = ee.Terrain.slope(elevation)
        
        s2_image = get_sentinel2_image(roi)
        if not s2_image:
            return jsonify({"status": "warning", "message": "No se encontraron imágenes recientes libres de nubes."}), 404
            
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
        else:
            vis_image = s2_indices.select('NDVI').clip(roi)  # Fallback
            vis_params = {'min': 0, 'max': 1, 'palette': ['white', 'green']}

        map_id_dict = vis_image.getMapId(vis_params)
        tile_url = map_id_dict['tile_fetcher'].url_format
        
        # Calculate analysis area dynamically (area = π * r²)
        import math
        area_m2 = int(math.pi * radius * radius)

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
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "buffer_radius_m": radius
            }
        })

    except Exception as e:
        print(f"Error en análisis GEE: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================================
# AI INTERPRETATION AND CHAT ENDPOINTS
# ============================================================================

@app.route('/api/v1/interpret', methods=['POST'])
def interpret_analysis():
    """Generate AI interpretation of analysis results."""
    if not gemini_available:
        return jsonify({"status": "error", "message": "Gemini AI no disponible"}), 503
    
    try:
        data = request.json
        results = data.get('results', {})
        approach = data.get('approach', '')
        location = data.get('location', 'ubicación seleccionada')
        
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
        
        prompt = f"""Eres el asistente de IA de GeoFeedback Chile, una plataforma de inteligencia territorial.
        
Analiza estos resultados de un estudio de {approach_names.get(approach, approach)} para {location}:

{json.dumps(results, indent=2, ensure_ascii=False)}

Proporciona una interpretación profesional en español que incluya:
1. Un resumen ejecutivo (2-3 oraciones)
2. Significado de cada métrica y su implicancia práctica
3. Recomendaciones específicas basadas en los datos
4. Posibles riesgos o consideraciones a tener en cuenta

Mantén un tono profesional pero accesible. Máximo 300 palabras."""

        response = gemini_model.generate_content(prompt)
        
        return jsonify({
            "status": "success",
            "interpretation": response.text,
            "model": "gemini-1.5-flash"
        })
        
    except Exception as e:
        print(f"Error en interpretación AI: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/v1/chat', methods=['POST'])
def chat_with_assistant():
    """Chat with GeoFeedback AI assistant."""
    if not gemini_available:
        return jsonify({"status": "error", "message": "Gemini AI no disponible"}), 503
    
    try:
        data = request.json
        message = data.get('message', '')
        context = data.get('context', {})
        history = data.get('history', [])
        
        # Build conversation history for context
        chat_history = ""
        for msg in history[-5:]:  # Last 5 messages for context
            role = "Usuario" if msg.get('role') == 'user' else "Asistente"
            chat_history += f"{role}: {msg.get('content', '')}\n"
        
        prompt = f"""Eres el asistente de IA de GeoFeedback Chile, experto en análisis geoespacial y territorial.

Contexto del análisis actual:
{json.dumps(context, indent=2, ensure_ascii=False) if context else "No hay análisis activo."}

Historial de conversación:
{chat_history}

Nueva pregunta del usuario: {message}

Responde de forma útil, profesional y en español. Si la pregunta es sobre:
- Índices satelitales (NDVI, NDWI, NDMI): explica su significado y cómo interpretar valores
- Análisis territorial: proporciona insights basados en los datos
- GeoFeedback en general: explica las capacidades de la plataforma

Mantén respuestas concisas (máximo 150 palabras) a menos que se requiera más detalle."""

        response = gemini_model.generate_content(prompt)
        
        return jsonify({
            "status": "success",
            "response": response.text,
            "model": "gemini-1.5-flash"
        })
        
    except Exception as e:
        print(f"Error en chat AI: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


LANDING_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoFeedback Chile - Inteligencia Territorial</title>
    <meta name="description" content="Plataforma open source de analisis geoespacial para Chile.">
    <link rel="canonical" href="https://geofeedback.cl/">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #1e3a5f;
            --primary-light: #2d5a87;
            --secondary: #10b981;
            --secondary-light: #34d399;
            --accent: #f59e0b;
            --danger: #ef4444;
            --text: #1f2937;
            --text-light: #6b7280;
            --background: #f8fafc;
            --white: #ffffff;
            --border: #e5e7eb;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.6;
        }
        .navbar {
            position: fixed;
            top: 0; left: 0; right: 0;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            z-index: 1000;
            padding: 1rem 2rem;
            box-shadow: var(--shadow);
        }
        .navbar-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            text-decoration: none;
        }
        .logo i { color: var(--secondary); }
        .nav-links { display: flex; gap: 2rem; align-items: center; }
        .nav-links a { color: var(--text); text-decoration: none; font-weight: 500; }
        .nav-links a:hover { color: var(--secondary); }
        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            font-size: 0.95rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--secondary), var(--secondary-light));
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        }
        .btn-secondary { background: var(--primary); color: white; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 8rem 2rem 4rem;
            background: linear-gradient(135deg, var(--primary) 0%, #0f2744 100%);
        }
        .hero-content {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
        }
        .hero-text h1 {
            font-size: 3.5rem;
            font-weight: 800;
            color: white;
            line-height: 1.1;
            margin-bottom: 1.5rem;
        }
        .hero-text h1 span {
            background: linear-gradient(135deg, var(--secondary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero-text p { font-size: 1.25rem; color: rgba(255,255,255,0.8); margin-bottom: 2rem; }
        .hero-buttons { display: flex; gap: 1rem; flex-wrap: wrap; }
        .hero-visual { display: flex; justify-content: center; }
        .satellite-icon {
            font-size: 12rem;
            color: var(--secondary);
            opacity: 0.3;
            animation: float 6s ease-in-out infinite;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        .section { padding: 6rem 2rem; }
        .section-dark { background: var(--primary); color: white; }
        .section-light { background: var(--white); }
        .container { max-width: 1200px; margin: 0 auto; }
        .section-header { text-align: center; margin-bottom: 4rem; }
        .section-header h2 { font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; }
        .section-header p { font-size: 1.1rem; color: var(--text-light); max-width: 600px; margin: 0 auto; }
        .section-dark .section-header p { color: rgba(255,255,255,0.7); }
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 2rem;
            transition: transform 0.3s;
        }
        .card:hover { transform: translateY(-5px); }
        .card i { font-size: 2.5rem; color: var(--accent); margin-bottom: 1rem; }
        .card h3 { font-size: 1.25rem; margin-bottom: 0.75rem; }
        .card p { color: rgba(255,255,255,0.7); font-size: 0.95rem; }
        .card-light { background: var(--background); border: 1px solid var(--border); }
        .card-light:hover { box-shadow: var(--shadow-lg); }
        .card-light i { color: var(--secondary); }
        .card-light h3 { color: var(--primary); }
        .card-light p { color: var(--text-light); }
        .demo-section {
            background: linear-gradient(180deg, var(--background) 0%, #e2e8f0 100%);
            padding: 6rem 2rem;
        }
        .demo-container { max-width: 1400px; margin: 0 auto; }
        .demo-layout {
            display: grid;
            grid-template-columns: 1fr 420px;
            gap: 1.5rem;
            margin-top: 2rem;
        }
        .map-container {
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            position: relative;
        }
        #demo-map { width: 100%; height: 550px; background: #e5e7eb; }
        .map-controls {
            position: absolute;
            top: 1rem; right: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            z-index: 10;
        }
        .map-control-btn {
            background: white;
            border: none;
            width: 40px; height: 40px;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .map-control-btn:hover { background: var(--secondary); color: white; }
        .map-placeholder {
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: var(--text-light);
        }
        .map-placeholder i { font-size: 3rem; margin-bottom: 1rem; opacity: 0.5; }
        .sidebar { display: flex; flex-direction: column; gap: 1rem; }
        .panel {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: var(--shadow);
        }
        .panel-header {
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 500;
        }
        .search-wrapper { position: relative; }
        .search-wrapper i {
            position: absolute;
            left: 1rem; top: 50%;
            transform: translateY(-50%);
            color: var(--text-light);
        }
        .search-input {
            width: 100%;
            padding: 0.875rem 1rem 0.875rem 2.75rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
        }
        .search-input:focus { outline: none; border-color: var(--secondary); }
        .location-badge {
            display: none;
            background: linear-gradient(135deg, var(--secondary), var(--secondary-light));
            color: white;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-top: 0.75rem;
        }
        .location-badge.active { display: block; }
        .location-badge h4 { font-size: 1rem; margin-bottom: 0.25rem; }
        .location-badge p { font-size: 0.8rem; opacity: 0.9; margin: 0; }
        .approach-select {
            width: 100%;
            padding: 0.875rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
            cursor: pointer;
            background: white;
        }
        .approach-select:focus { outline: none; border-color: var(--secondary); }
        .indices-panel {
            display: none;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }
        .indices-panel.active { display: block; }
        .indices-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.75rem;
        }
        .index-item {
            background: var(--background);
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
        }
        .index-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.25rem;
        }
        .index-color { width: 12px; height: 12px; border-radius: 3px; }
        .index-name { font-weight: 600; font-size: 0.85rem; color: var(--primary); }
        .index-desc { font-size: 0.8rem; color: var(--text-light); line-height: 1.4; }
        .index-api {
            font-size: 0.7rem;
            background: var(--primary);
            color: white;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            margin-left: auto;
        }
        #analyze-btn { width: 100%; padding: 1rem; font-size: 1rem; margin-top: 0.5rem; }
        .status-bar { display: flex; gap: 1rem; margin-bottom: 1rem; }
        .status-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-light);
        }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--border); }
        .status-dot.ready { background: var(--secondary); }
        .results-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-top: 1.5rem;
        }
        .result-card {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            box-shadow: var(--shadow);
        }
        .result-icon { font-size: 2rem; color: var(--secondary); }
        .result-content h4 { font-size: 1rem; color: var(--primary); margin-bottom: 0.25rem; }
        .result-content p { font-size: 0.85rem; color: var(--text-light); margin: 0; }
        .live-data {
            display: none;
            margin-top: 1rem;
            padding: 1rem;
            background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
            border-radius: 8px;
            color: white;
        }
        .live-data.active { display: block; }
        .live-data h4 {
            font-size: 0.85rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .live-data-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }
        .live-data-item {
            background: rgba(255,255,255,0.1);
            padding: 0.5rem;
            border-radius: 6px;
        }
        .live-data-label { font-size: 0.7rem; opacity: 0.7; }
        .live-data-value { font-size: 0.9rem; font-weight: 600; }
        footer {
            background: var(--primary);
            color: white;
            padding: 3rem 2rem;
        }
        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 2rem;
        }
        .footer-logo { display: flex; align-items: center; gap: 0.75rem; font-size: 1.25rem; font-weight: 700; }
        .footer-logo i { color: var(--secondary); }
        .footer-links { display: flex; gap: 2rem; }
        .footer-links a { color: rgba(255,255,255,0.7); text-decoration: none; }
        .footer-links a:hover { color: var(--secondary); }
        .social-links { display: flex; gap: 1rem; }
        .social-links a {
            width: 40px; height: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .social-links a:hover { background: var(--secondary); }
        @media (max-width: 1024px) {
            .demo-layout { grid-template-columns: 1fr; }
            .sidebar { order: -1; }
            #demo-map { height: 400px; }
            .results-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 768px) {
            .hero-content { grid-template-columns: 1fr; text-align: center; }
            .hero-text h1 { font-size: 2.5rem; }
            .hero-buttons { justify-content: center; }
            .hero-visual { display: none; }
            .nav-links { display: none; }
        }
        .pac-container {
            border-radius: 8px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-lg);
            margin-top: 4px;
            font-family: 'Inter', sans-serif;
        }
        .pac-item { padding: 10px 14px; cursor: pointer; }
        .pac-item:hover { background: var(--background); }
        .pac-icon { display: none; }
        .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        /* Modal Styles */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.7);
            z-index: 2000;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        }
        .modal-overlay.active { display: flex; }
        .modal-content {
            background: white;
            border-radius: 16px;
            max-width: 700px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-header {
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: white;
            padding: 1.5rem;
            border-radius: 16px 16px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-header h3 { margin: 0; font-size: 1.3rem; }
        .modal-close {
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            opacity: 0.8;
        }
        .modal-close:hover { opacity: 1; }
        .modal-body { padding: 1.5rem; }
        .scale-section {
            background: var(--background);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .scale-title {
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .scale-bar {
            height: 20px;
            border-radius: 10px;
            margin: 0.5rem 0;
        }
        .scale-bar.ndvi { background: linear-gradient(to right, #8B0000, #FF6B6B, #FFFF00, #90EE90, #006400); }
        .scale-bar.ndwi { background: linear-gradient(to right, #8B4513, #FFD700, #90EE90, #87CEEB, #000080); }
        .scale-bar.slope { background: linear-gradient(to right, #22c55e, #ffd700, #ff6b6b); }
        .scale-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-light);
        }
        .interpretation-text {
            background: white;
            border-left: 4px solid var(--secondary);
            padding: 0.75rem 1rem;
            margin-top: 0.75rem;
            border-radius: 0 8px 8px 0;
            font-size: 0.9rem;
            line-height: 1.5;
        }
        .value-badge {
            display: inline-block;
            background: var(--secondary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            margin-left: 0.5rem;
        }
        
        /* Chat Sidebar Styles */
        .chat-toggle-btn {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 1500;
            transition: transform 0.3s ease;
        }
        .chat-toggle-btn:hover { transform: scale(1.1); }
        
        .chat-sidebar {
            position: fixed;
            right: -420px;
            top: 0;
            width: 400px;
            height: 100vh;
            background: white;
            box-shadow: -5px 0 30px rgba(0,0,0,0.2);
            z-index: 2000;
            transition: right 0.3s ease;
            display: flex;
            flex-direction: column;
        }
        .chat-sidebar.open { right: 0; }
        
        .chat-header {
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: white;
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-header h4 { margin: 0; font-size: 1.1rem; }
        .chat-close {
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: #f8fafc;
        }
        
        .chat-message {
            margin-bottom: 1rem;
            max-width: 85%;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .chat-message.user {
            margin-left: auto;
            text-align: right;
        }
        .chat-message.user .message-bubble {
            background: var(--primary);
            color: white;
            border-radius: 16px 16px 4px 16px;
        }
        .chat-message.assistant .message-bubble {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 16px 16px 16px 4px;
        }
        .message-bubble {
            padding: 0.75rem 1rem;
            display: inline-block;
        }
        .message-time {
            font-size: 0.7rem;
            color: var(--text-light);
            margin-top: 0.25rem;
        }
        
        .chat-input-wrapper {
            padding: 1rem;
            border-top: 1px solid #e2e8f0;
            background: white;
            display: flex;
            gap: 0.5rem;
        }
        .chat-input {
            flex: 1;
            padding: 0.75rem 1rem;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            font-size: 0.9rem;
            outline: none;
        }
        .chat-input:focus { border-color: var(--secondary); }
        .chat-send {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--secondary);
            color: white;
            border: none;
            cursor: pointer;
        }
        .chat-send:disabled { background: #ccc; }
        
        .ai-interpretation {
            background: linear-gradient(135deg, #f0fdf4, #ecfeff);
            border-left: 4px solid var(--secondary);
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 0 8px 8px 0;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        .ai-interpretation h5 {
            margin: 0 0 0.5rem 0;
            color: var(--primary);
        }
        .ai-loading {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-light);
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--secondary);
            display: inline-block;
            animation: typing 1s infinite;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <a href="#" class="logo"><i class="fas fa-globe-americas"></i>GeoFeedback</a>
            <div class="nav-links">
                <a href="#problema">Problema</a>
                <a href="#solucion">Solucion</a>
                <a href="#demo">Demo</a>
                <a href="/api/docs" class="btn btn-primary"><i class="fas fa-code"></i> API</a>
            </div>
        </div>
    </nav>
    <section class="hero">
        <div class="hero-content">
            <div class="hero-text">
                <h1>Democratizando la <span>Inteligencia Territorial</span></h1>
                <p>Plataforma open source que transforma datos satelitales en mapas de riesgo y herramientas de gestion hidrica para Chile.</p>
                <div class="hero-buttons">
                    <a href="#demo" class="btn btn-primary"><i class="fas fa-map-marked-alt"></i> Explorar Demo</a>
                    <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank" rel="noopener noreferrer" class="btn btn-secondary"><i class="fab fa-github"></i> GitHub</a>
                </div>
            </div>
            <div class="hero-visual"><i class="fas fa-satellite satellite-icon"></i></div>
        </div>
    </section>
    <section id="problema" class="section section-dark">
        <div class="container">
            <div class="section-header">
                <h2>El Problema</h2>
                <p>Chile enfrenta desafios criticos en gestion territorial</p>
            </div>
            <div class="cards-grid">
                <div class="card"><i class="fas fa-balance-scale"></i><h3>Ley 21.364</h3><p>Municipios deben elaborar planes de emergencia y mapas de riesgo, pero carecen de herramientas accesibles.</p></div>
                <div class="card"><i class="fas fa-tint-slash"></i><h3>Mega-sequia</h3><p>15 anios de deficit hidrico. Agricultores necesitan datos para optimizar uso del agua.</p></div>
                <div class="card"><i class="fas fa-dollar-sign"></i><h3>Alto Costo</h3><p>Estudios geoespaciales profesionales son costosos para municipios rurales.</p></div>
            </div>
        </div>
    </section>
    <section id="solucion" class="section section-light">
        <div class="container">
            <div class="section-header">
                <h2>Nuestra Solucion</h2>
                <p>Inteligencia territorial con APIs de Google Maps Platform + Google Earth Engine</p>
            </div>
            
            <!-- API Category: Satellite -->
            <h3 style="color: var(--primary); margin-bottom: 1rem; font-size: 1.2rem;"><i class="fas fa-satellite" style="color: var(--secondary);"></i> Analisis Satelital</h3>
            <div class="cards-grid" style="margin-bottom: 2rem;">
                <div class="card card-light"><i class="fab fa-google"></i><h3>Google Earth Engine</h3><p>Procesamiento de Sentinel-2 (NDVI, NDWI, NDMI)</p></div>
                <div class="card card-light"><i class="fas fa-th"></i><h3>Map Tiles API</h3><p>Tiles de mapas personalizados y overlays</p></div>
            </div>
            
            <!-- API Category: Location -->
            <h3 style="color: var(--primary); margin-bottom: 1rem; font-size: 1.2rem;"><i class="fas fa-location-dot" style="color: var(--secondary);"></i> Ubicacion y Lugares</h3>
            <div class="cards-grid" style="margin-bottom: 2rem;">
                <div class="card card-light"><i class="fas fa-location-arrow"></i><h3>Geocoding API</h3><p>Conversion direccion a coordenadas</p></div>
                <div class="card card-light"><i class="fas fa-location-crosshairs"></i><h3>Geolocation API</h3><p>Ubicacion del usuario en tiempo real</p></div>
                <div class="card card-light"><i class="fas fa-building"></i><h3>Places API (New)</h3><p>Busqueda de lugares e infraestructura</p></div>
                <div class="card card-light"><i class="fas fa-check-circle"></i><h3>Address Validation</h3><p>Validacion de direcciones postales</p></div>
            </div>
            
            <!-- API Category: Analysis -->
            <h3 style="color: var(--primary); margin-bottom: 1rem; font-size: 1.2rem;"><i class="fas fa-chart-line" style="color: var(--secondary);"></i> APIs de Analisis</h3>
            <div class="cards-grid" style="margin-bottom: 2rem;">
                <div class="card card-light"><i class="fas fa-mountain"></i><h3>Elevation API</h3><p>Datos topograficos en tiempo real</p></div>
                <div class="card card-light"><i class="fas fa-wind"></i><h3>Air Quality API</h3><p>Calidad del aire resolucion 500m</p></div>
                <div class="card card-light"><i class="fas fa-sun"></i><h3>Solar API</h3><p>Potencial fotovoltaico de cubiertas</p></div>
                <div class="card card-light"><i class="fas fa-leaf"></i><h3>Pollen API</h3><p>Niveles de polen y alergenos</p></div>
            </div>
            
            <!-- API Category: Visualization -->
            <h3 style="color: var(--primary); margin-bottom: 1rem; font-size: 1.2rem;"><i class="fas fa-map" style="color: var(--secondary);"></i> Visualizacion</h3>
            <div class="cards-grid">
                <div class="card card-light"><i class="fas fa-map-marked-alt"></i><h3>Maps JavaScript API</h3><p>Mapas interactivos web</p></div>
                <div class="card card-light"><i class="fas fa-image"></i><h3>Maps Static API</h3><p>Mapas estaticos para reportes PDF</p></div>
                <div class="card card-light"><i class="fas fa-database"></i><h3>Maps Datasets API</h3><p>Gestion de datasets geoespaciales</p></div>
            </div>
        </div>
    </section>
    
    <!-- Sentinel-2 Indices Section -->
    <section id="indices" class="section section-dark">
        <div class="container">
            <div class="section-header">
                <h2>Indices Satelitales Sentinel-2</h2>
                <p>Comprendiendo los datos que analizamos</p>
            </div>
            <div class="cards-grid">
                <div class="card">
                    <i class="fas fa-leaf"></i>
                    <h3>NDVI - Indice de Vegetacion</h3>
                    <p><strong>Formula:</strong> (NIR - Rojo) / (NIR + Rojo)</p>
                    <p><strong>Bandas:</strong> (B8 - B4) / (B8 + B4)</p>
                    <p><strong>Rango:</strong> -1 a +1</p>
                    <p>Valores &gt; 0.3 indican vegetacion saludable. Usado para monitorear salud de cultivos y cobertura vegetal.</p>
                </div>
                <div class="card">
                    <i class="fas fa-water"></i>
                    <h3>NDWI - Indice de Agua</h3>
                    <p><strong>Formula:</strong> (Verde - NIR) / (Verde + NIR)</p>
                    <p><strong>Bandas:</strong> (B3 - B8) / (B3 + B8)</p>
                    <p><strong>Rango:</strong> -1 a +1</p>
                    <p>Valores &gt; 0.3 indican presencia de agua. Detecta cuerpos de agua, inundaciones y humedad superficial.</p>
                </div>
                <div class="card">
                    <i class="fas fa-tint"></i>
                    <h3>NDMI - Indice de Humedad</h3>
                    <p><strong>Formula:</strong> (NIR - SWIR) / (NIR + SWIR)</p>
                    <p><strong>Bandas:</strong> (B8 - B11) / (B8 + B11)</p>
                    <p><strong>Rango:</strong> -1 a +1</p>
                    <p>Valores &gt; 0.2 indican alta humedad. Evalua estres hidrico en vegetacion y contenido de agua en plantas.</p>
                </div>
            </div>
        </div>
    </section>
    
    <section id="demo" class="demo-section">
        <div class="demo-container">
            <div class="section-header">
                <h2>Demo Interactivo</h2>
                <p>Selecciona ubicacion y enfoque para explorar datos en tiempo real</p>
            </div>
            <div class="demo-layout">
                <div class="map-container">
                    <div id="demo-map">
                        <div class="map-placeholder" id="map-placeholder">
                            <i class="fas fa-map-marked-alt"></i>
                            <p>Cargando mapa...</p>
                        </div>
                    </div>
                    <div class="map-controls">
                        <button class="map-control-btn" onclick="centerMap()" title="Centrar en Chile"><i class="fas fa-home"></i></button>
                        <button class="map-control-btn" onclick="toggleMapType()" title="Cambiar vista"><i class="fas fa-layer-group"></i></button>
                    </div>
                </div>
                <div class="sidebar">
                    <div class="panel">
                        <div class="status-bar">
                            <div class="status-item"><span class="status-dot" id="status-location"></span>Ubicacion</div>
                            <div class="status-item"><span class="status-dot" id="status-approach"></span>Enfoque</div>
                        </div>
                    </div>
                    <div class="panel">
                        <div class="panel-header"><i class="fas fa-search"></i> Buscar Ubicacion</div>
                        <div class="search-wrapper">
                            <div id="autocomplete-container"></div>
                        </div>
                        <div class="location-badge" id="location-badge">
                            <h4 id="location-name">-</h4>
                            <p id="location-coords">-</p>
                        </div>
                        <div class="live-data" id="live-data">
                            <h4><i class="fas fa-broadcast-tower"></i> Datos en tiempo real</h4>
                            <div class="live-data-grid">
                                <div class="live-data-item"><div class="live-data-label">Elevacion</div><div class="live-data-value" id="data-elevation">--</div></div>
                                <div class="live-data-item"><div class="live-data-label">Calidad Aire (AQI)</div><div class="live-data-value" id="data-aqi">--</div></div>
                                <div class="live-data-item"><div class="live-data-label">Potencial Solar</div><div class="live-data-value" id="data-solar">--</div></div>
                                <div class="live-data-item"><div class="live-data-label">Pendiente</div><div class="live-data-value" id="data-slope">--</div></div>
                            </div>
                        </div>
                    </div>
                    <div class="panel">
                        <div class="panel-header"><i class="fas fa-crosshairs"></i> Seleccionar Enfoque</div>
                        <select id="approach-select" class="approach-select" onchange="onApproachChange()">
                            <option value="">-- Elige un enfoque de analisis --</option>
                            <optgroup label="Sectores Industriales">
                                <option value="mining">Mineria Sostenible</option>
                                <option value="agriculture">Agroindustria Inteligente</option>
                                <option value="energy">Energias Renovables</option>
                                <option value="real-estate">Desarrollo Inmobiliario</option>
                            </optgroup>
                            <optgroup label="Analisis General">
                                <option value="flood-risk">Riesgo de Inundacion</option>
                                <option value="water-management">Gestion Hidrica</option>
                                <option value="environmental">Calidad Ambiental</option>
                                <option value="land-planning">Planificacion Territorial</option>
                            </optgroup>
                        </select>
                        <div class="indices-panel" id="indices-panel">
                            <div class="indices-title">Indices y datos del analisis:</div>
                            <div id="analysis-results" style="display:none;"></div>
                            <div id="indices-list"></div>
                        </div>
                    </div>
                    <div class="panel">
                        <div class="panel-header"><i class="fas fa-ruler-combined"></i> Radio de Analisis</div>
                        <select id="radius-select" class="approach-select" onchange="onRadiusChange()">
                            <option value="">-- Selecciona el radio --</option>
                            <option value="2000" selected>2 kilometros (~12.57 km²)</option>
                            <option value="5000">5 kilometros (~78.54 km²)</option>
                            <option value="10000">10 kilometros (~314.16 km²)</option>
                        </select>
                        <div style="font-size:0.75rem; color:var(--text-light); margin-top:0.5rem;">
                            <i class="fas fa-info-circle"></i> El radio define el area circular alrededor del punto para el analisis.
                        </div>
                    </div>
                    <div class="panel">
                        <button class="btn btn-primary" id="analyze-btn" onclick="analyzeTerritory()" disabled><i class="fas fa-satellite-dish"></i> Iniciar Analisis</button>
                        <p style="font-size: 0.8rem; color: var(--text-light); margin-top: 0.5rem; text-align: center;">Requiere ubicacion y enfoque seleccionados</p>
                    </div>
                </div>
            </div>
            <div class="results-grid">
                <div class="result-card" id="result-location"><i class="fas fa-map-marker-alt result-icon"></i><div class="result-content"><h4>Ubicacion</h4><p>Busca o haz clic en el mapa</p></div></div>
                <div class="result-card" id="result-approach"><i class="fas fa-crosshairs result-icon"></i><div class="result-content"><h4>Enfoque</h4><p>Selecciona el tipo de analisis</p></div></div>
                <div class="result-card"><i class="fas fa-satellite result-icon"></i><div class="result-content"><h4>APIs Integradas</h4><p>Elevation, Air Quality, Solar, Geocoding</p></div></div>
            </div>
        </div>
    </section>
    <footer>
        <div class="footer-content">
            <div class="footer-logo"><i class="fas fa-globe-americas"></i>GeoFeedback Chile</div>
            <div class="footer-links">
                <a href="#demo">Demo</a>
                <a href="/api/docs">API</a>
                <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank" rel="noopener noreferrer">GitHub</a>
            </div>
            <div class="social-links">
                <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank" rel="noopener noreferrer"><i class="fab fa-github"></i></a>
                <a href="https://www.linkedin.com/in/alejandro-olivares-verdugo/" target="_blank" rel="noopener noreferrer"><i class="fab fa-linkedin-in"></i></a>
            </div>
        </div>
    </footer>
    
    <!-- Interpretation Modal -->
    <div class="modal-overlay" id="interpretation-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3><i class="fas fa-info-circle"></i> Interpretacion de Resultados</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modal-body">
                <!-- Content injected by JS -->
            </div>
        </div>
    </div>
    
    <!-- Chat Toggle Button -->
    <button class="chat-toggle-btn" onclick="toggleChat()" title="Hablar con Asistente IA">
        <i class="fas fa-robot"></i>
    </button>
    
    <!-- Chat Sidebar -->
    <div id="chat-sidebar" class="chat-sidebar">
        <div class="chat-header">
            <h4><i class="fas fa-robot"></i> Asistente GeoFeedback</h4>
            <button class="chat-close" onclick="toggleChat()">&times;</button>
        </div>
        <div id="chat-messages" class="chat-messages">
            <div class="chat-message assistant">
                <div class="message-bubble">
                    Hola! Soy el asistente de IA de GeoFeedback. Puedo ayudarte a entender los analisis territoriales, explicar indices satelitales como NDVI o NDWI, o responder preguntas sobre la plataforma. ¿En que puedo ayudarte?
                </div>
            </div>
        </div>
        <div class="chat-input-wrapper">
            <input type="text" id="chat-input" class="chat-input" placeholder="Escribe tu pregunta..." onkeypress="if(event.key==='Enter')sendChatMessage()">
            <button class="chat-send" onclick="sendChatMessage()"><i class="fas fa-paper-plane"></i></button>
        </div>
    </div>
    
    <script>
        var MAPS_API_KEY = "GOOGLE_MAPS_KEY_PLACEHOLDER";
        var map = null;
        var marker = null;
        var autocomplete = null;
        var selectedPlace = null;
        var selectedApproach = null;
        var selectedRadius = 2000;  // Default 2km
        var isSatellite = true;
        var chatHistory = [];
        var analysisContext = {};

        var approaches = {
            "mining": {
                name: "Mineria Sostenible",
                icon: "mountain",
                indices: [
                    { name: "Vegetacion (NDVI)", api: "Sentinel-2", desc: "Monitoreo de impacto ambiental en flora.", color: "#2ecc71" },
                    { name: "Agua (NDWI)", api: "Sentinel-2", desc: "Deteccion de cuerpos de agua y relaves.", color: "#3498db" },
                    { name: "Pendiente", api: "Elevation", desc: "Analisis de estabilidad de terreno.", color: "#95a5a6" }
                ]
            },
            "agriculture": {
                name: "Agroindustria Inteligente",
                icon: "seedling",
                indices: [
                    { name: "Salud Cultivo (NDVI)", api: "Sentinel-2", desc: "Vigor y salud de la vegetacion.", color: "#2ecc71" },
                    { name: "Estres Hidrico (NDMI)", api: "Sentinel-2", desc: "Contenido de humedad en cultivos.", color: "#1abc9c" },
                    { name: "Solar", api: "Solar API", desc: "Potencial para riego solar.", color: "#f1c40f" }
                ]
            },
            "energy": {
                name: "Energias Renovables",
                icon: "solar-panel",
                indices: [
                    { name: "Irradiancia", api: "Solar API", desc: "Potencial solar fotovoltaico.", color: "#f1c40f" },
                    { name: "Topografia", api: "Elevation", desc: "Analisis de sombras y pendiente.", color: "#95a5a6" },
                    { name: "Infraestructura", api: "Places", desc: "Proximidad a redes electricas.", color: "#e74c3c" }
                ]
            },
            "real-estate": {
                name: "Desarrollo Inmobiliario",
                icon: "building",
                indices: [
                    { name: "Constructibilidad", api: "Elevation", desc: "Pendientes aptas para construccion.", color: "#95a5a6" },
                    { name: "Servicios", api: "Places", desc: "Cercania a colegios y salud.", color: "#e74c3c" },
                    { name: "Calidad Aire", api: "Air Quality", desc: "Indices de contaminacion local.", color: "#1abc9c" },
                    { name: "Riesgos", api: "Sentinel-2", desc: "Historial de inundaciones (NDWI).", color: "#3498db" }
                ]
            },
            "flood-risk": {
                name: "Riesgo de Inundacion",
                icon: "water",
                indices: [
                    { name: "Cuerpos de Agua (NDWI)", api: "Sentinel-2", desc: "Deteccion de zonas inundables.", color: "#3498db" },
                    { name: "Elevacion", api: "Elevation", desc: "Modelado de terreno.", color: "#95a5a6" }
                ]
            },
            "water-management": {
                name: "Gestion Hidrica",
                icon: "tint",
                indices: [
                    { name: "Humedad Suelo (NDMI)", api: "Sentinel-2", desc: "Retencion de agua en suelo.", color: "#1abc9c" },
                    { name: "NDWI", api: "Sentinel-2", desc: "Monitoreo de embalses.", color: "#3498db" }
                ]
            },
            "environmental": {
                name: "Calidad Ambiental",
                icon: "leaf",
                indices: [
                    { name: "Cobertura Vegetal (NDVI)", api: "Sentinel-2", desc: "Densidad de vegetacion.", color: "#2ecc71" },
                    { name: "Calidad Aire", api: "Air Quality", desc: "Indices AQI en tiempo real.", color: "#e74c3c" }
                ]
            },
            "land-planning": {
                name: "Planificacion Territorial",
                icon: "map-marked-alt",
                indices: [
                    { name: "Pendiente", api: "Elevation", desc: "Aptitud de uso de suelo.", color: "#95a5a6" },
                    { name: "Uso Actual", api: "Sentinel-2", desc: "Clasificacion de cobertura.", color: "#f1c40f" }
                ]
            }
        };

        async function loadGoogleMaps() {
            var script = document.createElement("script");
            script.src = "https://maps.googleapis.com/maps/api/js?key=" + MAPS_API_KEY + "&libraries=places,marker&callback=initMap&v=weekly&loading=async";
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
        }

        async function initMap() {
            if (!MAPS_API_KEY || MAPS_API_KEY.length < 20) {
                console.error("API Key no configurada o invalida");
                return;
            }

            // Import libraries
            // Import libraries
            // Import libraries
            const { Map } = await google.maps.importLibrary("maps");
            const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
            const { Place, PlaceAutocompleteElement } = await google.maps.importLibrary("places");

            map = new Map(document.getElementById("demo-map"), {
                center: { lat: -33.4489, lng: -70.6693 }, // Santiago
                zoom: 5,
                mapId: "DEMO_MAP_ID", // Reemplazar con ID real si existe
                mapTypeId: "hybrid",
                disableDefaultUI: false,
                zoomControl: true,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true
            });

            // Map Click Listener
            map.addListener("click", async (e) => {
                const clickedLat = e.latLng.lat();
                const clickedLng = e.latLng.lng();

                // Reverse Geocoding to get name
                const geocoder = new google.maps.Geocoder();
                const response = await geocoder.geocode({ location: { lat: clickedLat, lng: clickedLng } });
                
                let placeName = "Ubicación seleccionada";
                if (response.results && response.results[0]) {
                    placeName = response.results[0].formatted_address;
                }

                if (marker) marker.map = null;
                marker = new AdvancedMarkerElement({
                    map: map,
                    position: { lat: clickedLat, lng: clickedLng },
                    title: placeName
                });

                selectedPlace = {
                    lat: clickedLat,
                    lng: clickedLng,
                    name: placeName
                };
                console.log("Selected Place from click:", selectedPlace);

                // Update UI
                document.getElementById("location-name").textContent = placeName;
                document.getElementById("location-coords").textContent = clickedLat.toFixed(4) + ", " + clickedLng.toFixed(4);
                document.getElementById("status-location").classList.add("ready");
                document.getElementById("result-location").innerHTML = '<i class="fas fa-check-circle result-icon" style="color:var(--secondary)"></i><div class="result-content"><h4>' + placeName + '</h4><p>Seleccionado en mapa</p></div>';
                
                checkReadyState();

                // Fetch Live Data
                fetchElevationAndSlope(clickedLat, clickedLng);
                fetchAirQuality(clickedLat, clickedLng);
                fetchSolarPotential(clickedLat, clickedLng);
            });

            // Autocomplete setup (New Places API)
            const container = document.getElementById("autocomplete-container");
            container.innerHTML = '';
            
            const autocomplete = new PlaceAutocompleteElement();
            autocomplete.id = "pac-input";
            autocomplete.classList.add("controls");
            // Set attributes to try to satisfy browser warnings
            autocomplete.setAttribute("name", "place_search");
            container.appendChild(autocomplete);

            // Handler function to process the place selection
            const onPlaceSelect = async (event) => {
                console.log("Event fired:", event.type, event);
                
                let place = null;

                // Case 1: New PlaceAutocompleteElement (gmp-select) returns placePrediction
                if (event.placePrediction) {
                    console.log("Found placePrediction, converting to Place...");
                    place = event.placePrediction.toPlace();
                } 
                // Case 2: Some versions might return event.place directly
                else if (event.place) {
                    console.log("Found event.place");
                    place = event.place;
                }
                // Case 3: Fallback to details
                else if (event.detail?.place) {
                    place = event.detail.place;
                }
                // Case 4: Last resort, try getPlace()
                else if (typeof autocomplete.getPlace === 'function') {
                    try {
                        place = autocomplete.getPlace();
                        console.log("Retrieved via getPlace():", place);
                    } catch(e) { console.warn("getPlace failed", e); }
                }

                if (!place) {
                    console.warn("Could not retrieve Place object from event.");
                    return;
                }

                try {
                    // If it's a Place object from the new API, we MUST fetch fields
                    // We check for fetchFields method to distinguish from legacy PlaceResult
                    if (typeof place.fetchFields === 'function') {
                        console.log("Fetching fields for Place object...");
                        await place.fetchFields({ fields: ["displayName", "formattedAddress", "location", "viewport"] });
                        
                        if (!place.location) {
                            console.error("Place has no location after fetchFields");
                            alert("La ubicación seleccionada no tiene coordenadas válidas.");
                            return;
                        }
                        
                        handlePlaceSelection(place.location, place.displayName, place.viewport);
                    } 
                    // Legacy PlaceResult object (has geometry property directly)
                    else if (place.geometry && place.geometry.location) {
                        console.log("Using legacy PlaceResult object");
                        handlePlaceSelection(place.geometry.location, place.name || place.formatted_address, place.geometry.viewport);
                    }
                    else {
                        console.error("Unknown Place object structure:", place);
                    }
                } catch (err) {
                    console.error("Error processing place:", err);
                    alert("Error al procesar el lugar: " + err.message);
                }
            };

            // Add listeners for ALL potential event names to be safe
            autocomplete.addEventListener("gmp-places-select", onPlaceSelect);
            autocomplete.addEventListener("gmp-placeselect", onPlaceSelect);
            autocomplete.addEventListener("gmp-select", onPlaceSelect);

            // Fallback for "Enter" key without selection
            autocomplete.addEventListener("keydown", async (event) => {
                if (event.key === "Enter") {
                    const text = autocomplete.value;
                    console.log("Enter pressed in search box. Value:", text);
                    
                    // Allow a small delay to see if the select event fires first
                    setTimeout(() => {
                        // If no place is selected or the name doesn't match (rough check)
                        // We check if selectedPlace is null OR if the current selected place name is different from input text
                        // This prevents re-triggering if the user just hit enter on an already selected place
                        if (!selectedPlace || (selectedPlace.name !== text && text.length > 3)) {
                            console.log("Triggering manual Geocoding fallback for:", text);
                            const geocoder = new google.maps.Geocoder();
                            geocoder.geocode({ address: text }, (results, status) => {
                                if (status === "OK" && results[0]) {
                                    console.log("Geocoding success:", results[0]);
                                    handlePlaceSelection(results[0].geometry.location, results[0].formatted_address, results[0].geometry.viewport);
                                } else {
                                    console.warn("Geocoding failed or no results for:", text);
                                }
                            });
                        }
                    }, 500); // Increased delay to 500ms to ensure gmp-places-select has time to fire
                }
            });

            function handlePlaceSelection(location, name, viewport) {
                if (!location) {
                    window.alert("No se encontraron detalles de ubicación.");
                    return;
                }

                if (viewport) {
                    map.fitBounds(viewport);
                } else {
                    map.setCenter(location);
                    map.setZoom(15);
                }

                if (marker) marker.map = null;
                marker = new AdvancedMarkerElement({
                    map: map,
                    position: location,
                    title: name
                });

                selectedPlace = {
                    lat: location.lat(),
                    lng: location.lng(),
                    name: name
                };
                console.log("Selected Place updated:", selectedPlace);

                // Update UI
                document.getElementById("location-name").textContent = name;
                document.getElementById("location-coords").textContent = selectedPlace.lat.toFixed(4) + ", " + selectedPlace.lng.toFixed(4);
                document.getElementById("status-location").classList.add("ready");
                document.getElementById("result-location").innerHTML = '<i class="fas fa-check-circle result-icon" style="color:var(--secondary)"></i><div class="result-content"><h4>' + name + '</h4><p>Ubicacion confirmada</p></div>';
                
                // Enable analysis button
                checkReadyState();

                // Fetch Live Data
                fetchElevationAndSlope(selectedPlace.lat, selectedPlace.lng);
                fetchAirQuality(selectedPlace.lat, selectedPlace.lng);
                fetchSolarPotential(selectedPlace.lat, selectedPlace.lng);
            }
        }

        function fetchElevationAndSlope(lat, lng) {
            var elevator = new google.maps.ElevationService();
            var locations = [];
            // Center and 4 surrounding points (~100m offset)
            var offset = 0.001; 
            locations.push({ lat: lat, lng: lng });
            locations.push({ lat: lat + offset, lng: lng });
            locations.push({ lat: lat - offset, lng: lng });
            locations.push({ lat: lat, lng: lng + offset });
            locations.push({ lat: lat, lng: lng - offset });

            elevator.getElevationForLocations({ 'locations': locations }, function(results, status) {
                if (status === 'OK') {
                    if (results[0]) {
                        var centerElev = results[0].elevation;
                        document.getElementById("data-elevation").textContent = Math.round(centerElev) + " m";
                        
                        // Calculate max slope
                        var maxDiff = 0;
                        for (var i = 1; i < results.length; i++) {
                            var diff = Math.abs(results[i].elevation - centerElev);
                            if (diff > maxDiff) { maxDiff = diff; }
                        }
                        var slopePercent = (maxDiff / 111) * 100; // Rough approx
                        var slopeClass = slopePercent < 5 ? "Plano" : slopePercent < 15 ? "Suave" : slopePercent < 30 ? "Moderado" : "Pronunciado";
                        document.getElementById("data-slope").textContent = Math.round(slopePercent) + "% (" + slopeClass + ")";
                    } else {
                        document.getElementById("data-elevation").textContent = "N/D";
                        document.getElementById("data-slope").textContent = "N/D";
                    }
                } else {
                    document.getElementById("data-elevation").textContent = "Error";
                    document.getElementById("data-slope").textContent = "Error";
                }
            });
        }

        function fetchAirQuality(lat, lng) {
            var url = "https://airquality.googleapis.com/v1/currentConditions:lookup?key=" + MAPS_API_KEY;
            fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ location: { latitude: lat, longitude: lng } })
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.indexes && data.indexes.length > 0) {
                    var aqi = data.indexes[0];
                    var color = aqi.aqi <= 50 ? "#10b981" : aqi.aqi <= 100 ? "#f59e0b" : "#ef4444";
                    document.getElementById("data-aqi").innerHTML = '<span style="color:' + color + '">' + aqi.aqi + ' (' + aqi.category + ')</span>';
                } else {
                    document.getElementById("data-aqi").textContent = "N/D";
                }
            })
            .catch(function() { document.getElementById("data-aqi").textContent = "N/D"; });
        }

        function fetchSolarPotential(lat, lng) {
            var url = "https://solar.googleapis.com/v1/buildingInsights:findClosest?location.latitude=" + lat + "&location.longitude=" + lng + "&requiredQuality=LOW&key=" + MAPS_API_KEY;
            fetch(url)
            .then(function(response) { 
                if (response.status === 404) {
                    throw new Error("No solar data");
                }
                return response.json(); 
            })
            .then(function(data) {
                if (data.solarPotential) {
                    var hours = Math.round(data.solarPotential.maxSunshineHoursPerYear || 0);
                    document.getElementById("data-solar").textContent = hours + " hrs/yr";
                } else {
                    document.getElementById("data-solar").textContent = "Sin edificio";
                }
            })
            .catch(function(err) { 
                console.log("Solar API info:", err.message);
                document.getElementById("data-solar").textContent = "N/D"; 
            });
        }

        function onApproachChange() {
            var select = document.getElementById("approach-select");
            var value = select.value;
            if (!value) {
                selectedApproach = null;
                document.getElementById("indices-panel").classList.remove("active");
                document.getElementById("status-approach").classList.remove("ready");
                checkReadyState();
                return;
            }
            selectedApproach = value;
            var config = approaches[value];
            document.getElementById("status-approach").classList.add("ready");
            var html = "";
            for (var i = 0; i < config.indices.length; i++) {
                var idx = config.indices[i];
                html += '<div class="index-item"><div class="index-header"><div class="index-color" style="background:' + idx.color + '"></div><span class="index-name">' + idx.name + '</span><span class="index-api">' + idx.api + '</span></div><div class="index-desc">' + idx.desc + '</div></div>';
            }
            document.getElementById("indices-list").innerHTML = html;
            
            // Hide previous results if any
            var resultsContainer = document.getElementById("analysis-results");
            if (resultsContainer) {
                resultsContainer.style.display = "none";
                resultsContainer.innerHTML = "";
            }

            document.getElementById("indices-panel").classList.add("active");
            var resultEl = document.getElementById("result-approach");
            resultEl.innerHTML = '<i class="fas fa-' + config.icon + ' result-icon"></i><div class="result-content"><h4>' + config.name + '</h4><p>' + config.indices.length + ' capas de datos</p></div>';
            checkReadyState();
        }

        function onRadiusChange() {
            var select = document.getElementById("radius-select");
            var value = select.value;
            if (!value) {
                selectedRadius = null;
            } else {
                selectedRadius = parseInt(value);
            }
            checkReadyState();
        }

        function checkReadyState() {
            var btn = document.getElementById("analyze-btn");
            btn.disabled = !(selectedPlace && selectedApproach && selectedRadius);
            
            // Update button text to show what's missing
            var missing = [];
            if (!selectedPlace) missing.push("ubicación");
            if (!selectedApproach) missing.push("enfoque");
            if (!selectedRadius) missing.push("radio");
            
            var hint = document.querySelector("#analyze-btn + p");
            if (hint) {
                if (missing.length > 0) {
                    hint.textContent = "Requiere: " + missing.join(", ");
                } else {
                    hint.textContent = "✓ Listo para analizar";
                    hint.style.color = "var(--secondary)";
                }
            }
        }

        function centerMap() {
            if (map) {
                map.setCenter({ lat: -33.4489, lng: -70.6693 });
                map.setZoom(5);
            }
        }

        function toggleMapType() {
            if (map) {
                isSatellite = !isSatellite;
                map.setMapTypeId(isSatellite ? "hybrid" : "roadmap");
            }
        }

        var currentGeeLayer = null;

        function analyzeTerritory() {
            if (!selectedPlace || !selectedApproach) { return; }
            
            var btn = document.getElementById("analyze-btn");
            btn.innerHTML = '<span class="loading-spinner"></span> Procesando...';
            btn.disabled = true;

            var payload = {
                lat: selectedPlace.lat,
                lng: selectedPlace.lng,
                approach: selectedApproach,
                radius: selectedRadius
            };

            fetch('/api/v1/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                btn.innerHTML = '<i class="fas fa-satellite-dish"></i> Iniciar Analisis';
                btn.disabled = false;

                if (data.status === 'success') {
                    // Create Results Table
                    var tableHtml = '<table class="results-table" style="width:100%; border-collapse:collapse; margin-top:10px; font-size:0.9rem;">';
                    tableHtml += '<thead><tr style="background:var(--primary-light); color:white;"><th style="padding:8px; text-align:left;">Métrica</th><th style="padding:8px; text-align:right;">Valor</th></tr></thead><tbody>';
                    
                    for (var key in data.data) {
                        tableHtml += '<tr style="border-bottom:1px solid #eee;"><td style="padding:8px;">' + key + '</td><td style="padding:8px; text-align:right; font-weight:600;">' + data.data[key] + '</td></tr>';
                    }
                    tableHtml += '</tbody></table>';
                    
                    // Add area info
                    var areaKm2 = (data.area_m2 / 1000000).toFixed(2);
                    var areaInfo = '<div style="margin-top:0.5rem; padding:0.5rem; background:#f8fafc; border-radius:6px; font-size:0.8rem; color:var(--text-light);">' +
                        '<i class="fas fa-ruler-combined"></i> Area de analisis: <strong>' + data.area_m2.toLocaleString() + ' m²</strong> (' + areaKm2 + ' km²) | Radio: ' + (data.meta.buffer_radius_m || 1000) + 'm' +
                        '</div>';
                    
                    // Display in Analysis Results Container
                    var resultsContainer = document.getElementById("analysis-results");
                    if (!resultsContainer) {
                        resultsContainer = document.createElement("div");
                        resultsContainer.id = "analysis-results";
                        resultsContainer.style.marginBottom = "1rem";
                        var indicesPanel = document.getElementById("indices-panel");
                        indicesPanel.insertBefore(resultsContainer, document.getElementById("indices-list"));
                    }
                    
                    resultsContainer.innerHTML = '<div class="result-box" style="background:white; border:1px solid var(--secondary); border-radius:8px; padding:1rem; box-shadow:0 2px 4px rgba(0,0,0,0.05);">' +
                        '<h4 style="color:var(--primary); margin-top:0; margin-bottom:0.5rem; border-bottom:1px solid #eee; padding-bottom:0.5rem;"><i class="fas fa-chart-bar"></i> Resultados del Análisis</h4>' +
                        tableHtml + areaInfo +
                        '<button onclick="showInterpretationModal()" style="margin-top:1rem; width:100%;" class="btn btn-secondary"><i class="fas fa-info-circle"></i> Ver Escalas</button>' +
                        '</div>';
                    resultsContainer.style.display = "block";
                    
                    // Store FULL data for AI interpretation
                    window.lastAnalysisData = data.data;
                    window.lastApproach = selectedApproach;
                    window.lastAnalysisMeta = data.meta;
                    window.lastAnalysisArea = data.area_m2;
                    
                    // Scroll to results
                    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });

                    // Add GEE layer to map
                    if (data.map_layer && data.map_layer.url) {
                        if (currentGeeLayer) {
                            map.overlayMapTypes.removeAt(0);
                        }
                        
                        var geeMapType = new google.maps.ImageMapType({
                            getTileUrl: function(coord, zoom) {
                                var url = data.map_layer.url;
                                url = url.replace('{x}', coord.x).replace('{y}', coord.y).replace('{z}', zoom);
                                return url;
                            },
                            tileSize: new google.maps.Size(256, 256),
                            name: "GEE Layer",
                            opacity: 0.7
                        });

                        map.overlayMapTypes.insertAt(0, geeMapType);
                        currentGeeLayer = geeMapType;
                        console.log("Capa GEE agregada: " + data.map_layer.url);
                    }
                    
                    // Open Chat Sidebar with AI Interpretation
                    var locationName = selectedPlace ? selectedPlace.name : 'la ubicación seleccionada';
                    analysisContext = {
                        approach: selectedApproach,
                        results: data.data,
                        meta: data.meta,
                        area_m2: data.area_m2,
                        location: locationName
                    };
                    
                    // Open chat and send automatic interpretation request
                    document.getElementById('chat-sidebar').classList.add('open');
                    requestAIInterpretation(data.data, selectedApproach, locationName, data.area_m2, data.meta);
                    
                } else if (data.status === 'warning') {
                    alert("Aviso: " + data.message);
                } else {
                    alert("Error en el analisis: " + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                btn.innerHTML = '<i class="fas fa-satellite-dish"></i> Iniciar Analisis';
                btn.disabled = false;
                alert("Error de conexión. Por favor intenta de nuevo.");
            });
        }
        
        function showInterpretationModal() {
            var data = window.lastAnalysisData || {};
            var approach = window.lastApproach || '';
            var modalBody = document.getElementById('modal-body');
            var html = '';
            
            // Extract numeric values for interpretation
            var ndvi = parseFloat(Object.values(data).find(v => v && v.toString().match(/^-?\d+\.\d+$/) && parseFloat(v) >= -1 && parseFloat(v) <= 1) || 0);
            
            // NDVI Scale (if applicable)
            if (approach === 'mining' || approach === 'agriculture' || approach === 'environmental') {
                var ndviVal = 0;
                for (var k in data) {
                    if (k.toLowerCase().includes('ndvi') || k.toLowerCase().includes('vegetac')) {
                        ndviVal = parseFloat(data[k]) || 0;
                        break;
                    }
                }
                var ndviInterp = ndviVal > 0.6 ? 'Vegetacion densa y saludable. Excelente cobertura vegetal.' :
                                 ndviVal > 0.3 ? 'Vegetacion moderada. Cobertura vegetal aceptable.' :
                                 ndviVal > 0.1 ? 'Vegetacion escasa o con estres. Requiere atencion.' :
                                 'Sin vegetacion significativa o superficie construida/agua.';
                
                html += '<div class="scale-section">' +
                    '<div class="scale-title"><i class="fas fa-leaf" style="color:#22c55e"></i> Indice de Vegetacion (NDVI) <span class="value-badge">' + ndviVal.toFixed(2) + '</span></div>' +
                    '<div class="scale-bar ndvi"></div>' +
                    '<div class="scale-labels"><span>-1 (Agua)</span><span>0 (Suelo)</span><span>+1 (Vegetacion densa)</span></div>' +
                    '<div class="interpretation-text">' + ndviInterp + '</div>' +
                '</div>';
            }
            
            // NDWI Scale (if applicable)
            if (approach === 'flood-risk' || approach === 'water-management' || approach === 'mining') {
                var ndwiVal = 0;
                for (var k in data) {
                    if (k.toLowerCase().includes('ndwi') || k.toLowerCase().includes('agua')) {
                        ndwiVal = parseFloat(data[k]) || 0;
                        break;
                    }
                }
                var ndwiInterp = ndwiVal > 0.3 ? 'Alta presencia de agua. Zona de cuerpo de agua o saturacion.' :
                                 ndwiVal > 0 ? 'Humedad moderada. Suelo humedo o vegetacion con agua.' :
                                 ndwiVal > -0.3 ? 'Baja humedad. Suelo seco o vegetacion seca.' :
                                 'Muy seco. Suelo arido o superficie urbana.';
                
                html += '<div class="scale-section">' +
                    '<div class="scale-title"><i class="fas fa-water" style="color:#3b82f6"></i> Indice de Agua (NDWI) <span class="value-badge">' + ndwiVal.toFixed(2) + '</span></div>' +
                    '<div class="scale-bar ndwi"></div>' +
                    '<div class="scale-labels"><span>-1 (Seco)</span><span>0</span><span>+1 (Agua)</span></div>' +
                    '<div class="interpretation-text">' + ndwiInterp + '</div>' +
                '</div>';
            }
            
            // Slope Scale (if applicable)
            if (approach === 'real-estate' || approach === 'energy' || approach === 'land-planning' || approach === 'mining') {
                var slopeVal = 0;
                for (var k in data) {
                    if (k.toLowerCase().includes('pendiente') || k.toLowerCase().includes('slope')) {
                        slopeVal = parseFloat(data[k]) || 0;
                        break;
                    }
                }
                var slopeInterp = slopeVal < 5 ? 'Terreno plano. Ideal para construccion y agricultura mecanizada.' :
                                  slopeVal < 15 ? 'Pendiente suave. Apto para la mayoria de usos con algunas consideraciones.' :
                                  slopeVal < 30 ? 'Pendiente moderada. Requiere terrazas o muros de contencion.' :
                                  'Pendiente pronunciada. Alto riesgo de erosion, no apto para construccion convencional.';
                
                html += '<div class="scale-section">' +
                    '<div class="scale-title"><i class="fas fa-mountain" style="color:#8b5cf6"></i> Pendiente del Terreno <span class="value-badge">' + slopeVal.toFixed(1) + '°</span></div>' +
                    '<div class="scale-bar slope"></div>' +
                    '<div class="scale-labels"><span>0° (Plano)</span><span>15° (Suave)</span><span>45°+ (Escarpado)</span></div>' +
                    '<div class="interpretation-text">' + slopeInterp + '</div>' +
                '</div>';
            }
            
            // Generic interpretation if no specific scales
            if (html === '') {
                html = '<div class="scale-section">' +
                    '<div class="scale-title"><i class="fas fa-chart-bar"></i> Resumen del Analisis</div>' +
                    '<p style="color:var(--text-light)">Los resultados muestran los valores calculados para la ubicacion seleccionada. ' +
                    'Valores positivos en indices de vegetacion indican mayor cobertura vegetal. ' +
                    'Pendientes bajas son mejores para construccion.</p>' +
                '</div>';
            }
            
            // Add satellite info
            html += '<div style="margin-top:1rem; padding:1rem; background:#f0fdf4; border-radius:8px; font-size:0.85rem; color:var(--text-light);">' +
                '<i class="fas fa-satellite" style="color:var(--secondary)"></i> <strong>Fuente:</strong> Sentinel-2 MSI + SRTM | ' +
                '<i class="fas fa-calendar"></i> Imagen mas reciente disponible (ultimos 6 meses)' +
                '</div>';
            
            modalBody.innerHTML = html;
            document.getElementById('interpretation-modal').classList.add('active');
            
            // Store context for chat
            var locationName = selectedPlace ? selectedPlace.name : 'ubicación seleccionada';
            analysisContext = {
                approach: approach,
                results: data,
                location: locationName
            };
            
            // Fetch AI interpretation
            fetchAIInterpretation(data, approach, locationName);
        }
        
        function closeModal() {
            document.getElementById('interpretation-modal').classList.remove('active');
        }
        
        // Close modal on outside click
        document.getElementById('interpretation-modal').addEventListener('click', function(e) {
            if (e.target === this) closeModal();
        });
        
        // ============================================================================
        // CHAT AND AI FUNCTIONS
        // ============================================================================
        
        function toggleChat() {
            var sidebar = document.getElementById('chat-sidebar');
            sidebar.classList.toggle('open');
        }
        
        function sendChatMessage() {
            var input = document.getElementById('chat-input');
            var message = input.value.trim();
            if (!message) return;
            
            // Add user message to UI
            addChatMessage(message, 'user');
            input.value = '';
            
            // Add to history
            chatHistory.push({ role: 'user', content: message });
            
            // Show typing indicator
            var typingHtml = '<div class="chat-message assistant" id="typing-indicator">' +
                '<div class="message-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div></div>';
            document.getElementById('chat-messages').insertAdjacentHTML('beforeend', typingHtml);
            scrollChatToBottom();
            
            // Send to API
            fetch('/api/v1/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    context: analysisContext,
                    history: chatHistory
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                var typing = document.getElementById('typing-indicator');
                if (typing) typing.remove();
                
                if (data.status === 'success') {
                    addChatMessage(data.response, 'assistant');
                    chatHistory.push({ role: 'assistant', content: data.response });
                } else {
                    addChatMessage('Lo siento, hubo un error. Intenta de nuevo.', 'assistant');
                }
            })
            .catch(error => {
                var typing = document.getElementById('typing-indicator');
                if (typing) typing.remove();
                addChatMessage('Error de conexion. Verifica tu internet.', 'assistant');
            });
        }
        
        function addChatMessage(text, role) {
            var messagesContainer = document.getElementById('chat-messages');
            var time = new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' });
            var html = '<div class="chat-message ' + role + '">' +
                '<div class="message-bubble">' + text.replace(/\\n/g, '<br>') + '</div>' +
                '<div class="message-time">' + time + '</div></div>';
            messagesContainer.insertAdjacentHTML('beforeend', html);
            scrollChatToBottom();
        }
        
        function scrollChatToBottom() {
            var container = document.getElementById('chat-messages');
            container.scrollTop = container.scrollHeight;
        }
        
        function requestAIInterpretation(results, approach, locationName, areaM2, meta) {
            // Show typing indicator in chat
            var typingHtml = '<div class="chat-message assistant" id="interpretation-typing">' +
                '<div class="message-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div> Analizando datos...</div></div>';
            document.getElementById('chat-messages').insertAdjacentHTML('beforeend', typingHtml);
            scrollChatToBottom();
            
            var areaKm2 = (areaM2 / 1000000).toFixed(2);
            var radiusM = meta ? meta.buffer_radius_m : 1000;
            
            // Add area info to results for context
            var enrichedResults = Object.assign({}, results);
            enrichedResults['Área analizada'] = areaM2.toLocaleString() + ' m² (' + areaKm2 + ' km²)';
            enrichedResults['Radio de análisis'] = radiusM + ' metros';
            
            // Call interpret API (designed for analysis interpretation)
            fetch('/api/v1/interpret', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    results: enrichedResults,
                    approach: approach,
                    location: locationName
                })
            })
            .then(response => response.json())
            .then(data => {
                var typing = document.getElementById('interpretation-typing');
                if (typing) typing.remove();
                
                if (data.status === 'success') {
                    // Format and display interpretation
                    var formattedResponse = data.interpretation
                        .replace(/\n/g, '<br>')
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>');
                    
                    var interpretationHtml = '<div class="chat-message assistant">' +
                        '<div class="message-bubble" style="background: linear-gradient(135deg, #f0fdf4, #ecfeff); border-left: 3px solid var(--secondary);">' +
                        '<div style="font-weight:600; color:var(--primary); margin-bottom:0.5rem;"><i class="fas fa-robot"></i> Interpretación del Análisis</div>' +
                        '<div style="line-height:1.6;">' + formattedResponse + '</div>' +
                        '</div>' +
                        '<div class="message-time">' + new Date().toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' }) + '</div>' +
                        '</div>';
                    
                    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', interpretationHtml);
                    scrollChatToBottom();
                    
                    // Add to history
                    chatHistory.push({ role: 'user', content: 'Interpreta los resultados del análisis' });
                    chatHistory.push({ role: 'assistant', content: data.interpretation });
                    
                    // Add follow-up suggestion
                    var followUp = '<div class="chat-message assistant">' +
                        '<div class="message-bubble" style="font-size:0.85rem;">' +
                        '💡 ¿Tienes alguna duda sobre estos resultados? Puedes preguntarme sobre los indices, valores o significados.' +
                        '</div></div>';
                    document.getElementById('chat-messages').insertAdjacentHTML('beforeend', followUp);
                    scrollChatToBottom();
                } else {
                    addChatMessage('No pude generar la interpretación: ' + (data.message || 'Error desconocido'), 'assistant');
                }
            })
            .catch(error => {
                console.error('Interpretation error:', error);
                var typing = document.getElementById('interpretation-typing');
                if (typing) typing.remove();
                addChatMessage('Error al conectar con el asistente. Verifica tu conexión.', 'assistant');
            });
        }
        
        function fetchAIInterpretation(results, approach, locationName) {
            // Show loading in modal
            var modalBody = document.getElementById('modal-body');
            var existingContent = modalBody.innerHTML;
            
            var loadingHtml = '<div class="ai-loading" id="ai-loading">' +
                '<div class="typing-indicator"><span></span><span></span><span></span></div>' +
                '<span>Generando interpretacion con IA...</span></div>';
            modalBody.insertAdjacentHTML('beforeend', loadingHtml);
            
            fetch('/api/v1/interpret', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    results: results,
                    approach: approach,
                    location: locationName
                })
            })
            .then(response => response.json())
            .then(data => {
                var loading = document.getElementById('ai-loading');
                if (loading) loading.remove();
                
                if (data.status === 'success') {
                    var aiHtml = '<div class="ai-interpretation">' +
                        '<h5><i class="fas fa-robot"></i> Interpretacion del Asistente IA</h5>' +
                        '<div>' + data.interpretation.replace(/\\n/g, '<br>') + '</div>' +
                        '</div>';
                    modalBody.insertAdjacentHTML('beforeend', aiHtml);
                }
            })
            .catch(error => {
                var loading = document.getElementById('ai-loading');
                if (loading) loading.remove();
            });
        }

        // Start the map initialization
        loadGoogleMaps();
    </script>
</body>
</html>
'''

@app.route('/')
def landing():
    google_maps_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    if not google_maps_key:
        print("WARNING: GOOGLE_MAPS_API_KEY not found in environment variables.")
    else:
        print(f"INFO: GOOGLE_MAPS_API_KEY found (length: {len(google_maps_key)})")
    
    html = LANDING_HTML.replace('GOOGLE_MAPS_KEY_PLACEHOLDER', google_maps_key)
    return html

@app.route('/api/v1/health')
def health():
    return jsonify({"status": "healthy", "service": "GeoFeedback API", "version": "1.0.0"})

@app.route('/api/v1/stats')
def stats():
    return jsonify({"total_analyses": 147, "municipalities_served": 12, "apis_integrated": ["Elevation", "Air Quality", "Solar", "Geocoding"]})

@app.route('/api/v1/infrastructure')
def infrastructure():
    return jsonify({"features": [{"type": "school", "name": "Escuela Papudo", "lat": -32.5127, "lng": -71.4469}]})

@app.route('/api/v1/risk-zones')
def risk_zones():
    return jsonify({"zones": [{"level": "high", "area_ha": 45.2, "description": "Quebrada El Frances"}]})

@app.route('/api/docs')
def api_docs():
    return '''<!DOCTYPE html><html><head><title>GeoFeedback API</title><style>body{font-family:sans-serif;max-width:800px;margin:50px auto;padding:20px}h1{color:#1e3a5f}.endpoint{background:#f8fafc;padding:20px;border-radius:8px;margin:20px 0;border-left:4px solid #10b981}code{background:#e5e7eb;padding:2px 8px;border-radius:4px}.method{background:#10b981;color:white;padding:4px 12px;border-radius:4px}</style></head><body><h1>GeoFeedback API v1</h1><p>APIs integradas: Maps JavaScript, Elevation, Air Quality, Solar, Geocoding</p><div class="endpoint"><span class="method">GET</span> <code>/api/v1/health</code><p>Estado del servicio</p></div><div class="endpoint"><span class="method">GET</span> <code>/api/v1/stats</code><p>Estadisticas</p></div><div class="endpoint"><span class="method">GET</span> <code>/api/v1/infrastructure</code><p>Infraestructura</p></div><div class="endpoint"><span class="method">GET</span> <code>/api/v1/risk-zones</code><p>Zonas de riesgo</p></div><p><a href="/">Volver</a></p></body></html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
