-- ============================================================================
-- FUNCIONES PL/pgSQL PERSONALIZADAS - GEOFEEDBACK PAPUDO
-- ============================================================================
-- Funciones espaciales optimizadas para consultas de riesgo
-- Autor: GeoFeedback Chile
-- Fecha: Noviembre 2025
-- ============================================================================

\c geofeedback_papudo

SET search_path = processed, public;

-- ============================================================================
-- FUNCIÓN 1: Obtener riesgo en un punto específico
-- ============================================================================

CREATE OR REPLACE FUNCTION api.get_risk_at_point(
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION
)
RETURNS TABLE (
    risk_level INTEGER,
    risk_name VARCHAR,
    risk_color VARCHAR,
    area_km2 DOUBLE PRECISION,
    id INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.risk_level,
        p.risk_name,
        p.risk_color,
        p.area_km2,
        p.id
    FROM processed.amenaza_poligonos p
    WHERE ST_Contains(
        p.geom,
        ST_Transform(
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326),
            32719
        )
    )
    LIMIT 1;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION api.get_risk_at_point IS 'Obtiene nivel de riesgo para coordenadas lon/lat (EPSG:4326)';

-- Ejemplo de uso:
-- SELECT * FROM api.get_risk_at_point(-71.449, -32.507);

-- ============================================================================
-- FUNCIÓN 2: Estadísticas por nivel de riesgo
-- ============================================================================

