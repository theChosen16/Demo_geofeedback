# GeoServer - GeoFeedback Papudo

Configuración de GeoServer con Docker para publicar servicios OGC estándar (WMS/WFS) de las capas de riesgo de inundación e infraestructura crítica.

## Componentes

- **GeoServer 2.24.0** (kartoza/geoserver)
- **PostgreSQL 16 + PostGIS 3.4** (postgis/postgis)
- **Servicios OGC**: WMS, WFS, WCS
- **Estilos SLD** personalizados para visualización

## Requisitos Previos

- Docker 20.10+ y Docker Compose 2.0+
- 4GB RAM disponible
- Puerto 8080 (GeoServer) y 5433 (PostgreSQL) libres

## Inicio Rápido

### 1. Levantar Servicios

```bash
cd geoserver
docker-compose up -d
```

Esto levantará:
- PostGIS en puerto `5433`
- GeoServer en puerto `8080`

### 2. Cargar Datos

```bash
cd scripts
./load_data.sh
```

Este script exporta datos de tu PostgreSQL local (puerto 5432) y los carga en el contenedor.

### 3. Configurar GeoServer

```bash
cd scripts
./setup_geoserver.sh
```

Este script configura automáticamente:
- Workspace `geofeedback`
- DataStores PostGIS
- Publica capas `amenaza_poligonos` y `facilities_risk`
- Aplica estilos SLD

### 4. Verificar

Abrir en navegador: http://localhost:8080/geoserver/web

**Credenciales:**
- Usuario: `admin`
- Password: `GeoFeedback2025`

## Estructura de Directorios

```
geoserver/
├── docker-compose.yml      # Configuración Docker
├── init/                   # Scripts SQL de inicialización
│   └── 01_init_database.sql
├── styles/                 # Estilos SLD
│   ├── risk_polygons.sld
│   └── infrastructure.sld
├── scripts/                # Scripts de automatización
│   ├── setup_geoserver.sh  # Configuración automática
│   └── load_data.sh        # Carga de datos
├── data/                   # Datos auxiliares (auto-creado)
└── README.md               # Esta documentación
```

## Servicios OGC

### Capas Publicadas

1. **geofeedback:amenaza_poligonos**
   - Polígonos de zonas de riesgo (Alto/Medio/Bajo)
   - SRS: EPSG:32719 (UTM 19S)
   - Estilo: risk_style.sld

2. **geofeedback:facilities_risk**
   - Infraestructura crítica con nivel de riesgo
   - SRS: EPSG:32719 (UTM 19S)
   - Estilo: infrastructure_style.sld

### WMS (Web Map Service)

**GetCapabilities:**
```
http://localhost:8080/geoserver/geofeedback/wms?service=WMS&request=GetCapabilities
```

**GetMap (Zonas de Riesgo):**
```
http://localhost:8080/geoserver/geofeedback/wms?
  service=WMS&
  version=1.1.0&
  request=GetMap&
  layers=geofeedback:amenaza_poligonos&
  bbox=-71.50,-32.54,-71.42,-32.47&
  width=800&
  height=600&
  srs=EPSG:4326&
  format=image/png&
  styles=risk_style
```

**GetFeatureInfo:**
```
http://localhost:8080/geoserver/geofeedback/wms?
  service=WMS&
  version=1.1.0&
  request=GetFeatureInfo&
  layers=geofeedback:amenaza_poligonos&
  query_layers=geofeedback:amenaza_poligonos&
  bbox=-71.50,-32.54,-71.42,-32.47&
  width=800&
  height=600&
  x=400&
  y=300&
  srs=EPSG:4326&
  info_format=application/json
```

### WFS (Web Feature Service)

**GetCapabilities:**
```
http://localhost:8080/geoserver/geofeedback/wfs?service=WFS&request=GetCapabilities
```

**GetFeature (GeoJSON):**
```
http://localhost:8080/geoserver/geofeedback/wfs?
  service=WFS&
  version=2.0.0&
  request=GetFeature&
  typeName=geofeedback:amenaza_poligonos&
  outputFormat=application/json
```

**GetFeature con Filtro (Alto Riesgo):**
```
http://localhost:8080/geoserver/geofeedback/wfs?
  service=WFS&
  version=2.0.0&
  request=GetFeature&
  typeName=geofeedback:amenaza_poligonos&
  outputFormat=application/json&
  CQL_FILTER=risk_level=3
```

## Integración con QGIS

### Agregar Capa WMS

1. Abrir QGIS
2. Layer → Add Layer → Add WMS/WMTS Layer
3. New Connection:
   - Name: `GeoFeedback Papudo`
   - URL: `http://localhost:8080/geoserver/geofeedback/wms`
4. Connect → Seleccionar capa → Add

### Agregar Capa WFS

1. Layer → Add Layer → Add WFS Layer
2. New Connection:
   - Name: `GeoFeedback Papudo WFS`
   - URL: `http://localhost:8080/geoserver/geofeedback/wfs`
3. Connect → Seleccionar capa → Add

## Integración con Leaflet

