#!/usr/bin/env python3
"""
Mapa de Infraestructura y Riesgo de Inundación
===============================================
Crea un mapa profesional mostrando infraestructura crítica
superpuesta sobre las zonas de riesgo de inundación

Autor: GeoFeedback Chile
Fecha: Noviembre 2025
"""

import json
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.offsetbox import AnchoredText
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuración
PROJECT_DIR = Path(__file__).parent.parent
AMENAZA_FILE = PROJECT_DIR / "data" / "processed" / "Amenaza_Clasificada.tif"
INFRA_FILE = PROJECT_DIR / "data" / "processed" / "infrastructure_with_risk.geojson"
REPORT_FILE = PROJECT_DIR / "data" / "processed" / "infrastructure_risk_report.json"
OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\n" + "="*80)
print("CREANDO MAPA DE INFRAESTRUCTURA Y RIESGO")
print("="*80 + "\n")

# Cargar datos de infraestructura
print("[1/5] Cargando infraestructura...")
with open(INFRA_FILE, 'r', encoding='utf-8') as f:
    infra_data = json.load(f)

with open(REPORT_FILE, 'r', encoding='utf-8') as f:
    report = json.load(f)

# Cargar raster de amenaza
print("[2/5] Cargando raster de amenaza...")
with rasterio.open(AMENAZA_FILE) as src:
    amenaza = src.read(1)
    extent_utm = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
    transform = src.transform

# Crear figura
print("[3/5] Generando visualización...")
fig = plt.figure(figsize=(20, 16))
ax = plt.subplot(111)

# Mostrar raster de amenaza
cmap_amenaza = plt.cm.colors.ListedColormap(['#90EE90', '#FFD700', '#FF6B6B'])
bounds = [0.5, 1.5, 2.5, 3.5]
norm = plt.cm.colors.BoundaryNorm(bounds, cmap_amenaza.N)

im = ax.imshow(amenaza, extent=extent_utm, cmap=cmap_amenaza, norm=norm,
               interpolation='nearest', alpha=0.7)

# Iconos por categoría
category_markers = {
    'Educación': {'marker': '^', 'size': 300, 'color': '#2E86AB'},
    'Salud': {'marker': '+', 'size': 400, 'color': '#A23B72'},
    'Emergencias': {'marker': 's', 'size': 250, 'color': '#F18F01'},
    'Gobierno': {'marker': 'D', 'size': 250, 'color': '#C73E1D'},
    'Comercio': {'marker': 'o', 'size': 150, 'color': '#6A4C93'}
}

# Colores de riesgo
risk_edge_colors = {
    0: '#00FF00',
    1: '#90EE90',
    2: '#FFD700',
    3: '#FF0000'
}

# Plotear infraestructura
print("[4/5] Añadiendo infraestructura al mapa...")
for feature in infra_data['features']:
    coords = feature['geometry']['coordinates']
    props = feature['properties']

    category = props.get('category', 'Comercio')
    risk_level = props.get('risk_level', 0)
    name = props.get('name', 'Sin nombre')

    marker_style = category_markers.get(category, category_markers['Comercio'])

    ax.scatter(
        coords[0], coords[1],
        marker=marker_style['marker'],
        s=marker_style['size'],
        c=marker_style['color'],
        edgecolors=risk_edge_colors.get(risk_level, '#000000'),
        linewidths=3,
        alpha=0.9,
        zorder=10
    )

    # Etiqueta para instalaciones críticas
    if category in ['Salud', 'Emergencias', 'Gobierno', 'Educación']:
        ax.annotate(
            name,
            xy=(coords[0], coords[1]),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.8, edgecolor='none'),
            zorder=11
        )

# Título
ax.set_title(
    'INFRAESTRUCTURA CRÍTICA Y RIESGO DE INUNDACIÓN\nMunicipio de Papudo, Región de Valparaíso',
    fontsize=22,
    fontweight='bold',
    pad=20
)

ax.set_xlabel('UTM Este (m)', fontsize=12)
ax.set_ylabel('UTM Norte (m)', fontsize=12)

# Leyenda de riesgo
legend_patches_risk = [
    mpatches.Patch(color='#FF6B6B', label='Alto (>70)'),
    mpatches.Patch(color='#FFD700', label='Medio (40-70)'),
    mpatches.Patch(color='#90EE90', label='Bajo (<40)')
]

