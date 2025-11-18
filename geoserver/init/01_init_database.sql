-- ============================================================================
-- INICIALIZACIÓN DE BASE DE DATOS GEOFEEDBACK PAPUDO
-- Para uso en contenedor Docker PostGIS
-- ============================================================================

-- Crear extensiones
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Crear schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS processed;
CREATE SCHEMA IF NOT EXISTS infrastructure;
CREATE SCHEMA IF NOT EXISTS metadata;
CREATE SCHEMA IF NOT EXISTS api;

COMMENT ON SCHEMA raw IS 'Datos crudos sin procesar';
COMMENT ON SCHEMA processed IS 'Datos procesados y analizados';
COMMENT ON SCHEMA infrastructure IS 'Infraestructura crítica';
COMMENT ON SCHEMA metadata IS 'Metadatos y configuración';
COMMENT ON SCHEMA api IS 'Funciones y vistas para API';

-- Tabla de polígonos de riesgo
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

CREATE INDEX idx_amenaza_geom ON processed.amenaza_poligonos USING GIST(geom);
CREATE INDEX idx_amenaza_risk ON processed.amenaza_poligonos(risk_level);

COMMENT ON TABLE processed.amenaza_poligonos IS 'Polígonos de amenaza de inundación clasificados por nivel de riesgo';

-- Tabla de instalaciones
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

CREATE INDEX idx_facilities_geom ON infrastructure.facilities USING GIST(geom);

COMMENT ON TABLE infrastructure.facilities IS 'Infraestructura crítica de Papudo';

-- Tabla de instalaciones con riesgo
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

CREATE INDEX idx_facilities_risk_geom ON infrastructure.facilities_risk USING GIST(geom);
CREATE INDEX idx_facilities_risk_level ON infrastructure.facilities_risk(risk_level);

COMMENT ON TABLE infrastructure.facilities_risk IS 'Infraestructura con nivel de riesgo asignado';

-- Tabla de metadatos
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

-- Configuración
CREATE TABLE IF NOT EXISTS metadata.config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Log de cambios
CREATE TABLE IF NOT EXISTS metadata.change_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    operation VARCHAR(10),
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- Insertar configuración inicial
INSERT INTO metadata.config (key, value, description) VALUES
    ('crs_utm', 'EPSG:32719', 'Sistema de coordenadas UTM Zone 19S'),
    ('crs_wgs84', 'EPSG:4326', 'Sistema de coordenadas WGS84'),
    ('municipality', 'Papudo', 'Municipalidad'),
    ('region', 'Valparaíso', 'Región'),
    ('country', 'Chile', 'País'),
    ('analysis_date', CURRENT_DATE::TEXT, 'Fecha del análisis'),
    ('version', '1.0.0', 'Versión del sistema')
ON CONFLICT (key) DO NOTHING;

-- Insertar metadata del análisis
INSERT INTO metadata.analysis_runs (
    analysis_type,
    municipality,
    total_area_km2,
    high_risk_km2,
    medium_risk_km2,
    low_risk_km2,
    notes
) VALUES (
    'Flood Risk Analysis',
    'Papudo',
    1925.32,
    450.13,
    852.47,
    622.72,
    'Análisis inicial combinando pendiente, NDVI y depresiones topográficas'
) ON CONFLICT DO NOTHING;

GRANT USAGE ON SCHEMA raw, processed, infrastructure, metadata, api TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA raw, processed, infrastructure, metadata, api TO PUBLIC;