CREATE OR REPLACE FUNCTION api.get_risk_statistics()
RETURNS TABLE (
    risk_level INTEGER,
    risk_name VARCHAR,
    risk_color VARCHAR,
    num_polygons BIGINT,
    total_area_km2 DOUBLE PRECISION,
    percentage DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    WITH totals AS (
        SELECT SUM(area_km2) AS total_area
        FROM processed.amenaza_poligonos
    )
    SELECT
        p.risk_level,
        p.risk_name,
        p.risk_color,
        COUNT(*)::BIGINT AS num_polygons,
        ROUND(SUM(p.area_km2)::numeric, 2)::DOUBLE PRECISION AS total_area_km2,
        ROUND((SUM(p.area_km2) / t.total_area * 100)::numeric, 2)::DOUBLE PRECISION AS percentage
    FROM processed.amenaza_poligonos p, totals t
    GROUP BY p.risk_level, p.risk_name, p.risk_color, t.total_area
    ORDER BY p.risk_level DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION api.get_risk_statistics IS 'Retorna estadísticas resumidas por nivel de riesgo';

-- ============================================================================
-- FUNCIÓN 3: Polígonos dentro de un bounding box
-- ============================================================================

CREATE OR REPLACE FUNCTION api.get_polygons_in_bbox(
    min_lon DOUBLE PRECISION,
    min_lat DOUBLE PRECISION,
    max_lon DOUBLE PRECISION,
    max_lat DOUBLE PRECISION,
    risk_filter INTEGER DEFAULT NULL
)
RETURNS TABLE (
    id INTEGER,
    risk_level INTEGER,
    risk_name VARCHAR,
    risk_color VARCHAR,
    area_km2 DOUBLE PRECISION,
    geojson TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.risk_level,
        p.risk_name,
        p.risk_color,
        p.area_km2,
        ST_AsGeoJSON(ST_Transform(p.geom, 4326))::TEXT AS geojson
    FROM processed.amenaza_poligonos p
    WHERE ST_Intersects(
        p.geom,
        ST_Transform(
            ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
            32719
        )
    )
    AND (risk_filter IS NULL OR p.risk_level = risk_filter)
    ORDER BY p.area_km2 DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION api.get_polygons_in_bbox IS 'Retorna polígonos dentro de un bbox (lon/lat) con filtro opcional de riesgo';

-- ============================================================================
-- FUNCIÓN 4: Área total en riesgo dentro de un radio
-- ============================================================================

CREATE OR REPLACE FUNCTION api.get_risk_within_radius(
    center_lon DOUBLE PRECISION,
    center_lat DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION
)
RETURNS TABLE (
    risk_level INTEGER,
    risk_name VARCHAR,
    area_within_radius_km2 DOUBLE PRECISION
) AS $$
DECLARE
    center_point GEOMETRY;
BEGIN
    -- Convertir punto a UTM 19S
    center_point := ST_Transform(
        ST_SetSRID(ST_MakePoint(center_lon, center_lat), 4326),
        32719
    );

    RETURN QUERY
    SELECT
        p.risk_level,
        p.risk_name,
        ROUND(SUM(
            ST_Area(
                ST_Intersection(
                    p.geom,
                    ST_Buffer(center_point, radius_meters)
                )
            ) / 1e6
        )::numeric, 2)::DOUBLE PRECISION AS area_within_radius_km2
    FROM processed.amenaza_poligonos p
    WHERE ST_DWithin(p.geom, center_point, radius_meters)
    GROUP BY p.risk_level, p.risk_name
    ORDER BY p.risk_level DESC;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION api.get_risk_within_radius IS 'Calcula área en riesgo dentro de un radio (metros) desde un punto';

-- ============================================================================
-- FUNCIÓN 5: Polígonos más grandes por nivel de riesgo
-- ============================================================================

CREATE OR REPLACE FUNCTION api.get_top_polygons(
    risk_filter INTEGER DEFAULT NULL,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id INTEGER,
    risk_level INTEGER,
    risk_name VARCHAR,
    area_km2 DOUBLE PRECISION,
    perimeter_km DOUBLE PRECISION,
    geojson TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.risk_level,
        p.risk_name,
        p.area_km2,
        ROUND((p.perimeter_m / 1000)::numeric, 2)::DOUBLE PRECISION AS perimeter_km,
        ST_AsGeoJSON(ST_Transform(p.geom, 4326))::TEXT AS geojson
    FROM processed.amenaza_poligonos p
    WHERE (risk_filter IS NULL OR p.risk_level = risk_filter)
    ORDER BY p.area_km2 DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION api.get_top_polygons IS 'Retorna los N polígonos más grandes, con filtro opcional de nivel';

-- ============================================================================
-- FUNCIÓN 6: Generar FeatureCollection GeoJSON completo
-- ============================================================================

CREATE OR REPLACE FUNCTION api.get_all_polygons_geojson(
    risk_filter INTEGER DEFAULT NULL,
    simplify_tolerance DOUBLE PRECISION DEFAULT 0
)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    WITH features AS (
        SELECT json_build_object(
            'type', 'Feature',
            'id', id,
            'geometry', ST_AsGeoJSON(
                CASE
                    WHEN simplify_tolerance > 0 THEN
                        ST_Transform(ST_Simplify(geom, simplify_tolerance), 4326)
                    ELSE
                        ST_Transform(geom, 4326)
                END
            )::json,
            'properties', json_build_object(
                'id', id,
                'risk_level', risk_level,
                'risk_name', risk_name,
                'risk_color', risk_color,
                'area_km2', area_km2,
                'perimeter_m', perimeter_m
            )
        ) AS feature
        FROM processed.amenaza_poligonos
        WHERE (risk_filter IS NULL OR risk_level = risk_filter)
    )
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', json_agg(feature)
    )
    INTO result
    FROM features;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION api.get_all_polygons_geojson IS 'Genera GeoJSON FeatureCollection completo con filtro opcional';

-- ============================================================================
-- FUNCIÓN 7: Consulta de valor de raster en un punto
-- ============================================================================

CREATE OR REPLACE FUNCTION api.get_raster_value_at_point(
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    raster_type VARCHAR DEFAULT 'amenaza_clasificada'
)
RETURNS TABLE (
    value DOUBLE PRECISION,
    raster_name VARCHAR
) AS $$
DECLARE
    point_geom GEOMETRY;
    raster_value DOUBLE PRECISION;
BEGIN
    -- Convertir punto a UTM 19S
    point_geom := ST_Transform(
        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326),
        32719
    );

    -- Obtener valor del raster correspondiente
    IF raster_type = 'amenaza_clasificada' THEN
        SELECT (ST_Value(rast, point_geom))
        INTO raster_value
        FROM processed.amenaza_clasificada
        WHERE ST_Intersects(rast, point_geom)
        LIMIT 1;
    ELSIF raster_type = 'score_continuo' THEN
        SELECT (ST_Value(rast, point_geom))
        INTO raster_value
        FROM processed.amenaza_score_continuo
        WHERE ST_Intersects(rast, point_geom)
        LIMIT 1;
    ELSIF raster_type = 'pendiente' THEN
        SELECT (ST_Value(rast, point_geom))
        INTO raster_value
        FROM processed.pendiente
        WHERE ST_Intersects(rast, point_geom)
        LIMIT 1;
    END IF;

    RETURN QUERY SELECT raster_value, raster_type;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION api.get_raster_value_at_point IS 'Consulta valor de raster en punto (amenaza_clasificada, score_continuo, pendiente)';

-- ============================================================================
-- FUNCIÓN 8: Health check de la base de datos
-- ============================================================================

CREATE OR REPLACE FUNCTION api.health_check()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'status', 'OK',
        'timestamp', CURRENT_TIMESTAMP,
        'database', current_database(),
        'postgis_version', postgis_version(),
        'tables', (
            SELECT json_object_agg(tablename, row_count)
            FROM (
                SELECT
                    tablename,
                    (xpath('/row/cnt/text()', query_to_xml(
                        format('SELECT COUNT(*) AS cnt FROM processed.%I', tablename),
                        FALSE, TRUE, ''
                    )))[1]::text::int AS row_count
                FROM pg_tables
                WHERE schemaname = 'processed'
                    AND tablename IN ('amenaza_poligonos', 'amenaza_clasificada', 'amenaza_score_continuo', 'pendiente')
            ) t
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION api.health_check IS 'Retorna estado de salud de la base de datos';

-- ============================================================================
-- PERMISOS PARA USUARIO API
-- ============================================================================

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA api TO geofeedback_api;
ALTER DEFAULT PRIVILEGES IN SCHEMA api GRANT EXECUTE ON FUNCTIONS TO geofeedback_api;

-- ============================================================================
-- TESTING DE FUNCIONES
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'TESTING DE FUNCIONES'
\echo '============================================================================'

\echo ''
\echo '1. Health Check:'
SELECT api.health_check();

\echo ''
\echo '2. Estadísticas de riesgo:'
SELECT * FROM api.get_risk_statistics();

\echo ''
\echo '3. Top 5 polígonos más grandes (riesgo alto):'
SELECT id, area_km2, perimeter_km
FROM api.get_top_polygons(3, 5);

\echo ''
\echo '============================================================================'
\echo '✅ FUNCIONES CREADAS EXITOSAMENTE'
\echo '============================================================================'
\echo 'Funciones disponibles en schema api:'
\echo '  1. get_risk_at_point(lon, lat)'
\echo '  2. get_risk_statistics()'
\echo '  3. get_polygons_in_bbox(min_lon, min_lat, max_lon, max_lat, risk_filter)'
\echo '  4. get_risk_within_radius(lon, lat, radius_m)'
\echo '  5. get_top_polygons(risk_filter, limit)'
\echo '  6. get_all_polygons_geojson(risk_filter, simplify)'
\echo '  7. get_raster_value_at_point(lon, lat, raster_type)'
\echo '  8. health_check()'
\echo ''
\echo 'Próximo paso: Crear vistas materializadas'
\echo '  → psql -U geofeedback -d geofeedback_papudo -f scripts/sql/05_create_views.sql'
\echo '============================================================================'
