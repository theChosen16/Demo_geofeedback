import logging
import sys
import os
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

# Configurar logging detallado al inicio
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("="*50)
logger.info("INICIANDO GEOFEEDBACK PAPUDO API")
logger.info(f"Python Version: {sys.version}")
logger.info("="*50)

app = Flask(__name__)
CORS(app)

# ===========================================================================
# LANDING PAGE - HTML INLINE
# ===========================================================================

@app.route('/')
def index():
    logger.info("Request received at /")
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoFeedback Papudo - Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { font-size: 2.5rem; margin-bottom: 10px; color: #64ffda; }
        .subtitle { color: #8892b0; margin-bottom: 40px; }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 { color: #64ffda; margin-bottom: 16px; font-size: 1.2rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px; }
        .stat { text-align: center; padding: 16px; background: rgba(100,255,218,0.1); border-radius: 8px; }
        .stat-value { font-size: 2rem; font-weight: bold; color: #64ffda; }
        .stat-label { color: #8892b0; font-size: 0.85rem; margin-top: 4px; }
        .risk-high { color: #ff6b6b !important; }
        .risk-medium { color: #ffd93d !important; }
        .risk-low { color: #6bcb77 !important; }
        .endpoint { 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 12px 16px;
            background: rgba(255,255,255,0.03);
            border-radius: 6px;
            margin-bottom: 8px;
        }
        .endpoint:hover { background: rgba(100,255,218,0.1); }
        .method { 
            background: #64ffda; 
            color: #1a1a2e; 
            padding: 4px 8px; 
            border-radius: 4px; 
            font-size: 0.75rem; 
            font-weight: bold;
        }
        a { color: #64ffda; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #64ffda;
            color: #1a1a2e;
            border-radius: 6px;
            font-weight: bold;
            margin-top: 16px;
        }
        .btn:hover { background: #4fd1c5; text-decoration: none; }
        .footer { margin-top: 40px; text-align: center; color: #8892b0; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌊 GeoFeedback Papudo</h1>
        <p class="subtitle">Sistema de Análisis de Riesgo de Inundación</p>
        
        <div class="card">
            <h2>📊 Estadísticas del Área de Estudio</h2>
            <div class="stats-grid">
                <div class="stat">
                    <div class="stat-value">20</div>
                    <div class="stat-label">Instalaciones</div>
                </div>
                <div class="stat">
                    <div class="stat-value risk-high">5</div>
                    <div class="stat-label">Riesgo Alto</div>
                </div>
                <div class="stat">
                    <div class="stat-value risk-medium">8</div>
                    <div class="stat-label">Riesgo Medio</div>
                </div>
                <div class="stat">
                    <div class="stat-value risk-low">7</div>
                    <div class="stat-label">Riesgo Bajo</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔌 API Endpoints Disponibles</h2>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/v1/health">/api/v1/health</a></span>
                <span style="color:#8892b0">Estado del sistema</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/v1/stats">/api/v1/stats</a></span>
                <span style="color:#8892b0">Estadísticas generales</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/v1/infrastructure">/api/v1/infrastructure</a></span>
                <span style="color:#8892b0">Infraestructura crítica</span>
            </div>
            <div class="endpoint">
                <span><span class="method">GET</span> <a href="/api/docs">/api/docs</a></span>
                <span style="color:#8892b0">Documentación API</span>
            </div>
        </div>
        
        <div class="card">
            <h2>🗺️ Visor de Mapas Interactivo</h2>
            <p style="color: #8892b0; margin-bottom: 16px;">
                Explora las zonas de riesgo de inundación en Papudo con nuestro visor web.
            </p>
            <a href="https://thechosen16.github.io/Demo_geofeedback/" target="_blank" class="btn">
                Ver Mapa Interactivo →
            </a>
        </div>
        
        <div class="footer">
            <p>GeoFeedback Chile • Noviembre 2025</p>
            <p style="margin-top:8px"><a href="https://github.com/theChosen16/Demo_geofeedback">📁 Repositorio GitHub</a></p>
        </div>
    </div>
</body>
</html>'''

@app.route('/favicon.ico')
def favicon():
    return '', 204

# ===========================================================================
# API ENDPOINTS
# ===========================================================================

@app.route('/api/v1/health')
def health():
    """Health check - sin dependencia de BD"""
    logger.info("Health check requested")
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'service': 'GeoFeedback Papudo API'
    })


@app.route('/api/v1/stats')
def stats():
    """Estadísticas de Papudo (datos estáticos del análisis)"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'location': 'Papudo, Región de Valparaíso, Chile',
        'area_km2': 15.4,
        'statistics': {
            'total_facilities': 20,
            'high_risk': 5,
            'medium_risk': 8,
            'low_risk': 7
        },
        'risk_distribution': [
            {'level': 3, 'name': 'Alto', 'color': '#ff6b6b', 'count': 5, 'percentage': 25.0},
            {'level': 2, 'name': 'Medio', 'color': '#ffd93d', 'count': 8, 'percentage': 40.0},
            {'level': 1, 'name': 'Bajo', 'color': '#6bcb77', 'count': 7, 'percentage': 35.0}
        ]
    })


@app.route('/api/v1/infrastructure')
def infrastructure():
    """Infraestructura crítica de Papudo"""
    facilities = [
        {'id': 1, 'name': 'Hospital de Papudo', 'category': 'health', 'risk_level': 3, 'risk_name': 'Alto', 'lat': -32.5067, 'lon': -71.4492},
        {'id': 2, 'name': 'Escuela Básica Papudo', 'category': 'education', 'risk_level': 2, 'risk_name': 'Medio', 'lat': -32.5089, 'lon': -71.4478},
        {'id': 3, 'name': 'Bomberos Papudo', 'category': 'emergency', 'risk_level': 1, 'risk_name': 'Bajo', 'lat': -32.5102, 'lon': -71.4501},
        {'id': 4, 'name': 'Municipalidad de Papudo', 'category': 'government', 'risk_level': 2, 'risk_name': 'Medio', 'lat': -32.5095, 'lon': -71.4485},
        {'id': 5, 'name': 'Carabineros Papudo', 'category': 'emergency', 'risk_level': 1, 'risk_name': 'Bajo', 'lat': -32.5078, 'lon': -71.4510},
    ]
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'count': len(facilities),
        'facilities': facilities
    })


@app.route('/api/docs')
def docs():
    """Documentación de la API"""
    return jsonify({
        'name': 'GeoFeedback Papudo API',
        'version': '1.0.0',
        'description': 'API REST para consultas de riesgo de inundación en Papudo, Chile',
        'base_url': 'https://demogeofeedback-production.up.railway.app',
        'endpoints': {
            'GET /': 'Landing page con estadísticas',
            'GET /api/v1/health': 'Health check del servicio',
            'GET /api/v1/stats': 'Estadísticas generales del área',
            'GET /api/v1/infrastructure': 'Lista de infraestructura crítica',
            'GET /api/docs': 'Esta documentación'
        },
        'repository': 'https://github.com/theChosen16/Demo_geofeedback'
    })


# ===========================================================================
# ERROR HANDLERS
# ===========================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado', 'status': 404}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {error}", exc_info=True)
    return jsonify({'error': 'Error interno del servidor', 'status': 500}), 500


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)