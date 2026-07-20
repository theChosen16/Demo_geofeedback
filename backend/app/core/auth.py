import datetime
import logging
from typing import Optional

import jwt
from fastapi import Request, Response, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlmodel import Session

from app.core.config import settings
from app.db.session import get_session
from app.db.models import User

logger = logging.getLogger(__name__)

SESSION_COOKIE_NAME = "session"
SESSION_TTL_DAYS = 30
JWT_ALGORITHM = "HS256"

# Transporte HTTP reutilizado para verificar tokens de Google: la librería cachea
# internamente las claves públicas de Google en vez de refetchearlas en cada login.
_google_auth_request = google_requests.Request()


# Un SECRET_KEY corto/predecible es fuerza-bruteable offline contra un HS256 JWT robado;
# quien recupere la clave puede forjar un "sub" arbitrario y tomar cualquier cuenta, ya que
# _resolve_user_from_request() confía en ese campo sin ninguna otra verificación. Se exige un
# mínimo aquí (no solo en el comentario) para que una clave débil falle ruidosamente en vez de
# aceptarse en silencio.
_MIN_SECRET_KEY_LENGTH = 32


def _get_signing_key() -> str:
    if not settings.SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY no está configurado: es requerido para firmar sesiones de usuario. "
            "Define la variable de entorno SECRET_KEY (>=32 bytes aleatorios) en el backend."
        )
    if len(settings.SECRET_KEY) < _MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f"SECRET_KEY es demasiado corto ({len(settings.SECRET_KEY)} caracteres, "
            f"mínimo {_MIN_SECRET_KEY_LENGTH}): un secreto débil es fuerza-bruteable offline "
            "contra un JWT de sesión robado. Define uno más largo y aleatorio."
        )
    return settings.SECRET_KEY


def verify_google_id_token(credential: str) -> dict:
    """
    Verifica un ID token de Google Identity Services: firma criptográfica, emisor
    y audiencia (debe coincidir con nuestro GOOGLE_OAUTH_CLIENT_ID).
    Lanza ValueError (o una subclase de google.auth.exceptions.GoogleAuthError) si el
    token es inválido, expiró, o no fue emitido para esta aplicación.
    """
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        raise RuntimeError("GOOGLE_OAUTH_CLIENT_ID no está configurado en el backend.")

    return google_id_token.verify_oauth2_token(
        credential,
        _google_auth_request,
        audience=settings.GOOGLE_OAUTH_CLIENT_ID,
    )


def create_session_token(user: User) -> str:
    """Emite un JWT de sesión propio (independiente del de Google) para las siguientes peticiones."""
    now = datetime.datetime.now(datetime.UTC)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": now,
        "exp": now + datetime.timedelta(days=SESSION_TTL_DAYS),
    }
    return jwt.encode(payload, _get_signing_key(), algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> Optional[dict]:
    """Decodifica y valida el JWT de sesión propio. Retorna None si es inválido, está mal
    firmado, o expiró (nunca lanza excepción: se trata como 'no autenticado')."""
    try:
        return jwt.decode(token, _get_signing_key(), algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as e:
        logger.info(f"Sesión inválida o expirada: {e}")
        return None


def set_session_cookie(response: Response, token: str) -> None:
    """Emite la cookie de sesión. httpOnly + SameSite=Lax porque la SPA se sirve
    same-origin desde este mismo backend (ver app/main.py), sin fricción de CORS."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=bool(settings.RAILWAY_ENVIRONMENT),
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def _resolve_user_from_request(request: Request, session: Session) -> Optional[User]:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    payload = decode_session_token(token)
    if not payload:
        return None

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None

    return session.get(User, user_id)


def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    """Dependencia FastAPI: exige sesión válida, 401 en caso contrario."""
    user = _resolve_user_from_request(request, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return user


def get_optional_user(request: Request, session: Session = Depends(get_session)) -> Optional[User]:
    """Dependencia FastAPI: usuario si hay sesión válida, None si es un visitante anónimo."""
    return _resolve_user_from_request(request, session)
