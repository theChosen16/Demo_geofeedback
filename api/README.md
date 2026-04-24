# API REST - GeoFeedback Papudo

API RESTful construida con Flask para consultar datos de riesgo de inundación e infraestructura crítica del municipio de Papudo.

## Nota de actualización (Abril 2026)

- El contador público de la home usa `GET /api/v1/stats` con contrato `{ "visits": int, "analyses": int }`.
- La inicialización de base de datos para Railway (`scripts/init_railway_db.py`) ahora ejecuta también `scripts/sql/06_create_analytics_tables.sql`.
- Si las tablas `metadata.page_visits` o `metadata.api_usage_logs` faltan en runtime, `api/database.py` las crea de forma idempotente y reintenta la operación una vez.
- `GET /api/v1/observability` expone estado crítico del servicio y retorna `503` cuando analytics o dependencias clave están degradadas.
- `scripts/monitor_deploy.py` permite monitoreo reusable con `--url` y `--once`, sin dependencia de `requests`.
- Se recomienda ejecutar CI local con:

```bash
python -m compileall api scripts tests
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/monitor_deploy.py --url https://geofeedback.cl --once
```

## Características

- **RESTful API** con endpoints documentados
- **CORS habilitado** para integración con aplicaciones web
- **Conexión a PostGIS** para consultas espaciales
- **JSON responses** con datos geoespaciales
- **Error handling** robusto
- **Health check** para monitoreo

## Requisitos

- Python 3.8+
- PostgreSQL 12+ con PostGIS 3.0+
- Base de datos `geofeedback_papudo` configurada

## Instalación

1. **Instalar dependencias:**

```bash
cd api
pip install -r requirements.txt
```

2. **Configurar base de datos (opcional):**

Crear archivo `.env` con configuración personalizada:

```bash
DB_NAME=geofeedback_papudo
DB_USER=geofeedback
DB_PASSWORD=Papudo2025
DB_HOST=localhost
DB_PORT=5432
```

## Uso

### Iniciar el servidor

```bash
python app.py
```

La API estará disponible en: http://localhost:5000

### Modo producción

Para producción, usar un servidor WSGI como Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Endpoints

### Raíz - Documentación

```
GET /
```

Retorna documentación de endpoints disponibles.

**Respuesta:**
```json
{
  "name": "GeoFeedback Papudo API",
  "version": "1.0.0",
  "endpoints": { ... }
}
```

### Health Check

```
GET /api/v1/health
```

Verifica el estado de la API y la conexión a la base de datos.

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T15:30:00",
  "database": { "connected": true, "version": "PostgreSQL 16.10" }
}
```

### Observability

```
GET /api/v1/observability
```

Entrega un snapshot operativo del servicio, incluyendo checks críticos, dependencias opcionales y estado del contador público.

**Respuesta saludable:**
```json
{
  "status": "healthy",
  "critical_checks": {
    "database": true,
    "analytics": true,
    "google_earth_engine": true,
    "google_maps_key": true
  },
  "optional_checks": {
    "gemini": true,
    "redis": true
  },
  "analytics": {
    "page_visits_table": true,
    "api_usage_logs_table": true,
    "role_configured": true,
    "ready": true
  },
  "public_stats": {
    "visits": 120,
    "analyses": 48
  }
}
```

Cuando el estado crítico está degradado, el endpoint responde `503` para que el monitor o el despliegue puedan detectarlo.

### Métricas Públicas

```
GET /api/v1/stats
```

Retorna únicamente el contador público usado en la home.

**Respuesta:**
```json
{
  "visits": 120,
  "analyses": 48
}
```

### Estadísticas Generales

```
GET /api/v1/stats
```

Obtiene estadísticas de riesgo globales.

**Respuesta:**
```json
{
  "timestamp": "2025-11-18T15:30:00",
  "statistics": [
    {
      "risk_level": 3,
      "risk_name": "Alto",
      "risk_color": "#FF6B6B",
      "num_polygons": 550,
      "total_area_km2": 450.13,
      "percentage": 23.38
    },
    ...
  ]
}
```

### Riesgo en Punto Específico

```
GET /api/v1/risk/point?lon=-71.4492&lat=-32.5067
```

Consulta el nivel de riesgo en coordenadas específicas (WGS84).

**Parámetros:**
- `lon` (float, requerido): Longitud
- `lat` (float, requerido): Latitud

**Respuesta:**
```json
{
  "lon": -71.4492,
  "lat": -32.5067,
  "risk_level": 2,
  "risk_name": "Medio",
  "risk_color": "#FFD700",
  "area_km2": 0.85,
  "polygon_id": 1523
}
```

### Polígonos en Bounding Box

```
GET /api/v1/risk/bbox?minLon=-71.50&minLat=-32.54&maxLon=-71.42&maxLat=-32.47
```

Obtiene todos los polígonos de riesgo dentro de un área rectangular.

**Parámetros:**
- `minLon`, `minLat`, `maxLon`, `maxLat` (float, requeridos)

**Respuesta:**
```json
{
  "bbox": { "minLon": -71.50, "minLat": -32.54, ... },
  "count": 125,
  "polygons": [
    {
      "poly_id": 1,
      "risk_level": 2,
      "risk_name": "Medio",
      "area_km2": 0.85,
      "geojson": { "type": "Polygon", "coordinates": [...] }
    },
    ...
  ]
}
```

### Toda la Infraestructura

```
GET /api/v1/infrastructure
```

Lista todas las instalaciones de infraestructura con su nivel de riesgo.

**Respuesta:**
```json
{
  "timestamp": "2025-11-18T15:30:00",
  "count": 20,
  "facilities": [
    {
      "id": 1,
      "name": "Escuela Básica Papudo",
      "category": "Educación",
      "risk_level": 2,
      "risk_name": "Medio",
      "risk_color": "#FFD700",
      "coordinates": { "lon": -71.4510, "lat": -32.5055 },
      "geometry": { ... }
    },
    ...
  ]
}
```

### Infraestructura por ID

```
GET /api/v1/infrastructure/5
```

Obtiene detalles de una instalación específica.

**Respuesta:**
```json
{
  "id": 5,
  "osm_id": 123456789,
  "name": "CESFAM Papudo",
  "category": "Salud",
  "amenity": "clinic",
  "risk_level": 2,
  "coordinates": { "lon": -71.4485, "lat": -32.5080 },
  "geometry": { ... }
}
```

### Infraestructura por Nivel de Riesgo

```
GET /api/v1/infrastructure/risk/2
```

Filtra instalaciones por nivel de riesgo (1=Bajo, 2=Medio, 3=Alto).

**Respuesta:**
```json
{
  "risk_level": 2,
  "count": 20,
  "facilities": [...]
}
```

### Infraestructura por Categoría

```
GET /api/v1/infrastructure/category/Educación
```

Filtra instalaciones por categoría.

**Categorías válidas:**
- `Educación`
- `Salud`
- `Emergencias`
- `Gobierno`
- `Comercio`

**Respuesta:**
```json
{
  "category": "Educación",
  "count": 5,
  "facilities": [...]
}
```

## Códigos de Estado HTTP

- `200 OK`: Solicitud exitosa
- `400 Bad Request`: Parámetros inválidos
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor
- `503 Service Unavailable`: Servicio no disponible (ej. BD desconectada)

## Ejemplos de Uso

### cURL

```bash
# Health check
curl http://localhost:5000/api/v1/health

