#!/usr/bin/env python3
"""
API REST para GeoFeedback Papudo
=================================
API Flask para consultar datos de riesgo de inundación e infraestructura crítica

Endpoints:
- GET /api/v1/health - Health check
- GET /api/v1/stats - Estadísticas generales
- GET /api/v1/risk/point?lon=X&lat=Y - Riesgo en punto específico
- GET /api/v1/risk/bbox?minLon=X&minLat=Y&maxLon=X&maxLat=Y - Polígonos en área
- GET /api/v1/infrastructure - Toda la infraestructura
- GET /api/v1/infrastructure/{id} - Infraestructura específica
- GET /api/v1/infrastructure/risk/{level} - Infraestructura por nivel de riesgo
- GET /api/v1/infrastructure/category/{category} - Infraestructura por categoría

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
DB_CONFIG = {
    'dbname': 'geofeedback_papudo',
    'user': 'geofeedback',
    'password': 'Papudo2025',
    'host': 'localhost',
    'port': 5432
}

# ===========================================================================
# DATABASE CONNECTION
# ===========================================================================

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        app.logger.error(f"Database connection error: {e}")
        return None

def query_db(query, params=None, fetchone=False):
    """Execute database query"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        result = cur.fetchone() if fetchone else cur.fetchall()
        cur.close()
        conn.close()
        return result
    except Exception as e:
        app.logger.error(f"Query error: {e}")
        if conn:
            conn.close()
        return None

# ===========================================================================
# ERROR HANDLERS
# ===========================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500

# ===========================================================================
# API ROUTES
# ===========================================================================

