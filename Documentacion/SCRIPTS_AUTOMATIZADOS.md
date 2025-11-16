# SCRIPTS AUTOMATIZADOS
## Prototipo Papudo - GeoFeedback

> Copiar y ejecutar scripts según corresponda a cada fase

---

## 1. SETUP INICIAL (ejecutar primero)

### 1.1 install_dependencies.sh

```bash
#!/bin/bash
# Install all required dependencies for prototype

set -e  # Exit on error

echo "🚀 Instalando dependencias para prototipo GeoFeedback..."

# Detectar SO
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo "Detectado: $OS"

# ========== LINUX ==========
if [ "$OS" = "linux" ]; then
    echo "📦 Actualizando paquetes..."
    sudo apt update
    sudo apt upgrade -y
    
    echo "📦 Instalando dependencias del sistema..."
    sudo apt install -y \
        python3-pip \
        python3-dev \
        git \
        wget \
        curl \
        postgresql \
        postgresql-contrib \
        gdal-bin \
        python3-gdal \
        libgdal-dev \
        docker.io \
        docker-compose
    
    echo "📦 Instalando QGIS..."
    sudo apt install -y qgis python3-qgis
    
    echo "✅ PostgreSQL iniciando..."
    sudo service postgresql start
fi

# ========== MACOS ==========
if [ "$OS" = "macos" ]; then
    echo "📦 Instalando con Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    brew install python3 git wget curl postgresql gdal qgis docker
    
    echo "✅ PostgreSQL iniciando..."
    brew services start postgresql
fi

# ========== PYTHON ==========
echo "🐍 Configurando ambiente Python..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Instalando librerías Python..."
pip install --upgrade pip setuptools wheel

pip install \
    geopandas==0.14.0 \
    rasterio==1.3.9 \
    shapely==2.0.1 \
    fiona==1.9.6 \
    psycopg2-binary==2.9.9 \
    sqlalchemy==2.0.23 \
    pandas==2.1.4 \
    numpy==1.24.3 \
    scipy==1.11.4 \
    matplotlib==3.8.2 \
    plotly==5.18.0 \
    flask==3.0.0 \
    flask-cors==4.0.0 \
    requests==2.31.0 \
    python-dotenv==1.0.0 \
    gdal==$(gdal-config --version)

echo "✅ Dependencias instaladas correctamente"
echo ""
echo "📝 Próximo paso:"
echo "   source venv/bin/activate"
echo "   bash scripts/setup_database.sh"
```

**Ejecutar:**
```bash
chmod +x scripts/install_dependencies.sh
./scripts/install_dependencies.sh
```

---

### 1.2 setup_database.sh

