#!/usr/bin/env python3
"""
Descargar DEM SRTM automáticamente para Papudo
"""

import elevation
import os

# Cambiar al directorio del proyecto
project_dir = os.path.expanduser('~/geofeedback-papudo')
os.chdir(project_dir)

# Crear carpeta
os.makedirs('data/raw', exist_ok=True)

# Definir bounding box (Papudo + buffer)
# (west, south, east, north)
bounds = (-71.6, -32.6, -71.2, -32.2)

# Descargar SRTM 30m
print("Descargando DEM SRTM para Papudo...")
print(f"Área: {bounds}")
print("Esto puede tomar varios minutos...")

try:
    output_path = os.path.join(project_dir, 'data', 'raw', 'SRTM_Papudo_DEM.tif')
    elevation.clip(
        bounds=bounds,
        output=output_path,
        product='SRTM1',  # 30m resolución
        margin='0.01'
    )

    print("✓ DEM descargado exitosamente")
    print("  Ubicación: data/raw/SRTM_Papudo_DEM.tif")

    # Limpiar archivos temporales
    elevation.clean()
    print("✓ Archivos temporales eliminados")

except Exception as e:
    print(f"✗ Error al descargar DEM: {e}")
    print("  Intenta descargar manualmente desde OpenTopography o USGS")
