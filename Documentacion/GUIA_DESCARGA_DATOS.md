# Guía Completa: Descarga de Datos Fuente
## Prototipo Papudo - GeoFeedback Chile

**Duración estimada**: 2-4 horas (depende de velocidad de internet)  
**Requisitos**: Cuenta Google (para Earth Engine), conexión estable  

---

## 📋 Resumen de Datos Necesarios

| Dato | Fuente | Resolución | Tamaño | Tiempo |
|------|--------|------------|--------|--------|
| NDVI Sentinel-2 | Google Earth Engine | 10m | 50-100 MB | 1-2h |
| Límite municipal | IDE Chile | Vector | 1 MB | 5 min |
| DEM SRTM | USGS/OpenTopography | 30m | 5-10 MB | 10 min |
| Hidrografía | IDE Chile | Vector | 2-5 MB | 5 min |

---

## 1️⃣ Sentinel-2 desde Google Earth Engine (NDVI)

### 1.1 Preparación Inicial

**Paso 1**: Registrar cuenta en Google Earth Engine
1. Ve a [earthengine.google.com/signup](https://earthengine.google.com/signup)
2. Regístrate con tu cuenta Google
3. Selecciona: **"Academia e Investigación"** o **"No comercial"**
4. Espera aprobación (puede tomar 1-2 días)

**Paso 2**: Acceder al Code Editor
1. Ve a [code.earthengine.google.com](https://code.earthengine.google.com/)
2. Verifica que tengas acceso (no debe mostrar error)

### 1.2 Script de Descarga

Copia y pega este código completo en el editor:

```javascript
// ========================================
// SCRIPT: Descarga NDVI Papudo
// Autor: GeoFeedback Chile
// Fecha: Noviembre 2025
// ========================================

// PASO 1: Definir área de interés (AOI)
var papudo = ee.Geometry.Point([-71.4408, -32.4283]).buffer(5000);

// Centrar mapa en Papudo
Map.centerObject(papudo, 12);
Map.addLayer(papudo, {color: 'red'}, 'AOI Papudo');

// PASO 2: Filtrar colección Sentinel-2
var s2_collection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
  .filterBounds(papudo)
  .filterDate('2024-05-01', '2024-08-31')  // Período húmedo (otoño-invierno)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
  .sort('CLOUDY_PIXEL_PERCENTAGE');

// Información de colección
print('Total de imágenes encontradas:', s2_collection.size());
print('Imagen con menos nubes:', s2_collection.first());

// PASO 3: Seleccionar mejor imagen
var s2_image = s2_collection.first();

// PASO 4: Calcular NDVI
// NDVI = (NIR - RED) / (NIR + RED)
// B8 = Near Infrared (NIR)
// B4 = Red
var ndvi = s2_image.normalizedDifference(['B8', 'B4']).rename('NDVI');

// PASO 5: Visualizar NDVI
var ndvi_viz = {
  min: -0.2,
  max: 0.8,
  palette: [
    '0000ff',  // Agua (azul)
    '00ffff',  // Suelo desnudo (cyan)
    'ffff00',  // Pastos (amarillo)
    '00ff00',  // Vegetación media (verde claro)
    '006400'   // Vegetación densa (verde oscuro)
  ]
};

Map.addLayer(ndvi, ndvi_viz, 'NDVI Papudo');

// PASO 6: Exportar a Google Drive
Export.image.toDrive({
  image: ndvi,
  description: 'Sentinel2_NDVI_Papudo',
  folder: 'GeoFeedback',  // Se creará automáticamente en Drive
  fileNamePrefix: 'Sentinel2_NDVI_Papudo',
  scale: 10,  // Resolución 10 metros
  region: papudo,
  maxPixels: 1e9,
  fileFormat: 'GeoTIFF',
  formatOptions: {
    cloudOptimized: true
  }
});

// PASO 7: Opcional - Exportar también bandas RGB para visualización
var rgb = s2_image.select(['B4', 'B3', 'B2']);

Export.image.toDrive({
  image: rgb,
  description: 'Sentinel2_RGB_Papudo',
  folder: 'GeoFeedback',
  scale: 10,
  region: papudo,
  maxPixels: 1e9,
  fileFormat: 'GeoTIFF'
});

print('✓ Scripts de exportación configurados');
print('→ Ve a la pestaña "Tasks" para ejecutar');
```

### 1.3 Ejecutar Descarga

**Paso 1**: Pegar código en el editor
- Borra cualquier código existente
- Pega el script completo

**Paso 2**: Ejecutar script
- Click en botón **"Run"** (arriba)
- Espera que aparezca mapa centrado en Papudo
- Revisa consola (derecha) para ver número de imágenes encontradas

**Paso 3**: Iniciar tareas de exportación
1. Click en pestaña **"Tasks"** (arriba derecha, ícono de engranaje)
2. Verás 2 tareas:
   - `Sentinel2_NDVI_Papudo`
   - `Sentinel2_RGB_Papudo` (opcional)
3. Click en **"RUN"** junto a cada tarea
4. En el diálogo, confirma:
   - ✅ Folder: `GeoFeedback`
   - ✅ File format: `GeoTIFF`
   - Click **"Run"**

**Paso 4**: Esperar descarga
- Tiempo estimado: 30 minutos - 2 horas
- Status visible en pestaña "Tasks"
- Estados: `READY` → `RUNNING` → `COMPLETED`

**Paso 5**: Descargar desde Google Drive
1. Ve a [drive.google.com](https://drive.google.com)
2. Busca carpeta **"GeoFeedback"**
3. Descarga archivos `.tif`
4. Guarda en tu computadora:
   ```
   ~/geofeedback-papudo/data/raw/Sentinel2_NDVI_Papudo.tif
   ~/geofeedback-papudo/data/raw/Sentinel2_RGB_Papudo.tif  (opcional)
   ```

### 1.4 Verificar Descarga

```bash
cd ~/geofeedback-papudo/data/raw

# Verificar que el archivo existe
ls -lh Sentinel2_NDVI_Papudo.tif

# Ver información del archivo
gdalinfo Sentinel2_NDVI_Papudo.tif | head -20

# Debe mostrar:
# - Size: aprox. 500-1000 x 500-1000 píxeles
# - Origin: cerca de (-71.6, -32.2)
# - Pixel Size: (10, -10)
# - Band 1: NDVI
```

### 1.5 Solución de Problemas

| Problema | Solución |
|----------|----------|
| "Account not registered" | Espera aprobación de cuenta (1-2 días) |
| "No images found" | Ajusta fechas o aumenta % nubes a 30% |
| Descarga muy lenta | Normal para imágenes grandes, espera o prueba horario nocturno |
| Archivo muy grande | Reduce buffer de 5000m a 3000m |

---

## 2️⃣ Datos IDE Chile (Límites Municipales)

### 2.1 Crear Estructura de Carpetas

```bash
mkdir -p ~/geofeedback-papudo/data/raw/IDE_Chile
cd ~/geofeedback-papudo/data/raw/IDE_Chile
```

### 2.2 Opción A: Descarga Directa WFS (Recomendada)

**Ventajas**: Automática, actualizada, reproducible

```bash
#!/bin/bash
# Script de descarga IDE Chile

# 1. LÍMITE MUNICIPAL DE PAPUDO
echo "Descargando límite municipal..."
wget --no-check-certificate -O Limite_Papudo.zip \
"https://www.geoportal.cl/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=sdesgg:division_politica_administrativa&CQL_FILTER=NOMBRE='PAPUDO'&outputFormat=SHAPE-ZIP"

unzip -o Limite_Papudo.zip -d Limite_Papudo
echo "✓ Límite municipal descargado"

# 2. HIDROGRAFÍA (ríos y esteros)
echo "Descargando hidrografía..."
wget --no-check-certificate -O Hidrografia_Papudo.zip \
"https://www.geoportal.cl/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=hidro:red_hidro_red_lineal&bbox=-71.6,-32.6,-71.2,-32.2&outputFormat=SHAPE-ZIP"

unzip -o Hidrografia_Papudo.zip -d Hidrografia
echo "✓ Hidrografía descargada"

# 3. EQUIPAMIENTO PÚBLICO (opcional)
echo "Descargando equipamiento..."
wget --no-check-certificate -O Equipamiento_Papudo.zip \
"https://www.geoportal.cl/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=equipamiento:equipamiento&bbox=-71.6,-32.6,-71.2,-32.2&outputFormat=SHAPE-ZIP"

unzip -o Equipamiento_Papudo.zip -d Equipamiento
echo "✓ Equipamiento descargado"

# 4. VÍAS DE ACCESO
echo "Descargando vías..."
wget --no-check-certificate -O Vias_Papudo.zip \
"https://www.geoportal.cl/geoserver/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=vialidad:vialidad&bbox=-71.6,-32.6,-71.2,-32.2&outputFormat=SHAPE-ZIP"

unzip -o Vias_Papudo.zip -d Vias
echo "✓ Vías descargadas"

echo ""
echo "✅ Todos los datos de IDE Chile descargados"
ls -lh
```

**Ejecutar**:
```bash
chmod +x download_ide_chile.sh
./download_ide_chile.sh
```

### 2.3 Opción B: Descarga Manual desde Portal

**Paso 1**: Acceder al portal
- Ve a [ide.cl/geovisor](https://www.ide.cl/geovisor/)

**Paso 2**: Buscar capa
1. En barra de búsqueda, escribe: **"División Política Administrativa"**
2. Click en la capa
3. Activar capa (checkbox)

**Paso 3**: Filtrar por Papudo
1. Click derecho en la capa → **"Tabla de atributos"**
2. En filtro, escribe: `NOMBRE = 'PAPUDO'`
3. Selecciona la fila de Papudo

**Paso 4**: Descargar
1. Click en capa → **"Descargar"**
2. Formato: **Shapefile**
3. Zona seleccionada: ✅ Activar
4. Click **"Descargar"**
5. Guarda el `.zip` y extrae en `data/raw/IDE_Chile/Limite_Papudo/`

**Paso 5**: Repetir para otras capas
- Hidrografía: Capa `Red Hidrográfica`
- Equipamiento: Capa `Equipamiento Público`
- Vías: Capa `Red Vial`

### 2.4 Verificar Descargas

```bash
cd ~/geofeedback-papudo/data/raw/IDE_Chile

# Listar archivos
find . -name "*.shp" -type f

# Debe mostrar:
# ./Limite_Papudo/division_politica_administrativa.shp
# ./Hidrografia/red_hidro_red_lineal.shp
# ./Equipamiento/equipamiento.shp
# ./Vias/vialidad.shp

# Ver información de un shapefile
ogrinfo -so Limite_Papudo/division_politica_administrativa.shp division_politica_administrativa

# Verificar proyección (debe ser EPSG:4326 o 32719)
ogrinfo Limite_Papudo/division_politica_administrativa.shp \
  -al | grep "PROJCS\|GEOGCS"
```

---

## 3️⃣ DEM SRTM (Modelo de Elevación)

### 3.1 Opción A: OpenTopography (Recomendada)

**Ventajas**: Mejor resolución (30m), pre-procesado, gratuito

**Paso 1**: Registrar cuenta
1. Ve a [opentopography.org](https://portal.opentopography.org/)
2. Click **"Sign In"** → **"Register"**
3. Completa formulario (gratuito)
4. Confirma email

**Paso 2**: Seleccionar dataset
1. Ve a [Raster Data](https://portal.opentopography.org/raster)
2. Busca: **"SRTM GL1 (Global 30m)"**
3. Click en el dataset

**Paso 3**: Definir área de descarga
1. En mapa, navega a Papudo (-71.44, -32.43)
2. Usa herramienta **"Draw Rectangle"**
3. O ingresa coordenadas manualmente:
   ```
   West: -71.6
   South: -32.6
   East: -71.2
   North: -32.2
   ```

**Paso 4**: Configurar descarga
- Output Format: **GeoTiff**
- Spatial Reference: **UTM Zone 19S (EPSG:32719)**
- Job Description: `DEM_Papudo`
- Click **"Submit"**

**Paso 5**: Descargar
1. Recibirás email cuando esté listo (5-20 min)
2. O revisa en [My Jobs](https://portal.opentopography.org/myJobs)
3. Click **"Download"**
4. Guarda como: `SRTM_Papudo_DEM.tif`

### 3.2 Opción B: USGS Earth Explorer

**Paso 1**: Registrar cuenta
1. Ve a [earthexplorer.usgs.gov](https://earthexplorer.usgs.gov/)
2. Click **"Register"** → Completa formulario

**Paso 2**: Buscar área
1. En **"Search Criteria"**:
   - Address/Place: `Papudo, Chile`
   - O Lat/Lon: `-32.4283, -71.4408`
2. Date Range: Cualquiera (DEM es estático)

**Paso 3**: Seleccionar dataset
1. Click **"Data Sets"**
2. Expand: **Digital Elevation**
3. Marca: **☑ SRTM 1 Arc-Second Global**

**Paso 4**: Ver resultados
1. Click **"Results"**
2. Encuentra tile que contiene Papudo
   - Tile: `S33W072` (aproximado)
3. Click en ícono **"Download Options"** (disco)

**Paso 5**: Descargar
1. Selecciona: **GeoTIFF 1 Arc-second**
2. Click **"Download"**
3. Descomprime el `.zip`
4. Renombra archivo como: `SRTM_Papudo_DEM.tif`

### 3.3 Opción C: Python Automático (Avanzado)

**Instalar librería**:
```bash
pip install elevation
```

**Script Python**:
```python
#!/usr/bin/env python3
"""
Descargar DEM SRTM automáticamente
"""

import elevation
import os

# Crear carpeta
os.makedirs('data/raw', exist_ok=True)

# Definir bounding box (Papudo + buffer)
# (west, south, east, north)
bounds = (-71.6, -32.6, -71.2, -32.2)

# Descargar SRTM 30m
print("Descargando DEM SRTM...")
elevation.clip(
    bounds=bounds,
    output='data/raw/SRTM_Papudo_DEM.tif',
    product='SRTM1',  # 30m resolución
    margin='0.01'
)

print("✓ DEM descargado")

# Limpiar archivos temporales
elevation.clean()
```

**Ejecutar**:
```bash
python3 download_dem.py
```

### 3.4 Verificar DEM

```bash
cd ~/geofeedback-papudo/data/raw

# Ver información
gdalinfo SRTM_Papudo_DEM.tif

# Información clave a verificar:
# - Size: ~400x400 píxeles (depende del área)
# - Pixel Size: (0.000277..., -0.000277...) = 30m aprox
# - Band 1: Elevation (metros)
# - NoData Value: -32768 (océano)

# Estadísticas de elevación
gdalinfo -stats SRTM_Papudo_DEM.tif | grep -A 5 "Band 1"

# Valores esperados para Papudo:
# - Minimum: 0m (nivel del mar)
# - Maximum: 400-600m (cerros)
# - Mean: 100-200m
```

### 3.5 Recortar DEM al AOI Exacto (Opcional)

Si el DEM descargado es muy grande:

```bash
# Recortar usando límite municipal
gdalwarp -cutline IDE_Chile/Limite_Papudo/division_politica_administrativa.shp \
         -crop_to_cutline \
         -dstnodata -9999 \
         SRTM_Papudo_DEM.tif \
         SRTM_Papudo_DEM_recortado.tif

# Reemplazar original
mv SRTM_Papudo_DEM_recortado.tif SRTM_Papudo_DEM.tif
```

---

## 4️⃣ Datos Adicionales Opcionales

### 4.1 OpenStreetMap (Calles y Edificios)

```python
#!/usr/bin/env python3
"""
Descargar datos OSM para Papudo
"""

import osmnx as ox
import geopandas as gpd

# Descargar red vial
print("Descargando red vial OSM...")
G = ox.graph_from_place("Papudo, Valparaíso, Chile", network_type='all')
gdf_vias = ox.graph_to_gdfs(G, nodes=False)
gdf_vias.to_file('data/raw/OSM_Vias_Papudo.shp')

# Descargar edificios
print("Descargando edificios OSM...")
edificios = ox.geometries_from_place(
    "Papudo, Valparaíso, Chile",
    tags={'building': True}
)
edificios.to_file('data/raw/OSM_Edificios_Papudo.shp')

print("✓ Datos OSM descargados")
```

### 4.2 Datos Climáticos (DGA)

Descarga manual desde [explorador.cr2.cl](https://explorador.cr2.cl):
1. Navega a Papudo
2. Selecciona: Precipitación histórica
3. Periodo: 2010-2024
4. Descarga CSV

---

## 5️⃣ Estructura Final de Carpetas

Después de todas las descargas, debes tener:

```
~/geofeedback-papudo/
└── data/
    └── raw/
        ├── Sentinel2_NDVI_Papudo.tif     (~80 MB)
        ├── Sentinel2_RGB_Papudo.tif      (~200 MB, opcional)
        ├── SRTM_Papudo_DEM.tif           (~8 MB)
        │
        ├── IDE_Chile/
        │   ├── Limite_Papudo/
        │   │   ├── division_politica_administrativa.shp
        │   │   ├── division_politica_administrativa.shx
        │   │   ├── division_politica_administrativa.dbf
        │   │   └── division_politica_administrativa.prj
        │   │
        │   ├── Hidrografia/
        │   │   └── red_hidro_red_lineal.*
        │   │
        │   ├── Equipamiento/
        │   │   └── equipamiento.*
        │   │
        │   └── Vias/
        │       └── vialidad.*
        │
        └── OSM/ (opcional)
            ├── OSM_Vias_Papudo.shp
            └── OSM_Edificios_Papudo.shp
```

---

## 6️⃣ Script de Verificación Completo

Guarda esto como `verify_data.sh` y ejecuta para verificar todas las descargas:

```bash
#!/bin/bash
# Verificación completa de datos descargados

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Verificando datos descargados..."
echo ""

cd ~/geofeedback-papudo/data/raw || exit 1

# 1. Sentinel-2 NDVI
echo "1️⃣  Sentinel-2 NDVI"
if [ -f "Sentinel2_NDVI_Papudo.tif" ]; then
    SIZE=$(du -h Sentinel2_NDVI_Papudo.tif | cut -f1)
    echo -e "${GREEN}✓${NC} Sentinel2_NDVI_Papudo.tif (${SIZE})"
    
    # Verificar que sea GeoTIFF válido
    if gdalinfo Sentinel2_NDVI_Papudo.tif > /dev/null 2>&1; then
        DIMS=$(gdalinfo Sentinel2_NDVI_Papudo.tif | grep "Size is" | sed 's/Size is //')
        echo "  Dimensiones: $DIMS píxeles"
    else
        echo -e "${RED}✗${NC} Archivo corrupto"
    fi
else
    echo -e "${RED}✗${NC} Falta: Sentinel2_NDVI_Papudo.tif"
fi

echo ""

# 2. DEM SRTM
echo "2️⃣  DEM SRTM"
if [ -f "SRTM_Papudo_DEM.tif" ]; then
    SIZE=$(du -h SRTM_Papudo_DEM.tif | cut -f1)
    echo -e "${GREEN}✓${NC} SRTM_Papudo_DEM.tif (${SIZE})"
    
    if gdalinfo -stats SRTM_Papudo_DEM.tif > /dev/null 2>&1; then
        MIN=$(gdalinfo -stats SRTM_Papudo_DEM.tif | grep "Minimum=" | sed 's/.*Minimum=\([0-9.-]*\).*/\1/')
        MAX=$(gdalinfo -stats SRTM_Papudo_DEM.tif | grep "Maximum=" | sed 's/.*Maximum=\([0-9.-]*\).*/\1/')
        echo "  Elevación: ${MIN}m - ${MAX}m"
    fi
else
    echo -e "${RED}✗${NC} Falta: SRTM_Papudo_DEM.tif"
fi

echo ""

# 3. IDE Chile
echo "3️⃣  IDE Chile"
if [ -d "IDE_Chile" ]; then
    echo -e "${GREEN}✓${NC} Carpeta IDE_Chile existe"
    
    # Verificar shapefiles
    SHAPEFILES=$(find IDE_Chile -name "*.shp" | wc -l)
    echo "  Shapefiles encontrados: $SHAPEFILES"
    
    if [ -f "IDE_Chile/Limite_Papudo/division_politica_administrativa.shp" ]; then
        echo -e "  ${GREEN}✓${NC} Límite municipal"
    else
        echo -e "  ${YELLOW}⚠${NC}  Falta límite municipal"
    fi
    
    if [ -d "IDE_Chile/Hidrografia" ]; then
        echo -e "  ${GREEN}✓${NC} Hidrografía"
    else
        echo -e "  ${YELLOW}⚠${NC}  Falta hidrografía (opcional)"
    fi
else
    echo -e "${RED}✗${NC} Falta: carpeta IDE_Chile/"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Resumen
ARCHIVOS_REQUERIDOS=3
ARCHIVOS_PRESENTES=0

[ -f "Sentinel2_NDVI_Papudo.tif" ] && ((ARCHIVOS_PRESENTES++))
[ -f "SRTM_Papudo_DEM.tif" ] && ((ARCHIVOS_PRESENTES++))
[ -d "IDE_Chile" ] && ((ARCHIVOS_PRESENTES++))

if [ $ARCHIVOS_PRESENTES -eq $ARCHIVOS_REQUERIDOS ]; then
    echo -e "${GREEN}✅ Todos los datos requeridos están presentes${NC}"
    echo ""
    echo "📊 Tamaño total:"
    du -sh .
    echo ""
    echo "➡️  Próximo paso: python3 scripts/analysis_flooding.py"
else
    echo -e "${YELLOW}⚠️  Faltan $((ARCHIVOS_REQUERIDOS - ARCHIVOS_PRESENTES)) archivos requeridos${NC}"
    echo "Revisa las instrucciones de descarga arriba."
fi
```

**Ejecutar**:
```bash
chmod +x verify_data.sh
./verify_data.sh
```

---

## 7️⃣ Solución de Problemas Comunes

### Problema: Google Earth Engine no funciona

**Síntomas**: Error "Account not registered"

**Soluciones**:
1. Espera 24-48h para aprobación de cuenta
2. Verifica email de confirmación
3. Re-registra en [signup.earthengine.google.com](https://signup.earthengine.google.com)

### Problema: Descargas de IDE Chile fallan

**Síntomas**: Error 404 o timeout

**Soluciones**:
```bash
# Usar mirror alternativo
wget --no-check-certificate --timeout=30 --tries=3 \
  -O Limite_Papudo.zip "URL_AQUI"

# O descargar manualmente desde portal
```

### Problema: DEM muy grande

**Solución**: Recortar al área exacta
```bash
gdalwarp -te -71.6 -32.6 -71.2 -32.2 \
         SRTM_original.tif \
         SRTM_Papudo_DEM.tif
```

### Problema: Archivos corruptos

**Verificar integridad**:
```bash
# Para GeoTIFF
gdalinfo archivo.tif

# Para Shapefile
ogrinfo archivo.shp
```

Si falla, vuelve a descargar.

---

## 8️⃣ Próximos Pasos

Una vez verificados todos los datos:

```bash
# 1. Activar ambiente Python
cd ~/geofeedback-papudo
source venv/bin/activate

# 2. Ejecutar análisis
python3 scripts/analysis_flooding.py

# Debe generar:
# data/processed/Amenaza_Clasificada.tif
# data/processed/Amenaza_Poligonos.shp
# data/processed/Estadisticas_Amenaza.csv
```

---

## 📞 Contacto y Soporte

- **Errores GEE**: [developers.google.com/earth-engine/support](https://developers.google.com/earth-engine/support)
- **Errores IDE Chile**: [ide.cl/contacto](https://www.ide.cl/contacto)
- **Errores USGS**: [earthexplorer.usgs.gov/contact](https://earthexplorer.usgs.gov/contact)

---

**Documento preparado**: Noviembre 2025  
**Versión**: 1.0  
**Autor**: Equipo GeoFeedback Chile
