import ee
import os
import json
from google.oauth2 import service_account

def init_gee():
    """
    Inicializa Google Earth Engine.
    Prioridad de autenticación:
    1. Variable de entorno GOOGLE_APPLICATION_CREDENTIALS_JSON (Contenido JSON raw)
    2. Archivo service-account-key.json en carpeta api/
    3. Credenciales por defecto (gcloud)
    """
    try:
        # 1. Intentar cargar desde variable de entorno (Mejor práctica para Railway/Prod)
        env_creds_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if env_creds_json:
            print("Iniciando GEE desde variable de entorno...")
            try:
                creds_dict = json.loads(env_creds_json)
                credentials = service_account.Credentials.from_service_account_info(creds_dict)
                scoped_credentials = credentials.with_scopes(
                    ['https://www.googleapis.com/auth/cloud-platform',
                     'https://www.googleapis.com/auth/earthengine'])
                ee.Initialize(credentials=scoped_credentials)
                print("GEE inicializado correctamente desde ENV VAR.")
                return True
            except json.JSONDecodeError:
                print("Error: La variable GOOGLE_APPLICATION_CREDENTIALS_JSON no es un JSON válido.")
            except Exception as e:
                print(f"Error usando credenciales de entorno: {e}")

        # 2. Intentar cargar desde archivo (Desarrollo local)
        key_path = os.path.join(os.path.dirname(__file__), 'service-account-key.json')
        if os.path.exists(key_path):
            print(f"Iniciando GEE con archivo de clave: {key_path}")
            credentials = service_account.Credentials.from_service_account_file(key_path)
            scoped_credentials = credentials.with_scopes(
                ['https://www.googleapis.com/auth/cloud-platform',
                 'https://www.googleapis.com/auth/earthengine'])
            
            ee.Initialize(credentials=scoped_credentials)
            print("GEE inicializado correctamente con Service Account (Archivo).")
            return True
        
        # 3. Fallback a credenciales por defecto
        print("No se encontraron credenciales explícitas, intentando default...")
        try:
            ee.Initialize()
            print("GEE inicializado con credenciales por defecto.")
            return True
        except Exception as e:
            print(f"Error en autenticación por defecto: {e}")
            return False

    except Exception as e:
        print(f"Error crítico inicializando GEE: {e}")
        return False
