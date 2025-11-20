#!/usr/bin/env python3
"""
Configuración de la aplicación GeoFeedback
Maneja variables de entorno para desarrollo y producción
"""

import os
import socket
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env (solo en desarrollo)
load_dotenv()

def resolve_ipv4(hostname):
    """
    Resuelve un hostname a su dirección IPv4.
    Necesario porque Railway tiene conectividad limitada con IPv6 externo.
    """
    try:
        # Forzar resolución IPv4 usando AF_INET
        result = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
        logger.info(f"✓ Resolved {hostname} to IPv4: {result}")
        return result
    except (socket.gaierror, IndexError) as e:
        # Si falla la resolución IPv4, devolver el hostname original
        logger.warning(f"✗ Failed to resolve {hostname} to IPv4: {e}")
        return hostname

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
    DATABASE_URL = os.getenv('DATABASE_URL')

    if DATABASE_URL:
        # Parsear DATABASE_URL (formato Railway/Heroku)
        # postgresql://user:password@host:port/database
        url = urlparse(DATABASE_URL)

        # Resolver hostname a IPv4 para evitar problemas con IPv6 en Railway
        resolved_ip = resolve_ipv4(url.hostname) if url.hostname else '127.0.0.1'

        DB_CONFIG = {
            'dbname': url.path[1:],  # Remover el / inicial
            'user': url.username,
            'password': url.password,
            'hostaddr': resolved_ip,  # Usar hostaddr para bypass DNS y forzar IPv4
            'host': url.hostname,     # Mantener host original para autenticación SSL
            'port': url.port or 5432
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