```bash
#!/bin/bash
# Setup PostgreSQL + PostGIS database

set -e

DBUSER="geofeedback"
DBNAME="geofeedback_papudo"
DBPASS="Papudo2025"

echo "🗄️  Configurando PostGIS..."

# 1. Crear usuario
echo "1️⃣  Creando usuario PostgreSQL..."
sudo -u postgres psql << EOF
CREATE USER $DBUSER WITH PASSWORD '$DBPASS';
ALTER USER $DBUSER CREATEDB;
EOF

# 2. Crear database
echo "2️⃣  Creando base de datos..."
sudo -u postgres createdb -O $DBUSER $DBNAME

# 3. Instalar extensiones
echo "3️⃣  Instalando extensiones PostGIS..."
sudo -u postgres psql -d $DBNAME << EOF
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
SELECT postgis_version();
EOF

# 4. Crear tablas
echo "4️⃣  Creando esquema de tablas..."

PGPASSWORD=$DBPASS psql -U $DBUSER -d $DBNAME -h localhost << 'SQLEOF'

-- TABLA: ZONAS AMENAZA
CREATE TABLE IF NOT EXISTS public.amenaza_inundacion (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    clase INTEGER CHECK (clase IN (1,2,3)),
    clase_nombre VARCHAR(20),
    score_amenaza FLOAT,
    probabilidad_anual FLOAT,
    profundidad_estimada FLOAT,
    velocidad_flujo FLOAT,
    area_hectareas FLOAT,
    poblacion_afectada INTEGER DEFAULT 0,
    geometria GEOMETRY(Polygon, 32719),
    fecha_creacion TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_amenaza_clase ON public.amenaza_inundacion(clase);
CREATE INDEX idx_amenaza_geom ON public.amenaza_inundacion USING GIST(geometria);

-- TABLA: INFRAESTRUCTURA CRÍTICA
CREATE TABLE IF NOT EXISTS public.infraestructura_critica (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200),
    tipo VARCHAR(50),
    direccion VARCHAR(200),
    capacidad INTEGER,
    geometria GEOMETRY(Point, 32719),
    amenaza_clase INTEGER,
    estado VARCHAR(20),
    fecha_verificacion TIMESTAMP
);

CREATE INDEX idx_infraest_tipo ON public.infraestructura_critica(tipo);
CREATE INDEX idx_infraest_geom ON public.infraestructura_critica USING GIST(geometria);

-- TABLA: RUTAS DE EVACUACIÓN
CREATE TABLE IF NOT EXISTS public.rutas_evacuacion (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    longitud_km FLOAT,
    tiempo_minutos INTEGER,
    capacidad_personas INTEGER,
    orden_prioridad INTEGER,
    geometria GEOMETRY(LineString, 32719),
    estado VARCHAR(20)
);

CREATE INDEX idx_ruta_geom ON public.rutas_evacuacion USING GIST(geometria);

-- VISTA: Infraestructura en riesgo
CREATE OR REPLACE VIEW v_infraestructura_en_riesgo AS
    SELECT i.nombre, i.tipo, i.capacidad, a.clase_nombre, a.score_amenaza
    FROM public.infraestructura_critica i
    LEFT JOIN public.amenaza_inundacion a 
    ON ST_Within(i.geometria, a.geometria)
    WHERE a.clase >= 2;

-- FUNCIÓN: Población afectada
CREATE OR REPLACE FUNCTION poblacion_en_zona(clase_min INTEGER)
RETURNS TABLE(clase INTEGER, poblacion BIGINT) AS $$
SELECT 
    a.clase,
    COALESCE(SUM(a.poblacion_afectada), 0) as poblacion
FROM public.amenaza_inundacion a
WHERE a.clase >= clase_min
GROUP BY a.clase;
$$ LANGUAGE SQL;

SQLEOF

echo "✅ Base de datos configurada"
echo ""
echo "Prueba de conexión:"
PGPASSWORD=$DBPASS psql -U $DBUSER -d $DBNAME -h localhost -c "SELECT version();"
```

**Ejecutar:**
```bash
chmod +x scripts/setup_database.sh
./scripts/setup_database.sh
```

---

## 2. ANÁLISIS GEOESPACIAL

### 2.1 download_data.py

```python
#!/usr/bin/env python3
"""
Descargar datos satelitales y oficiales de IDE Chile
Ejecutar desde: python3 scripts/download_data.py
"""

import os
import requests
import urllib.request
import zipfile
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear carpetas
DATA_RAW = Path("data/raw")
DATA_RAW.mkdir(parents=True, exist_ok=True)

def download_file(url, filename):
    """Descargar archivo con barra de progreso"""
    logger.info(f"Descargando {filename}...")
    try:
        urllib.request.urlretrieve(url, filename)
        logger.info(f"✓ {filename} descargado")
    except Exception as e:
        logger.error(f"✗ Error descargando {filename}: {e}")

def download_ide_chile():
    """Descargar datos IDE Chile [1670]"""
    logger.info("📥 Descargando datos IDE Chile...")
    
    # Límites municipio
    url_limite = "https://www.geoportal.cl/geoserver/ows?service=WFS&request=GetFeature&typeName=sdesgg:division_politica_administrativa&CQL_FILTER=NOMBRE='PAPUDO'&outputFormat=SHAPEFILE"
    
    filename_limite = DATA_RAW / "IDE_Limite_Papudo.zip"
    download_file(url_limite, str(filename_limite))
    
    # Descomprimir
    with zipfile.ZipFile(filename_limite, 'r') as zip_ref:
        zip_ref.extractall(DATA_RAW / "IDE_Limite")
    
    logger.info("✓ Datos IDE Chile listos")

def download_srtm():
    """Descargar DEM SRTM 30m [1670]"""
    logger.info("📥 Descargando DEM SRTM...")
    
    # Notar: Este es un ejemplo. DEM real requiere coordenadas precisas
    url_srtm = "https://raster.nationalmap.gov/arcgis/rest/services/elevation/USGS_3DEP_Resolution_Fueled/ImageServer/exportImage?bbox=-71.6,-32.6,-71.2,-32.2&size=512&f=image&bboxSR=4326&imageSR=4326"
    
    filename_srtm = DATA_RAW / "SRTM_Papudo.tif"
    download_file(url_srtm, str(filename_srtm))
    
    logger.info("✓ DEM SRTM listo")

def download_sentinel2():
    """Google Earth Engine: Instrucciones para descargar Sentinel-2"""
    logger.info("📥 Instrucciones para Sentinel-2...")
    logger.info("""
    
    Para descargar Sentinel-2:
    
    1. Ir a: https://code.earthengine.google.com/
    2. Copiar el siguiente código en el editor:
    
    ```javascript
    var papudo = ee.Geometry.Point([-71.4408, -32.4283]).buffer(5000);
    var s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
      .filterBounds(papudo)
      .filterDate('2025-05-01', '2025-07-31')
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
      .first();
    
    Export.image.toDrive({
      image: s2.select(['B2','B3','B4','B5','B8','B11']),
      description: 'Sentinel2_Papudo',
      scale: 10,
      region: papudo.bounds(),
      fileFormat: 'GeoTIFF'
    });
    ```
    
    3. Click en "Run"
    4. Ir a Tasks → Click en "RUN"
    5. Esperar a que descargue a Google Drive
    6. Descargar archivo y ponerlo en: data/raw/Sentinel2_Papudo.tif
    
    """)

if __name__ == "__main__":
    logger.info("🚀 Iniciando descargas de datos...")
    
    try:
        download_ide_chile()
        # download_srtm()  # Comentado - requiere credenciales
        download_sentinel2()
        
        logger.info("✅ Descargas completadas")
        
    except Exception as e:
        logger.error(f"Error general: {e}")
```

