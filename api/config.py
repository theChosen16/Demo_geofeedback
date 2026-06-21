#!/usr/bin/env python3
"""
Configuración de la aplicación GeoFeedback
==========================================
Maneja variables de entorno para desarrollo y producción (Railway)

Características:
- Parseo robusto de DATABASE_URL
- Fallback a variables individuales
- Resolución IPv4 para bypass de problemas IPv6
- Valores por defecto seguros para Railway free tier

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import os
import logging
import socket
import sys
from urllib.parse import urlparse

# Cargar .env solo si existe (desarrollo local)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv no es necesario en producción

# Configurar logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def resolve_ipv4(hostname: str) -> str:
    """
    Resuelve hostname a IPv4 únicamente.
    Railway tiene problemas con IPv6, esto lo bypasea.
    """
    try:
        # Forzar resolución IPv4 (AF_INET)
        result = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if result:
            ipv4 = result[0][4][0]
            logger.info(f"Resolved {hostname} -> {ipv4}")
            return ipv4
    except socket.gaierror as e:
        logger.warning(f"Could not resolve {hostname} to IPv4: {e}")
    return hostname  # Fallback al hostname original


class Config:
    """Configuración centralizada de la aplicación."""

    # =========================================================================
    # FLASK
    # =========================================================================
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # In a real deployment (Railway) the SECRET_KEY MUST be provided
        # explicitly — fail hard rather than run with an unknown/ephemeral key.
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            raise RuntimeError(
                "SECRET_KEY no configurada en producción. "
                "Define la variable de entorno SECRET_KEY."
            )
        # Local development only: use a cryptographically-random ephemeral key
        # instead of the previous predictable id()-based value.
        import warnings
        import secrets
        warnings.warn(
            "SECRET_KEY no configurada. Generando una key aleatoria efímera "
            "para desarrollo local SOLAMENTE."
        )
        SECRET_KEY = secrets.token_hex(32)
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    ENV = os.getenv('FLASK_ENV', 'production')

    # NOTE: CORS is configured exclusively via the ALLOWED_ORIGINS env var,
    # read directly in app.py. This module previously also parsed a
    # CORS_ORIGINS variable that nothing ever imported, while .env.example
    # documented it as if it were the real CORS switch — an operator who set
    # CORS_ORIGINS following the docs would unknowingly leave the app fully
    # open to cross-origin requests in production. Removed to avoid confusion;
    # see ALLOWED_ORIGINS in api/.env.example.

    # =========================================================================
    # API
    # =========================================================================
    API_TITLE = os.getenv('API_TITLE', 'GeoFeedback Papudo API')
    API_VERSION = os.getenv('API_VERSION', '1.0.0')
    API_PREFIX = os.getenv('API_PREFIX', '/api/v1')

    # =========================================================================
    # DATABASE
    # =========================================================================
    DATABASE_URL = os.getenv('DATABASE_URL')

    @classmethod
    def get_db_config(cls) -> dict:
        """
        Construye configuración de BD desde DATABASE_URL o variables individuales.
        Incluye resolución IPv4 para compatibilidad con Railway.
        """
        if cls.DATABASE_URL:
            url = urlparse(cls.DATABASE_URL)
            hostname = url.hostname or 'localhost'

            # Resolver a IPv4 para evitar problemas de conectividad
            resolved_ip = resolve_ipv4(hostname)

            db_name = url.path.lstrip('/')
            db_port = url.port or 5432

            config = {
                'dbname': db_name,
                'user': url.username,
                'password': url.password,
                'port': db_port,
            }

            # Usar hostaddr para bypass DNS + host para SSL verification
            if resolved_ip != hostname:
                config['hostaddr'] = resolved_ip
                config['host'] = hostname  # Necesario para SNI/SSL
            else:
                config['host'] = hostname

            # SSL mode según el entorno
            if 'supabase' in hostname or 'neon' in hostname:
                sslmode = 'require'
            elif 'railway' in hostname or 'localhost' in hostname:
                sslmode = 'disable'
            else:
                sslmode = 'prefer'
            config['sslmode'] = sslmode

            logger.info(f"DB Config: ***:{db_port}/{db_name} (sslmode={sslmode})")
            return config

        # Fallback: Variables individuales (desarrollo local)
        # NOTA: En producción, asegurar que estas variables de entorno estén definidas.
        return {
            'dbname': os.getenv('DB_NAME', 'geofeedback_papudo'),
            'user': os.getenv('DB_USER', 'geofeedback'),
            'password': os.getenv('DB_PASSWORD'), # Sin default inseguro
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'sslmode': 'disable'
        }

    # Configuración de BD lista para usar
    DB_CONFIG = None  # Se inicializa después

    # =========================================================================
    # SERVER (Gunicorn) - Optimizado para Railway Free Tier
    # =========================================================================
    WORKERS = int(os.getenv('WORKERS', 2))  # Máximo 2 para 512MB RAM
    THREADS = int(os.getenv('THREADS', 2))
    TIMEOUT = int(os.getenv('TIMEOUT', 120))
    BIND_ADDRESS = os.getenv('BIND_ADDRESS', '0.0.0.0:5000')

    # =========================================================================
    # LOGGING
    # =========================================================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # =========================================================================
    # REDIS / CACHE
    # =========================================================================
    REDIS_URL = os.environ.get('REDIS_URL')


# Inicializar DB_CONFIG
Config.DB_CONFIG = Config.get_db_config()

# Exportar instancia
config = Config()

# Para compatibilidad con código existente que usa: from config import config
# y accede a config.DB_CONFIG directamente
DB_CONFIG = Config.DB_CONFIG
