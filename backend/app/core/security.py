import os
import time
import hmac
import hashlib
import logging
import threading
from collections import defaultdict
from fastapi import Request, HTTPException, status
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configurar logs estructurados para Loki
def log_event(event_type: str, **kwargs):
    """Genera logs en formato JSON para Grafana/Loki Stack."""
    import datetime
    log_data = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "event": event_type,
        "environment": settings.RAILWAY_ENVIRONMENT or "local",
        **kwargs
    }
    # Enviar al stdout (line-buffered flush) para que Railway/Grafana lo capturen
    print(import_json_dumps(log_data), flush=True)

def import_json_dumps(data):
    import json
    return json.dumps(data)

# Conexión a Redis
redis_client = None
if settings.REDIS_URL:
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        logger.info("Redis inicializado y conectado en FastAPI.")
    except Exception as e:
        logger.error(f"Error conectando a Redis en FastAPI: {e}")
        redis_client = None


def get_client_ip(request: Request) -> str:
    """Obtiene la IP real del cliente desde la cabecera X-Forwarded-For del proxy de Railway."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",")]
        return ips[-1] if ips[-1] else request.client.host or "127.0.0.1"
    return request.client.host or "127.0.0.1"


# HMAC SHA-256 IP Anonymization
_raw_salt = settings.IP_HASH_SALT or settings.SECRET_KEY
if not _raw_salt:
    logger.warning("IP_HASH_SALT y SECRET_KEY desconfigurados: usando salt por defecto en tiempo de ejecución para anonimización de IP.")
    _raw_salt = "geofeedback_default_ip_anonymization_salt_2026"

_IP_HASH_KEY = _raw_salt.encode()

def hash_ip(ip: str) -> str:
    """Anonimiza la IP con un HMAC-SHA256 usando salt secreto."""
    if not ip:
        return ""
    return hmac.new(_IP_HASH_KEY, ip.encode(), hashlib.sha256).hexdigest()



class RateLimiter:
    """Hybrid Rate Limiter: Redis con Fallback a memoria local."""
    def __init__(self, key_prefix: str, max_requests: int = 10, window_seconds: int = 60):
        self.prefix = key_prefix
        self.max_requests = max_requests
        self.window = window_seconds
        
        # Fallback local
        self._requests = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 300

    def _cleanup_old_entries(self, now: float):
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._last_cleanup = now
        stale_keys = [k for k, v in self._requests.items() if not v or now - v[-1] > self.window]
        for k in stale_keys:
            del self._requests[k]

    def is_allowed(self, client_ip: str) -> bool:
        if redis_client:
            redis_key = f"rate_limit:{self.prefix}:{client_ip}"
            try:
                pipe = redis_client.pipeline()
                pipe.incr(redis_key)
                pipe.expire(redis_key, self.window, nx=True)
                results = pipe.execute()
                request_count = results[0]
                
                if request_count > self.max_requests:
                    log_event('rate_limit_exceeded', ip=hash_ip(client_ip), prefix=self.prefix, backend='redis')
                    return False
                return True
            except Exception as e:
                logger.error(f"Error en Redis RateLimiter: {e}, fallback a memoria")
        
        now = time.time()
        with self._lock:
            self._cleanup_old_entries(now)
            self._requests[client_ip] = [t for t in self._requests[client_ip] if now - t < self.window]
            if len(self._requests[client_ip]) >= self.max_requests:
                log_event('rate_limit_exceeded', ip=hash_ip(client_ip), prefix=self.prefix, backend='memory')
                return False
            self._requests[client_ip].append(now)
            return True


# Instancias de limitadores de peticiones
analysis_limiter = RateLimiter(key_prefix='analyze', max_requests=10, window_seconds=60)
contact_limiter = RateLimiter(key_prefix='contact', max_requests=5, window_seconds=60)
visit_limiter = RateLimiter(key_prefix='visit', max_requests=30, window_seconds=60)
stats_limiter = RateLimiter(key_prefix='stats', max_requests=60, window_seconds=60)
# El frontend consulta el estado de la tarea cada 2s (~30 req/min por análisis activo).
# 90/min deja holgura para varios análisis concurrentes por IP y acota el agotamiento
# de recursos (DoS) de un cliente sondeando el backend de resultados de Celery/Redis.
#
# Nota de alcance: esto NO añade una verificación de "ownership" del task_id, ni
# pretende hacerlo. Con ~122 bits de entropía (uuid4 por defecto de Celery, ver
# app/tasks/worker.py) la fuerza bruta ya era inviable sin este límite. El único
# control de acceso real de GET /analyze/status/{task_id} sigue siendo la propia
# impredecibilidad del task_id: quien lo obtenga (p.ej. filtrado por logs, Referer,
# o un futuro enlace "compartir resultados" en la URL) puede leer ese análisis. Si
# algún día se reduce esa entropía o el task_id se expone en una ruta/URL del SPA,
# esta invariante se rompe y pasa a ser una exposición de datos explotable.
status_limiter = RateLimiter(key_prefix='status', max_requests=90, window_seconds=60)

# Login/logout: acotado más estricto que el resto porque cada intento implica una
# verificación criptográfica contra Google y una escritura en la tabla de usuarios.
auth_limiter = RateLimiter(key_prefix='auth', max_requests=10, window_seconds=60)

# Lectura/edición del propio historial de análisis (usuario ya autenticado).
me_limiter = RateLimiter(key_prefix='me', max_requests=30, window_seconds=60)


def verify_rate_limit(limiter: RateLimiter):
    """Generador de dependencia para inyectar rate limits en los endpoints de FastAPI."""
    def dependency(request: Request):
        ip = get_client_ip(request)
        if not limiter.is_allowed(ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas solicitudes. Intenta de nuevo en un minuto."
            )
    return dependency
