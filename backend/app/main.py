import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, status, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.core.config import settings
from app.core.gee import init_gee
from app.db.session import init_db, get_session
from app.db.models import PageVisit
from app.core.security import verify_rate_limit, visit_limiter, hash_ip, get_client_ip

# Endpoints
from app.api.endpoints.analyze import router as analyze_router
from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.stats import router as stats_router
from app.api.endpoints.observability import router as observability_router
from app.api.endpoints.contact import router as contact_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación: inicialización y apagado."""
    logger.info("Iniciando GeoFeedback API...")
    
    # 1. Inicializar base de datos
    db_ok = init_db()
    if not db_ok:
        logger.error("No se pudo conectar o inicializar la base de datos.")
        
    # 2. Inicializar Google Earth Engine
    gee_ok = init_gee()
    if not gee_ok:
        logger.error("No se pudo inicializar Google Earth Engine.")
        
    yield
    logger.info("Apagando GeoFeedback API...")


# Instanciar FastAPI con los Swagger docs apuntando a /api/docs para coincidir con el legacy
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configurar middleware de CORS (Fail-closed en producción si no hay orígenes)
origins = settings.cors_origins
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    logger.warning("CORS deshabilitado (Fail-closed en producción). Define ALLOWED_ORIGINS.")


# Middleware para inyectar cabeceras de seguridad HTTP
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
    
    if settings.RAILWAY_ENVIRONMENT:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
    # Content-Security-Policy (CSP) adaptado para APIs y Mapas
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' blob: https://maps.googleapis.com https://*.gstatic.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
        "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob: https://*.googleapis.com https://*.gstatic.com https://earthengine.googleapis.com https://*.google.com https://cdn.jsdelivr.net; "
        "connect-src 'self' data: https://*.googleapis.com https://*.gstatic.com https://earthengine.googleapis.com https://api.resend.com; "
        "worker-src 'self' blob:; "
        "frame-src 'self' https://*.google.com https://*.googleapis.com https://*.gstatic.com"
    )
    return response


# ============================================================================
# Rutas de Configuración Pública y Logs de Visitas
# ============================================================================

@app.get("/api/v1/config/maps-key")
async def get_maps_key():
    """Retorna la clave pública de Google Maps para el frontend."""
    return {"google_maps_api_key": settings.GOOGLE_MAPS_API_KEY}


@app.post("/api/v1/visit", dependencies=[Depends(verify_rate_limit(visit_limiter))])
async def log_visit(request: Request, session: Session = Depends(get_session)):
    """
    Registra una visita anónima desde el frontend.
    Rate-limitado por IP para evitar spam o saturación de la base de datos.
    """
    try:
        ip = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        ip_hash = hash_ip(ip)
        
        visit = PageVisit(
            page="/",
            user_agent=user_agent,
            ip_hash=ip_hash
        )
        session.add(visit)
        session.commit()
        return {"status": "success", "message": "Visita registrada"}
    except Exception as e:
        logger.error(f"Error registrando visita: {e}")
        return {"status": "error", "message": "No se pudo registrar la visita"}


# ============================================================================
# Redirecciones heredadas (Legacy Redirects)
# ============================================================================

@app.get("/api")
@app.get("/api/")
async def api_redirect():
    return RedirectResponse(url="/api/docs", status_code=status.HTTP_302_FOUND)


@app.get("/contact")
@app.get("/contact/")
async def contact_redirect():
    return RedirectResponse(url="/#contacto", status_code=status.HTTP_302_FOUND)


# Health Check
@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "GeoFeedback API", "version": settings.API_VERSION}


# Registrar los sub-routers en el endpoint raíz /api/v1
app.include_router(analyze_router, prefix=settings.API_PREFIX, tags=["Análisis Satelital"])
app.include_router(chat_router, prefix=settings.API_PREFIX, tags=["AI Chatbot"])
app.include_router(stats_router, prefix=settings.API_PREFIX, tags=["Estadísticas Públicas"])
app.include_router(observability_router, prefix=settings.API_PREFIX, tags=["Observabilidad"])
app.include_router(contact_router, prefix=settings.API_PREFIX, tags=["Formulario Contacto"])


# ============================================================================
# Servir Frontend React SPA
# ============================================================================
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Determinar la ruta de frontend/dist dinámicamente
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
candidates = [
    os.path.join(base_dir, "frontend", "dist"),
    os.path.join("/app", "frontend", "dist"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist"),
]
frontend_dist_dir = candidates[0]
for candidate in candidates:
    if os.path.exists(os.path.join(candidate, "assets")):
        frontend_dist_dir = candidate
        break

frontend_assets_dir = os.path.join(frontend_dist_dir, "assets")

# Montar los assets estáticos si existen
if os.path.exists(frontend_assets_dir):
    app.mount("/assets", StaticFiles(directory=frontend_assets_dir), name="assets")
    logger.info(f"Frontend assets montados desde: {frontend_assets_dir}")
else:
    logger.warning(f"No se encontró el directorio de assets del frontend: {frontend_assets_dir}")

@app.get("/{fallback_path:path}")
async def serve_frontend(fallback_path: str):
    """
    Ruta fallback para servir la SPA en React (HTML5 History Mode).
    Redirige cualquier petición no capturada por la API al index.html de React.
    """
    # Evitar secuestrar rutas inexistentes de la API o la documentación
    if fallback_path.startswith("api") or fallback_path.startswith("docs"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ruta de API no encontrada")
        
    index_file = os.path.join(frontend_dist_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
        
    return {
        "message": "Welcome to GeoFeedback API. Frontend not compiled yet.",
        "docs_url": "/api/docs"
    }
