# QUICK-START GUIDE
## Prototipo Demo: Mapa de Riesgo Inundación Papudo

**Duración**: Comenzar HOY, terminado en 3-4 semanas  
**Equipo**: Desarrollador TI + Ingeniera Ambiental  
**Costo**: $0 USD  

---

## 🚀 SEMANA 1: SETUP INICIAL (5 días)

### DÍA 1: Instalación Stack Open Source

```bash
# Ubuntu/Debian/WSL2 (ejecutar en terminal)

# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias base
sudo apt install -y \
  python3-pip \
  git \
  curl \
  wget \
  postgresql \
  postgresql-contrib \
  gdal-bin \
  qgis \
  docker.io \
  docker-compose

# 3. Crear carpeta proyecto
mkdir -p ~/geofeedback-papudo && cd ~/geofeedback-papudo

# 4. Crear ambiente Python
python3 -m venv venv
source venv/bin/activate

# 5. Instalar librerías Python [1670]
pip install geopandas rasterio shapely fiona \
  psycopg2-binary sqlalchemy pandas numpy \
  flask flask-cors requests python-dotenv

# 6. Iniciar PostgreSQL
sudo service postgresql start

# 7. Verificar instalaciones
python3 --version
qgis --version
psql --version
git --version

echo "✓ Stack instalado. Verificar sin errores arriba"
```

### DÍA 2: Configuración Base de Datos PostGIS

```bash
# Crear usuario y BD
sudo -u postgres psql << EOF
CREATE USER geofeedback WITH PASSWORD 'Papudo2025';
CREATE DATABASE geofeedback_papudo OWNER geofeedback;
\c geofeedback_papudo
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
SELECT postgis_version();
EOF

# Debe mostrar: "version": "POSTGIS 3.3.x"

# Verificar conexión
psql -U geofeedback -d geofeedback_papudo -h localhost
# Escribir: \dt (debe estar vacío)
# Escribir: \q (salir)
```

### DÍA 3: Descargar Datos Fuente

**Ingeniera Ambiental: Ejecutar en Google Earth Engine**

```javascript
// Copiar en https://code.earthengine.google.com/

// Define AOI (Papudo + 5km buffer)
var papudo = ee.Geometry.Point([-71.4408, -32.4283]).buffer(5000);

// Descargar Sentinel-2 (puede tomar 30min-1h)
var s2_col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
  .filterBounds(papudo)
  .filterDate('2025-05-01', '2025-07-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10));

// Calcular NDVI
var ndvi = s2_col.first()
  .normalizedDifference(['B8', 'B4'])
  .rename('NDVI');

// Exportar a Google Drive
Export.image.toDrive({
  image: ndvi,
  description: 'Sentinel2_NDVI_Papudo',
  scale: 10,
  region: papudo.bounds(),
  fileFormat: 'GeoTIFF'
});

// Ejecutar "Run" (botón arriba)
// Esperar a que aparezca tarea en "Tasks" (arriba derecha)
// Hacer click en "RUN"
// Revisar Google Drive cuando termine
```

**Descargar datos IDE Chile [1670]**

```bash
# Descargar datos municipio (shapefiles)
wget https://www.geoportal.cl/geoserver/ows?service=WFS&request=GetFeature&typeName=sdesgg:division_politica_administrativa&CQL_FILTER=NOMBRE='PAPUDO'&outputFormat=SHAPEFILE -O IDE_Chile_Papudo.zip

unzip IDE_Chile_Papudo.zip

# Descargar DEM SRTM
wget https://cloud.sdsc.edu/v1/AUTH_cryosphere/Raster/DEM/SRTM_GL1_Ellip/SRTM_GL1_Ellip_srtm.zip -O SRTM_Papudo.zip

unzip SRTM_Papudo.zip
```

### DÍA 4-5: Preparación Datos en QGIS

**En QGIS (abrir aplicación)**

```
1. Abrir QGIS
2. Project → New
3. Layer → Add Layer → Add Raster Layer
   - Seleccionar: Sentinel2_NDVI_Papudo.tif
   - OK
4. Layer → Add Layer → Add Vector Layer
   - Seleccionar: IDE_Chile_Papudo.shp
   - OK
5. Visualizar que ambas capas se cargan correctamente
6. Zoom a Papudo: View → Zoom to Layer
7. Guardar proyecto: File → Save As → "Papudo_Proyecto.qgz"
```

**Verificación:**
```bash
# Asegurar que archivo DEM esté en carpeta correcta
ls -la ~/geofeedback-papudo/data/raw/
# Debe mostrar: SRTM_*.tif, IDE_*.shp, Sentinel2_*.tif
```

---

## 🗺️ SEMANA 2: ANÁLISIS GEOESPACIAL (8 días)

