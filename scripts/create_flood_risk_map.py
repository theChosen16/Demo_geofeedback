#!/usr/bin/env python3
"""
Generación de Mapa Visual - Riesgo de Inundación Papudo
========================================================
Crea un mapa simbólico con visualización profesional

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm
import rasterio
from rasterio.plot import show
import geopandas as gpd
import warnings
warnings.filterwarnings('ignore')

# Configuración
project_dir = os.path.expanduser('~/geofeedback-papudo')
os.chdir(project_dir)

print("=" * 80)
print("GENERACIÓN DE MAPA VISUAL - RIESGO DE INUNDACIÓN")
print("=" * 80)

# Instalar matplotlib si es necesario
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend sin GUI para WSL
except:
    pass

# ============================================================================
# CARGAR DATOS
# ============================================================================
print("\n[1/4] Cargando datos procesados...")

# Cargar clasificación de amenaza
amenaza_path = 'data/processed/Amenaza_Clasificada.tif'
if not os.path.exists(amenaza_path):
    print("  ✗ Error: Ejecuta primero 'python3 scripts/analysis_flooding.py'")
    exit(1)

with rasterio.open(amenaza_path) as src:
    amenaza = src.read(1)
    amenaza_meta = src.meta
    amenaza_extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]

print(f"  ✓ Amenaza cargada: {amenaza.shape}")

# Cargar límite de Papudo
limite_path = 'data/raw/IDE_Chile/Limite_Papudo/papudo.shp'
if os.path.exists(limite_path):
    limite_gdf = gpd.read_file(limite_path)
    # Reproyectar a UTM 19S si es necesario
    if limite_gdf.crs != 'EPSG:32719':
        limite_gdf = limite_gdf.to_crs('EPSG:32719')
    print(f"  ✓ Límite de Papudo cargado")
else:
    limite_gdf = None
    print(f"  ⚠ Límite de Papudo no encontrado")

# ============================================================================
# CREAR MAPA PRINCIPAL
# ============================================================================
print("\n[2/4] Generando mapa principal...")

# Configurar figura con múltiples paneles
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], width_ratios=[3, 1],
                      hspace=0.3, wspace=0.3)

# Panel principal: Mapa de amenaza
ax_main = fig.add_subplot(gs[0, :])

# Definir colores personalizados
colors = ['#FFFFFF', '#00FF00', '#FFFF00', '#FF0000']  # Blanco, Verde, Amarillo, Rojo
cmap = ListedColormap(colors)
bounds = [0, 0.5, 1.5, 2.5, 3.5]
norm = BoundaryNorm(bounds, cmap.N)

# Plotear amenaza
im = ax_main.imshow(amenaza, cmap=cmap, norm=norm, extent=amenaza_extent,
                    interpolation='nearest', alpha=0.8)

# Agregar límite municipal si existe
if limite_gdf is not None:
    limite_gdf.boundary.plot(ax=ax_main, color='black', linewidth=2, label='Límite Papudo')

# Configurar ejes
ax_main.set_xlabel('Este (m) - UTM 19S', fontsize=12, fontweight='bold')
ax_main.set_ylabel('Norte (m) - UTM 19S', fontsize=12, fontweight='bold')
ax_main.set_title('MAPA DE RIESGO DE INUNDACIÓN - PAPUDO\nComuna de Papudo, Región de Valparaíso',
                  fontsize=16, fontweight='bold', pad=20)

# Grid
ax_main.grid(True, alpha=0.3, linestyle='--')
ax_main.ticklabel_format(style='plain', axis='both')

# Leyenda personalizada
legend_elements = [
    mpatches.Patch(facecolor='#FF0000', edgecolor='black', label='🔴 Riesgo ALTO (≥70)'),
    mpatches.Patch(facecolor='#FFFF00', edgecolor='black', label='🟡 Riesgo MEDIO (40-70)'),
    mpatches.Patch(facecolor='#00FF00', edgecolor='black', label='🟢 Riesgo BAJO (<40)'),
]
if limite_gdf is not None:
    legend_elements.append(mpatches.Patch(facecolor='none', edgecolor='black',
                                         linewidth=2, label='Límite Municipal'))

ax_main.legend(handles=legend_elements, loc='upper right', fontsize=11,
              framealpha=0.9, edgecolor='black')

# ============================================================================
# PANEL: ESTADÍSTICAS
# ============================================================================
print("\n[3/4] Agregando estadísticas...")

ax_stats = fig.add_subplot(gs[1, 0])
ax_stats.axis('off')

# Calcular estadísticas
pixeles_totales = np.sum(amenaza > 0)
pixeles_rojo = np.sum(amenaza == 3)
pixeles_amarillo = np.sum(amenaza == 2)
pixeles_verde = np.sum(amenaza == 1)

# Calcular áreas (asumiendo pixel de ~30m)
pixel_size = abs(amenaza_meta['transform'][0])
pixel_area_km2 = (pixel_size ** 2) / 1e6

area_total = pixeles_totales * pixel_area_km2
area_rojo = pixeles_rojo * pixel_area_km2
area_amarillo = pixeles_amarillo * pixel_area_km2
area_verde = pixeles_verde * pixel_area_km2

# Texto de estadísticas
stats_text = f"""
ESTADÍSTICAS DEL ANÁLISIS
{'=' * 40}

