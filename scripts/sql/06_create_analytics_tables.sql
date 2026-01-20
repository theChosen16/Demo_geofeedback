-- ============================================================================
-- ANALYTICS TABLES - GEOFEEDBACK
-- ============================================================================
-- Table for tracking page visits
CREATE TABLE IF NOT EXISTS metadata.page_visits (
    id SERIAL PRIMARY KEY,
    visit_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    page VARCHAR(255) DEFAULT '/',
    user_agent TEXT,
    ip_hash VARCHAR(64) -- Store hash only for privacy
);
COMMENT ON TABLE metadata.page_visits IS 'Registro anónimo de visitas a la página';
-- Table for tracking API analysis usage
CREATE TABLE IF NOT EXISTS metadata.api_usage_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(100),
    location_name VARCHAR(255),
    coordinates GEOMETRY(Point, 4326),
    approach VARCHAR(100),
    status VARCHAR(50)
);
COMMENT ON TABLE metadata.api_usage_logs IS 'Log de uso de APIs de análisis';
-- Index for performance
CREATE INDEX IF NOT EXISTS idx_page_visits_date ON metadata.page_visits(visit_date);
CREATE INDEX IF NOT EXISTS idx_api_usage_date ON metadata.api_usage_logs(timestamp);
-- Grant permissions to api user
GRANT SELECT,
    INSERT ON metadata.page_visits TO geofeedback_api;
GRANT SELECT,
    INSERT ON metadata.api_usage_logs TO geofeedback_api;
GRANT USAGE,
    SELECT ON SEQUENCE metadata.page_visits_id_seq TO geofeedback_api;
GRANT USAGE,
    SELECT ON SEQUENCE metadata.api_usage_logs_id_seq TO geofeedback_api;