### DÍA 6-9: Análisis de Inundación (Ingeniera Ambiental)

**Script Principal: analysis_flooding.py**

```bash
cd ~/geofeedback-papudo
nano analysis_flooding.py
```

Copiar código (ver sección 3.1.2 del plan principal):

```python
import rasterio
import geopandas as gpd
import numpy as np
from scipy.ndimage import binary_dilation
import pandas as pd

# Cargar datos [1670]
dem_path = 'data/raw/SRTM_Papudo_DEM.tif'
ndvi_path = 'data/raw/Sentinel2_NDVI_Papudo.tif'

with rasterio.open(dem_path) as src:
    dem = src.read(1)
    dem_meta = src.meta
    dem_profile = src.profile

with rasterio.open(ndvi_path) as src:
    ndvi = src.read(1)

# PASO 1: Calcular pendiente
from scipy.ndimage import gradient
dy, dx = gradient(dem)
pendiente = np.arctan(np.sqrt(dx**2 + dy**2)) * 180 / np.pi

# PASO 2: Crear mapa de amenaza (combinación factores)
amenaza_score = np.zeros_like(dem, dtype=float)

# Factor 1: Pendiente baja = más riesgo
amenaza_score[pendiente < 2] = 100
amenaza_score[(pendiente >= 2) & (pendiente < 5)] = 70
amenaza_score[(pendiente >= 5)] = 20

# Factor 2: NDVI bajo = suelo impermeable = más riesgo
amenaza_score = np.where(ndvi < -0.2, amenaza_score * 1.3,
                        np.where(ndvi < 0.3, amenaza_score * 1.1,
                        amenaza_score * 0.9))

# PASO 3: Clasificar en 3 clases
amenaza_clase = np.zeros_like(amenaza_score, dtype=np.uint8)
amenaza_clase[amenaza_score >= 70] = 3   # Roja
amenaza_clase[(amenaza_score >= 40) & (amenaza_score < 70)] = 2  # Amarilla
amenaza_clase[amenaza_score < 40] = 1   # Verde

# PASO 4: Exportar raster
output_profile = dem_profile.copy()
output_profile.update({'dtype': 'uint8', 'count': 1})

with rasterio.open('data/processed/Amenaza_Clasificada.tif', 'w', **output_profile) as dst:
    dst.write(amenaza_clase, 1)

print("✓ Análisis completado: Amenaza_Clasificada.tif")
print(f"  Píxeles Rojo: {np.sum(amenaza_clase == 3)}")
print(f"  Píxeles Amarillo: {np.sum(amenaza_clase == 2)}")
print(f"  Píxeles Verde: {np.sum(amenaza_clase == 1)}")
```

**Ejecutar análisis:**
```bash
cd ~/geofeedback-papudo
python3 analysis_flooding.py
# Debe generar: data/processed/Amenaza_Clasificada.tif
```

### DÍA 10-11: Análisis Infraestructura Crítica

```bash
nano analysis_infrastructure.py
```

```python
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Cargar datos
ide_data = gpd.read_file('data/raw/IDE_Chile_Papudo.shp')
amenaza = gpd.read_file('data/processed/Amenaza_Poligonos.shp')

# Análisis: Infraestructura en zonas riesgo
infraest_riesgo = gpd.sjoin(ide_data, amenaza, how='inner', predicate='within')

# Guardar resultado
infraest_riesgo.to_file('data/processed/Infraestructura_Riesgo.shp')

# Estadísticas
print(f"✓ Infraestructura crítica en zona riesgo: {len(infraest_riesgo)} elementos")
print(infraest_riesgo.to_csv('data/processed/Infraestructura_Riesgo.csv', index=False))
```

**Ejecutar:**
```bash
python3 analysis_infrastructure.py
```

---

## 🗄️ SEMANA 3: BASE DE DATOS Y BACKEND (7 días)

### DÍA 12-13: Configurar PostGIS

```bash
# Crear tablas
psql -U geofeedback -d geofeedback_papudo -f database/setup_postgis.sql
# (Ver archivo completo en plan principal, sección 3.1.4)
```

### DÍA 14-16: Desarrollo API REST (Flask)

```bash
# Crear estructura
mkdir -p backend/{templates,static}
cd backend

# Crear app.py
nano app.py
# (Copiar código de sección 3.1.6 del plan principal)

# Crear requirements.txt
cat > requirements.txt << EOF
Flask==3.0.0
Flask-CORS==4.0.0
psycopg2-binary==2.9.9
geopandas==0.14.0
sqlalchemy==2.0.23
EOF

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor (prueba)
python3 app.py
# Debe mostrar: "Running on http://127.0.0.1:5000"
```

### DÍA 17-18: Configurar GeoServer [1670]

