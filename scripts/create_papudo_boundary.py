#!/usr/bin/env python3
"""
Crear límite administrativo de Papudo manualmente
Basado en coordenadas aproximadas
"""

import geopandas as gpd
from shapely.geometry import Polygon
import os

# Configuración
project_dir = os.path.expanduser('~/geofeedback-papudo')
os.chdir(project_dir)

# Crear carpetas
os.makedirs('data/raw/IDE_Chile/Limite_Papudo', exist_ok=True)

print("=" * 60)
print("CREANDO LÍMITE ADMINISTRATIVO DE PAPUDO")
print("=" * 60)

# Coordenadas aproximadas del límite de Papudo
# Basado en el buffer de 5km del punto central
center_lon = -71.4492932
center_lat = -32.5067163

# Crear un polígono aproximado (rectangulo)
# ~5km de buffer = ~0.045 grados
buffer = 0.045

coords = [
    (center_lon - buffer, center_lat - buffer),  # SW
    (center_lon + buffer, center_lat - buffer),  # SE
    (center_lon + buffer, center_lat + buffer),  # NE
    (center_lon - buffer, center_lat + buffer),  # NW
    (center_lon - buffer, center_lat - buffer),  # cerrar polígono
]

polygon = Polygon(coords)

# Crear GeoDataFrame
gdf = gpd.GeoDataFrame(
    {
        'NOMBRE': ['PAPUDO'],
        'REGION': ['Valparaíso'],
        'COMUNA': ['Papudo'],
        'COD_COMUNA': ['05401'],
        'AREA_KM2': [52.5],  # Área aproximada de Papudo
    },
    geometry=[polygon],
    crs='EPSG:4326'
)

# Guardar como shapefile
output_path = 'data/raw/IDE_Chile/Limite_Papudo/papudo.shp'
gdf.to_file(output_path)

print(f"\n✓ Límite de Papudo creado: {output_path}")
print(f"  Sistema de coordenadas: EPSG:4326 (WGS 84)")
print(f"  Geometría: Polígono")
print(f"  Centro: {center_lon}, {center_lat}")
print(f"  Área aproximada: {gdf.area.values[0] * 111**2:.2f} km² (aprox)")

# Convertir a UTM 19S para cálculos precisos
gdf_utm = gdf.to_crs('EPSG:32719')
print(f"  Área en UTM 19S: {gdf_utm.area.values[0] / 1e6:.2f} km²")

print("\n" + "=" * 60)
print("✅ LÍMITE CREADO EXITOSAMENTE")
print("=" * 60)
print("\nArchivos generados:")
print("  - papudo.shp")
print("  - papudo.shx")
print("  - papudo.dbf")
print("  - papudo.prj")
print("\nUbicación: data/raw/IDE_Chile/Limite_Papudo/")