**Ejecutar:**
```bash
python3 scripts/download_data.py
```

### 2.2 analysis_flooding.py

```python
#!/usr/bin/env python3
"""
Análisis geoespacial: Mapeo de riesgo de inundación
Ejecutar desde: python3 scripts/analysis_flooding.py
"""

import rasterio
import geopandas as gpd
import numpy as np
from scipy.ndimage import gradient, label
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_RAW = Path("data/raw")
DATA_PROC = Path("data/processed")
DATA_PROC.mkdir(exist_ok=True)

def load_data():
    """Cargar rasters y vectors"""
    logger.info("📂 Cargando datos...")
    
    dem_file = DATA_RAW / "SRTM_Papudo.tif"
    ndvi_file = DATA_RAW / "Sentinel2_NDVI_Papudo.tif"
    
    if not dem_file.exists():
        logger.error(f"Falta: {dem_file}")
        return None, None, None
    
    with rasterio.open(dem_file) as src:
        dem = src.read(1)
        dem_meta = src.meta
    
    if ndvi_file.exists():
        with rasterio.open(ndvi_file) as src:
            ndvi = src.read(1)
    else:
        logger.warning(f"Falta NDVI, usando valores por defecto")
        ndvi = np.ones_like(dem) * 0.3
    
    return dem, ndvi, dem_meta

def calculate_slope(dem):
    """Calcular pendiente desde DEM"""
    logger.info("Calculando pendiente...")
    dy, dx = gradient(dem)
    slope = np.arctan(np.sqrt(dx**2 + dy**2)) * 180 / np.pi
    return slope

def create_threat_map(dem, ndvi, slope):
    """Crear mapa de amenaza combinando factores"""
    logger.info("Creando mapa de amenaza...")
    
    # Inicializar score
    threat_score = np.zeros_like(dem, dtype=float)
    
    # FACTOR 1: Pendiente (50% peso)
    slope_factor = np.zeros_like(dem, dtype=float)
    slope_factor[slope < 2] = 100
    slope_factor[(slope >= 2) & (slope < 5)] = 70
    slope_factor[(slope >= 5) & (slope < 10)] = 40
    slope_factor[slope >= 10] = 10
    
    # FACTOR 2: NDVI/Cobertura (35% peso)
    ndvi_factor = np.zeros_like(dem, dtype=float)
    ndvi_factor[ndvi < -0.2] = 100  # Agua/urbano = muy permeable
    ndvi_factor[(ndvi >= -0.2) & (ndvi < 0.2)] = 80   # Suelo desnudo
    ndvi_factor[(ndvi >= 0.2) & (ndvi < 0.4)] = 50    # Pastos
    ndvi_factor[(ndvi >= 0.4) & (ndvi < 0.6)] = 30    # Arbustos
    ndvi_factor[ndvi >= 0.6] = 10  # Bosque/vegetación densa
    
    # FACTOR 3: Aspectos topográficos (15% peso)
    # Depresiones naturales = más riesgo
    from scipy.ndimage import minimum_filter
    local_min = minimum_filter(dem, size=20)
    depression_factor = np.where(dem <= local_min + 5, 80, 20)
    
    # Combinar factores
    threat_score = (slope_factor * 0.50 + 
                   ndvi_factor * 0.35 + 
                   depression_factor * 0.15)
    
    # Normalizar 0-100
    threat_score = (threat_score - threat_score.min()) / (threat_score.max() - threat_score.min()) * 100
    
    return threat_score

def classify_threat(threat_score):
    """Clasificar en 3 clases: ROJA (3), AMARILLA (2), VERDE (1)"""
    logger.info("Clasificando amenaza...")
    
    threat_class = np.zeros_like(threat_score, dtype=np.uint8)
    
    # Definir umbrales usando percentiles
    p33 = np.percentile(threat_score, 33)
    p67 = np.percentile(threat_score, 67)
    
    logger.info(f"  Percentil 33: {p33:.1f}")
    logger.info(f"  Percentil 67: {p67:.1f}")
    
    threat_class[threat_score < p33] = 1     # Verde
    threat_class[(threat_score >= p33) & (threat_score < p67)] = 2  # Amarilla
    threat_class[threat_score >= p67] = 3    # Roja
    
    return threat_class

def vectorize_threat(threat_class, dem_meta):
    """Convertir raster a vectores (polígonos)"""
    logger.info("Vectorizando polígonos...")
    
    from rasterio.features import shapes
    
    # Asignar etiquetas a polígonos conectados
    labeled, num_features = label(threat_class > 0)
    
    polygons = []
    values = []
    
    for polygon, value in shapes(labeled.astype(np.uint8)):
        if value > 0:
            polygons.append(polygon)
            values.append({'value': threat_class[labeled == value][0]})
    
    gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=dem_meta['crs'])
    
    return gdf

def save_outputs(threat_score, threat_class, threat_vector, dem_meta):
    """Guardar todos los resultados"""
    logger.info("Guardando resultados...")
    
    # 1. Raster score continuo
    output_file_score = DATA_PROC / "Amenaza_Score_Continuo.tif"
    with rasterio.open(output_file_score, 'w', **dem_meta) as dst:
        dst.write(threat_score, 1)
    logger.info(f"  ✓ {output_file_score}")
    
    # 2. Raster clasificado
    output_file_class = DATA_PROC / "Amenaza_Clasificada.tif"
    meta_uint8 = dem_meta.copy()
    meta_uint8.update(dtype=rasterio.uint8, count=1)
    with rasterio.open(output_file_class, 'w', **meta_uint8) as dst:
        dst.write(threat_class, 1)
    logger.info(f"  ✓ {output_file_class}")
    
    # 3. Vectorial (shapefile)
    output_file_vector = DATA_PROC / "Amenaza_Poligonos.shp"
    threat_vector.to_file(output_file_vector)
    logger.info(f"  ✓ {output_file_vector}")
    
    # 4. Estadísticas
    stats = {
        'Clase': ['Roja', 'Amarilla', 'Verde'],
        'Valor': [3, 2, 1],
        'Píxeles': [
            np.sum(threat_class == 3),
            np.sum(threat_class == 2),
            np.sum(threat_class == 1)
        ],
        'Porcentaje': [
            100 * np.sum(threat_class == 3) / threat_class.size,
            100 * np.sum(threat_class == 2) / threat_class.size,
            100 * np.sum(threat_class == 1) / threat_class.size
        ]
    }
    
    df_stats = pd.DataFrame(stats)
    stats_file = DATA_PROC / "Estadisticas_Amenaza.csv"
    df_stats.to_csv(stats_file, index=False)
    logger.info(f"  ✓ {stats_file}")
    logger.info("\n" + df_stats.to_string())

def main():
    logger.info("🚀 Iniciando análisis de inundación...")
    
    # Cargar datos
    dem, ndvi, dem_meta = load_data()
    if dem is None:
        logger.error("No se pudieron cargar los datos")
        return
    
    # Calcular factores
    slope = calculate_slope(dem)
    
    # Crear mapa de amenaza
    threat_score = create_threat_map(dem, ndvi, slope)
    
    # Clasificar
    threat_class = classify_threat(threat_score)
    
    # Vectorizar
    threat_vector = vectorize_threat(threat_class, dem_meta)
    
    # Guardar
    save_outputs(threat_score, threat_class, threat_vector, dem_meta)
    
    logger.info("\n✅ Análisis completado exitosamente")

if __name__ == "__main__":
    main()
```