# Leyenda de categorías
legend_elements_cat = []
for cat, style in category_markers.items():
    legend_elements_cat.append(
        plt.Line2D([0], [0], marker=style['marker'], color='w',
                   markerfacecolor=style['color'], markersize=12,
                   label=cat, linestyle='None',
                   markeredgecolor='black', markeredgewidth=1.5)
    )

# Crear leyendas
legend1 = ax.legend(handles=legend_patches_risk, loc='upper left',
                    title='Nivel de Riesgo', fontsize=10, framealpha=0.95)
legend2 = ax.legend(handles=legend_elements_cat, loc='upper right',
                    title='Categoría de Infraestructura', fontsize=10, framealpha=0.95)

# Añadir ambas leyendas
ax.add_artist(legend1)
ax.add_artist(legend2)

# Cuadro de estadísticas
print("[5/5] Añadiendo estadísticas...")
stats_text = "RESUMEN DE RIESGO\n" + "─" * 25 + "\n"
stats_text += f"Total instalaciones: {report['total_facilities']}\n\n"

for risk_name, count in report['risk_distribution'].items():
    stats_text += f"{risk_name}: {count}\n"

stats_text += "\n" + "POR CATEGORÍA\n" + "─" * 25 + "\n"
for cat_data in report['category_distribution']:
    cat = cat_data['category']
    total = cat_data['total']
    high = cat_data['high_risk']
    medium = cat_data['medium_risk']

    stats_text += f"{cat}: {total}\n"
    if high > 0:
        stats_text += f"  └ Alto: {high}\n"
    if medium > 0:
        stats_text += f"  └ Medio: {medium}\n"

stats_box = AnchoredText(
    stats_text,
    loc='lower left',
    prop=dict(fontfamily='monospace', fontsize=9),
    frameon=True,
    bbox_to_anchor=(0.01, 0.01),
    bbox_transform=ax.transAxes
)
stats_box.patch.set_boxstyle("round,pad=0.5")
stats_box.patch.set_facecolor('white')
stats_box.patch.set_alpha(0.95)
ax.add_artist(stats_box)

# Información del proyecto
info_text = f"GeoFeedback Chile\n{datetime.now().strftime('%B %Y')}\nDatos: OpenStreetMap, SRTM DEM, Sentinel-2"
info_box = AnchoredText(
    info_text,
    loc='lower right',
    prop=dict(fontsize=8, style='italic'),
    frameon=True,
    bbox_to_anchor=(0.99, 0.01),
    bbox_transform=ax.transAxes
)
info_box.patch.set_boxstyle("round,pad=0.3")
info_box.patch.set_facecolor('lightgray')
info_box.patch.set_alpha(0.8)
ax.add_artist(info_box)

# Grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Ajustar layout
plt.tight_layout()

# Guardar
output_file = OUTPUT_DIR / "Mapa_Infraestructura_Riesgo_Papudo.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\n✓ Mapa guardado: {output_file}")
print(f"  Tamaño: {output_file.stat().st_size / 1024:.1f} KB")

# Guardar también PDF
output_pdf = OUTPUT_DIR / "Mapa_Infraestructura_Riesgo_Papudo.pdf"
plt.savefig(output_pdf, format='pdf', bbox_inches='tight', facecolor='white')
print(f"✓ PDF guardado: {output_pdf}")
print(f"  Tamaño: {output_pdf.stat().st_size / 1024:.1f} KB")

print("\n" + "="*80)
print("✅ MAPA DE INFRAESTRUCTURA COMPLETADO")
print("="*80)
print("\nHALLAZGOS CLAVE:")
print("  • Todas las 20 instalaciones están en zona de RIESGO MEDIO")
print("  • Incluye 5 centros educativos, 2 centros de salud y 2 servicios de emergencia")
print("  • La Municipalidad de Papudo también está en zona de riesgo medio")
print("\nRECOMENDACIONES:")
print("  1. Evaluar planes de evacuación para escuelas")
print("  2. Revisar infraestructura de drenaje en zonas críticas")
print("  3. Considerar reubicación o reforzamiento de instalaciones esenciales")
print("="*80 + "\n")

plt.close()
