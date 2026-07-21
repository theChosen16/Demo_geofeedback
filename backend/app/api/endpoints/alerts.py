import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from geoalchemy2.elements import WKTElement

from app.core.auth import get_current_user
from app.db.session import get_session
from app.db.models import User, UserAlert

logger = logging.getLogger(__name__)

router = APIRouter()

class AlertCreate(BaseModel):
    location_name: str = Field(..., max_length=255)
    lat: float
    lng: float
    radius: int
    approach: str = Field(..., max_length=100)
    trigger_type: str = Field(default="ndvi_below", max_length=50) # ndvi_below, ndwi_above, ndmi_below, ndvi_drop_pct
    trigger_value: float = Field(default=0.3)

class AlertResponse(BaseModel):
    id: int
    location_name: str
    lat: float
    lng: float
    radius: int
    approach: str
    trigger_type: str
    trigger_value: float
    is_active: bool
    last_index_value: Optional[float] = None

    class Config:
        orm_mode = True

@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_in: AlertCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Crea una nueva alerta de monitoreo satelital para el usuario autenticado.
    El plan gratuito está limitado a 1 alerta activa como máximo.
    """
    # Verificar si el usuario ya tiene alertas activas
    existing_alerts = session.exec(
        select(UserAlert).where(UserAlert.user_id == user.id, UserAlert.is_active == True)
    ).all()
    
    if len(existing_alerts) >= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Has alcanzado el límite de 1 alerta activa en el plan gratuito. Elimina tu alerta existente para crear una nueva o suscríbete a un plan de pago."
        )

    # Validar coordenadas básicas
    if not (-90 <= alert_in.lat <= 90) or not (-180 <= alert_in.lng <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coordenadas latitud o longitud inválidas."
        )

    # Validar trigger type
    valid_triggers = ["ndvi_below", "ndwi_above", "ndmi_below", "ndvi_drop_pct"]
    if alert_in.trigger_type not in valid_triggers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de disparador inválido. Opciones válidas: {', '.join(valid_triggers)}"
        )

    alert = UserAlert(
        user_id=user.id,
        location_name=alert_in.location_name,
        lat=alert_in.lat,
        lng=alert_in.lng,
        radius=alert_in.radius,
        approach=alert_in.approach,
        coordinates=WKTElement(f"POINT({alert_in.lng} {alert_in.lat})", srid=4326),
        trigger_type=alert_in.trigger_type,
        trigger_value=alert_in.trigger_value,
        is_active=True
    )
    
    try:
        session.add(alert)
        session.commit()
        session.refresh(alert)
        logger.info(f"Usuario {user.id} creó alerta {alert.id} para {alert.location_name}")
        return alert
    except Exception as e:
        session.rollback()
        logger.error(f"Error al guardar alerta para usuario {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al guardar la alerta territorial."
        )

@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Retorna todas las alertas (activas e inactivas) del usuario autenticado."""
    alerts = session.exec(
        select(UserAlert).where(UserAlert.user_id == user.id)
    ).all()
    return alerts

@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Elimina permanentemente una alerta si pertenece al usuario autenticado."""
    alert = session.get(UserAlert, alert_id)
    if not alert or alert.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada o no tienes permisos para acceder a ella."
        )
        
    try:
        session.delete(alert)
        session.commit()
        logger.info(f"Usuario {user.id} eliminó alerta {alert_id}")
        return
    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando alerta {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar la alerta."
        )
