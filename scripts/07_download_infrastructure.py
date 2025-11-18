#!/usr/bin/env python3
"""
Descarga de Infraestructura Crítica desde OpenStreetMap
========================================================
Descarga datos de infraestructura para análisis de riesgo en Papudo

Categorías de infraestructura:
- Educación: Escuelas, colegios, jardines infantiles
- Salud: Hospitales, postas, clínicas
- Emergencias: Bomberos, carabineros, PDI
- Servicios: Municipalidad, servicios públicos
- Comercio: Supermercados, farmacias
- Edificios: Todos los edificios OSM

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import os
import sys
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, box
import requests
import json
from pathlib import Path
import time

# Colores
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{'='*80}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{text}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{'='*80}{bcolors.ENDC}\n")

def print_success(text):
    print(f"{bcolors.OKGREEN}✓ {text}{bcolors.ENDC}")

def print_error(text):
    print(f"{bcolors.FAIL}✗ {text}{bcolors.ENDC}")

def print_info(text):
    print(f"{bcolors.OKCYAN}ℹ {text}{bcolors.ENDC}")

# Configuración
PROJECT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_DIR / "data" / "infrastructure"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Área de interés: Papudo
# Basado en el boundary creado anteriormente
PAPUDO_BOUNDS = {
    'name': 'Papudo',
    'min_lon': -71.49,
    'min_lat': -32.54,
    'max_lon': -71.42,
    'max_lat': -32.47
}

# ============================================================================
# FUNCIÓN 1: Consulta Overpass API (OpenStreetMap)
# ============================================================================

def query_overpass(query, max_retries=3):
    """
    Consulta la Overpass API de OpenStreetMap
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    for attempt in range(max_retries):
        try:
            print_info(f"Consultando Overpass API... (intento {attempt + 1}/{max_retries})")
            response = requests.post(overpass_url, data={'data': query}, timeout=60)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print_warning(f"Rate limit alcanzado, esperando 60 segundos...")
                time.sleep(60)
            else:
                print_error(f"Error HTTP {response.status_code}")

        except Exception as e:
            print_error(f"Error en consulta: {e}")
            if attempt < max_retries - 1:
                time.sleep(10)

    return None

# ============================================================================
# FUNCIÓN 2: Descargar categorías de infraestructura
# ============================================================================

def download_infrastructure_category(category_name, osm_tags, bbox):
    """
    Descarga una categoría específica de infraestructura
    """
    print_info(f"Descargando: {category_name}")

    # Construir query Overpass
    bbox_str = f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}"

    # Construir filtros de tags
    tag_filters = []
    for key, values in osm_tags.items():
        if isinstance(values, list):
            for value in values:
                tag_filters.append(f'["{key}"="{value}"]')
        else:
            tag_filters.append(f'["{key}"="{values}"]')

    tag_filter_str = ''.join(tag_filters)

    query = f"""
    [out:json][timeout:60];
    (
      node{tag_filter_str}({bbox_str});
      way{tag_filter_str}({bbox_str});
      relation{tag_filter_str}({bbox_str});
    );
    out center;
    """

    result = query_overpass(query)

    if not result or 'elements' not in result:
        print_warning(f"No se encontraron datos para {category_name}")
        return None

    elements = result['elements']

    if not elements:
        print_warning(f"No hay elementos en {category_name}")
        return None

    # Convertir a GeoDataFrame
    features = []

    for element in elements:
        try:
            # Obtener coordenadas
            if element['type'] == 'node':
                lon, lat = element['lon'], element['lat']
            elif 'center' in element:
                lon, lat = element['center']['lon'], element['center']['lat']
            else:
                continue

            # Extraer tags relevantes
            tags = element.get('tags', {})

            feature = {
                'osm_id': element['id'],
                'osm_type': element['type'],
                'name': tags.get('name', 'Sin nombre'),
                'category': category_name,
                'amenity': tags.get('amenity', ''),
                'building': tags.get('building', ''),
                'shop': tags.get('shop', ''),
                'healthcare': tags.get('healthcare', ''),
                'emergency': tags.get('emergency', ''),
                'office': tags.get('office', ''),
                'addr_street': tags.get('addr:street', ''),
                'addr_number': tags.get('addr:housenumber', ''),
                'geometry': Point(lon, lat)
            }

            features.append(feature)

        except Exception as e:
            print_error(f"Error procesando elemento {element.get('id')}: {e}")

    if not features:
        print_warning(f"No se pudieron procesar elementos de {category_name}")
        return None

    gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')

    # Convertir a UTM 19S
    gdf = gdf.to_crs('EPSG:32719')

    print_success(f"{category_name}: {len(gdf)} elementos descargados")

    return gdf

# ============================================================================
# FUNCIÓN 3: Descargar edificios (simplificado)
# ============================================================================

