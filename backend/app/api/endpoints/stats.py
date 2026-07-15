from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func

from app.db.session import get_session
from app.db.models import PageVisit, ApiUsageLog
from app.core.security import verify_rate_limit, stats_limiter

router = APIRouter()

@router.get("/stats")
async def get_stats(
    session: Session = Depends(get_session),
    _ = Depends(verify_rate_limit(stats_limiter))
):
    """
    Retorna estadísticas públicas (visitas totales y análisis exitosos)
    para el contador de la landing page.
    Incluye fallback seguro a ceros en caso de fallas de base de datos.
    """
    try:
        # Contar total de visitas
        visits_count = session.exec(select(func.count(PageVisit.id))).one()
        
        # Contar total de análisis exitosos
        analyses_count = session.exec(
            select(func.count(ApiUsageLog.id)).where(ApiUsageLog.status == "success")
        ).one()
        
        return {
            "visits": int(visits_count or 0),
            "analyses": int(analyses_count or 0)
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error consultando estadísticas: {e}")
        return {"visits": 0, "analyses": 0}