Área Total Analizada: {area_total:.2f} km²

Distribución de Riesgo:
  🔴 Riesgo ALTO:   {area_rojo:6.2f} km² ({pixeles_rojo/pixeles_totales*100:5.1f}%)
  🟡 Riesgo MEDIO:  {area_amarillo:6.2f} km² ({pixeles_amarillo/pixeles_totales*100:5.1f}%)
  🟢 Riesgo BAJO:   {area_verde:6.2f} km² ({pixeles_verde/pixeles_totales*100:5.1f}%)

Metodología:
  • Pendiente topográfica (50%)
  • Cobertura del suelo NDVI (35%)
  • Depresiones topográficas (15%)

Resolución: {pixel_size:.0f}m
Sistema: UTM Zone 19S (EPSG:32719)
"""

ax_stats.text(0.05, 0.95, stats_text, transform=ax_stats.transAxes,
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

# ============================================================================
# PANEL: GRÁFICO DE TORTA
# ============================================================================
ax_pie = fig.add_subplot(gs[1, 1])

# Datos para pie chart
sizes = [area_rojo, area_amarillo, area_verde]
labels = ['Alto', 'Medio', 'Bajo']
colors_pie = ['#FF0000', '#FFFF00', '#00FF00']
explode = (0.1, 0.05, 0)  # Destacar riesgo alto

wedges, texts, autotexts = ax_pie.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
                                       autopct='%1.1f%%', shadow=True, startangle=90)

# Mejorar texto
for text in texts:
    text.set_fontsize(11)
    text.set_fontweight('bold')
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(10)

ax_pie.set_title('Distribución por Nivel de Riesgo', fontsize=11, fontweight='bold', pad=10)

# ============================================================================
# AGREGAR METADATA Y GUARDAR
# ============================================================================
print("\n[4/4] Guardando mapa...")

# Texto de pie de página
footer_text = (
    "Fuente de datos: Sentinel-2 (NDVI), SRTM DEM 30m | "
    "Análisis: GeoFeedback Chile | "
    f"Fecha: Noviembre 2025 | "
    "Proyección: UTM 19S (EPSG:32719)"
)
fig.text(0.5, 0.02, footer_text, ha='center', fontsize=9, style='italic', color='gray')

# Guardar con alta resolución
output_path = 'data/processed/Mapa_Riesgo_Inundacion_Papudo.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"  ✓ Mapa guardado: {output_path}")

# También guardar versión PDF
output_pdf = 'data/processed/Mapa_Riesgo_Inundacion_Papudo.pdf'
plt.savefig(output_pdf, bbox_inches='tight', facecolor='white')
print(f"  ✓ Versión PDF: {output_pdf}")

plt.close()

print("\n" + "=" * 80)
print("✅ MAPA VISUAL GENERADO EXITOSAMENTE")
print("=" * 80)
print(f"\nArchivos generados:")
print(f"  • {output_path} (300 DPI)")
print(f"  • {output_pdf}")
print(f"\nPuedes ver el mapa en:")
print(f"  Windows: C:\\Users\\alean\\Desktop\\Geofeedback\\Demo\\data\\processed\\")
print(f"  WSL: ~/geofeedback-papudo/data/processed/")
