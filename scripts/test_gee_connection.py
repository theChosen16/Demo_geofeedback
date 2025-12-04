import sys
import os

# Agregar el directorio 'api' al path para poder importar gee_config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))

from gee_config import init_gee
import ee

def test_connection():
    print("=== Probando conexión a Google Earth Engine ===")
    
    if init_gee():
        print("\n✅ Inicialización exitosa.")
        
        try:
            print("Intentando operación simple (getInfo de SRTM)...")
            image = ee.Image('CGIAR/SRTM90_V4')
            info = image.getInfo()
            print(f"✅ Operación exitosa. ID de imagen: {info.get('id')}")
            print(f"Bandas disponibles: {[b['id'] for b in info.get('bands', [])]}")
        except Exception as e:
            print(f"❌ Error al ejecutar operación en GEE: {e}")
    else:
        print("\n❌ Falló la inicialización.")
        print("Asegúrate de tener 'service-account-key.json' en la carpeta 'api/'")
        print("O ejecuta 'earthengine authenticate' para desarrollo local.")

if __name__ == "__main__":
    test_connection()
