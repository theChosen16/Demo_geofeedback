import datetime
import logging
import ee
from sqlmodel import Session, select
from app.tasks.celery_app import celery_app
from app.tasks.worker import init_gee, get_sentinel2_image, calculate_indices, get_info_with_timeout
from app.db.session import engine
from app.db.models import UserAlert, User
from app.core.notifications import send_alert_email

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.tasks_periodic.check_active_alerts")
def check_active_alerts():
    """
    Tarea periódica ejecutada por Celery Beat para procesar todas las alertas activas
    de los usuarios, calcular los índices de Earth Engine más recientes y enviar
    correos electrónicos si se cumplen las condiciones de alerta.
    """
    logger.info("Iniciando verificación periódica de alertas de usuarios...")
    
    # Asegurar inicialización de Earth Engine
    try:
        ee.Initialize()
    except Exception:
        logger.warning("GEE no inicializado en el hilo actual de Beat/Worker. Reintentando...")
        init_gee()

    with Session(engine) as session:
        # Consultar todas las alertas activas
        alerts = session.exec(select(UserAlert).where(UserAlert.is_active == True)).all()
        logger.info(f"Se encontraron {len(alerts)} alertas activas para procesar.")
        
        for alert in alerts:
            # Si es semanal, saltar si ya se revisó en los últimos 6 días
            if alert.frequency == "weekly" and alert.last_checked_at:
                days_since_check = (datetime.datetime.now(datetime.UTC) - alert.last_checked_at).days
                if days_since_check < 6:
                    logger.info(f"Saltando alerta semanal {alert.id} ({alert.location_name}) - revisada hace {days_since_check} días.")
                    continue

            # Obtener el usuario
            user = session.get(User, alert.user_id)
            if not user or not user.email:
                logger.warning(f"Usuario {alert.user_id} no encontrado o sin correo para alerta {alert.id}. Saltando.")
                continue
                
            try:
                # Ejecutar análisis rápido de Earth Engine para el punto
                point = ee.Geometry.Point([alert.lng, alert.lat])
                roi = point.buffer(alert.radius)
                
                s2_image = get_sentinel2_image(roi)
                if not s2_image:
                    logger.warning(f"No se encontraron imágenes satelitales recientes para la alerta {alert.id} ({alert.location_name}).")
                    continue
                    
                s2_indices = calculate_indices(s2_image)
                mean_reducer = ee.Reducer.mean()
                
                # Seleccionar el índice correspondiente
                index_to_select = "NDVI"
                if alert.approach in ["water-management", "flood-risk", "real-estate"]:
                    index_to_select = "NDWI"
                elif alert.approach in ["agriculture", "fire-risk"]:
                    if alert.trigger_type == "ndmi_below":
                        index_to_select = "NDMI"
                    else:
                        index_to_select = "NDVI"
                else:
                    if alert.trigger_type == "ndwi_above":
                        index_to_select = "NDWI"
                    elif alert.trigger_type == "ndmi_below":
                        index_to_select = "NDMI"
                    else:
                        index_to_select = "NDVI"

                stats_image = s2_indices.select([index_to_select])
                
                # Reducir región para obtener el promedio
                stats = stats_image.reduceRegion(
                    reducer=mean_reducer,
                    geometry=roi,
                    scale=20,
                    maxPixels=1e8
                )
                
                stats_val = get_info_with_timeout(stats, timeout=20)
                if not stats_val or index_to_select not in stats_val:
                    logger.warning(f"No se pudo extraer el promedio para el índice {index_to_select} en alerta {alert.id}.")
                    continue
                    
                current_value = float(stats_val[index_to_select])
                logger.info(f"Alerta {alert.id} ({alert.location_name}): {index_to_select} actual = {current_value:.4f}")
                
                # Evaluar disparador/trigger
                triggered = False
                trigger_desc = ""
                
                if alert.trigger_type == "ndvi_below" and index_to_select == "NDVI":
                    triggered = current_value < alert.trigger_value
                    trigger_desc = f"NDVI menor a {alert.trigger_value}"
                elif alert.trigger_type == "ndwi_above" and index_to_select == "NDWI":
                    triggered = current_value > alert.trigger_value
                    trigger_desc = f"NDWI mayor a {alert.trigger_value}"
                elif alert.trigger_type == "ndmi_below" and index_to_select == "NDMI":
                    triggered = current_value < alert.trigger_value
                    trigger_desc = f"NDMI menor a {alert.trigger_value}"
                elif alert.trigger_type == "ndvi_drop_pct" and index_to_select == "NDVI":
                    if alert.last_index_value is not None:
                        # Caída de porcentaje respecto al último valor guardado
                        drop_pct = ((alert.last_index_value - current_value) / alert.last_index_value) * 100
                        triggered = drop_pct >= alert.trigger_value
                        trigger_desc = f"Caída de NDVI mayor o igual a {alert.trigger_value}% (último valor: {alert.last_index_value:.4f}, caída calculada: {drop_pct:.1f}%)"
                    else:
                        logger.info(f"Primer chequeo para alerta {alert.id} con caída porcentual. Guardando valor base.")
                
                # Si se disparó el evento, enviar correo electrónico
                if triggered:
                    logger.info(f"¡DISPARADO! Alerta {alert.id} cumple condición. Enviando correo...")
                    send_alert_email(
                        to_email=user.email,
                        location_name=alert.location_name,
                        trigger_desc=trigger_desc,
                        index_name=index_to_select,
                        current_value=current_value
                    )
                
                # Actualizar el registro de la alerta en la base de datos
                alert.last_checked_at = datetime.datetime.now(datetime.UTC)
                alert.last_index_value = current_value
                session.add(alert)
                
            except Exception as e:
                logger.error(f"Error procesando la alerta periódica {alert.id} ({alert.location_name}): {e}")
                
        session.commit()
    logger.info("Verificación periódica de alertas finalizada.")
