-- ============================================================================
-- CONFIGURACIÓN INICIAL DE POSTGIS - GEOFEEDBACK PAPUDO
-- ============================================================================
-- Base de datos geoespacial moderna y escalable
-- Autor: GeoFeedback Chile
-- Fecha: Noviembre 2025
-- PostgreSQL 16 + PostGIS 3.4
-- ============================================================================

-- Conectar a la base de datos
\c geofeedback_papudo

-- ============================================================================
-- PASO 1: HABILITAR EXTENSIONES
-- ============================================================================

-- PostGIS (ya debería estar, pero verificamos)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Extensiones adicionales para rendimiento y funcionalidad
CREATE EXTENSION IF NOT EXISTS btree_gist;      -- Índices GiST mejorados
CREATE EXTENSION IF NOT EXISTS pg_trgm;         -- Búsqueda de texto fuzzy
CREATE EXTENSION IF NOT EXISTS tablefunc;       -- Funciones de tabla cruzada

-- Verificar versiones
SELECT postgis_full_version();

-- ============================================================================
-- PASO 2: CREAR SCHEMAS ORGANIZADOS
-- ============================================================================

-- Schema para datos raw (originales)
CREATE SCHEMA IF NOT EXISTS raw;
COMMENT ON SCHEMA raw IS 'Datos geoespaciales originales (DEM, NDVI, límites)';

-- Schema para datos procesados (análisis)
CREATE SCHEMA IF NOT EXISTS processed;
COMMENT ON SCHEMA processed IS 'Resultados de análisis de riesgo de inundación';

-- Schema para infraestructura crítica
CREATE SCHEMA IF NOT EXISTS infrastructure;
COMMENT ON SCHEMA infrastructure IS 'Datos de infraestructura pública y privada';

-- Schema para metadatos y auditoría
CREATE SCHEMA IF NOT EXISTS metadata;
COMMENT ON SCHEMA metadata IS 'Metadatos de análisis, timestamps, versiones';

-- Schema para vistas públicas (API)
CREATE SCHEMA IF NOT EXISTS api;
COMMENT ON SCHEMA api IS 'Vistas y funciones expuestas para API REST';

-- ============================================================================
-- PASO 3: CONFIGURAR PARÁMETROS DE RENDIMIENTO
-- ============================================================================

-- Aumentar work_mem para operaciones espaciales (solo para esta sesión)
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';

-- Habilitar parallel query para operaciones pesadas
SET max_parallel_workers_per_gather = 4;

-- ============================================================================
-- PASO 4: CREAR TABLA DE METADATOS DE ANÁLISIS
-- ============================================================================

CREATE TABLE IF NOT EXISTS metadata.analysis_runs (
    id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(100) NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    municipality VARCHAR(100) DEFAULT 'Papudo',
    region VARCHAR(100) DEFAULT 'Valparaíso',

    -- Datos de entrada
    dem_source VARCHAR(255),
    ndvi_source VARCHAR(255),
    resolution_meters NUMERIC,

    -- Parámetros del análisis
    slope_weight NUMERIC DEFAULT 0.50,
    ndvi_weight NUMERIC DEFAULT 0.35,
    depression_weight NUMERIC DEFAULT 0.15,

    -- Resultados
    total_area_km2 NUMERIC,
    high_risk_km2 NUMERIC,
    medium_risk_km2 NUMERIC,
    low_risk_km2 NUMERIC,

    -- Metadata técnica
    crs VARCHAR(50) DEFAULT 'EPSG:32719',
    processing_time_seconds NUMERIC,
    script_version VARCHAR(20),
    notes TEXT,

    CONSTRAINT chk_weights CHECK (slope_weight + ndvi_weight + depression_weight = 1.0)
);

COMMENT ON TABLE metadata.analysis_runs IS 'Registro de análisis de riesgo ejecutados';

-- Índice en fecha
CREATE INDEX idx_analysis_runs_date ON metadata.analysis_runs(analysis_date DESC);

