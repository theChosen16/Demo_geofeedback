#!/usr/bin/env python3
"""
Testing y Validación de PostGIS
================================
Valida la configuración completa de la base de datos geoespacial

Tests:
- Conectividad
- Tablas y schemas
- Índices espaciales
- Funciones personalizadas
- Vistas materializadas
- Consultas espaciales
- Rendimiento

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import time

# Configuración
DB_PARAMS = {
    'dbname': 'geofeedback_papudo',
    'user': 'geofeedback',
    'password': 'Papudo2025',
    'host': 'localhost'
}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{'='*80}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{text}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{'='*80}{bcolors.ENDC}\n")

def print_success(text):
    print(f"{bcolors.OKGREEN}✓ {text}{bcolors.ENDC}")

def print_error(text):
    print(f"{bcolors.FAIL}✗ {text}{bcolors.ENDC}")

def print_info(text):
    print(f"{bcolors.OKCYAN}ℹ {text}{bcolors.ENDC}")

def print_warning(text):
    print(f"{bcolors.WARNING}⚠ {text}{bcolors.ENDC}")

# ============================================================================
# TEST 1: CONECTIVIDAD
# ============================================================================

def test_connectivity():
    print_header("TEST 1: CONECTIVIDAD A POSTGRESQL")

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT version(), current_database(), current_user")
        result = cur.fetchone()

        print_success(f"Conexión establecida")
        print_info(f"Database: {result['current_database']}")
        print_info(f"User: {result['current_user']}")
        print_info(f"PostgreSQL: {result['version'].split(',')[0]}")

        # PostGIS version
        cur.execute("SELECT postgis_full_version()")
        postgis_version = cur.fetchone()['postgis_full_version']
        print_info(f"PostGIS: {postgis_version.split('POSTGIS=')[1].split()[0]}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print_error(f"Error de conexión: {e}")
        return False

# ============================================================================
# TEST 2: SCHEMAS Y TABLAS
# ============================================================================

def test_schemas_and_tables():
    print_header("TEST 2: SCHEMAS Y TABLAS")

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Verificar schemas
        expected_schemas = ['raw', 'processed', 'infrastructure', 'metadata', 'api']
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = ANY(%s)
        """, (expected_schemas,))

        schemas = [row['schema_name'] for row in cur.fetchall()]

        for schema in expected_schemas:
            if schema in schemas:
                print_success(f"Schema '{schema}' existe")
            else:
                print_error(f"Schema '{schema}' NO existe")

        # Verificar tablas principales
        expected_tables = {
            'processed': ['amenaza_poligonos', 'amenaza_clasificada', 'amenaza_score_continuo', 'pendiente'],
            'metadata': ['analysis_runs', 'config', 'change_log']
        }

        for schema, tables in expected_tables.items():
            cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = %s AND tablename = ANY(%s)
            """, (schema, tables))

            found_tables = [row['tablename'] for row in cur.fetchall()]

            for table in tables:
                full_name = f"{schema}.{table}"
                if table in found_tables:
                    # Contar filas
                    try:
                        cur.execute(f"SELECT COUNT(*) as cnt FROM {full_name}")
                        count = cur.fetchone()['cnt']
                        print_success(f"Tabla '{full_name}' existe ({count:,} filas)")
                    except:
                        print_success(f"Tabla '{full_name}' existe")
                else:
                    print_error(f"Tabla '{full_name}' NO existe")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================================
# TEST 3: ÍNDICES ESPACIALES
# ============================================================================

def test_spatial_indexes():
    print_header("TEST 3: ÍNDICES ESPACIALES")

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname IN ('processed', 'api')
                AND indexdef LIKE '%gist%'
            ORDER BY tablename, indexname
        """)

        indexes = cur.fetchall()

        if indexes:
            print_success(f"Encontrados {len(indexes)} índices espaciales:")
            for idx in indexes:
                print_info(f"  • {idx['tablename']}: {idx['indexname']}")
        else:
            print_warning("No se encontraron índices espaciales")

        cur.close()
        conn.close()
        return len(indexes) > 0

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================================
# TEST 4: FUNCIONES PERSONALIZADAS
# ============================================================================

def test_custom_functions():
    print_header("TEST 4: FUNCIONES PERSONALIZADAS")

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Listar funciones en schema api
        cur.execute("""
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'api'
                AND routine_type = 'FUNCTION'
            ORDER BY routine_name
        """)

        functions = [row['routine_name'] for row in cur.fetchall()]

        expected_functions = [
            'get_risk_at_point',
            'get_risk_statistics',
            'get_polygons_in_bbox',
            'get_risk_within_radius',
            'get_top_polygons',
            'get_all_polygons_geojson',
            'get_raster_value_at_point',
            'health_check',
            'refresh_all_views'
        ]

        for func in expected_functions:
            if func in functions:
                print_success(f"Función 'api.{func}' existe")
            else:
                print_error(f"Función 'api.{func}' NO existe")

        # Test función health_check
        print_info("\nEjecutando health_check()...")
        cur.execute("SELECT api.health_check()")
        health = cur.fetchone()['health_check']
        print(json.dumps(health, indent=2))

        # Test función get_risk_statistics
        print_info("\nEjecutando get_risk_statistics()...")
        cur.execute("SELECT * FROM api.get_risk_statistics()")
        stats = cur.fetchall()
        for stat in stats:
            print_info(f"  {stat['risk_name']}: {stat['total_area_km2']} km² ({stat['percentage']}%)")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================================
