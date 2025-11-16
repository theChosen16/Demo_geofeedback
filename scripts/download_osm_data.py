#!/usr/bin/env python3
"""
Descargar datos de OpenStreetMap para Papudo
Incluye: límites administrativos, vías, edificios
"""

import osmnx as ox
import geopandas as gpd
import os

# Configuración
project_dir = os.path.expanduser('~/geofeedback-papudo')
os.chdir(project_dir)

# Crear carpetas
os.makedirs('data/raw/OSM', exist_ok=True)

print("=" * 60)
print("DESCARGA DE DATOS OPENSTREETMAP - PAPUDO")
print("=" * 60)

try:
    # 1. LÍMITE ADMINISTRATIVO DE PAPUDO
    print("\n1. Descargando límite administrativo de Papudo...")
    try:
        # Buscar Papudo en OpenStreetMap
        gdf_limite = ox.geocode_to_gdf("Papudo, Valparaíso, Chile", which_result=1)

        # Guardar como shapefile
        output_path = 'data/raw/OSM/Limite_Papudo.shp'
        gdf_limite.to_file(output_path)

        print(f"   ✓ Límite descargado: {output_path}")
        print(f"   Área: {gdf_limite.geometry.area.values[0]:.6f} grados²")

    except Exception as e:
        print(f"   ✗ Error al descargar límite: {e}")
        print("   Intentando método alternativo...")

        # Método alternativo: crear polígono manual con coordenadas
        from shapely.geometry import box
        import pandas as pd

        # Bbox aproximado de Papudo
        west, south, east, north = -71.48, -32.52, -71.42, -32.48
        geom = box(west, south, east, north)

        gdf_limite = gpd.GeoDataFrame(
            {'name': ['Papudo'], 'admin_level': [8]},
            geometry=[geom],
            crs='EPSG:4326'
        )
        gdf_limite.to_file('data/raw/OSM/Limite_Papudo.shp')
        print("   ✓ Límite creado con bbox aproximado")

    # 2. RED VIAL
    print("\n2. Descargando red vial...")
    try:
        # Obtener bbox del límite
        bounds = gdf_limite.total_bounds  # [west, south, east, north]

        # Descargar red vial usando bbox
        bbox = (bounds[3], bounds[1], bounds[2], bounds[0])  # (north, south, east, west)
        G = ox.graph_from_bbox(bbox=bbox, network_type='all')

        # Convertir a GeoDataFrame
        gdf_vias = ox.graph_to_gdfs(G, nodes=False, edges=True)

        # Guardar
        output_path = 'data/raw/OSM/Vias_Papudo.shp'
        gdf_vias.to_file(output_path)

        print(f"   ✓ Red vial descargada: {output_path}")
        print(f"   Total de vías: {len(gdf_vias)}")

    except Exception as e:
        print(f"   ✗ Error al descargar vías: {e}")

    # 3. EDIFICIOS
    print("\n3. Descargando edificios...")
    try:
        # Descargar edificios usando bbox
        gdf_edificios = ox.features_from_bbox(
            bbox=bbox,
            tags={'building': True}
        )

        # Guardar solo columnas relevantes
        cols_relevantes = ['geometry', 'building', 'name']
        cols_disponibles = [c for c in cols_relevantes if c in gdf_edificios.columns]
        gdf_edificios = gdf_edificios[cols_disponibles]

        output_path = 'data/raw/OSM/Edificios_Papudo.shp'
        gdf_edificios.to_file(output_path)

        print(f"   ✓ Edificios descargados: {output_path}")
        print(f"   Total edificios: {len(gdf_edificios)}")

    except Exception as e:
        print(f"   ✗ Error al descargar edificios: {e}")

    # 4. AMENIDADES (escuelas, hospitales, etc.)
    print("\n4. Descargando amenidades (servicios públicos)...")
    try:
        gdf_amenidades = ox.features_from_bbox(
            bbox=bbox,
            tags={'amenity': True}
        )

        # Filtrar solo puntos y polígonos
        gdf_amenidades = gdf_amenidades[gdf_amenidades.geometry.type.isin(['Point', 'Polygon'])]

        # Guardar
        cols_relevantes = ['geometry', 'amenity', 'name']
        cols_disponibles = [c for c in cols_relevantes if c in gdf_amenidades.columns]
        gdf_amenidades = gdf_amenidades[cols_disponibles]

        output_path = 'data/raw/OSM/Amenidades_Papudo.shp'
        gdf_amenidades.to_file(output_path)

        print(f"   ✓ Amenidades descargadas: {output_path}")
        print(f"   Total amenidades: {len(gdf_amenidades)}")

    except Exception as e:
        print(f"   ✗ Error al descargar amenidades: {e}")

    print("\n" + "=" * 60)
    print("✅ DESCARGA COMPLETADA")
    print("=" * 60)
    print("\nArchivos generados en: data/raw/OSM/")
    print("  - Limite_Papudo.shp")
    print("  - Vias_Papudo.shp")
    print("  - Edificios_Papudo.shp")
    print("  - Amenidades_Papudo.shp")

except Exception as e:
    print(f"\n✗ Error general: {e}")
    print("\nSi el error persiste, intenta descargar manualmente desde:")
    print("  - https://www.openstreetmap.org/")
    print("  - https://download.geofabrik.de/south-america/chile.html")