```javascript
// Agregar capa WMS al mapa Leaflet
const wmsLayer = L.tileLayer.wms('http://localhost:8080/geoserver/geofeedback/wms', {
    layers: 'geofeedback:amenaza_poligonos',
    format: 'image/png',
    transparent: true,
    attribution: 'GeoFeedback Chile',
    styles: 'risk_style'
});

wmsLayer.addTo(map);

// GetFeatureInfo al hacer click
map.on('click', function(e) {
    const latlng = e.latlng;
    const bounds = map.getBounds();
    const size = map.getSize();

    const url = 'http://localhost:8080/geoserver/geofeedback/wms?' +
        'SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&' +
        'LAYERS=geofeedback:amenaza_poligonos&' +
        'QUERY_LAYERS=geofeedback:amenaza_poligonos&' +
        'STYLES=&BBOX=' + bounds.toBBoxString() + '&' +
        'HEIGHT=' + size.y + '&WIDTH=' + size.x + '&' +
        'FORMAT=image/png&INFO_FORMAT=application/json&' +
        'SRS=EPSG:4326&' +
        'X=' + Math.round(e.containerPoint.x) + '&' +
        'Y=' + Math.round(e.containerPoint.y);

    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Feature info:', data);
        });
});
```

## Gestión de Contenedores

### Ver Logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo GeoServer
docker-compose logs -f geoserver

# Solo PostGIS
docker-compose logs -f postgis
```

### Reiniciar Servicios

```bash
# Reiniciar todo
docker-compose restart

# Reiniciar solo GeoServer
docker-compose restart geoserver
```

### Detener Servicios

```bash
docker-compose down
```

### Detener y Eliminar Volúmenes

```bash
docker-compose down -v
```

## Administración de GeoServer

### Interfaz Web

URL: http://localhost:8080/geoserver/web

**Secciones principales:**
- **Layer Preview**: Vista previa de capas
- **Layers**: Gestión de capas
- **Stores**: Gestión de datastores
- **Workspaces**: Gestión de workspaces
- **Styles**: Gestión de estilos SLD
- **Settings**: Configuración global

### REST API

GeoServer incluye una REST API completa para automatización.

**Ejemplos:**

```bash
# Listar workspaces
curl -u admin:GeoFeedback2025 \
  http://localhost:8080/geoserver/rest/workspaces.json

# Listar capas
curl -u admin:GeoFeedback2025 \
  http://localhost:8080/geoserver/rest/layers.json

# Obtener info de capa
curl -u admin:GeoFeedback2025 \
  http://localhost:8080/geoserver/rest/layers/geofeedback:amenaza_poligonos.json
```

## Estilos SLD

### Modificar Estilos

Los estilos se encuentran en `styles/`:
- `risk_polygons.sld` - Estilo para zonas de riesgo
- `infrastructure.sld` - Estilo para infraestructura

Para aplicar cambios:

1. Editar archivo SLD
2. Subir nuevo estilo:
```bash
curl -u admin:GeoFeedback2025 \
  -X PUT \
  -H "Content-Type: application/vnd.ogc.sld+xml" \
  --data-binary @styles/risk_polygons.sld \
  http://localhost:8080/geoserver/rest/workspaces/geofeedback/styles/risk_style
```

## Conexión Directa a PostGIS

El contenedor PostgreSQL está expuesto en el puerto `5433`:

```bash
# Desde línea de comandos
psql -h localhost -p 5433 -U geofeedback -d geofeedback_papudo

# Desde código Python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="geofeedback_papudo",
    user="geofeedback",
    password="Papudo2025"
)
```

## Troubleshooting

### GeoServer no arranca

```bash
# Ver logs
docker-compose logs geoserver

# Verificar memoria
docker stats

# Reiniciar limpio
docker-compose down
docker-compose up -d
```

### Error de conexión a PostGIS

```bash
# Verificar que PostGIS esté corriendo
docker-compose ps

# Verificar conectividad
docker exec geofeedback_postgis pg_isready -U geofeedback

# Probar conexión
docker exec -it geofeedback_postgis psql -U geofeedback -d geofeedback_papudo
```

### Capas no se muestran

1. Verificar que datos estén cargados:
```bash
docker exec geofeedback_postgis psql -U geofeedback -d geofeedback_papudo \
  -c "SELECT COUNT(*) FROM processed.amenaza_poligonos;"
```

2. Recalcular bounds en GeoServer:
   - Web UI → Layers → Seleccionar capa → Edit
   - Compute from data → Save

### Performance lenta

Aumentar memoria para GeoServer en `docker-compose.yml`:

```yaml
GEOSERVER_JAVA_OPTS: >-
  -Xms1g
  -Xmx4g
```

## Producción

Para despliegue en producción:

1. **Cambiar credenciales** en `docker-compose.yml`
2. **Usar volúmenes externos** para persistencia
3. **Configurar HTTPS** con reverse proxy (nginx)
4. **Limitar acceso** con firewall
5. **Configurar backups** automáticos
6. **Monitorear** con Prometheus/Grafana

### Ejemplo con HTTPS (nginx)

```nginx
server {
    listen 443 ssl;
    server_name geoserver.tudominio.cl;

    ssl_certificate /etc/letsencrypt/live/tudominio.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tudominio.cl/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Recursos Adicionales

- [Documentación GeoServer](https://docs.geoserver.org/)
- [Especificación WMS](https://www.ogc.org/standards/wms)
- [Especificación WFS](https://www.ogc.org/standards/wfs)
- [SLD Cookbook](https://docs.geoserver.org/latest/en/user/styling/sld/cookbook/)
- [REST API Reference](https://docs.geoserver.org/latest/en/user/rest/)

## Soporte

Para problemas o preguntas, abrir un issue en el repositorio del proyecto.

---

**GeoFeedback Chile** - Noviembre 2025
