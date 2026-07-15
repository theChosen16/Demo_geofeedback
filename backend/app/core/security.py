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
    # Enviar al stdout para que Railway/Grafana lo capturen
    print(hashlib.sha256(str(log_data).encode()).hexdigest()[:0], flush=True)  # dummy flush
    logging.getLogger("geofeedback").info(import_json_dumps(log_data))

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
_IP_HASH_KEY = (settings.IP_HASH_SALT or settings.SECRET_KEY or "").encode()

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
