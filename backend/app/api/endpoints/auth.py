import datetime
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.auth import (
    verify_google_id_token,
    create_session_token,
    set_session_cookie,
    clear_session_cookie,
    get_current_user,
)
from app.core.security import verify_rate_limit, auth_limiter, me_limiter
from app.db.session import get_session
from app.db.models import User, UserAnalysis

logger = logging.getLogger(__name__)
router = APIRouter()


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., description="ID token JWT emitido por Google Identity Services")


class UserOut(BaseModel):
    email: str
    name: Optional[str] = None
    picture_url: Optional[str] = None


def _user_out(user: User) -> UserOut:
    return UserOut(email=user.email, name=user.name, picture_url=user.picture_url)


@router.post("/auth/google", dependencies=[Depends(verify_rate_limit(auth_limiter))])
async def login_with_google(data: GoogleLoginRequest, response: Response, session: Session = Depends(get_session)):
    """
    Verifica el ID token de Google Identity Services (firma, emisor, audiencia),
    crea o actualiza el usuario correspondiente y abre una sesión propia (cookie httpOnly).
    """
    try:
        claims = verify_google_id_token(data.credential)
    except Exception as e:
        logger.warning(f"Falla verificando ID token de Google: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google inválido")

    google_sub = claims.get("sub")
    email = claims.get("email")
    if not google_sub or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de Google incompleto")

    user = session.exec(select(User).where(User.google_sub == google_sub)).first()
    now = datetime.datetime.now()

    if user:
        user.email = email
        user.name = claims.get("name")
        user.picture_url = claims.get("picture")
        user.last_login_at = now
        session.add(user)
    else:
        user = User(
            google_sub=google_sub,
            email=email,
            name=claims.get("name"),
            picture_url=claims.get("picture"),
        )
        session.add(user)

    session.commit()
    session.refresh(user)

    token = create_session_token(user)
    set_session_cookie(response, token)

    return {"status": "success", "user": _user_out(user)}


@router.post("/auth/logout")
async def logout(response: Response):
    clear_session_cookie(response)
    return {"status": "success"}


@router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    return {"user": _user_out(user)}


class AnalysisHistoryItem(BaseModel):
    task_id: str
    location_name: str
    lat: float
    lng: float
    radius: int
    approach: str
    timestamp: str
    indices: Optional[dict] = None
    chart_data: Optional[list] = None
    map_layer: Optional[dict] = None
    meta_date: Optional[str] = None
    interpreted_result: Optional[str] = None


def _to_history_item(row: UserAnalysis) -> AnalysisHistoryItem:
    return AnalysisHistoryItem(
        task_id=row.task_id,
        location_name=row.location_name,
        lat=row.lat,
        lng=row.lng,
        radius=row.radius,
        approach=row.approach,
        timestamp=row.created_at.strftime("%H:%M:%S"),
        indices=row.indices,
        chart_data=row.chart_data,
        map_layer={"url": row.map_layer_url} if row.map_layer_url else None,
        meta_date=row.image_date,
        interpreted_result=row.interpretation,
    )


@router.get("/me/analyses", response_model=List[AnalysisHistoryItem], dependencies=[Depends(verify_rate_limit(me_limiter))])
async def list_my_analyses(
    days: int = 30,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Historial de análisis del usuario logeado, más recientes primero (usado para
    restaurar el historial de la SPA y alimentar el Pulso Territorial)."""
    days = max(1, min(days, 365))
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)

    rows = session.exec(
        select(UserAnalysis)
        .where(UserAnalysis.user_id == user.id)
        .where(UserAnalysis.created_at >= cutoff)
        .order_by(UserAnalysis.created_at.desc())
        .limit(50)
    ).all()

    return [_to_history_item(r) for r in rows]


class AnalysisPatchRequest(BaseModel):
    interpretation: Optional[str] = Field(default=None, max_length=5000)
    chart_data: Optional[list] = Field(default=None)


@router.patch("/me/analyses/{task_id}", dependencies=[Depends(verify_rate_limit(me_limiter))])
async def patch_analysis(
    task_id: str,
    data: AnalysisPatchRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    El frontend llama esto para adjuntar al historial del usuario piezas que llegan después
    del resultado satelital inicial (que ya se muestra de inmediato): la interpretación de
    Gemini y/o la serie temporal del Pulso Territorial. Ambos campos son opcionales y solo
    se actualiza lo que venga en el body.
    """
    row = session.exec(
        select(UserAnalysis)
        .where(UserAnalysis.task_id == task_id)
        .where(UserAnalysis.user_id == user.id)
    ).first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análisis no encontrado")

    if data.interpretation is not None:
        row.interpretation = data.interpretation
    if data.chart_data is not None:
        row.chart_data = data.chart_data

    session.add(row)
    session.commit()

    return {"status": "success"}
