#!/usr/bin/env python3
"""
Descarga Simple de Infraestructura desde OpenStreetMap
=======================================================
Versión ligera que no requiere geopandas

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import json
import time
import os
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests no está instalado. Instalando...")
    os.system("pip3 install requests --user --quiet")
    import requests

# Colores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

# Configuración
PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "data" / "infrastructure"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Área de Papudo
BBOX = {
    'min_lat': -32.54,
    'min_lon': -71.49,
    'max_lat': -32.47,
    'max_lon': -71.42
}

print(f"\n{BLUE}{'='*80}{END}")
print(f"{BLUE}DESCARGA DE INFRAESTRUCTURA - PAPUDO{END}")
print(f"{BLUE}{'='*80}{END}\n")

# Categorías de infraestructura con tags OSM
CATEGORIES = {
    'educacion': {
        'name': 'Educación',
        'tags': '[amenity~"school|kindergarten|college"]'
    },
    'salud': {
        'name': 'Salud',
        'tags': '[amenity~"hospital|clinic|doctors|pharmacy"]'
    },
    'emergencias': {
        'name': 'Emergencias',
        'tags': '[amenity~"fire_station|police"]'
    },
    'gobierno': {
        'name': 'Gobierno',
        'tags': '[amenity~"townhall|public_building"]'
    },
    'comercio': {
        'name': 'Comercio',
        'tags': '[shop~"supermarket|convenience|mall"]'
    }
}

def query_overpass(query, max_retries=3):
    """Consulta Overpass API"""
    url = "https://overpass-api.de/api/interpreter"

    for attempt in range(max_retries):
        try:
            print(f"{YELLOW}  Consultando API... (intento {attempt + 1}/{max_retries}){END}")
            response = requests.post(url, data={'data': query}, timeout=60)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"{YELLOW}  Rate limit, esperando 60s...{END}")
                time.sleep(60)
            else:
                print(f"{RED}  Error HTTP {response.status_code}{END}")

        except Exception as e:
            print(f"{RED}  Error: {e}{END}")
            if attempt < max_retries - 1:
                time.sleep(10)

    return None

def osm_to_geojson(osm_data):
    """Convierte OSM JSON a GeoJSON"""
    features = []

    for element in osm_data.get('elements', []):
        # Obtener coordenadas
        if element['type'] == 'node':
            lon, lat = element['lon'], element['lat']
        elif 'center' in element:
            lon, lat = element['center']['lon'], element['center']['lat']
        else:
            continue

        # Propiedades
        tags = element.get('tags', {})
        properties = {
            'osm_id': element['id'],
            'osm_type': element['type'],
            'name': tags.get('name', 'Sin nombre'),
            'amenity': tags.get('amenity', ''),
            'shop': tags.get('shop', ''),
            'building': tags.get('building', ''),
            'addr_street': tags.get('addr:street', ''),
            'addr_number': tags.get('addr:housenumber', '')
        }

        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat]
            },
            'properties': properties
        }

        features.append(feature)

    return {
        'type': 'FeatureCollection',
        'features': features
    }

# Descargar cada categoría
all_features = []
stats = {}

for key, cat in CATEGORIES.items():
    print(f"\n{BLUE}Categoría: {cat['name']}{END}")

    bbox_str = f"{BBOX['min_lat']},{BBOX['min_lon']},{BBOX['max_lat']},{BBOX['max_lon']}"

    query = f"""
    [out:json][timeout:60];
    (
      node{cat['tags']}({bbox_str});
      way{cat['tags']}({bbox_str});
      relation{cat['tags']}({bbox_str});
    );
    out center;
    """

    result = query_overpass(query)

    if result:
        geojson = osm_to_geojson(result)
        count = len(geojson['features'])

        if count > 0:
            # Añadir categoría a cada feature
            for feat in geojson['features']:
                feat['properties']['category'] = cat['name']
                all_features.append(feat)

            # Guardar categoría individual
            output_file = OUTPUT_DIR / f"{key}.geojson"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(geojson, f, indent=2, ensure_ascii=False)

            print(f"{GREEN}  ✓ {cat['name']}: {count} elementos{END}")
            print(f"{GREEN}  ✓ Guardado: {output_file.name}{END}")
            stats[cat['name']] = count
        else:
            print(f"{YELLOW}  ⚠ Sin elementos{END}")
            stats[cat['name']] = 0

    time.sleep(2)  # Pausa entre consultas

# Guardar todo combinado
if all_features:
    combined_geojson = {
        'type': 'FeatureCollection',
        'features': all_features
    }

    output_combined = OUTPUT_DIR / "infraestructura_completa.geojson"
    with open(output_combined, 'w', encoding='utf-8') as f:
        json.dump(combined_geojson, f, indent=2, ensure_ascii=False)

    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{GREEN}✓ DESCARGA COMPLETADA{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    print(f"Total de elementos: {len(all_features)}")
    print("\nDistribución por categoría:")
    for cat, count in stats.items():
        print(f"  • {cat}: {count}")

    print(f"\nArchivo combinado: {output_combined}")
    print(f"\nPróximo paso: Análisis de riesgo")
    print(f"  python scripts/08_analyze_infrastructure_risk.py\n")

else:
    print(f"\n{RED}✗ No se descargó ninguna infraestructura{END}\n")
    print(f"{YELLOW}Nota: Papudo es una comuna pequeña, puede tener pocos datos en OSM{END}")
    print(f"{YELLOW}Se creará infraestructura de ejemplo para la demo...{END}\n")

    # Crear datos de ejemplo
    example_features = [
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-71.4492, -32.5067]},
            'properties': {
                'name': 'Municipalidad de Papudo',
                'category': 'Gobierno',
                'amenity': 'townhall'
            }
        },
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-71.4510, -32.5055]},
            'properties': {
                'name': 'Escuela Básica Papudo',
                'category': 'Educación',
                'amenity': 'school'
            }
        },
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-71.4485, -32.5080]},
            'properties': {
                'name': 'Posta de Salud Rural',
                'category': 'Salud',
                'amenity': 'clinic'
            }
        },
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-71.4475, -32.5070]},
            'properties': {
                'name': 'Cuartel de Bomberos',
                'category': 'Emergencias',
                'amenity': 'fire_station'
            }
        },
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-71.4520, -32.5090]},
            'properties': {
                'name': 'Supermercado Local',
                'category': 'Comercio',
                'shop': 'supermarket'
            }
        }
    ]

    example_geojson = {
        'type': 'FeatureCollection',
        'features': example_features
    }

    output_example = OUTPUT_DIR / "infraestructura_completa.geojson"
    with open(output_example, 'w', encoding='utf-8') as f:
        json.dump(example_geojson, f, indent=2, ensure_ascii=False)

    print(f"{GREEN}✓ Infraestructura de ejemplo creada: {output_example}{END}\n")
