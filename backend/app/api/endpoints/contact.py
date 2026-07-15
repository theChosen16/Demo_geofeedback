import re
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

from app.core.security import verify_rate_limit, contact_limiter, log_event
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

class ContactRequest(BaseModel):
    name: str = Field(..., max_length=100)
    company: str = Field("", max_length=100)
    email: EmailStr = Field(..., max_length=254)
    message: str = Field(..., max_length=2000)


async def send_email_resend_async(name: str, company: str, email: str, message: str) -> bool:
    """Envía el correo electrónico de contacto utilizando Resend API."""
    resend_api_key = settings.RESEND_API_KEY
    if not resend_api_key:
        logger.warning("RESEND_API_KEY no configurado. Ignorando envío de correo.")
        return False
        
    from_email = "GeoFeedback <contacto@geofeedback.cl>"
    destination_email = settings.RESEND_TO_EMAIL
    
    email_data = {
        "from": from_email,
        "to": [destination_email],
        "reply_to": email,
        "subject": f"[GeoFeedback Web] Nuevo contacto de {name}",
        "text": f"Nombre: {name}\nEmpresa: {company}\nEmail: {email}\n\nMensaje: {message}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                "https://api.resend.com/emails",
                json=email_data,
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if res.status_code in [200, 201]:
                log_event("contact_email_sent", status="success", destination=destination_email)
                return True
            else:
                log_event("contact_email_error", status_code=res.status_code, error=res.text)
                return False
    except Exception as e:
        log_event("contact_system_error", error=str(e))
        return False


@router.post("/contact", dependencies=[Depends(verify_rate_limit(contact_limiter))])
async def contact_form(data: ContactRequest):
    """
    Recibe los datos del formulario de contacto y envía un correo electrónico a través de Resend.
    """
    success = await send_email_resend_async(
        name=data.name.strip(),
        company=data.company.strip(),
        email=data.email.strip(),
        message=data.message.strip()
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar el mensaje. Por favor intenta de nuevo más tarde."
        )
        
    return {"status": "success", "message": "Mensaje enviado correctamente"}
