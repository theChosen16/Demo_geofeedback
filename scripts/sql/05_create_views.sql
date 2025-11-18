-- ============================================================================
-- VISTAS MATERIALIZADAS - GEOFEEDBACK PAPUDO
-- ============================================================================
-- Vistas precalculadas para consultas frecuentes y dashboards
-- Autor: GeoFeedback Chile
-- Fecha: Noviembre 2025
-- ============================================================================

\c geofeedback_papudo

-- ============================================================================
-- VISTA 1: Resumen Estadístico General
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS api.risk_summary AS
SELECT
    COUNT(*) AS total_polygons,
    ROUND(SUM(area_km2)::numeric, 2) AS total_area_km2,
    ROUND(MIN(area_m2)::numeric, 2) AS min_area_m2,
    ROUND(MAX(area_m2)::numeric, 2) AS max_area_m2,
    ROUND(AVG(area_m2)::numeric, 2) AS avg_area_m2,
    CURRENT_TIMESTAMP AS last_updated
FROM processed.amenaza_poligonos;

CREATE UNIQUE INDEX ON api.risk_summary ((1));

COMMENT ON MATERIALIZED VIEW api.risk_summary IS 'Resumen estadístico general (actualizar con REFRESH MATERIALIZED VIEW)';

-- ============================================================================
-- VISTA 2: Estadísticas por Nivel de Riesgo
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS api.risk_by_level AS
WITH totals AS (
    SELECT SUM(area_km2) AS total_area
    FROM processed.amenaza_poligonos
)
SELECT
    p.risk_level,
    p.risk_name,
    p.risk_color,
    COUNT(*) AS num_polygons,
    ROUND(SUM(p.area_km2)::numeric, 2) AS total_area_km2,
    ROUND(MIN(p.area_m2)::numeric, 2) AS min_area_m2,
    ROUND(MAX(p.area_m2)::numeric, 2) AS max_area_m2,
    ROUND(AVG(p.area_m2)::numeric, 2) AS avg_area_m2,
    ROUND((SUM(p.area_km2) / t.total_area * 100)::numeric, 2) AS percentage,
    CURRENT_TIMESTAMP AS last_updated
FROM processed.amenaza_poligonos p, totals t
GROUP BY p.risk_level, p.risk_name, p.risk_color, t.total_area
ORDER BY p.risk_level DESC;

CREATE UNIQUE INDEX ON api.risk_by_level (risk_level);

COMMENT ON MATERIALIZED VIEW api.risk_by_level IS 'Estadísticas detalladas por nivel de riesgo';

-- ============================================================================
-- VISTA 3: Top 100 Polígonos Más Grandes
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS api.top_polygons AS
SELECT
    poly_id,
    risk_level,
    risk_name,
    risk_color,
    ROUND(area_km2::numeric, 4) AS area_km2,
    ROUND((perimeter_m / 1000)::numeric, 2) AS perimeter_km,
    ST_Transform(geom, 4326) AS geom_wgs84,
    ROW_NUMBER() OVER (PARTITION BY risk_level ORDER BY area_km2 DESC) AS rank_within_level
FROM processed.amenaza_poligonos
ORDER BY area_km2 DESC
LIMIT 100;

CREATE UNIQUE INDEX ON api.top_polygons (poly_id);
CREATE INDEX ON api.top_polygons USING GIST (geom_wgs84);
CREATE INDEX ON api.top_polygons (risk_level, rank_within_level);

COMMENT ON MATERIALIZED VIEW api.top_polygons IS 'Top 100 polígonos más grandes con geometrías en WGS84';

-- ============================================================================
-- VISTA 4: Grid de Resumen (para heatmaps)
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS api.risk_grid_500m AS
WITH grid AS (
    -- Crear grid de 500x500m sobre el extent total
    SELECT
        (ST_SquareGrid(
            500,
            ST_Extent(geom)
        )).*
    FROM processed.amenaza_poligonos
)
SELECT
    ROW_NUMBER() OVER() AS grid_id,
    g.geom,
    ST_X(ST_Centroid(ST_Transform(g.geom, 4326))) AS center_lon,
    ST_Y(ST_Centroid(ST_Transform(g.geom, 4326))) AS center_lat,
    -- Riesgo predominante en la celda
    (
        SELECT p.risk_level
        FROM processed.amenaza_poligonos p
        WHERE ST_Intersects(p.geom, g.geom)
        GROUP BY p.risk_level
        ORDER BY SUM(ST_Area(ST_Intersection(p.geom, g.geom))) DESC
        LIMIT 1
    ) AS predominant_risk,
    -- Área total en riesgo alto
    COALESCE(
        (SELECT SUM(ST_Area(ST_Intersection(p.geom, g.geom))) / 1e6
         FROM processed.amenaza_poligonos p
         WHERE p.risk_level = 3 AND ST_Intersects(p.geom, g.geom)),
        0
    ) AS high_risk_km2,
    -- Área total en riesgo medio
    COALESCE(
        (SELECT SUM(ST_Area(ST_Intersection(p.geom, g.geom))) / 1e6
         FROM processed.amenaza_poligonos p
         WHERE p.risk_level = 2 AND ST_Intersects(p.geom, g.geom)),
        0
    ) AS medium_risk_km2,
    -- Área total en riesgo bajo
    COALESCE(
        (SELECT SUM(ST_Area(ST_Intersection(p.geom, g.geom))) / 1e6
         FROM processed.amenaza_poligonos p
         WHERE p.risk_level = 1 AND ST_Intersects(p.geom, g.geom)),
        0
    ) AS low_risk_km2