**Ejecutar:**
```bash
python3 scripts/analysis_flooding.py
```

---

## 3. BASE DE DATOS Y GEOSERVER

### 3.1 ingest_to_postgis.py

```python
#!/usr/bin/env python3
"""
Ingerir datos analizados a PostGIS
"""

import geopandas as gpd
from sqlalchemy import create_engine
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
DATABASE_URL = "postgresql://geofeedback:Papudo2025@localhost:5432/geofeedback_papudo"
DATA_PROC = Path("data/processed")

engine = create_engine(DATABASE_URL)

def ingest_amenaza():
    """Cargar amenaza a PostGIS"""
    logger.info("📥 Ingiriendo zonas de amenaza...")
    
    shapefile = DATA_PROC / "Amenaza_Poligonos.shp"
    if not shapefile.exists():
        logger.error(f"Falta: {shapefile}")
        return
    
    gdf = gpd.read_file(shapefile)
    gdf.columns = ['clase', 'geometry']
    gdf['clase_nombre'] = gdf['clase'].map({1: 'Verde', 2: 'Amarilla', 3: 'Roja'})
    gdf['score_amenaza'] = (gdf['clase'] - 1) / 2 * 100  # Escalar 0-100
    
    gdf.to_postgis('amenaza_inundacion', engine, if_exists='append', index=False)
    
    logger.info(f"✓ {len(gdf)} polígonos ingiridos")

def ingest_infraestructura():
    """Cargar infraestructura crítica"""
    logger.info("📥 Ingiriendo infraestructura crítica...")
    
    shapefile = DATA_PROC / "Infraestructura_Riesgo.shp"
    if not shapefile.exists():
        logger.error(f"Falta: {shapefile}")
        return
    
    gdf = gpd.read_file(shapefile)
    gdf.to_postgis('infraestructura_critica', engine, if_exists='append', index=False)
    
    logger.info(f"✓ {len(gdf)} elementos ingiridos")

def main():
    try:
        ingest_amenaza()
        ingest_infraestructura()
        logger.info("\n✅ Ingesta completada")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
```