def download_buildings(bbox):
    """
    Descarga edificios de OSM (versión simplificada para evitar sobrecarga)
    """
    print_info("Descargando edificios...")

    bbox_str = f"{bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']}"

    # Query solo para edificios
    query = f"""
    [out:json][timeout:120];
    (
      way["building"]({bbox_str});
      relation["building"]({bbox_str});
    );
    out center;
    """

    result = query_overpass(query)

    if not result or 'elements' not in result:
        print_warning("No se encontraron edificios")
        return None

    elements = result['elements']
    features = []

    for element in elements:
        try:
            if 'center' in element:
                lon, lat = element['center']['lon'], element['center']['lat']
            else:
                continue

            tags = element.get('tags', {})

            feature = {
                'osm_id': element['id'],
                'osm_type': element['type'],
                'name': tags.get('name', 'Edificio sin nombre'),
                'category': 'Edificios',
                'building': tags.get('building', 'yes'),
                'building_levels': tags.get('building:levels', ''),
                'addr_street': tags.get('addr:street', ''),
                'addr_number': tags.get('addr:housenumber', ''),
                'geometry': Point(lon, lat)
            }

            features.append(feature)

        except Exception as e:
            continue

    if not features:
        print_warning("No se pudieron procesar edificios")
        return None

    gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
    gdf = gdf.to_crs('EPSG:32719')

    print_success(f"Edificios: {len(gdf)} elementos descargados")

    return gdf

# ============================================================================
# MAIN
# ============================================================================

def main():
    print_header("DESCARGA DE INFRAESTRUCTURA CRÍTICA - PAPUDO")

    print_info(f"Área de interés: {PAPUDO_BOUNDS['name']}")
    print_info(f"Bbox: [{PAPUDO_BOUNDS['min_lon']}, {PAPUDO_BOUNDS['min_lat']}, {PAPUDO_BOUNDS['max_lon']}, {PAPUDO_BOUNDS['max_lat']}]")

    # Definir categorías de infraestructura
    categories = {
        'Educación': {
            'amenity': ['school', 'kindergarten', 'college', 'university']
        },
        'Salud': {
            'amenity': ['hospital', 'clinic', 'doctors', 'pharmacy'],
            'healthcare': ['hospital', 'clinic', 'doctor']
        },
        'Emergencias': {
            'amenity': ['fire_station', 'police'],
            'emergency': ['fire_station', 'ambulance_station']
        },
        'Gobierno': {
            'amenity': ['townhall', 'public_building'],
            'office': ['government']
        },
        'Comercio': {
            'shop': ['supermarket', 'convenience', 'mall'],
            'amenity': ['marketplace']
        },
        'Servicios Básicos': {
            'amenity': ['fuel', 'bank', 'post_office']
        }
    }

    # Descargar cada categoría
    all_infrastructure = []

    for category_name, osm_tags in categories.items():
        gdf = download_infrastructure_category(category_name, osm_tags, PAPUDO_BOUNDS)

        if gdf is not None and not gdf.empty:
            all_infrastructure.append(gdf)

            # Guardar categoría individual
            output_file = OUTPUT_DIR / f"{category_name.replace(' ', '_').lower()}.geojson"
            gdf.to_file(output_file, driver='GeoJSON')
            print_success(f"Guardado: {output_file}")

        time.sleep(2)  # Pausa para no saturar la API

    # Descargar edificios
    buildings_gdf = download_buildings(PAPUDO_BOUNDS)
    if buildings_gdf is not None and not buildings_gdf.empty:
        all_infrastructure.append(buildings_gdf)
        output_file = OUTPUT_DIR / "edificios.geojson"
        buildings_gdf.to_file(output_file, driver='GeoJSON')
        print_success(f"Guardado: {output_file}")

    # Combinar todo
    if all_infrastructure:
        print_info("\nCombinando todas las capas...")
        combined = gpd.GeoDataFrame(pd.concat(all_infrastructure, ignore_index=True))
        combined = combined.to_crs('EPSG:32719')

        # Guardar combinado
        output_combined = OUTPUT_DIR / "infraestructura_completa.geojson"
        combined.to_file(output_combined, driver='GeoJSON')

        # Guardar también como shapefile
        output_shp = OUTPUT_DIR / "infraestructura_completa.shp"
        combined.to_file(output_shp)

        print_header("RESUMEN DE DESCARGA")
        print_success(f"Total de elementos: {len(combined)}")

        print("\nDistribución por categoría:")
        for cat in combined['category'].value_counts().items():
            print_info(f"  • {cat[0]}: {cat[1]} elementos")

        print(f"\nArchivos guardados en: {OUTPUT_DIR}")
        print_success(f"✓ infraestructura_completa.geojson ({len(combined)} elementos)")
        print_success(f"✓ infraestructura_completa.shp")

        print("\nPróximo paso: Análisis de intersección con zonas de riesgo")
        print("  → python scripts/08_analyze_infrastructure_risk.py")

    else:
        print_error("No se descargó ninguna infraestructura")
        sys.exit(1)

if __name__ == '__main__':
    main()