# TEST 5: VISTAS MATERIALIZADAS
# ============================================================================

def test_materialized_views():
    print_header("TEST 5: VISTAS MATERIALIZADAS")

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                matviewname,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
            FROM pg_matviews
            WHERE schemaname = 'api'
            ORDER BY matviewname
        """)

        views = cur.fetchall()

        if views:
            print_success(f"Encontradas {len(views)} vistas materializadas:")
            for view in views:
                print_info(f"  • {view['matviewname']}: {view['size']}")
        else:
            print_warning("No se encontraron vistas materializadas")

        # Test contenido de vista risk_summary
        print_info("\nContenido de api.risk_summary:")
        cur.execute("SELECT * FROM api.risk_summary")
        summary = cur.fetchone()
        for key, value in summary.items():
            if key != 'last_updated':
                print_info(f"  {key}: {value}")

        cur.close()
        conn.close()
        return len(views) > 0

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================================
# TEST 6: CONSULTAS ESPACIALES
# ============================================================================

def test_spatial_queries():
    print_header("TEST 6: CONSULTAS ESPACIALES")

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Test 1: Punto en Papudo centro
        lon, lat = -71.449, -32.507
        print_info(f"Test: Consulta de riesgo en punto ({lon}, {lat})...")

        start = time.time()
        cur.execute("SELECT * FROM api.get_risk_at_point(%s, %s)", (lon, lat))
        result = cur.fetchone()
        elapsed = (time.time() - start) * 1000

        if result:
            print_success(f"Riesgo encontrado: {result['risk_name']} (nivel {result['risk_level']})")
            print_info(f"Tiempo de consulta: {elapsed:.2f} ms")
        else:
            print_warning("No se encontró riesgo en el punto (puede estar fuera del área)")

        # Test 2: Top polígonos
        print_info("\nTest: Top 5 polígonos más grandes...")
        cur.execute("SELECT poly_id, risk_name, area_km2 FROM api.get_top_polygons(NULL, 5)")
        top = cur.fetchall()

        for i, poly in enumerate(top, 1):
            print_info(f"  {i}. ID {poly['poly_id']}: {poly['area_km2']:.2f} km² ({poly['risk_name']})")

        # Test 3: Bbox query
        print_info("\nTest: Polígonos en bbox...")
        cur.execute("""
            SELECT COUNT(*) as cnt
            FROM api.get_polygons_in_bbox(-71.5, -32.6, -71.4, -32.4, NULL)
        """)
        bbox_count = cur.fetchone()['cnt']
        print_info(f"  Polígonos encontrados en bbox: {bbox_count}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================================
# TEST 7: RENDIMIENTO
# ============================================================================

def test_performance():
    print_header("TEST 7: BENCHMARK DE RENDIMIENTO")

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor(cursor_factory=RealDictCursor)

        benchmarks = [
            ("Punto espacial", "SELECT * FROM api.get_risk_at_point(-71.45, -32.50)"),
            ("Estadísticas", "SELECT * FROM api.get_risk_statistics()"),
            ("Top 10 polígonos", "SELECT * FROM api.get_top_polygons(NULL, 10)"),
            ("Health check", "SELECT api.health_check()"),
        ]

        for name, query in benchmarks:
            times = []
            for _ in range(5):  # 5 repeticiones
                start = time.time()
                cur.execute(query)
                cur.fetchall()
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            print_info(f"{name}:")
            print_info(f"  Promedio: {avg_time:.2f} ms | Min: {min_time:.2f} ms | Max: {max_time:.2f} ms")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================================
# RESUMEN FINAL
# ============================================================================

def print_final_summary(results):
    print_header("RESUMEN FINAL")

    total_tests = len(results)
    passed = sum(results.values())
    failed = total_tests - passed

    print(f"\nTests ejecutados: {total_tests}")
    print_success(f"Exitosos: {passed}")

    if failed > 0:
        print_error(f"Fallidos: {failed}")
        print_warning("\nTests fallidos:")
        for test_name, result in results.items():
            if not result:
                print_error(f"  • {test_name}")
    else:
        print_success("¡Todos los tests pasaron! ✨")

    print("\n" + "="*80)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f"\n{bcolors.BOLD}TESTING POSTGIS - GEOFEEDBACK PAPUDO{bcolors.ENDC}")
    print(f"{bcolors.BOLD}Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{bcolors.ENDC}")

    results = {}

    results['Conectividad'] = test_connectivity()
    results['Schemas y Tablas'] = test_schemas_and_tables()
    results['Índices Espaciales'] = test_spatial_indexes()
    results['Funciones Personalizadas'] = test_custom_functions()
    results['Vistas Materializadas'] = test_materialized_views()
    results['Consultas Espaciales'] = test_spatial_queries()
    results['Rendimiento'] = test_performance()

    print_final_summary(results)

    return all(results.values())

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