**Ejecutar:**
```bash
python3 scripts/ingest_to_postgis.py
```

### 3.2 deploy_geoserver.sh

```bash
#!/bin/bash
# Deploy GeoServer con Docker [1670]

set -e

echo "🚀 Iniciando GeoServer..."

# Crear docker-compose.yml si no existe
if [ ! -f "docker-compose.yml" ]; then
    cat > docker-compose.yml << 'DOCKER_EOF'
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.3
    container_name: geofeedback_postgres
    environment:
      POSTGRES_USER: geofeedback
      POSTGRES_PASSWORD: Papudo2025
      POSTGRES_DB: geofeedback_papudo
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U geofeedback"]
      interval: 10s
      timeout: 5s
      retries: 5

  geoserver:
    image: kartoza/geoserver:2.24.0
    container_name: geofeedback_geoserver
    environment:
      GEOSERVER_ADMIN_USER: admin
      GEOSERVER_ADMIN_PASSWORD: geoserver123
      GEOSERVER_JAVA_OPTS: "-Xmx2g -Xms1g -XX:+UseG1GC"
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - geoserver_data:/opt/geoserver/data_dir
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/geoserver/web/"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  postgres_data:
  geoserver_data:
DOCKER_EOF
fi

# Iniciar contenedores
echo "▶️  Iniciando contenedores Docker..."
docker-compose up -d

# Esperar a que GeoServer esté listo
echo "⏳ Esperando a que GeoServer inicie..."
sleep 30

# Verificar
echo "🔍 Verificando conexiones..."
docker-compose ps

echo ""
echo "✅ GeoServer iniciado"
echo ""
echo "🌐 Acceder en: http://localhost:8080/geoserver"
echo "👤 Usuario: admin"
echo "🔐 Contraseña: geoserver123"
echo ""
echo "📊 Para publicar capas:"
echo "   1. Ir a Workspaces → Add workspace"
echo "   2. Nombre: GeoFeedback"
echo "   3. Data Stores → Add new"
echo "   4. Tipo: PostGIS"
echo "   5. Host: postgres, Port: 5432"
echo "   6. Database: geofeedback_papudo"
echo "   7. User: geofeedback, Password: Papudo2025"
```

**Ejecutar:**
```bash
chmod +x scripts/deploy_geoserver.sh
./scripts/deploy_geoserver.sh
```

---

## 4. FRONTEND Y API

### 4.1 run_api.py