```bash
# Usando Docker
cd ~/geofeedback-papudo

cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  postgres:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_USER: geofeedback
      POSTGRES_PASSWORD: Papudo2025
      POSTGRES_DB: geofeedback_papudo
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  geoserver:
    image: kartoza/geoserver:2.24.0
    environment:
      GEOSERVER_ADMIN_USER: admin
      GEOSERVER_ADMIN_PASSWORD: geoserver123
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  postgres_data:
EOF

# Iniciar
docker-compose up -d

# Esperar 2 minutos
sleep 120

# Acceder
# http://localhost:8080/geoserver/web/
# Usuario: admin / Contraseña: geoserver123
```

---

## 🌐 SEMANA 4: FRONTEND Y TESTING (7 días)

### DÍA 19-22: Desarrollo Frontend (Leaflet)

```bash
mkdir -p frontend/templates frontend/static
cd frontend/templates

# Crear index.html (copiar de sección 3.1.7 del plan)
nano index.html
# (Copiar código completo HTML)

# Ejecutar servidor Flask con frontend
cd ~/geofeedback-papudo
python3 -m flask run --reload

# Abrir navegador: http://localhost:5000
```

### DÍA 23-25: Testing y Validación

**Checklist de pruebas:**

```bash
#!/bin/bash
# test_checklist.sh

echo "=== TESTING PROTOTIPO ==="

# 1. Database
echo "1. Probando conexión PostGIS..."
psql -U geofeedback -d geofeedback_papudo -c "SELECT postgis_version();" && echo "✓" || echo "✗"

# 2. API
echo "2. Probando API REST..."
curl -s http://localhost:5000/api/v1/health | grep "OK" && echo "✓" || echo "✗"

# 3. GeoServer
echo "3. Probando GeoServer..."
curl -s -u admin:geoserver123 http://localhost:8080/geoserver/web/ | grep "GeoServer" && echo "✓" || echo "✗"

# 4. Mapas
echo "4. Probando capas geoespaciales..."
curl -s http://localhost:5000/api/v1/amenaza/geojson | grep "features" && echo "✓" || echo "✗"

# 5. Frontend
echo "5. Probando página web..."
curl -s http://localhost:5000 | grep "GeoFeedback" && echo "✓" || echo "✗"

echo "=== TESTING COMPLETO ==="
```

**Ejecutar:**
```bash
chmod +x test_checklist.sh
./test_checklist.sh
```

### DÍA 26-28: Documentación

```bash
# Crear documentos finales
mkdir -p docs

# 1. README principal
nano docs/README.md
# Instrucciones setup, uso, troubleshooting

# 2. API Documentation
nano docs/API.md
# Endpoints, parámetros, ejemplos

# 3. Manual Usuario
nano docs/MANUAL_USUARIO.md
# Cómo usar visor web, interpretar mapas

# 4. Informe Técnico
nano docs/INFORME_TECNICO.md
# Metodología, resultados, conclusiones
```

---

## 📊 ENTREGABLES FINALES

Al finalizar las 4 semanas, debes tener:

```
✅ Visor web funcional (http://localhost:5000)
✅ Mapas interactivos de amenaza (3 clases: rojo/amarillo/verde)
✅ Base de datos PostGIS con análisis completo
✅ API REST con 10+ endpoints
✅ Servicios WMS/WFS en GeoServer [1670]
✅ Código reproducible (GitHub)
✅ Documentación técnica
✅ Informe ejecutivo PDF
✅ Todo en 100% open source ($0 USD)
```

---

## 🎯 PRÓXIMOS PASOS PARA EVALUADORES

1. **Descargar y ejecutar** prototipo localmente
2. **Probar visor web** - interactividad, capas, filtros
3. **Consultar base datos** - integridad, precisión
4. **Revisar código** - limpieza, documentación, reutilización
5. **Validar metodología** - rigor geoespacial, estándares OGC

---

## 📱 CONTACTO Y SOPORTE

En caso de errores durante implementación:

**Errores comunes y soluciones:**

| Error | Solución |
|-------|----------|
| `psql: connection refused` | `sudo service postgresql start` |
| `ModuleNotFoundError: geopandas` | `pip install geopandas` |
| `GeoServer not responding` | Esperar 2min después `docker-compose up` |
| `Sentinel-2 download slow` | Google Earth Engine tiene límites - usar VPN o esperar horarios bajos |

**Referencias documentales:**
- Plan principal: `PLAN_PROTOTIPO_GEOFEEDBACK_INUNDACION.md`
- Código completo: Disponible en cada sección
- Documentación open source: Ver enlaces en plan principal

---

**Versión**: 1.0  
**Fecha**: Noviembre 2025  
**Autores**: Equipo Técnico GeoFeedback Chile
