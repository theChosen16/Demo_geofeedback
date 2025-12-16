# GeoFeedback Chile - Documentación Técnica

> **Versión:** 3.0 | **Fecha:** Diciembre 2025
> **Demo en vivo:** https://geofeedback.cl

---

## Índice

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura](#arquitectura)
3. [APIs Integradas](#apis-integradas)
4. [Índices Satelitales](#índices-satelitales)
5. [Configuración de Railway](#configuración-de-railway)
6. [Variables de Entorno](#variables-de-entorno)
7. [Endpoints de la API](#endpoints-de-la-api)

---

## Descripción del Proyecto

GeoFeedback Chile es una plataforma de inteligencia territorial que transforma datos satelitales en mapas de riesgo y herramientas de gestión para Chile.

### Stack Tecnológico

| Componente | Tecnología                       |
| ---------- | -------------------------------- |
| Backend    | Python 3.11 + Flask              |
| AI         | Google Gemini 2.5 Flash          |
| Satélite   | Google Earth Engine (Sentinel-2) |
| Mapas      | Google Maps JavaScript API       |
| Deploy     | Railway (Docker)                 |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                   │
│  - Google Maps con AdvancedMarkerElement                │
│  - PlaceAutocompleteElement para búsqueda               │
│  - Modal de interpretación con escalas                  │
│  - Chat sidebar con Gemini AI                           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   Backend (Flask)                       │
│  /api/v1/analyze  → Google Earth Engine                 │
│  /api/v1/interpret → Gemini AI                          │
│  /api/v1/chat     → Gemini AI (conversacional)          │
└─────────────────────────────────────────────────────────┘
```

---

## APIs Integradas

### Google Earth Engine

- **Uso:** Procesamiento de imágenes Sentinel-2
- **Índices:** NDVI, NDWI, NDMI
- **Datos terreno:** SRTM v4 (elevación, pendiente)
- **Autenticación:** Service Account JSON

### Maps JavaScript API

- **Versión:** Weekly (última estable)
- **Características:** AdvancedMarkerElement, mapId
- **Tipo de mapa:** Hybrid (satélite + etiquetas)

### Elevation API

- **Endpoint:** `https://maps.googleapis.com/maps/api/elevation/json`
- **Datos:** Elevación en metros (LMSL)
- **Resolución:** Variable según zoom

### Air Quality API (Actualizado Abril 2024)

- **Endpoint:** `https://airquality.googleapis.com/v1/currentConditions:lookup`
- **Cobertura:** 100+ países, 500x500m resolución
- **Nuevo 2024:** Forecast endpoint (hasta 96 horas)
- **Índices:** 70+ AQIs disponibles

### Solar API (Actualizado 2024)

- **Endpoint:** `https://solar.googleapis.com/v1/buildingInsights:findClosest`
- **Cobertura 2024:** Expandida a Chile, Australia, Europa
- **Datos:** Horas sol/año, potencial fotovoltaico

### Pollen API

- **Endpoint:** `https://pollen.googleapis.com/v1/forecast:lookup`
- **Cobertura:** 65+ países, 1x1km resolución
- **Datos:** Pronóstico 5 días, niveles por tipo de planta

### Places API (New) - GA Febrero 2024

- **Características:**
  - PlaceAutocompleteElement (GA Mayo 2024)
  - 104 nuevos tipos de lugares
  - Campos: priceRange, pureServiceAreaBusiness

### Geocoding API

- **Uso:** Conversión dirección ↔ coordenadas
- **Reverse geocoding:** Click en mapa → nombre del lugar

### Gemini API (AI)

- **Modelo:** gemini-2.5-flash
- **Uso:** Interpretación de análisis, chatbot
- **SDK:** google-generativeai >= 0.3.0
- **Resilencia:** Retry automático con timeout de 30s

---

## Índices Satelitales

### NDVI - Normalized Difference Vegetation Index

```
NDVI = (NIR - Rojo) / (NIR + Rojo)
     = (B8 - B4) / (B8 + B4)

Rango: -1 a +1
> 0.6  → Vegetación densa
> 0.3  → Vegetación moderada
> 0.1  → Vegetación escasa
< 0.1  → Sin vegetación / agua
```

### NDWI - Normalized Difference Water Index

```
NDWI = (Verde - NIR) / (Verde + NIR)
     = (B3 - B8) / (B3 + B8)

Rango: -1 a +1
> 0.3  → Cuerpo de agua
> 0    → Humedad moderada
< 0    → Seco
```

### NDMI - Normalized Difference Moisture Index

```
NDMI = (NIR - SWIR) / (NIR + SWIR)
     = (B8 - B11) / (B8 + B11)

Rango: -1 a +1
> 0.2  → Alta humedad vegetación
< 0    → Estrés hídrico
```

---

## Configuración de Railway

### Variables de Entorno Requeridas

| Variable                              | Descripción                            |
| ------------------------------------- | -------------------------------------- |
| `GOOGLE_MAPS_API_KEY`                 | API Key para Maps Platform             |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Contenido del service-account-key.json |
| `GEMINI_API_KEY`                      | API Key de Gemini AI                   |
| `PORT`                                | (Automático) Puerto del servidor       |

### Configuración de Build

```toml
# railway.toml
[build]
  builder = "dockerfile"
  dockerfilePath = "api/Dockerfile"

[deploy]
  startCommand = "gunicorn app:app --bind 0.0.0.0:$PORT"
```

---

## Endpoints de la API

### GET /

Landing page con demo interactivo

### GET /api/v1/health

```json
{ "status": "healthy", "service": "GeoFeedback API" }
```

### POST /api/v1/analyze

Análisis territorial con Google Earth Engine

**Request:**

```json
{
  "lat": -33.4489,
  "lng": -70.6693,
  "approach": "agriculture"
}
```

**Response:**

```json
{
  "status": "success",
  "data": {"Vigor Vegetal (NDVI)": "0.45", ...},
  "map_layer": {"url": "https://earthengine.googleapis.com/..."}
}
```

### POST /api/v1/interpret

Interpretación AI de resultados

**Request:**

```json
{
  "results": { "NDVI": "0.45" },
  "approach": "agriculture",
  "location": "Papudo, Chile"
}
```

### POST /api/v1/chat

Chat conversacional con contexto

**Request:**

```json
{
  "message": "¿Qué significa un NDVI de 0.45?",
  "context": {...},
  "history": [...]
}
```

---

## Seguridad

- API Keys almacenadas en variables de entorno (no en código)
- Service Account con permisos mínimos para GEE
- CORS configurado para orígenes permitidos
- Credenciales en .gitignore

---

_© 2025 GeoFeedback Chile - Todos los derechos reservados_
