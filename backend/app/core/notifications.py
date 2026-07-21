import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_alert_email(to_email: str, location_name: str, trigger_desc: str, index_name: str, current_value: float) -> bool:
    """Envía un correo de alerta de anomalía a un usuario usando Resend."""
    resend_api_key = settings.RESEND_API_KEY
    if not resend_api_key:
        logger.warning("RESEND_API_KEY no configurado. Ignorando envío de correo de alerta.")
        return False
        
    from_email = "GeoFeedback Alertas <alertas@geofeedback.cl>"
    
    subject = f"⚠️ [GeoFeedback] Alerta de Anomalía Territorial en {location_name}"
    
    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #fcfcfc;">
        <h2 style="color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 10px;">Alerta de Cambio Territorial</h2>
        <p>Hola,</p>
        <p>Tu punto de monitoreo activo en <strong>{location_name}</strong> ha registrado un cambio que cumple con tu disparador configurado:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Detalle</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Valor</th>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Ubicación</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{location_name}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Índice Analizado</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{index_name}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Condición configurada</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{trigger_desc}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #d9534f;">Último Valor Registrado</td>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #d9534f;">{current_value:.4f}</td>
            </tr>
        </table>
        
        <p>Te recomendamos ingresar a <a href="https://geofeedback.cl" style="color: #0275d8; text-decoration: none; font-weight: bold;">GeoFeedback Chile</a> para explorar la última imagen satelital en el mapa interactivo y revisar el diagnóstico de <strong>GeoBot</strong>.</p>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;" />
        <p style="font-size: 12px; color: #777; text-align: center;">Este es un servicio de alerta automatizado de GeoFeedback.cl. Puedes desactivar esta alerta en cualquier momento desde tu panel de usuario.</p>
    </div>
    """
    
    email_data = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    
    try:
        with httpx.Client(timeout=15.0) as client:
            res = client.post(
                "https://api.resend.com/emails",
                json=email_data,
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if res.status_code in [200, 201]:
                logger.info(f"Correo de alerta enviado exitosamente a {to_email}")
                return True
            else:
                logger.error(f"Error al enviar correo de alerta de Resend: {res.status_code} - {res.text}")
                return False
    except Exception as e:
        logger.error(f"Error de red/sistema enviando correo de alerta: {e}")
        return False
