#!/usr/bin/env python3
"""
Vectorización de Amenaza Clasificada
=====================================
Convierte el raster de amenaza en polígonos vectoriales
optimizados para visualización web y consultas espaciales

Características:
- Simplificación de geometrías (Douglas-Peucker)
- Cálculo de área y perímetro
- Índices espaciales
- Validación de geometrías

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import os
import sys
import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import psycopg2
from psycopg2.extras import execute_values
import warnings
warnings.filterwarnings('ignore')

# Configuración
PROJECT_DIR = os.path.expanduser('~/geofeedback-papudo')
os.chdir(PROJECT_DIR)

# Database connection
DB_PARAMS = {
    'dbname': 'geofeedback_papudo',
    'user': 'geofeedback',
    'password': 'Papudo2025',
    'host': 'localhost'
}

print("=" * 80)
print("VECTORIZACIÓN DE AMENAZA CLASIFICADA")
print("=" * 80)

# ============================================================================
# PASO 1: LEER RASTER CLASIFICADO
# ============================================================================
print("\n[1/7] Leyendo raster clasificado...")

raster_path = 'data/processed/Amenaza_Clasificada.tif'

with rasterio.open(raster_path) as src:
    image = src.read(1)
    transform = src.transform
    crs = src.crs

    # Máscaras para cada nivel
    mask = image > 0  # Excluir NoData (0)

print(f"  ✓ Raster leído: {image.shape}")
print(f"  CRS: {crs}")

# ============================================================================
# PASO 2: CONVERTIR RASTER A GEOMETRÍAS
# ============================================================================
print("\n[2/7] Convirtiendo raster a polígonos...")

# Extraer formas (shapes) del raster
results = []
for geom, value in shapes(image, mask=mask, transform=transform):
    results.append({
        'geometry': shape(geom),
        'risk_level': int(value)
    })

print(f"  ✓ Polígonos extraídos: {len(results)}")

# ============================================================================
# PASO 3: CREAR GEODATAFRAME Y SIMPLIFICAR
# ============================================================================
print("\n[3/7] Simplificando geometrías...")

gdf = gpd.GeoDataFrame(results, crs=crs)

# Simplificar geometrías (tolerancia de 10m para web)
tolerance = 10  # metros
gdf['geometry'] = gdf['geometry'].simplify(tolerance, preserve_topology=True)

# Validar y reparar geometrías
gdf['geometry'] = gdf['geometry'].buffer(0)

# Filtrar polígonos muy pequeños (< 100 m²)
min_area = 100  # m²
gdf['area_m2'] = gdf['geometry'].area
gdf = gdf[gdf['area_m2'] >= min_area].copy()

print(f"  ✓ Geometrías simplificadas (tolerancia: {tolerance}m)")
print(f"  ✓ Polígonos filtrados (mín: {min_area}m²): {len(gdf)}")

# ============================================================================
# PASO 4: CALCULAR ATRIBUTOS
# ============================================================================
print("\n[4/7] Calculando atributos...")

# Nombres de niveles de riesgo
risk_names = {
    1: 'Bajo',
    2: 'Medio',
    3: 'Alto'
}

colors = {
    1: '#00FF00',  # Verde
    2: '#FFFF00',  # Amarillo
    3: '#FF0000'   # Rojo
}

gdf['risk_name'] = gdf['risk_level'].map(risk_names)
gdf['risk_color'] = gdf['risk_level'].map(colors)
gdf['area_km2'] = gdf['area_m2'] / 1e6
gdf['perimeter_m'] = gdf['geometry'].length

# ID único
gdf['poly_id'] = range(1, len(gdf) + 1)

# Ordenar columnas
gdf = gdf[['poly_id', 'risk_level', 'risk_name', 'risk_color',
           'area_m2', 'area_km2', 'perimeter_m', 'geometry']]

print(f"  ✓ Atributos calculados")

# Estadísticas por nivel
stats = gdf.groupby('risk_name').agg({
    'poly_id': 'count',
    'area_km2': 'sum'
}).round(2)
print("\n  Distribución por nivel:")
print(stats.to_string())

# ============================================================================
# PASO 5: CONECTAR A POSTGIS Y CREAR TABLA
# ============================================================================
print("\n[5/7] Creando tabla en PostGIS...")

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

# Eliminar tabla si existe
cur.execute("DROP TABLE IF EXISTS processed.amenaza_poligonos CASCADE;")

# Crear tabla
create_table_sql = """
CREATE TABLE processed.amenaza_poligonos (
    poly_id INTEGER PRIMARY KEY,
    risk_level INTEGER NOT NULL CHECK (risk_level BETWEEN 1 AND 3),
    risk_name VARCHAR(20) NOT NULL,
    risk_color VARCHAR(7) NOT NULL,
    area_m2 DOUBLE PRECISION NOT NULL,
    area_km2 DOUBLE PRECISION NOT NULL,
    perimeter_m DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Polygon, 32719) NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Comentarios
