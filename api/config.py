#!/usr/bin/env python3
"""
Configuración de la aplicación GeoFeedback
Maneja variables de entorno para desarrollo y producción
"""

import os
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env (solo en desarrollo)
load_dotenv()

class Config:
    """Configuración base"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    ENV = os.getenv('FLASK_ENV', 'production')

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # API
    API_TITLE = os.getenv('API_TITLE', 'GeoFeedback Papudo API')
    API_VERSION = os.getenv('API_VERSION', '1.0.0')
    API_PREFIX = os.getenv('API_PREFIX', '/api/v1')

    # Database - Railway proporciona DATABASE_URL automáticamente
    # Usando Supabase Session Pooler (IPv4-compatible, gratis)
    DATABASE_URL = os.getenv('DATABASE_URL')

    if DATABASE_URL:
        # Parsear DATABASE_URL (formato PostgreSQL estándar)
        # postgresql://user:password@host:port/database
        url = urlparse(DATABASE_URL)

        logger.info(f"Connecting to database: {url.hostname}:{url.port or 5432}")

        DB_CONFIG = {
            'dbname': url.path[1:],  # Remover el / inicial
            'user': url.username,
            'password': url.password,
            'host': url.hostname,    # Pooler maneja IPv4 automáticamente
            'port': url.port or 5432,
            'sslmode': 'disable'     # Railway Internal no usa SSL
        }
    else:
        # Configuración local/desarrollo
        DB_CONFIG = {
            'dbname': os.getenv('DB_NAME', 'geofeedback_papudo'),
            'user': os.getenv('DB_USER', 'geofeedback'),
            'password': os.getenv('DB_PASSWORD', 'Papudo2025'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432))
        }

    # Server
    WORKERS = int(os.getenv('WORKERS', 4))
    TIMEOUT = int(os.getenv('TIMEOUT', 120))
    BIND_ADDRESS = os.getenv('BIND_ADDRESS', '0.0.0.0:5000')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Exportar configuración
config = Config()