@app.route('/')
def index():
    """API root - Documentation"""
    return jsonify({
        'name': 'GeoFeedback Papudo API',
        'version': '1.0.0',
        'description': 'API REST para datos de riesgo de inundación',
        'endpoints': {
            'health': '/api/v1/health',
            'stats': '/api/v1/stats',
            'risk_point': '/api/v1/risk/point?lon=X&lat=Y',
            'risk_bbox': '/api/v1/risk/bbox?minLon=X&minLat=Y&maxLon=X&maxLat=Y',
            'infrastructure': '/api/v1/infrastructure',
            'infrastructure_by_id': '/api/v1/infrastructure/{id}',
            'infrastructure_by_risk': '/api/v1/infrastructure/risk/{level}',
            'infrastructure_by_category': '/api/v1/infrastructure/category/{category}'
        },
        'documentation': 'https://github.com/theChosen16/Demo_geofeedback'
    })

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    result = query_db("SELECT api.health_check() as health", fetchone=True)

    if result:
        health_data = result['health']
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': health_data
        })
    else:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'disconnected'
        }), 503

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get general statistics"""
    result = query_db("SELECT * FROM api.get_risk_statistics()")

    if result is None:
        return jsonify({'error': 'Error al obtener estadísticas'}), 500

    stats = []
    for row in result:
        stats.append({
            'risk_level': row['risk_level'],
            'risk_name': row['risk_name'],
            'risk_color': row['risk_color'],
            'num_polygons': row['num_polygons'],
            'total_area_km2': float(row['total_area_km2']) if row['total_area_km2'] else 0,
            'percentage': float(row['percentage']) if row['percentage'] else 0
        })

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'statistics': stats
    })

@app.route('/api/v1/risk/point', methods=['GET'])
def get_risk_at_point():
    """Get risk level at specific point"""
    lon = request.args.get('lon', type=float)
    lat = request.args.get('lat', type=float)

    if lon is None or lat is None:
        return jsonify({'error': 'Parámetros lon y lat requeridos'}), 400

    query = "SELECT * FROM api.get_risk_at_point(%s, %s)"
    result = query_db(query, (lon, lat), fetchone=True)

    if result is None:
        return jsonify({'error': 'Error al consultar riesgo'}), 500

    if result['risk_level'] is None:
        return jsonify({
            'lon': lon,
            'lat': lat,
            'risk_level': 0,
            'risk_name': 'Sin datos',
            'message': 'No hay datos de riesgo para esta ubicación'
        })

    return jsonify({
        'lon': lon,
        'lat': lat,
        'risk_level': result['risk_level'],
        'risk_name': result['risk_name'],
        'risk_color': result['risk_color'],
        'area_km2': float(result['area_km2']) if result['area_km2'] else 0,
        'polygon_id': result['poly_id']
    })

@app.route('/api/v1/risk/bbox', methods=['GET'])
def get_risk_in_bbox():
    """Get risk polygons in bounding box"""
    min_lon = request.args.get('minLon', type=float)
    min_lat = request.args.get('minLat', type=float)
    max_lon = request.args.get('maxLon', type=float)
    max_lat = request.args.get('maxLat', type=float)

    if None in [min_lon, min_lat, max_lon, max_lat]:
        return jsonify({'error': 'Parámetros minLon, minLat, maxLon, maxLat requeridos'}), 400

    query = "SELECT * FROM api.get_polygons_in_bbox(%s, %s, %s, %s)"
    result = query_db(query, (min_lon, min_lat, max_lon, max_lat))

    if result is None:
        return jsonify({'error': 'Error al consultar polígonos'}), 500

    polygons = []
    for row in result:
        polygons.append({
            'poly_id': row['poly_id'],
            'risk_level': row['risk_level'],
            'risk_name': row['risk_name'],
            'risk_color': row['risk_color'],
            'area_km2': float(row['area_km2']) if row['area_km2'] else 0,
            'geojson': json.loads(row['geojson'])
        })

    return jsonify({
        'bbox': {
            'minLon': min_lon,
            'minLat': min_lat,
            'maxLon': max_lon,
            'maxLat': max_lat
        },
        'count': len(polygons),
        'polygons': polygons
    })

@app.route('/api/v1/infrastructure', methods=['GET'])
def get_all_infrastructure():
    """Get all infrastructure facilities"""
    query = """
        SELECT
            id,
            name,
            category,
            risk_level,
            risk_name,
            risk_color,
            lon,
            lat,
            ST_AsGeoJSON(ST_Transform(geom, 4326))::json as geometry
        FROM infrastructure.facilities_risk
        ORDER BY risk_level DESC, name
    """

    result = query_db(query)

    if result is None:
        return jsonify({'error': 'Error al consultar infraestructura'}), 500

    facilities = []
    for row in result:
        facilities.append({
            'id': row['id'],
            'name': row['name'],
            'category': row['category'],
            'risk_level': row['risk_level'],
            'risk_name': row['risk_name'],
            'risk_color': row['risk_color'],
            'coordinates': {
                'lon': float(row['lon']) if row['lon'] else 0,
                'lat': float(row['lat']) if row['lat'] else 0
            },
            'geometry': row['geometry']
        })

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'count': len(facilities),
        'facilities': facilities
    })

@app.route('/api/v1/infrastructure/<int:facility_id>', methods=['GET'])
def get_infrastructure_by_id(facility_id):
    """Get specific infrastructure facility"""
    query = """
        SELECT
            id,
            osm_id,
            name,
            category,
            amenity,
            shop,
            risk_level,
            risk_name,
            risk_color,
            lon,
            lat,
            ST_AsGeoJSON(ST_Transform(geom, 4326))::json as geometry
        FROM infrastructure.facilities_risk
        WHERE id = %s
    """

    result = query_db(query, (facility_id,), fetchone=True)

    if result is None:
        return jsonify({'error': 'Instalación no encontrada'}), 404

    return jsonify({
        'id': result['id'],
        'osm_id': result['osm_id'],
        'name': result['name'],
        'category': result['category'],
        'amenity': result['amenity'],
        'shop': result['shop'],
        'risk_level': result['risk_level'],
        'risk_name': result['risk_name'],
        'risk_color': result['risk_color'],
        'coordinates': {
            'lon': float(result['lon']) if result['lon'] else 0,
            'lat': float(result['lat']) if result['lat'] else 0
        },
        'geometry': result['geometry']
    })

@app.route('/api/v1/infrastructure/risk/<int:risk_level>', methods=['GET'])
def get_infrastructure_by_risk(risk_level):
    """Get infrastructure by risk level"""
    if risk_level not in [1, 2, 3]:
        return jsonify({'error': 'Nivel de riesgo debe ser 1, 2 o 3'}), 400

    query = """
        SELECT
            id,
            name,
            category,
            risk_level,
            risk_name,
            risk_color,
            lon,
            lat
        FROM infrastructure.facilities_risk
        WHERE risk_level = %s
        ORDER BY category, name
    """

    result = query_db(query, (risk_level,))

    if result is None:
        return jsonify({'error': 'Error al consultar infraestructura'}), 500

    facilities = []
    for row in result:
        facilities.append({
            'id': row['id'],
            'name': row['name'],
            'category': row['category'],
            'risk_level': row['risk_level'],
            'risk_name': row['risk_name'],
            'risk_color': row['risk_color'],
            'coordinates': {
                'lon': float(row['lon']) if row['lon'] else 0,
                'lat': float(row['lat']) if row['lat'] else 0
            }
        })

    return jsonify({
        'risk_level': risk_level,
        'count': len(facilities),
        'facilities': facilities
    })

@app.route('/api/v1/infrastructure/category/<string:category>', methods=['GET'])
def get_infrastructure_by_category(category):
    """Get infrastructure by category"""
    valid_categories = ['Educación', 'Salud', 'Emergencias', 'Gobierno', 'Comercio']

    if category not in valid_categories:
        return jsonify({
            'error': 'Categoría inválida',
            'valid_categories': valid_categories
        }), 400

    query = """
        SELECT
            id,
            name,
            category,
            risk_level,
            risk_name,
            risk_color,
            lon,
            lat
        FROM infrastructure.facilities_risk
        WHERE category = %s
        ORDER BY risk_level DESC, name
    """

    result = query_db(query, (category,))

    if result is None:
        return jsonify({'error': 'Error al consultar infraestructura'}), 500

    facilities = []
    for row in result:
        facilities.append({
            'id': row['id'],
            'name': row['name'],
            'category': row['category'],
            'risk_level': row['risk_level'],
            'risk_name': row['risk_name'],
            'risk_color': row['risk_color'],
            'coordinates': {
                'lon': float(row['lon']) if row['lon'] else 0,
                'lat': float(row['lat']) if row['lat'] else 0
            }
        })

    return jsonify({
        'category': category,
        'count': len(facilities),
        'facilities': facilities
    })

# ===========================================================================
# RUN APPLICATION
# ===========================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("  GeoFeedback Papudo API")
    print("  Iniciando servidor Flask...")
    print("=" * 80)
    print()
    print("  API disponible en: http://localhost:5000")
    print("  Documentación: http://localhost:5000")
    print()
    print("  Endpoints:")
    print("    - GET /api/v1/health")
    print("    - GET /api/v1/stats")
    print("    - GET /api/v1/risk/point?lon=X&lat=Y")
    print("    - GET /api/v1/infrastructure")
    print()
    print("  Presiona Ctrl+C para detener")
    print("=" * 80)
    print()

    app.run(host='0.0.0.0', port=5000, debug=True)