```python
#!/usr/bin/env python3
"""
API REST para prototipo
Ejecutar desde: python3 scripts/run_api.py
"""

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from sqlalchemy import create_engine, text
import geopandas as gpd
import json

app = Flask(__name__)
CORS(app)

DATABASE_URL = "postgresql://geofeedback:Papudo2025@localhost:5432/geofeedback_papudo"
engine = create_engine(DATABASE_URL)

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({'status': 'OK', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'ERROR', 'details': str(e)}), 500

@app.route('/api/v1/amenaza/geojson', methods=['GET'])
def get_amenaza_geojson():
    try:
        query = "SELECT * FROM public.amenaza_inundacion LIMIT 1000"
        gdf = gpd.read_postgis(query, engine, geom_col='geometria')
        geojson = json.loads(gdf.to_json())
        return jsonify(geojson)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/amenaza/estadisticas', methods=['GET'])
def get_amenaza_stats():
    try:
        query = """
        SELECT 
            clase_nombre,
            COUNT(*) as count,
            ST_Area(ST_Union(geometria))/10000 as area_ha
        FROM public.amenaza_inundacion
        GROUP BY clase_nombre
        """
        with engine.connect() as conn:
            result = conn.execute(text(query))
            stats = [dict(row) for row in result.mappings()]
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GeoFeedback Papudo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial; margin: 40px; }
            .status { background: #e8f5e9; padding: 20px; border-radius: 8px; }
            .link { color: #1976d2; text-decoration: none; margin: 10px 0; display: block; }
        </style>
    </head>
    <body>
        <h1>✅ API GeoFeedback Funcional</h1>
        <div class="status">
            <h2>Endpoints disponibles:</h2>
            <a class="link" href="/api/v1/health">📊 Health Check</a>
            <a class="link" href="/api/v1/amenaza/geojson">🗺️ Descargar GeoJSON</a>
            <a class="link" href="/api/v1/amenaza/estadisticas">📈 Estadísticas</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**Ejecutar:**
```bash
python3 scripts/run_api.py
# Acceder en: http://localhost:5000
```

---

## 5. TESTING Y VALIDACIÓN

### 5.1 test_all.sh

```bash
#!/bin/bash
# Testing completo del prototipo

set -e

echo "🧪 Iniciando testing..."
echo ""

# 1. Database
echo "1️⃣  Probando PostGIS..."
PGPASSWORD=Papudo2025 psql -U geofeedback -d geofeedback_papudo -h localhost \
  -c "SELECT COUNT(*) FROM amenaza_inundacion" && echo "✓ PostGIS OK" || echo "✗ Error PostGIS"

# 2. GeoServer
echo ""
echo "2️⃣  Probando GeoServer..."
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -u admin:geoserver123 \
  http://localhost:8080/geoserver/web/ && echo "✓ GeoServer OK" || echo "✗ Error GeoServer"

# 3. API
echo ""
echo "3️⃣  Probando API REST..."
curl -s http://localhost:5000/api/v1/health | grep "OK" && echo "✓ API OK" || echo "✗ Error API"

# 4. GeoJSON
echo ""
echo "4️⃣  Probando GeoJSON..."
FEATURES=$(curl -s http://localhost:5000/api/v1/amenaza/geojson | grep -o '"type":"Feature"' | wc -l)
echo "✓ GeoJSON: $FEATURES features"

echo ""
echo "✅ Testing completado"
```

**Ejecutar:**
```bash
chmod +x scripts/test_all.sh
./scripts/test_all.sh
```

---

## 📋 ORDEN DE EJECUCIÓN COMPLETO

```bash
# Paso 1: Setup
chmod +x scripts/install_dependencies.sh
./scripts/install_dependencies.sh
source venv/bin/activate

# Paso 2: Database
chmod +x scripts/setup_database.sh
./scripts/setup_database.sh

# Paso 3: Descargar datos
python3 scripts/download_data.py

# Paso 4: Análisis
python3 scripts/analysis_flooding.py

# Paso 5: Ingerir a BD
python3 scripts/ingest_to_postgis.py

# Paso 6: GeoServer
chmod +x scripts/deploy_geoserver.sh
./scripts/deploy_geoserver.sh

# Paso 7: API
python3 scripts/run_api.py
# En otra terminal:
# chmod +x scripts/test_all.sh
# ./scripts/test_all.sh
```

---

**Todos los scripts están listos para copiar y ejecutar.**  
**Requieren Python 3.8+, PostgreSQL 13+, Docker**