# Estadísticas
curl http://localhost:5000/api/v1/stats

# Riesgo en punto
curl "http://localhost:5000/api/v1/risk/point?lon=-71.4492&lat=-32.5067"

# Infraestructura
curl http://localhost:5000/api/v1/infrastructure
```

### Python

```python
import requests

# Health check
response = requests.get('http://localhost:5000/api/v1/health')
print(response.json())

# Obtener instalaciones en riesgo alto
response = requests.get('http://localhost:5000/api/v1/infrastructure/risk/3')
facilities = response.json()['facilities']

for facility in facilities:
    print(f"{facility['name']} - {facility['category']}")
```

### JavaScript

```javascript
// Fetch statistics
fetch('http://localhost:5000/api/v1/stats')
  .then(response => response.json())
  .then(data => {
    console.log('Statistics:', data.statistics);
  });

// Get infrastructure
fetch('http://localhost:5000/api/v1/infrastructure')
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.count} facilities`);
    data.facilities.forEach(f => {
      console.log(`${f.name}: ${f.risk_name}`);
    });
  });
```

## Integración con Visor Web

El visor web puede consumir esta API para obtener datos dinámicos:

```javascript
// En web/js/map.js
async function loadDataFromAPI() {
    const response = await fetch('http://localhost:5000/api/v1/infrastructure');
    const data = await response.json();
    return data.facilities;
}
```

## Estructura del Proyecto

```
api/
├── app.py              # Aplicación principal Flask
├── requirements.txt    # Dependencias Python
├── README.md          # Esta documentación
└── .env.example       # Ejemplo de configuración
```

## Desarrollo

### Habilitar modo debug

El servidor ya viene configurado con `debug=True` en modo desarrollo. Para deshabilitarlo en producción, cambiar en `app.py`:

```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

### Agregar nuevo endpoint

1. Crear función en `app.py`:
```python
@app.route('/api/v1/nuevo-endpoint', methods=['GET'])
def nuevo_endpoint():
    # Lógica aquí
    return jsonify({'resultado': 'datos'})
```

2. Documentar en este README

### Testing

Para probar todos los endpoints:

```bash
# Instalar httpie
pip install httpie

# Probar endpoints
http GET http://localhost:5000/api/v1/health
http GET http://localhost:5000/api/v1/stats
http GET "http://localhost:5000/api/v1/risk/point?lon=-71.4492&lat=-32.5067"
```

## Seguridad

### Producción

Para producción, considerar:

1. **Variables de entorno**: No hardcodear credenciales
2. **HTTPS**: Usar certificados SSL/TLS
3. **Rate limiting**: Limitar requests por IP
4. **Authentication**: Implementar API keys o JWT
5. **Logging**: Registrar todas las peticiones
6. **CORS**: Restringir orígenes permitidos

Ejemplo con rate limiting:

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/v1/stats')
@limiter.limit("60 per minute")
def get_stats():
    # ...
```

## Despliegue

### Docker

Crear `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Construir y ejecutar:

```bash
docker build -t geofeedback-api .
docker run -p 5000:5000 geofeedback-api
```

## Soporte

Para problemas o sugerencias, abrir un issue en el repositorio.

## Licencia

Proyecto desarrollado por **GeoFeedback Chile** - Noviembre 2025
