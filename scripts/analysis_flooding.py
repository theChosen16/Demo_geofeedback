#!/usr/bin/env python3
"""
Análisis de Riesgo de Inundación - Papudo
===========================================
Calcula amenaza de inundación combinando:
- Pendiente topográfica (50%)
- Cobertura del suelo / NDVI (35%)
- Depresiones topográficas (15%)

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import os
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.fill import fillnodata
from scipy.ndimage import gaussian_filter, generic_filter
import geopandas as gpd
from shapely.geometry import shape
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Configuración
project_dir = os.path.expanduser('~/geofeedback-papudo')
os.chdir(project_dir)

print("=" * 80)
print("ANÁLISIS DE RIESGO DE INUNDACIÓN - PAPUDO")
print("=" * 80)

# Crear carpeta de salida
os.makedirs('data/processed', exist_ok=True)

# ============================================================================
# PASO 1: CARGAR Y REPROYECTAR DATOS A UTM 19S
# ============================================================================
print("\n[1/8] Cargando datos de entrada...")

dem_path = 'data/raw/SRTM_Papudo_DEM.tif'
ndvi_path = 'data/raw/Sentinel2_NDVI_Papudo.tif'

# Verificar archivos
if not os.path.exists(dem_path):
    raise FileNotFoundError(f"DEM no encontrado: {dem_path}")
if not os.path.exists(ndvi_path):
    raise FileNotFoundError(f"NDVI no encontrado: {ndvi_path}")

print(f"  ✓ DEM: {dem_path}")
print(f"  ✓ NDVI: {ndvi_path}")

# Leer DEM
with rasterio.open(dem_path) as src:
    dem_data = src.read(1)
    dem_meta = src.meta.copy()
    dem_transform = src.transform
    dem_crs = src.crs
    dem_bounds = src.bounds

print(f"\n  DEM - Tamaño: {dem_data.shape}, CRS: {dem_crs}")

# Reproyectar DEM a UTM 19S si es necesario
target_crs = 'EPSG:32719'  # UTM Zone 19S
if str(dem_crs) != target_crs:
    print(f"\n[2/8] Reproyectando DEM a UTM 19S...")

    transform, width, height = calculate_default_transform(
        dem_crs, target_crs, dem_data.shape[1], dem_data.shape[0],
        *dem_bounds
    )

    dem_utm = np.empty((height, width), dtype=dem_data.dtype)

    reproject(
        source=dem_data,
        destination=dem_utm,
        src_transform=dem_transform,
        src_crs=dem_crs,
        dst_transform=transform,
        dst_crs=target_crs,
        resampling=Resampling.bilinear
    )

    dem_data = dem_utm
    dem_transform = transform
    dem_crs = target_crs
    print(f"  ✓ DEM reproyectado - Nuevo tamaño: {dem_data.shape}")
else:
    print(f"  ✓ DEM ya está en UTM 19S")

# Leer NDVI
with rasterio.open(ndvi_path) as src:
    ndvi_data = src.read(1)
    ndvi_meta = src.meta.copy()
    ndvi_transform = src.transform
    ndvi_crs = src.crs

print(f"  NDVI - Tamaño: {ndvi_data.shape}, CRS: {ndvi_crs}")

# Reproyectar NDVI para que coincida con DEM
print(f"\n[3/8] Alineando NDVI con DEM...")

ndvi_aligned = np.empty(dem_data.shape, dtype=np.float32)

reproject(
    source=ndvi_data,
    destination=ndvi_aligned,
    src_transform=ndvi_transform,
    src_crs=ndvi_crs,
    dst_transform=dem_transform,
    dst_crs=dem_crs,
    resampling=Resampling.bilinear
)

print(f"  ✓ NDVI alineado - Tamaño: {ndvi_aligned.shape}")

# ============================================================================
# PASO 2: CALCULAR PENDIENTE
# ============================================================================
print("\n[4/8] Calculando pendiente...")

# Calcular gradientes (dx, dy)
pixel_size = dem_transform[0]  # metros
dy, dx = np.gradient(dem_data, pixel_size)

# Pendiente en grados
slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
slope_deg = np.degrees(slope_rad)

# Rellenar valores NoData
mask = (dem_data == dem_meta.get('nodata', -32768)) | np.isnan(dem_data)
slope_deg = np.where(mask, 0, slope_deg)

print(f"  ✓ Pendiente calculada")
print(f"    Min: {slope_deg.min():.2f}°, Max: {slope_deg.max():.2f}°, Media: {slope_deg.mean():.2f}°")

# ============================================================================
# PASO 3: CALCULAR SCORE DE AMENAZA
# ============================================================================
print("\n[5/8] Calculando score de amenaza...")

# Inicializar score
amenaza_score = np.zeros_like(dem_data, dtype=np.float32)

# FACTOR 1: PENDIENTE (50% del peso)
# Pendiente baja = MAYOR riesgo de inundación
score_pendiente = np.zeros_like(slope_deg)
score_pendiente[slope_deg < 2] = 100      # Plano - riesgo MUY ALTO
score_pendiente[(slope_deg >= 2) & (slope_deg < 5)] = 70   # Suave - riesgo ALTO
score_pendiente[(slope_deg >= 5) & (slope_deg < 10)] = 40  # Moderado - riesgo MEDIO
score_pendiente[slope_deg >= 10] = 10     # Pendiente fuerte - riesgo BAJO

print(f"  Factor 1 - Pendiente (50%):")
print(f"    Áreas planas (<2°): {np.sum(slope_deg < 2)} píxeles")
print(f"    Áreas suaves (2-5°): {np.sum((slope_deg >= 2) & (slope_deg < 5))} píxeles")

# FACTOR 2: NDVI / COBERTURA DEL SUELO (35% del peso)
# NDVI bajo = suelo desnudo/impermeable = MAYOR riesgo
score_ndvi = np.zeros_like(ndvi_aligned)
score_ndvi[ndvi_aligned < -0.1] = 100    # Agua/suelo desnudo - riesgo MUY ALTO
score_ndvi[(ndvi_aligned >= -0.1) & (ndvi_aligned < 0.2)] = 70   # Suelo poco vegetado - ALTO
score_ndvi[(ndvi_aligned >= 0.2) & (ndvi_aligned < 0.4)] = 40    # Vegetación media - MEDIO
score_ndvi[ndvi_aligned >= 0.4] = 10     # Vegetación densa - BAJO

# Manejar NoData en NDVI
score_ndvi = np.where(np.isnan(ndvi_aligned) | (ndvi_aligned == 0), 50, score_ndvi)

print(f"  Factor 2 - NDVI (35%):")
print(f"    Suelo desnudo (NDVI<-0.1): {np.sum(ndvi_aligned < -0.1)} píxeles")
print(f"    Vegetación media (0.2-0.4): {np.sum((ndvi_aligned >= 0.2) & (ndvi_aligned < 0.4))} píxeles")

# FACTOR 3: DEPRESIONES TOPOGRÁFICAS (15% del peso)
# Identificar áreas que acumulan agua
print(f"  Factor 3 - Depresiones (15%)...")

# Calcular mínimo local (depresiones)
def is_local_minimum(values):
    """Detecta si el pixel central es un mínimo local"""
    center = values[len(values)//2]
    return center < np.mean(values)

# Aplicar filtro para detectar depresiones
depression_mask = generic_filter(dem_data, is_local_minimum, size=5, mode='constant')

score_depression = np.where(depression_mask, 80, 20)

print(f"    Depresiones detectadas: {np.sum(depression_mask)} píxeles")

# COMBINAR FACTORES CON PESOS
amenaza_score = (
    score_pendiente * 0.50 +      # 50%
    score_ndvi * 0.35 +            # 35%
    score_depression * 0.15        # 15%
)

# Suavizar para eliminar ruido
amenaza_score = gaussian_filter(amenaza_score, sigma=1.5)

print(f"\n  ✓ Score de amenaza calculado")
print(f"    Min: {amenaza_score.min():.2f}, Max: {amenaza_score.max():.2f}, Media: {amenaza_score.mean():.2f}")

# ============================================================================
# PASO 4: CLASIFICAR EN 3 NIVELES DE RIESGO
# ============================================================================
print("\n[6/8] Clasificando en niveles de riesgo...")

amenaza_clasificada = np.zeros_like(amenaza_score, dtype=np.uint8)
amenaza_clasificada[amenaza_score >= 70] = 3   # ROJO - Riesgo ALTO
amenaza_clasificada[(amenaza_score >= 40) & (amenaza_score < 70)] = 2  # AMARILLO - Riesgo MEDIO
amenaza_clasificada[(amenaza_score > 0) & (amenaza_score < 40)] = 1    # VERDE - Riesgo BAJO
amenaza_clasificada[mask] = 0  # NoData

pixeles_totales = np.sum(amenaza_clasificada > 0)
pixeles_rojo = np.sum(amenaza_clasificada == 3)
pixeles_amarillo = np.sum(amenaza_clasificada == 2)
pixeles_verde = np.sum(amenaza_clasificada == 1)

print(f"  🔴 Riesgo ALTO (≥70):    {pixeles_rojo:6d} píxeles ({pixeles_rojo/pixeles_totales*100:5.2f}%)")
print(f"  🟡 Riesgo MEDIO (40-70): {pixeles_amarillo:6d} píxeles ({pixeles_amarillo/pixeles_totales*100:5.2f}%)")
print(f"  🟢 Riesgo BAJO (<40):    {pixeles_verde:6d} píxeles ({pixeles_verde/pixeles_totales*100:5.2f}%)")

# ============================================================================
# PASO 5: EXPORTAR RESULTADOS
# ============================================================================
print("\n[7/8] Exportando resultados...")

# Actualizar metadata para salida
output_meta = dem_meta.copy()
output_meta.update({
    'driver': 'GTiff',
    'height': dem_data.shape[0],
    'width': dem_data.shape[1],
    'transform': dem_transform,
    'crs': dem_crs,
    'compress': 'deflate',
    'dtype': 'float32'
})

# 1. Score continuo
with rasterio.open('data/processed/Amenaza_Score_Continuo.tif', 'w', **output_meta) as dst:
    dst.write(amenaza_score.astype(np.float32), 1)
print(f"  ✓ Amenaza_Score_Continuo.tif")

# 2. Clasificación 3 niveles
output_meta.update({'dtype': 'uint8', 'nodata': 0})
with rasterio.open('data/processed/Amenaza_Clasificada.tif', 'w', **output_meta) as dst:
    dst.write(amenaza_clasificada, 1)
    # Agregar tabla de colores
    dst.write_colormap(1, {
        0: (0, 0, 0, 0),         # NoData - transparente
        1: (0, 255, 0, 255),     # Verde - riesgo bajo
        2: (255, 255, 0, 255),   # Amarillo - riesgo medio
        3: (255, 0, 0, 255)      # Rojo - riesgo alto
    })
print(f"  ✓ Amenaza_Clasificada.tif")

# 3. Pendiente
with rasterio.open('data/processed/Pendiente.tif', 'w', **output_meta.update({'dtype': 'float32'}) or output_meta) as dst:
    dst.write(slope_deg.astype(np.float32), 1)
print(f"  ✓ Pendiente.tif")

# ============================================================================
# PASO 6: GENERAR ESTADÍSTICAS
# ============================================================================
print("\n[8/8] Generando estadísticas...")

# Calcular área (en km²)
pixel_area_m2 = pixel_size ** 2
pixel_area_km2 = pixel_area_m2 / 1e6

area_rojo = pixeles_rojo * pixel_area_km2
area_amarillo = pixeles_amarillo * pixel_area_km2
area_verde = pixeles_verde * pixel_area_km2
area_total = pixeles_totales * pixel_area_km2

# Crear DataFrame con estadísticas
stats = pd.DataFrame({
    'Nivel_Riesgo': ['ALTO (Rojo)', 'MEDIO (Amarillo)', 'BAJO (Verde)', 'TOTAL'],
    'Pixeles': [pixeles_rojo, pixeles_amarillo, pixeles_verde, pixeles_totales],
    'Area_km2': [area_rojo, area_amarillo, area_verde, area_total],
    'Porcentaje': [
        pixeles_rojo/pixeles_totales*100,
        pixeles_amarillo/pixeles_totales*100,
        pixeles_verde/pixeles_totales*100,
        100.0
    ],
    'Score_Min': [70, 40, 0, 0],
    'Score_Max': [100, 70, 40, 100]
})

stats.to_csv('data/processed/Estadisticas_Amenaza.csv', index=False)
print(f"  ✓ Estadisticas_Amenaza.csv")

# Mostrar resumen
print("\n" + "=" * 80)
print("RESUMEN DEL ANÁLISIS")
print("=" * 80)
print(stats.to_string(index=False))

print("\n" + "=" * 80)
print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
print("=" * 80)
print("\nArchivos generados en data/processed/:")
print("  1. Amenaza_Score_Continuo.tif  - Score de 0-100")
print("  2. Amenaza_Clasificada.tif     - 3 niveles (Rojo/Amarillo/Verde)")
print("  3. Pendiente.tif               - Pendiente en grados")
print("  4. Estadisticas_Amenaza.csv    - Resumen estadístico")
print("\nPróximo paso: Generar mapa visual")
print("  → python3 scripts/create_flood_risk_map.py")
