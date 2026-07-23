import os
import socket
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

logger = logging.getLogger(__name__)

def resolve_ipv4(hostname: str) -> str:
    """
    Resuelve hostname a IPv4 únicamente.
    Evita problemas de conectividad IPv6 en Railway.
    """
    try:
        result = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if result:
            ipv4 = result[0][4][0]
            logger.info(f"Resolved {hostname} -> {ipv4}")
            return ipv4
    except socket.gaierror as e:
        logger.warning(f"Could not resolve {hostname} to IPv4: {e}")
    return hostname

class Settings(BaseSettings):
    # Flask/Common
    SECRET_KEY: str = Field(default="")
    DEBUG: bool = Field(default=False)
    ENV: str = Field(default="production")

    # API configuration
    API_TITLE: str = Field(default="GeoFeedback API")
    API_VERSION: str = Field(default="2.0.0")
    API_PREFIX: str = Field(default="/api/v1")

    # CORS
    ALLOWED_ORIGINS: str = Field(default="")

    # Databases
    DATABASE_URL: Optional[str] = Field(default=None)
    REDIS_URL: Optional[str] = Field(default=None)

    # Google Services
    GOOGLE_MAPS_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL_NAME: str = Field(default="gemini-3.5-flash-lite")
    GOOGLE_APPLICATION_CREDENTIALS_JSON: Optional[str] = Field(default=None)
    GOOGLE_OAUTH_CLIENT_ID: str = Field(default="")

    # Email
    RESEND_API_KEY: Optional[str] = Field(default=None)
    RESEND_TO_EMAIL: str = Field(default="GeoFeedback.cl@gmail.com")

    # Observability
    OBSERVABILITY_TOKEN: Optional[str] = Field(default=None)
    LOG_LEVEL: str = Field(default="INFO")

    # Railway / Infrastructure
    PORT: int = Field(default=5000)
    RAILWAY_ENVIRONMENT: Optional[str] = Field(default=None)

    # IP Anonymization
    IP_HASH_SALT: Optional[str] = Field(default=None)

    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS == "*":
            if self.RAILWAY_ENVIRONMENT:
                return []  # Fail-closed in prod
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def db_config(self) -> Dict[str, Any]:
        """
        Construye la configuración de BD desde DATABASE_URL o variables individuales.
        Incluye la resolución a IPv4 necesaria para Railway.
        """
        if self.DATABASE_URL:
            url = urlparse(self.DATABASE_URL)
            hostname = url.hostname or "localhost"
            resolved_ip = resolve_ipv4(hostname)
            db_name = url.path.lstrip("/")
            db_port = url.port or 5432

            config = {
                "dbname": db_name,
                "user": url.username,
                "password": url.password,
                "port": db_port,
            }

            if resolved_ip != hostname:
                config["hostaddr"] = resolved_ip
                config["host"] = hostname
            else:
                config["host"] = hostname

            # SSL mode
            if "supabase" in hostname or "neon" in hostname:
                sslmode = "require"
            elif "railway" in hostname or "localhost" in hostname:
                sslmode = "disable"
            else:
                sslmode = "prefer"
            config["sslmode"] = sslmode
            return config

        # Fallback local
        return {
            "dbname": os.getenv("DB_NAME", "geofeedback_papudo"),
            "user": os.getenv("DB_USER", "geofeedback"),
            "password": os.getenv("DB_PASSWORD", ""),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "sslmode": "disable"
        }

    @property
    def db_connection_uri(self) -> str:
        """
        Devuelve el URI de conexión de base de datos para SQLModel/SQLAlchemy.
        """
        if self.DATABASE_URL:
            # Reemplazar host por la IP resuelta para evitar problemas de DNS de IPv6
            url = urlparse(self.DATABASE_URL)
            hostname = url.hostname or "localhost"
            resolved_ip = resolve_ipv4(hostname)
            
            # Usar la IP resuelta en el string de conexión
            port_str = f":{url.port}" if url.port else ""
            user_pass = f"{url.username}:{url.password}@" if url.username else ""
            
            # Si el host es localhost o una ip local, no forzar SSL
            ssl_param = ""
            if "supabase" in hostname or "neon" in hostname:
                ssl_param = "?sslmode=require"
            elif "railway" in hostname or "localhost" in hostname:
                ssl_param = "?sslmode=disable"
            
            return f"postgresql://{user_pass}{resolved_ip}{port_str}{url.path}{ssl_param}"
        
        # Fallback local
        db_user = os.getenv("DB_USER", "geofeedback")
        db_pass = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "geofeedback_papudo")
        return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?sslmode=disable"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
