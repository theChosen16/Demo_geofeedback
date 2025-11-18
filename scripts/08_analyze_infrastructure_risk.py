#!/usr/bin/env python3
"""
Análisis de Riesgo de Infraestructura Crítica
==============================================
Identifica qué infraestructura está en zonas de riesgo de inundación

Proceso:
1. Cargar infraestructura desde GeoJSON
2. Cargar polígonos de riesgo desde PostGIS
3. Realizar intersección espacial
4. Generar estadísticas y reporte
5. Guardar resultados en PostGIS

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime

# Colores
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
END = '\033[0m'

# Configuración
PROJECT_DIR = Path(__file__).parent.parent
INFRA_FILE = PROJECT_DIR / "data" / "infrastructure" / "infraestructura_completa.geojson"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DB_PARAMS = {
    'dbname': 'geofeedback_papudo',
    'user': 'geofeedback',
    'password': 'Papudo2025',
    'host': 'localhost'
}

print(f"\n{BLUE}{BOLD}{'='*80}{END}")
print(f"{BLUE}{BOLD}ANÁLISIS DE RIESGO DE INFRAESTRUCTURA CRÍTICA - PAPUDO{END}")
print(f"{BLUE}{BOLD}{'='*80}{END}\n")

# ============================================================================
# PASO 1: CARGAR INFRAESTRUCTURA
# ============================================================================

print(f"{CYAN}[1/5] Cargando infraestructura desde GeoJSON...{END}")

with open(INFRA_FILE, 'r', encoding='utf-8') as f:
    infra_data = json.load(f)

features = infra_data['features']
print(f"{GREEN}  ✓ Cargados {len(features)} elementos de infraestructura{END}")

# ============================================================================
# PASO 2: CONECTAR A POSTGIS Y CREAR TABLA
# ============================================================================

print(f"\n{CYAN}[2/5] Conectando a PostGIS y creando tablas...{END}")

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Crear tabla de infraestructura
cur.execute("""
    DROP TABLE IF EXISTS infrastructure.facilities CASCADE;

    CREATE TABLE infrastructure.facilities (
        id SERIAL PRIMARY KEY,
        osm_id BIGINT,
        osm_type VARCHAR(20),
        name VARCHAR(255),
        category VARCHAR(100),
        amenity VARCHAR(100),
        shop VARCHAR(100),
        building VARCHAR(100),
        addr_street VARCHAR(255),
        addr_number VARCHAR(50),
        lon DOUBLE PRECISION,
        lat DOUBLE PRECISION,
        geom GEOMETRY(Point, 32719),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    COMMENT ON TABLE infrastructure.facilities IS 'Infraestructura crítica de Papudo';
""")

print(f"{GREEN}  ✓ Tabla infrastructure.facilities creada{END}")

# ============================================================================
# PASO 3: INSERTAR INFRAESTRUCTURA
# ============================================================================

print(f"\n{CYAN}[3/5] Insertando infraestructura en PostGIS...{END}")

insert_sql = """
    INSERT INTO infrastructure.facilities
    (osm_id, osm_type, name, category, amenity, shop, building, addr_street, addr_number, lon, lat, geom)
    VALUES (
        %(osm_id)s,
        %(osm_type)s,
        %(name)s,
        %(category)s,
        %(amenity)s,
        %(shop)s,
        %(building)s,
        %(addr_street)s,
        %(addr_number)s,
        %(lon)s,
        %(lat)s,
        ST_Transform(ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326), 32719)
    )
"""

inserted = 0
for feature in features:
    props = feature['properties']
    coords = feature['geometry']['coordinates']

    data = {
        'osm_id': props.get('osm_id'),
        'osm_type': props.get('osm_type', ''),
        'name': props.get('name', 'Sin nombre'),
        'category': props.get('category', ''),
        'amenity': props.get('amenity', ''),
        'shop': props.get('shop', ''),
        'building': props.get('building', ''),
        'addr_street': props.get('addr_street', ''),
        'addr_number': props.get('addr_number', ''),
        'lon': coords[0],
        'lat': coords[1]
    }

    cur.execute(insert_sql, data)
    inserted += 1

conn.commit()
print(f"{GREEN}  ✓ {inserted} instalaciones insertadas{END}")

# Crear índice espacial
cur.execute("CREATE INDEX idx_facilities_geom ON infrastructure.facilities USING GIST(geom);")
conn.commit()
print(f"{GREEN}  ✓ Índice espacial creado{END}")

# ============================================================================
# PASO 4: ANÁLISIS DE INTERSECCIÓN CON RIESGO
# ============================================================================

print(f"\n{CYAN}[4/5] Analizando intersección con zonas de riesgo...{END}")

# Tabla de resultados
cur.execute("""
    DROP TABLE IF EXISTS infrastructure.facilities_risk CASCADE;

    CREATE TABLE infrastructure.facilities_risk AS
    SELECT
        f.id,
        f.osm_id,
        f.name,
        f.category,
        f.amenity,
        f.shop,
        f.lon,
        f.lat,
        COALESCE(p.risk_level, 0) AS risk_level,
        COALESCE(p.risk_name, 'Sin Riesgo') AS risk_name,
        COALESCE(p.risk_color, '#00FF00') AS risk_color,
        f.geom
    FROM infrastructure.facilities f
    LEFT JOIN processed.amenaza_poligonos p
        ON ST_Contains(p.geom, f.geom);

    CREATE INDEX idx_facilities_risk_geom ON infrastructure.facilities_risk USING GIST(geom);
    CREATE INDEX idx_facilities_risk_level ON infrastructure.facilities_risk(risk_level);

    COMMENT ON TABLE infrastructure.facilities_risk IS 'Infraestructura con nivel de riesgo asignado';