FROM grid g
WHERE EXISTS (
    SELECT 1
    FROM processed.amenaza_poligonos p
    WHERE ST_Intersects(p.geom, g.geom)
);

CREATE UNIQUE INDEX ON api.risk_grid_500m (grid_id);
CREATE INDEX ON api.risk_grid_500m USING GIST (geom);
CREATE INDEX ON api.risk_grid_500m (predominant_risk);

COMMENT ON MATERIALIZED VIEW api.risk_grid_500m IS 'Grid de 500x500m con resumen de riesgo por celda (para heatmaps)';

-- ============================================================================
-- VISTA 5: Extent y Bbox del Análisis
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS api.analysis_extent AS
SELECT
    ST_Extent(geom) AS extent_utm,
    ST_Extent(ST_Transform(geom, 4326)) AS extent_wgs84,
    ST_XMin(ST_Extent(ST_Transform(geom, 4326))) AS min_lon,
    ST_YMin(ST_Extent(ST_Transform(geom, 4326))) AS min_lat,
    ST_XMax(ST_Extent(ST_Transform(geom, 4326))) AS max_lon,
    ST_YMax(ST_Extent(ST_Transform(geom, 4326))) AS max_lat,
    ST_Centroid(ST_Collect(geom)) AS center_utm,
    ST_Transform(ST_Centroid(ST_Collect(geom)), 4326) AS center_wgs84
FROM processed.amenaza_poligonos;

CREATE UNIQUE INDEX ON api.analysis_extent ((1));

COMMENT ON MATERIALIZED VIEW api.analysis_extent IS 'Extent y centro del análisis en UTM y WGS84';

-- ============================================================================
-- FUNCIÓN PARA REFRESCAR TODAS LAS VISTAS
-- ============================================================================

CREATE OR REPLACE FUNCTION api.refresh_all_views()
RETURNS TABLE (
    view_name TEXT,
    status TEXT,
    refresh_time INTERVAL
) AS $$
DECLARE
    start_time TIMESTAMP;
    view_record RECORD;
BEGIN
    FOR view_record IN
        SELECT matviewname
        FROM pg_matviews
        WHERE schemaname = 'api'
        ORDER BY matviewname
    LOOP
        start_time := clock_timestamp();

        BEGIN
            EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY api.%I', view_record.matviewname);
            view_name := view_record.matviewname;
            status := 'OK';
            refresh_time := clock_timestamp() - start_time;
            RETURN NEXT;
        EXCEPTION
            WHEN OTHERS THEN
                view_name := view_record.matviewname;
                status := 'ERROR: ' || SQLERRM;
                refresh_time := clock_timestamp() - start_time;
                RETURN NEXT;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION api.refresh_all_views IS 'Refresca todas las vistas materializadas del schema api';

-- ============================================================================
-- TRIGGER PARA AUTO-REFRESH (OPCIONAL)
-- ============================================================================

-- Crear tabla de log de cambios
CREATE TABLE IF NOT EXISTS metadata.change_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    operation VARCHAR(10),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Función trigger
CREATE OR REPLACE FUNCTION metadata.log_change()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO metadata.change_log (table_name, operation)
    VALUES (TG_TABLE_NAME, TG_OP);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger a tabla de polígonos
DROP TRIGGER IF EXISTS trg_amenaza_poligonos_change ON processed.amenaza_poligonos;
CREATE TRIGGER trg_amenaza_poligonos_change
    AFTER INSERT OR UPDATE OR DELETE
    ON processed.amenaza_poligonos
    FOR EACH STATEMENT
    EXECUTE FUNCTION metadata.log_change();

-- ============================================================================
-- PERMISOS
-- ============================================================================

GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA api TO geofeedback_api;
GRANT EXECUTE ON FUNCTION api.refresh_all_views() TO geofeedback;

-- ============================================================================
-- REFRESCAR TODAS LAS VISTAS AHORA
-- ============================================================================

\echo ''
\echo '============================================================================'
\echo 'REFRESCANDO VISTAS MATERIALIZADAS...'
\echo '============================================================================'

REFRESH MATERIALIZED VIEW api.risk_summary;
REFRESH MATERIALIZED VIEW api.risk_by_level;
REFRESH MATERIALIZED VIEW api.top_polygons;
REFRESH MATERIALIZED VIEW api.risk_grid_500m;
REFRESH MATERIALIZED VIEW api.analysis_extent;

-- ============================================================================
-- VERIFICACIÓN
-- ============================================================================

\echo ''
\echo 'Vistas creadas:'
SELECT
    matviewname AS view_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size,
    (xpath('/row/cnt/text()', query_to_xml(
        format('SELECT COUNT(*) AS cnt FROM %I.%I', schemaname, matviewname),
        FALSE, TRUE, ''
    )))[1]::text::int AS row_count
FROM pg_matviews
WHERE schemaname = 'api'
ORDER BY matviewname;

\echo ''
\echo '============================================================================'
\echo '✅ VISTAS MATERIALIZADAS CREADAS'
\echo '============================================================================'
\echo 'Vistas disponibles:'
\echo '  • api.risk_summary - Resumen general'
\echo '  • api.risk_by_level - Estadísticas por nivel'
\echo '  • api.top_polygons - Top 100 polígonos más grandes'
\echo '  • api.risk_grid_500m - Grid para heatmaps'
\echo '  • api.analysis_extent - Extent del análisis'
\echo ''
\echo 'Para refrescar: SELECT * FROM api.refresh_all_views();'
\echo ''
\echo 'Próximo paso: Testing completo'
\echo '  → python3 scripts/06_test_postgis.py'
\echo '============================================================================'
