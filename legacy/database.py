import logging
import threading

import psycopg2
from psycopg2 import sql as psql

from config import DB_CONFIG

logger = logging.getLogger(__name__)

ANALYTICS_ROLE = 'geofeedback_api'
_ANALYTICS_BOOTSTRAP_LOCK = threading.Lock()


def _is_missing_table_error(error):
    return getattr(error, "pgcode", None) == "42P01"


def _ensure_analytics_tables(conn):
    """Create the analytics schema objects if they are missing."""
    with _ANALYTICS_BOOTSTRAP_LOCK:
        try:
            conn.rollback()
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS metadata")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS metadata.page_visits (
                        id SERIAL PRIMARY KEY,
                        visit_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        page VARCHAR(255) DEFAULT '/',
                        user_agent TEXT,
                        ip_hash VARCHAR(64)
                    )
                    """
                )
                cur.execute(
                    "COMMENT ON TABLE metadata.page_visits IS 'Registro anonimo de visitas a la pagina'"
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS metadata.api_usage_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        endpoint VARCHAR(100),
                        location_name VARCHAR(255),
                        coordinates GEOMETRY(Point, 4326),
                        approach VARCHAR(100),
                        status VARCHAR(50)
                    )
                    """
                )
                cur.execute(
                    "COMMENT ON TABLE metadata.api_usage_logs IS 'Log de uso de APIs de analisis'"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_page_visits_date ON metadata.page_visits(visit_date)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_api_usage_date ON metadata.api_usage_logs(timestamp)"
                )
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s)",
                    (ANALYTICS_ROLE,)
                )
                role_exists = cur.fetchone()[0]
                if role_exists:
                    role_id = psql.Identifier(ANALYTICS_ROLE)
                    cur.execute(psql.SQL("GRANT SELECT, INSERT ON metadata.page_visits TO {}").format(role_id))
                    cur.execute(psql.SQL("GRANT SELECT, INSERT ON metadata.api_usage_logs TO {}").format(role_id))
                    cur.execute(psql.SQL(
                        "GRANT USAGE, SELECT ON SEQUENCE metadata.page_visits_id_seq TO {}"
                    ).format(role_id))
                    cur.execute(psql.SQL(
                        "GRANT USAGE, SELECT ON SEQUENCE metadata.api_usage_logs_id_seq TO {}"
                    ).format(role_id))
                else:
                    logger.warning("Analytics grants skipped because role '%s' does not exist.", ANALYTICS_ROLE)
            conn.commit()
            return True
        except Exception as error:
            conn.rollback()
            logger.error("Error ensuring analytics tables: %s", error)
            return False


def _execute_with_analytics_recovery(conn, operation_name, operation, commit=False):
    try:
        with conn.cursor() as cur:
            result = operation(cur)
        if commit:
            conn.commit()
        return result
    except psycopg2.Error as error:
        conn.rollback()
        if not _is_missing_table_error(error):
            logger.error("Database error during %s: %s", operation_name, error)
            return None

        logger.warning(
            "Analytics table missing during %s; attempting lazy bootstrap.",
            operation_name
        )
        if not _ensure_analytics_tables(conn):
            return None

        try:
            with conn.cursor() as cur:
                result = operation(cur)
            if commit:
                conn.commit()
            return result
        except Exception as retry_error:
            conn.rollback()
            logger.error("Retry failed during %s after analytics bootstrap: %s", operation_name, retry_error)
            return None
    except Exception as error:
        conn.rollback()
        logger.error("Unexpected database error during %s: %s", operation_name, error)
        return None

def get_db_connection():
    """Establishes a connection to the database using DB_CONFIG."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None


def ensure_analytics_ready():
    """Eagerly bootstrap analytics tables to avoid first-request warnings."""
    conn = get_db_connection()
    if not conn:
        logger.warning("Analytics bootstrap skipped because database connection is unavailable.")
        return False

    try:
        return _ensure_analytics_tables(conn)
    finally:
        conn.close()

def log_visit(page='/', user_agent=None, ip_hash=None):
    """Logs a page visit to metadata.page_visits."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        def insert_visit(cur):
            cur.execute(
                """
                INSERT INTO metadata.page_visits (page, user_agent, ip_hash)
                VALUES (%s, %s, %s)
                """,
                (page, user_agent, ip_hash)
            )

        _execute_with_analytics_recovery(conn, "visit logging", insert_visit, commit=True)
    finally:
        conn.close()

def log_analysis(endpoint, location_name, lat, lng, approach, status='success'):
    """Logs an API analysis request to metadata.api_usage_logs."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        def insert_analysis(cur):
            cur.execute(
                """
                INSERT INTO metadata.api_usage_logs (endpoint, location_name, coordinates, approach, status)
                VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
                """,
                (endpoint, location_name, float(lng), float(lat), approach, status)
            )

        _execute_with_analytics_recovery(conn, "analysis logging", insert_analysis, commit=True)
    finally:
        conn.close()

def get_public_stats():
    """Retrieves public statistics for the dashboard."""
    conn = get_db_connection()
    stats = {"visits": 0, "analyses": 0}
    
    if not conn:
        return stats

    try:
        def fetch_stats(cur):
            cur.execute("SELECT COUNT(*) FROM metadata.page_visits")
            visits = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM metadata.api_usage_logs WHERE status = 'success'")
            analyses = cur.fetchone()[0]
            return {
                "visits": int(visits or 0),
                "analyses": int(analyses or 0)
            }

        recovered_stats = _execute_with_analytics_recovery(conn, "stats query", fetch_stats)
        if recovered_stats is not None:
            stats = recovered_stats
    finally:
        conn.close()

    return stats


def get_observability_snapshot():
    """Return database and analytics readiness without mutating state."""
    snapshot = {
        "database": {"connected": False},
        "analytics": {
            "page_visits_table": False,
            "api_usage_logs_table": False,
            "role_configured": False,
            "ready": False
        },
        "public_stats": {"visits": 0, "analyses": 0}
    }

    conn = get_db_connection()
    if not conn:
        return snapshot

    snapshot["database"]["connected"] = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    to_regclass('metadata.page_visits') IS NOT NULL,
                    to_regclass('metadata.api_usage_logs') IS NOT NULL,
                    EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s)
                """,
                (ANALYTICS_ROLE,)
            )
            page_visits_exists, api_usage_logs_exists, role_exists = cur.fetchone()
            snapshot["analytics"]["page_visits_table"] = bool(page_visits_exists)
            snapshot["analytics"]["api_usage_logs_table"] = bool(api_usage_logs_exists)
            snapshot["analytics"]["role_configured"] = bool(role_exists)
            snapshot["analytics"]["ready"] = bool(
                page_visits_exists and api_usage_logs_exists
            )

            if snapshot["analytics"]["ready"]:
                cur.execute("SELECT COUNT(*) FROM metadata.page_visits")
                snapshot["public_stats"]["visits"] = int(cur.fetchone()[0] or 0)
                cur.execute("SELECT COUNT(*) FROM metadata.api_usage_logs WHERE status = 'success'")
                snapshot["public_stats"]["analyses"] = int(cur.fetchone()[0] or 0)
    except Exception as error:
        logger.error("Error building observability snapshot: %s", error)
    finally:
        conn.close()

    return snapshot
