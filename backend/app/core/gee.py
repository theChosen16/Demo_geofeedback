import ee
import os
import json
import logging
from google.oauth2 import service_account
from app.core.config import settings

logger = logging.getLogger(__name__)

def init_gee() -> bool:
    """
    Inicializa Google Earth Engine.
    Prioridad de autenticación:
    1. Variable de entorno GOOGLE_APPLICATION_CREDENTIALS_JSON (Contenido JSON raw)
    2. Archivo service-account-key.json en la raíz del backend (legacy)
    3. Credenciales por defecto (gcloud)
    """
    try:
        # 1. Intentar cargar desde variable de entorno
        env_creds_json = settings.GOOGLE_APPLICATION_CREDENTIALS_JSON
        if env_creds_json:
            logger.info("Iniciando GEE desde variable de entorno...")
            try:
                creds_dict = json.loads(env_creds_json)
                project_id = creds_dict.get('project_id')
                credentials = service_account.Credentials.from_service_account_info(creds_dict)
                scoped_credentials = credentials.with_scopes([
                    'https://www.googleapis.com/auth/cloud-platform',
                    'https://www.googleapis.com/auth/earthengine'
                ])
                ee.Initialize(credentials=scoped_credentials, project=project_id)
                logger.info(f"GEE inicializado correctamente desde ENV VAR (Proyecto: {project_id}).")
                return True
            except json.JSONDecodeError:
                logger.error("Error: La variable GOOGLE_APPLICATION_CREDENTIALS_JSON no es un JSON válido.")
            except Exception as e:
                logger.error(f"Error usando credenciales de entorno: {e}")

        # 2. Intentar cargar desde archivo local (carpeta actual o padre)
        key_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'service-account-key.json'),
            os.path.join(os.path.dirname(__file__), 'service-account-key.json'),
            'service-account-key.json'
        ]
        
        for key_path in key_paths:
            if os.path.exists(key_path):
                logger.info(f"Iniciando GEE con archivo de clave: {key_path}")
                try:
                    with open(key_path, 'r', encoding='utf-8') as f:
                        creds_dict = json.load(f)
                    project_id = creds_dict.get('project_id')
                    credentials = service_account.Credentials.from_service_account_info(creds_dict)
                    scoped_credentials = credentials.with_scopes([
                        'https://www.googleapis.com/auth/cloud-platform',
                        'https://www.googleapis.com/auth/earthengine'
                    ])
                    ee.Initialize(credentials=scoped_credentials, project=project_id)
                    logger.info(f"GEE inicializado correctamente con Service Account (Archivo: {key_path}, Proyecto: {project_id}).")
                    return True
                except Exception as e:
                    logger.error(f"Error leyendo o usando archivo de clave {key_path}: {e}")
        
        # 3. Fallback a credenciales por defecto
        logger.info("No se encontraron credenciales explícitas, intentando default...")
        try:
            ee.Initialize()
            logger.info("GEE inicializado con credenciales por defecto.")
            return True
        except Exception as e:
            logger.error(f"Error en autenticación por defecto: {e}")
            return False

    except Exception as e:
        logger.error(f"Error crítico inicializando GEE: {e}")
        return False
