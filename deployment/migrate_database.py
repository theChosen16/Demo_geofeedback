#!/usr/bin/env python3
"""
Script de Migración de Base de Datos para Railway
==================================================
Inicializa la base de datos PostgreSQL con PostGIS y carga datos iniciales

Este script:
1. Crea extensiones PostGIS
2. Crea schemas organizados
3. Crea tablas con índices espaciales
4. Carga datos desde archivos locales
5. Crea funciones y vistas

Uso:
    python migrate_database.py

Variables de entorno requeridas (Railway las proporciona):
    DATABASE_URL - URL completa de conexión a PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import json
from pathlib import Path

# Colores para terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
END = '\033[0m'

def print_step(text):
    print(f"{BLUE}[→] {text}{END}")

def print_success(text):
    print(f"{GREEN}[✓] {text}{END}")

def print_error(text):
    print(f"{RED}[✗] {text}{END}")

def print_warning(text):
    print(f"{YELLOW}[!] {text}{END}")

# ============================================================================
# OBTENER CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

def get_db_config():
    """Obtiene configuración de BD desde DATABASE_URL o variables individuales"""
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        print_step("Usando DATABASE_URL de Railway")
        url = urlparse(database_url)
        return {
            'dbname': url.path[1:],
            'user': url.username,
            'password': url.password,
            'host': url.hostname,
            'port': url.port or 5432
        }
    else:
        print_step("Usando variables de entorno individuales")
        return {
            'dbname': os.getenv('DB_NAME', 'geofeedback_papudo'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432))
        }

# ============================================================================
# PASO 1: CREAR EXTENSIONES Y SCHEMAS
# ============================================================================

def create_extensions_and_schemas(conn):
    """Crea extensiones PostGIS y schemas organizados"""
    print_step("Creando extensiones PostGIS...")

    with conn.cursor() as cur:
        # Extensiones
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")
        print_success("Extensiones PostGIS creadas")

        # Schemas
        print_step("Creando schemas...")
        schemas = ['raw', 'processed', 'infrastructure', 'metadata', 'api']

        for schema in schemas:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
            cur.execute(f"COMMENT ON SCHEMA {schema} IS 'Schema para {schema}';")

        print_success(f"{len(schemas)} schemas creados")

    conn.commit()

# ============================================================================
# PASO 2: CREAR TABLAS
# ============================================================================

def create_tables(conn):
    """Crea todas las tablas necesarias"""
    print_step("Creando tablas...")

    with conn.cursor() as cur:
        # Tabla de polígonos de riesgo
        cur.execute("""
            CREATE TABLE IF NOT EXISTS processed.amenaza_poligonos (
                poly_id SERIAL PRIMARY KEY,
                risk_level INTEGER NOT NULL CHECK (risk_level IN (1, 2, 3)),
                risk_name VARCHAR(50) NOT NULL,
                risk_color VARCHAR(7) NOT NULL,
                area_m2 DOUBLE PRECISION,
                area_km2 DOUBLE PRECISION,
                perimeter_m DOUBLE PRECISION,
                geom GEOMETRY(Polygon, 32719) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_amenaza_geom
                ON processed.amenaza_poligonos USING GIST(geom);
            CREATE INDEX IF NOT EXISTS idx_amenaza_risk
                ON processed.amenaza_poligonos(risk_level);

            COMMENT ON TABLE processed.amenaza_poligonos IS
                'Polígonos de amenaza de inundación clasificados por nivel de riesgo';
        """)

        # Tabla de instalaciones
        cur.execute("""
            CREATE TABLE IF NOT EXISTS infrastructure.facilities (
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

            CREATE INDEX IF NOT EXISTS idx_facilities_geom
                ON infrastructure.facilities USING GIST(geom);

            COMMENT ON TABLE infrastructure.facilities IS
                'Infraestructura crítica de Papudo';
        """)

        # Tabla de instalaciones con riesgo
        cur.execute("""
            CREATE TABLE IF NOT EXISTS infrastructure.facilities_risk (
                id SERIAL PRIMARY KEY,
                osm_id BIGINT,
                name VARCHAR(255),
                category VARCHAR(100),
                amenity VARCHAR(100),
                shop VARCHAR(100),
                risk_level INTEGER,
                risk_name VARCHAR(50),
                risk_color VARCHAR(7),
                lon DOUBLE PRECISION,
                lat DOUBLE PRECISION,
                geom GEOMETRY(Point, 32719)
            );

            CREATE INDEX IF NOT EXISTS idx_facilities_risk_geom
                ON infrastructure.facilities_risk USING GIST(geom);
            CREATE INDEX IF NOT EXISTS idx_facilities_risk_level
                ON infrastructure.facilities_risk(risk_level);
        """)

        # Tabla de metadata
        cur.execute("""
            CREATE TABLE IF NOT EXISTS metadata.analysis_runs (
                id SERIAL PRIMARY KEY,
                analysis_type VARCHAR(100) NOT NULL,
                analysis_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                municipality VARCHAR(100) DEFAULT 'Papudo',
                slope_weight NUMERIC DEFAULT 0.50,
                ndvi_weight NUMERIC DEFAULT 0.35,
                depression_weight NUMERIC DEFAULT 0.15,
                total_area_km2 NUMERIC,
                high_risk_km2 NUMERIC,
                medium_risk_km2 NUMERIC,
                low_risk_km2 NUMERIC,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS metadata.config (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                description TEXT,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        print_success("Tablas creadas con índices espaciales")

    conn.commit()

# ============================================================================
# PASO 3: CARGAR DATOS DESDE GEOJSON
# ============================================================================

def load_infrastructure_data(conn):
    """Carga datos de infraestructura desde GeoJSON"""
    print_step("Cargando datos de infraestructura...")

    # Buscar archivo GeoJSON
    project_root = Path(__file__).parent.parent
    geojson_file = project_root / "data" / "processed" / "infrastructure_with_risk.geojson"

    if not geojson_file.exists():
        print_warning(f"Archivo no encontrado: {geojson_file}")
        print_warning("Saltando carga de infraestructura (se puede cargar después)")
        return

    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with conn.cursor() as cur:
        count = 0
        for feature in data['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']

            cur.execute("""
                INSERT INTO infrastructure.facilities_risk
                (osm_id, name, category, amenity, shop, risk_level, risk_name, risk_color, lon, lat, geom)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 32719))
            """, (
                props.get('osm_id'),
                props.get('name'),
                props.get('category'),
                props.get('amenity'),
                props.get('shop'),
                props.get('risk_level'),
                props.get('risk_name'),
                props.get('risk_color'),
                coords[0], coords[1],
                coords[0], coords[1]
            ))
            count += 1

        print_success(f"{count} instalaciones cargadas")

    conn.commit()

# ============================================================================
# PASO 4: CREAR FUNCIONES API
# ============================================================================

def create_api_functions(conn):
    """Crea funciones PL/pgSQL para la API"""
    print_step("Creando funciones API...")

    with conn.cursor() as cur:
        # Función: health_check
        cur.execute("""
            CREATE OR REPLACE FUNCTION api.health_check()
            RETURNS JSON
            LANGUAGE plpgsql
            AS $$
            DECLARE
                result JSON;
            BEGIN
                SELECT json_build_object(
                    'connected', true,
                    'database', current_database(),
                    'version', version(),
                    'postgis', postgis_version()
                ) INTO result;
                RETURN result;
            END;
            $$;
        """)

        # Función: get_risk_statistics
        cur.execute("""
            CREATE OR REPLACE FUNCTION api.get_risk_statistics()
            RETURNS TABLE (
                risk_level INTEGER,
                risk_name VARCHAR,
                risk_color VARCHAR,
                num_polygons BIGINT,
                total_area_km2 DOUBLE PRECISION,
                percentage DOUBLE PRECISION
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    p.risk_level,
                    p.risk_name,
                    p.risk_color,
                    COUNT(*) AS num_polygons,
                    SUM(p.area_km2) AS total_area_km2,
                    ROUND((SUM(p.area_km2) / (SELECT SUM(area_km2) FROM processed.amenaza_poligonos) * 100)::numeric, 2) AS percentage
                FROM processed.amenaza_poligonos p
                GROUP BY p.risk_level, p.risk_name, p.risk_color
                ORDER BY p.risk_level DESC;
            END;
            $$;
        """)

        # Función: get_risk_at_point
        cur.execute("""
            CREATE OR REPLACE FUNCTION api.get_risk_at_point(
                longitude DOUBLE PRECISION,
                latitude DOUBLE PRECISION
            )
            RETURNS TABLE (
                risk_level INTEGER,
                risk_name VARCHAR,
                risk_color VARCHAR,
                area_km2 DOUBLE PRECISION,
                poly_id INTEGER
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT
                    p.risk_level,
                    p.risk_name,
                    p.risk_color,
                    p.area_km2,
                    p.poly_id
                FROM processed.amenaza_poligonos p
                WHERE ST_Contains(
                    p.geom,
                    ST_Transform(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326), 32719)
                )
                LIMIT 1;
            END;
            $$;
        """)

        print_success("3 funciones API creadas")

    conn.commit()

# ============================================================================
# PASO 5: INSERTAR METADATA INICIAL
# ============================================================================

def insert_metadata(conn):
    """Inserta metadata de configuración"""
    print_step("Insertando metadata...")

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO metadata.config (key, value, description) VALUES
                ('crs_utm', 'EPSG:32719', 'Sistema de coordenadas UTM Zone 19S'),
                ('crs_wgs84', 'EPSG:4326', 'Sistema de coordenadas WGS84'),
                ('municipality', 'Papudo', 'Municipalidad'),
                ('region', 'Valparaíso', 'Región'),
                ('country', 'Chile', 'País'),
                ('version', '1.0.0', 'Versión del sistema')
            ON CONFLICT (key) DO NOTHING;
        """)

        print_success("Metadata insertada")

    conn.commit()

# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}MIGRACIÓN DE BASE DE DATOS - GEOFEEDBACK PAPUDO{END}")
    print(f"{BLUE}{'='*80}{END}\n")

    # Obtener configuración
    try:
        db_config = get_db_config()
        print_success(f"Conectando a: {db_config['host']}:{db_config['port']}/{db_config['dbname']}")
    except Exception as e:
        print_error(f"Error en configuración: {e}")
        sys.exit(1)

    # Conectar a la base de datos
    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False
        print_success("Conexión establecida")
    except Exception as e:
        print_error(f"Error de conexión: {e}")
        sys.exit(1)

    try:
        # Ejecutar pasos de migración
        create_extensions_and_schemas(conn)
        create_tables(conn)
        load_infrastructure_data(conn)
        create_api_functions(conn)
        insert_metadata(conn)

        print(f"\n{GREEN}{'='*80}{END}")
        print(f"{GREEN}✅ MIGRACIÓN COMPLETADA EXITOSAMENTE{END}")
        print(f"{GREEN}{'='*80}{END}\n")

    except Exception as e:
        conn.rollback()
        print_error(f"Error durante migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        conn.close()

if __name__ == '__main__':
    main()
