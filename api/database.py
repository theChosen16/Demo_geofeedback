import os
import psycopg2
import logging
from config import DB_CONFIG

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the database using DB_CONFIG."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def log_visit(page='/', user_agent=None, ip_hash=None):
    """Logs a page visit to metadata.page_visits."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO metadata.page_visits (page, user_agent, ip_hash)
                VALUES (%s, %s, %s)
                """,
                (page, user_agent, ip_hash)
            )
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging visit: {e}")
    finally:
        conn.close()

def log_analysis(endpoint, location_name, lat, lng, approach, status='success'):
    """Logs an API analysis request to metadata.api_usage_logs."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            # Create a simple point geometry from lat/lng
            # SRID 4326 is WGS84 (standard lat/lng)
            geom_sql = f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)"
            
            cur.execute(
                f"""
                INSERT INTO metadata.api_usage_logs (endpoint, location_name, coordinates, approach, status)
                VALUES (%s, %s, {geom_sql}, %s, %s)
                """,
                (endpoint, location_name, approach, status)
            )
        conn.commit()
    except Exception as e:
        logger.error(f"Error logging analysis: {e}")
    finally:
        conn.close()

def get_public_stats():
    """Retrieves public statistics for the dashboard."""
    conn = get_db_connection()
    stats = {"visits": 0, "analyses": 0}
    
    if not conn:
        return stats

    try:
        with conn.cursor() as cur:
            # Get total visits
            cur.execute("SELECT COUNT(*) FROM metadata.page_visits")
            stats["visits"] = cur.fetchone()[0]
            
            # Get total analyses
            cur.execute("SELECT COUNT(*) FROM metadata.api_usage_logs WHERE status = 'success'")
            stats["analyses"] = cur.fetchone()[0]
            
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
    finally:
        conn.close()
        
    return stats