""")

conn.commit()
print(f"{GREEN}  ✓ Análisis de intersección completado{END}")

# ============================================================================
# PASO 5: GENERAR ESTADÍSTICAS Y REPORTE
# ============================================================================

print(f"\n{CYAN}[5/5] Generando estadísticas y reporte...{END}")

# Estadísticas generales
cur.execute("""
    SELECT
        risk_level,
        risk_name,
        COUNT(*) as count,
        json_agg(json_build_object('name', name, 'category', category)) as facilities
    FROM infrastructure.facilities_risk
    GROUP BY risk_level, risk_name
    ORDER BY risk_level DESC
""")

stats = cur.fetchall()

print(f"\n{BLUE}{'='*80}{END}")
print(f"{BOLD}RESUMEN DE RIESGO POR INFRAESTRUCTURA{END}")
print(f"{BLUE}{'='*80}{END}\n")

total_count = 0
report_data = {
    'timestamp': datetime.now().isoformat(),
    'total_facilities': len(features),
    'risk_distribution': {},
    'detailed_facilities': {}
}

for stat in stats:
    risk_level = stat['risk_level']
    risk_name = stat['risk_name']
    count = stat['count']
    facilities = stat['facilities']

    total_count += count

    # Color según riesgo
    if risk_level == 3:
        color = RED
    elif risk_level == 2:
        color = YELLOW
    elif risk_level == 1:
        color = CYAN
    else:
        color = GREEN

    print(f"{color}{BOLD}{risk_name}: {count} instalaciones{END}")

    report_data['risk_distribution'][risk_name] = count
    report_data['detailed_facilities'][risk_name] = []

    # Listar instalaciones
    for facility in facilities:
        print(f"{color}  • {facility['name']} ({facility['category']}){END}")
        report_data['detailed_facilities'][risk_name].append(facility)

    print()

# Estadísticas por categoría
print(f"{BLUE}{'='*80}{END}")
print(f"{BOLD}DISTRIBUCIÓN POR CATEGORÍA{END}")
print(f"{BLUE}{'='*80}{END}\n")

cur.execute("""
    SELECT
        category,
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE risk_level = 3) as high_risk,
        COUNT(*) FILTER (WHERE risk_level = 2) as medium_risk,
        COUNT(*) FILTER (WHERE risk_level = 1) as low_risk,
        COUNT(*) FILTER (WHERE risk_level = 0) as no_risk
    FROM infrastructure.facilities_risk
    GROUP BY category
    ORDER BY total DESC
""")

category_stats = cur.fetchall()
report_data['category_distribution'] = []

for cat_stat in category_stats:
    print(f"{BOLD}{cat_stat['category']}{END} (Total: {cat_stat['total']})")
    print(f"  {RED}Alto: {cat_stat['high_risk']}{END} | ", end='')
    print(f"{YELLOW}Medio: {cat_stat['medium_risk']}{END} | ", end='')
    print(f"{CYAN}Bajo: {cat_stat['low_risk']}{END} | ", end='')
    print(f"{GREEN}Sin riesgo: {cat_stat['no_risk']}{END}")
    print()

    report_data['category_distribution'].append({
        'category': cat_stat['category'],
        'total': cat_stat['total'],
        'high_risk': cat_stat['high_risk'],
        'medium_risk': cat_stat['medium_risk'],
        'low_risk': cat_stat['low_risk'],
        'no_risk': cat_stat['no_risk']
    })

# Guardar reporte JSON
report_file = OUTPUT_DIR / "infrastructure_risk_report.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report_data, f, indent=2, ensure_ascii=False)

print(f"{GREEN}✓ Reporte guardado: {report_file}{END}\n")

# Exportar GeoJSON con riesgo
cur.execute("""
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(
            json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::json,
                'properties', json_build_object(
                    'name', name,
                    'category', category,
                    'risk_level', risk_level,
                    'risk_name', risk_name,
                    'risk_color', risk_color
                )
            )
        )
    )
    FROM infrastructure.facilities_risk
""")

geojson_result = list(cur.fetchone().values())[0]

geojson_file = OUTPUT_DIR / "infrastructure_with_risk.geojson"
with open(geojson_file, 'w', encoding='utf-8') as f:
    json.dump(geojson_result, f, indent=2, ensure_ascii=False)

print(f"{GREEN}✓ GeoJSON con riesgo: {geojson_file}{END}\n")

# ============================================================================
# FINALIZAR
# ============================================================================

cur.close()
conn.close()

print(f"{BLUE}{'='*80}{END}")
print(f"{GREEN}{BOLD}✅ ANÁLISIS DE RIESGO DE INFRAESTRUCTURA COMPLETADO{END}")
print(f"{BLUE}{'='*80}{END}\n")

print("Tablas PostGIS creadas:")
print("  • infrastructure.facilities - Infraestructura original")
print("  • infrastructure.facilities_risk - Con nivel de riesgo")
print()
print("Archivos generados:")
print(f"  • {report_file.name}")
print(f"  • {geojson_file.name}")
print()
print("Próximo paso: Crear mapa visual")
print("  python scripts/09_create_infrastructure_map.py")
print()