-- ============================================================================
-- PASO 5: CREAR TABLA DE CONFIGURACIÓN
-- ============================================================================

CREATE TABLE IF NOT EXISTS metadata.config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE metadata.config IS 'Configuración global del sistema';

-- Insertar configuraciones iniciales
INSERT INTO metadata.config (key, value, description) VALUES
    ('project_name', 'GeoFeedback Papudo', 'Nombre del proyecto'),
    ('municipality', 'Papudo', 'Municipio analizado'),
    ('region', 'Valparaíso', 'Región de Chile'),
    ('default_crs', 'EPSG:32719', 'Sistema de coordenadas UTM 19S'),
    ('risk_threshold_high', '70', 'Umbral para riesgo alto (score)'),
    ('risk_threshold_medium', '40', 'Umbral para riesgo medio (score)'),
    ('version', '1.0.0', 'Versión del sistema')
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- PASO 6: CREAR FUNCIONES AUXILIARES
-- ============================================================================

-- Función para obtener configuración
CREATE OR REPLACE FUNCTION metadata.get_config(config_key VARCHAR)
RETURNS TEXT AS $$
BEGIN
    RETURN (SELECT value FROM metadata.config WHERE key = config_key);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION metadata.get_config IS 'Obtiene valor de configuración por clave';

-- Función para logging
CREATE OR REPLACE FUNCTION metadata.log_message(
    message_level VARCHAR,
    message_text TEXT
)
RETURNS VOID AS $$
BEGIN
    RAISE NOTICE '[%] %', message_level, message_text;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PASO 7: CREAR USUARIO DE SOLO LECTURA (para API)
-- ============================================================================

-- Usuario para API (solo lectura)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'geofeedback_api') THEN
        CREATE ROLE geofeedback_api WITH LOGIN PASSWORD 'api_readonly_2025';
    END IF;
END
$$;

-- Permisos de lectura
GRANT CONNECT ON DATABASE geofeedback_papudo TO geofeedback_api;
GRANT USAGE ON SCHEMA raw, processed, infrastructure, api TO geofeedback_api;
GRANT SELECT ON ALL TABLES IN SCHEMA raw, processed, infrastructure, api TO geofeedback_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw, processed, infrastructure, api
    GRANT SELECT ON TABLES TO geofeedback_api;

-- ============================================================================
-- PASO 8: VERIFICACIÓN Y RESUMEN
-- ============================================================================

-- Mostrar schemas creados
SELECT
    schema_name,
    schema_owner,
    obj_description(nspname::regnamespace, 'pg_namespace') as description
FROM information_schema.schemata
JOIN pg_namespace ON schema_name = nspname
WHERE schema_name IN ('raw', 'processed', 'infrastructure', 'metadata', 'api')
ORDER BY schema_name;

-- Mostrar extensiones instaladas
SELECT
    extname as extension,
    extversion as version,
    nspname as schema
FROM pg_extension
JOIN pg_namespace ON extnamespace = pg_namespace.oid
WHERE extname LIKE 'postgis%' OR extname IN ('btree_gist', 'pg_trgm')
ORDER BY extname;

-- Mensaje final
SELECT metadata.log_message('INFO', 'Schema PostGIS configurado exitosamente');
SELECT metadata.log_message('INFO', 'Total schemas creados: 5');
SELECT metadata.log_message('INFO', 'Extensiones PostGIS activas: ' || count(*)::text)
FROM pg_extension WHERE extname LIKE 'postgis%';

\echo ''
\echo '============================================================================'
\echo '✅ CONFIGURACIÓN POSTGIS COMPLETADA'
\echo '============================================================================'
\echo 'Schemas creados: raw, processed, infrastructure, metadata, api'
\echo 'Próximo paso: Cargar datos raster'
\echo '  → bash scripts/02_load_raster_data.sh'
\echo '============================================================================'