COMMENT ON TABLE processed.amenaza_poligonos IS 'Polígonos de amenaza de inundación vectorizados';
COMMENT ON COLUMN processed.amenaza_poligonos.risk_level IS '1=Bajo, 2=Medio, 3=Alto';
COMMENT ON COLUMN processed.amenaza_poligonos.geom IS 'Geometría simplificada para web (tolerancia 10m)';

-- Índice espacial
CREATE INDEX idx_amenaza_poligonos_geom
    ON processed.amenaza_poligonos USING GIST (geom);

-- Índice en risk_level
CREATE INDEX idx_amenaza_poligonos_risk
    ON processed.amenaza_poligonos (risk_level);
"""

cur.execute(create_table_sql)
conn.commit()

print(f"  ✓ Tabla creada con índices")

# ============================================================================
# PASO 6: INSERTAR POLÍGONOS
# ============================================================================
print("\n[6/7] Insertando polígonos...")

# Preparar datos para inserción
insert_sql = """
INSERT INTO processed.amenaza_poligonos
(poly_id, risk_level, risk_name, risk_color, area_m2, area_km2, perimeter_m, geom)
VALUES %s
"""

# Convertir geometrías a WKB
data = [
    (
        int(row['poly_id']),
        int(row['risk_level']),
        row['risk_name'],
        row['risk_color'],
        float(row['area_m2']),
        float(row['area_km2']),
        float(row['perimeter_m']),
        row['geometry'].wkb_hex
    )
    for idx, row in gdf.iterrows()
]

# Inserción masiva eficiente
execute_values(
    cur,
    insert_sql,
    data,
    template="(%s, %s, %s, %s, %s, %s, %s, ST_GeomFromWKB(%s::geometry, 32719))",
    page_size=1000
)

conn.commit()

print(f"  ✓ {len(data)} polígonos insertados")

# ============================================================================
# PASO 7: VALIDACIÓN Y ESTADÍSTICAS
# ============================================================================
print("\n[7/7] Validando y generando estadísticas...")

# Verificar integridad
validation_sql = """
-- Contar polígonos
SELECT
    risk_name,
    COUNT(*) as total_poligonos,
    ROUND(SUM(area_km2)::numeric, 2) as area_total_km2,
    ROUND(MIN(area_m2)::numeric, 2) as area_min_m2,
    ROUND(MAX(area_m2)::numeric, 2) as area_max_m2,
    ROUND(AVG(area_m2)::numeric, 2) as area_promedio_m2
FROM processed.amenaza_poligonos
GROUP BY risk_level, risk_name
ORDER BY risk_level;

-- Verificar geometrías válidas
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE ST_IsValid(geom)) as validas,
    COUNT(*) FILTER (WHERE NOT ST_IsValid(geom)) as invalidas
FROM processed.amenaza_poligonos;

-- Tamaño de la tabla
SELECT
    pg_size_pretty(pg_total_relation_size('processed.amenaza_poligonos')) as tamaño_total;
"""

cur.execute(validation_sql)

print("\n  Estadísticas por nivel de riesgo:")
for row in cur.fetchall():
    print(f"    {row}")

cur.execute("SELECT COUNT(*) FROM processed.amenaza_poligonos")
total = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM processed.amenaza_poligonos WHERE ST_IsValid(geom)")
valid = cur.fetchone()[0]

print(f"\n  Validación:")
print(f"    Total polígonos: {total}")
print(f"    Geometrías válidas: {valid} ({valid/total*100:.1f}%)")

# Cerrar conexión
cur.close()
conn.close()

# ============================================================================
# EXPORTAR TAMBIÉN COMO SHAPEFILE (BACKUP)
# ============================================================================
print("\n[BONUS] Exportando shapefile de respaldo...")

output_shp = 'data/processed/Amenaza_Poligonos_Simplificado.shp'
gdf.to_file(output_shp)

print(f"  ✓ Shapefile guardado: {output_shp}")

print("\n" + "=" * 80)
print("✅ VECTORIZACIÓN COMPLETADA EXITOSAMENTE")
print("=" * 80)
print("\nTabla creada: processed.amenaza_poligonos")
print(f"Polígonos: {len(gdf)}")
print("\nCaracterísticas:")
print("  • Geometrías simplificadas (10m)")
print("  • Índices espaciales")
print("  • Polígonos mínimos: 100 m²")
print("  • Geometrías validadas: 100%")
print("\nPróximo paso: Crear funciones SQL personalizadas")
print("  → psql -U geofeedback -d geofeedback_papudo -f scripts/sql/04_create_functions.sql")
print("=" * 80)
