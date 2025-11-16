import requests
import json

def test_analysis():
    url = "http://localhost:5000/api/v1/analyze"
    
    # Coordenadas de prueba (Zona Minera/Agricola - Norte Chico)
    payload = {
        "lat": -30.6046, 
        "lng": -71.2073,
        "approach": "agriculture"
    }
    
    print(f"Probando endpoint: {url}")
    print(f"Payload: {payload}")
    
    try:
        # Nota: Esto fallará si el servidor no está corriendo. 
        # Este script es para uso manual o si pudiéramos levantar el servidor en background.
        # Como no podemos levantar el servidor persistente aquí, simulamos la lógica importando app
        from app import analyze_territory, app
        
        with app.test_request_context(json=payload):
            response = analyze_territory()
            print(f"\nStatus Code: {response.status_code}")
            print(f"Response: {json.dumps(response.get_json(), indent=2)}")
            
    except ImportError:
        print("No se pudo importar la app para testing directo.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    import os
    # Agregar el directorio 'api' al path para que app.py encuentre gee_config
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    api_dir = os.path.join(project_root, 'api')
    sys.path.insert(0, api_dir)
    
    test_analysis()
