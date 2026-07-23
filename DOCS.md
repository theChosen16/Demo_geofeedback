# GeoFeedback Chile - Documentación Técnica Completa

> **Versión:** 4.0 | **Fecha:** Julio 2026
> **Demo en vivo:** https://geofeedback.cl

---

## Índice

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Motor Satelital e Índices Espectrales (GEE)](#motor-satelital-e-índices-espectrales-gee)
4. [Enfoques de Análisis Territoriales](#enfoques-de-análisis-territoriales)
5. [GeoBot AI Diagnostic Engine 2.0](#geobot-ai-diagnostic-engine-20)
6. [Base de Datos Geoespacial PostGIS en Railway](#base-de-datos-geoespacial-postgis-en-railway)
7. [APIs e Integraciones Geoespaciales](#apis-e-integraciones-geoespaciales)
8. [Seguridad, QA y CI/CD](#seguridad-qa-y-cicd)
9. [Despliegue y Operación](#despliegue-y-operación)

---

## Descripción del Proyecto

**GeoFeedback Chile** es una plataforma avanzada de inteligencia geoespacial y teledetección satelital que procesa datos de observación de la Tierra a escala planetaria mediante **Google Earth Engine™ Enterprise**, traduciéndolos en mapas dinámicos y reportes ejecutivos impulsados por Inteligencia Artificial (**Google Gemini AI**).

---

## Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             Frontend (React 19 + Vite)                           │
│  - Rediseño "Enfoques Primero" & Matriz Informativa Científica                    │
│  - Visor Geoespacial interactivo con Google Maps JS API                           │
│  - Renderizado Enriquecido de GeoBot (GeoBotResponseViewer)                       │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          │ HTTP / REST API (JSON)
┌─────────────────────────────────────────▼────────────────────────────────────────┐
│                                 Backend (FastAPI)                                │
│  - /api/v1/analyze        → Enrutamiento de análisis geoespaciales               │
│  - /api/v1/chat/interpret → Motor de diagnóstico de GeoBot IA                    │
│  - /api/v1/chat/chat      → Chatbot conversacional interactivo                   │
│  - /api/v1/stats          → Métricas públicas de observabilidad                 │
└────────────────────┬────────────────────┬───────────────────────┬────────────────┘
                     │                    │                       │
┌────────────────────▼──────┐ ┌───────────▼──────────┐ ┌───────────▼───────────┐
│ Google Earth Engine (GEE) │ │  Redis Cache Server  │ │ Railway PostGIS DB    │
│  - Sentinel-2 MSI L2A     │ │  - Caché de análisis │ │  - Esquema metadata   │
│  - Copernicus DEM GLO-30  │ │  - Rate Limiting     │ │  - Historial & Users  │
└───────────────────────────┘ └──────────────────────┘ └───────────────────────┘
```

---

## Motor Satelital e Índices Espectrales (GEE)

La plataforma calcula **15 capas e índices satelitales/topográficos** procesando bandas multiespectrales de Sentinel-2 y el modelo de elevación digital Copernicus DEM GLO-30:

### 1. Índices Espectrales de Vegetación y Clorofila
- **NDVI (Normalized Difference Vegetation Index)**: `(B8 - B4) / (B8 + B4)`  
  *Evaluación de densidad foliar y salud vegetacional.*
- **EVI (Enhanced Vegetation Index)**: `2.5 * ((B8 - B4) / (B8 + 6.0*B4 - 7.5*B2 + 1.0))`  
  *Mayor sensibilidad en doseles foliares densos y corrección de efectos atmosféricos.*
- **SAVI (Soil Adjusted Vegetation Index)**: `((B8 - B4) / (B8 + B4 + 0.5)) * 1.5`  
  *Ajustado para eliminar la influencia del suelo en zonas áridas y semiáridas.*
- **NDRE (Normalized Difference Red Edge)**: `(B8 - B5) / (B8 + B5)`  
  *Medición de contenido de clorofila y nitrógeno para agricultura de precisión.*

### 2. Índices de Agua y Humedad
- **NDWI (Normalized Difference Water Index)**: `(B3 - B8) / (B3 + B8)`  
  *Detección de agua superficial en ríos, embalses y lagos.*
- **MNDWI (Modified NDWI)**: `(B3 - B11) / (B3 + B11)`  
  *Identificación de agua con supresión del ruido de construcciones urbanas.*
- **NDMI (Normalized Difference Moisture Index)**: `(B8 - B11) / (B8 + B11)`  
  *Estrés hídrico y contenido de humedad en la canopia vegetacional.*

### 3. Índices de Suelo, Incendios y Huella Urbana
- **NBR (Normalized Burn Ratio)**: `(B8 - B12) / (B8 + B12)`  
  *Severidad de cicatrices de incendios forestales y riesgo de combustión.*
- **NDBI (Normalized Difference Built-up Index)**: `(B11 - B8) / (B11 + B8)`  
  *Identificación de áreas construidas, infraestructura y pavimento.*
- **BSI (Bare Soil Index)**: `((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2))`  
  *Exposición de suelo desnudo, erosión y áreas despejadas.*

### 4. Capas Topográficas y Ambientales
- **DEM GLO-30**: Elevación topográfica sobre el nivel del mar (Copernicus DEM 30m).
- **Slope**: Pendiente del terreno medida en grados (°).
- **Aspect**: Orientación de ladera (Aspect en °) para potencial solar.
- **AQI**: Calidad del Aire en tiempo real (Google Air Quality API).
- **LST**: Temperatura Superficial Terrestre (Land Surface Temperature).

---

## Enfoques de Análisis Territoriales

El usuario ya no selecciona capas individuales manualmente; la plataforma funciona bajo el modelo **"Enfoques Primero"**:

| Enfoque | Propósito Técnico | Capas Activadas Automáticamente |
| :--- | :--- | :--- |
| **Agroindustria** | Monitoreo de cultivos, clorofila y estrés hídrico. | `ndvi`, `ndmi`, `savi`, `ndre`, `bsi` |
| **Minería Sostenible** | Control de expansión de faenas y erosión. | `ndvi`, `ndwi`, `bsi`, `ndbi`, `elevation` |
| **Energías Renovables** | Factibilidad solar y gradientes de ladera. | `solar`, `elevation`, `aspect`, `ndbi` |
| **Desarrollo Inmobiliario** | Uso de suelo urbano e islas de calor. | `ndbi`, `elevation`, `lst`, `mndwi` |
| **Riesgo de Incendio** | Evaluación de severidad y combustible forestal. | `nbr`, `ndmi`, `ndvi`, `elevation`, `lst` |
| **Riesgo de Inundación** | Cuerpos de agua y acumulación en zonas bajas. | `mndwi`, `ndwi`, `elevation`, `ndbi` |
| **Gestión Hídrica** | Monitoreo de embalses y humedad de suelos. | `ndwi`, `mndwi`, `ndmi`, `ndvi` |
| **Calidad Ambiental** | Auditoría foliar, calidad de aire e impacto. | `evi`, `ndvi`, `ndmi`, `aqi`, `bsi` |
| **Planificación Territorial** | Topografía, aptitud de suelos y construcción. | `elevation`, `ndbi`, `bsi`, `ndvi` |

---

## GeoBot AI Diagnostic Engine 2.0

El motor de diagnóstico de **GeoBot** estructura automáticamente las interpretaciones satelitales en 4 secciones delimitadas:

1. **📌 FICHA RESUMEN Y CONTEXTO SATELITAL**: Muestra ubicación, enfoque, satélite (Sentinel-2 L2A) y la fecha real de la toma.
2. **📊 MATRIZ TÉCNICA DE ÍNDICES Y ESTADOS**: Mapeo directo de métricas con badges de estado (🟢 Saludable/Óptimo, 🟡 Moderado/Atención, 🔴 Crítico/Alto Riesgo).
3. **🌱 EXPLICACIÓN LIMPIA TERRITORIAL**: Interpretación en lenguaje claro sobre la condición del suelo, agua y vegetación.
4. **🎯 RECOMENDACIONES TÁCTICAS**: Acciones prioritarias sugeridas para la toma de decisiones.

---

## Base de Datos Geoespacial PostGIS en Railway

La persistencia de datos relacionales y geoespaciales se administra en PostgreSQL con la extensión **PostGIS 3.7** activa bajo el esquema `metadata`:

- **`metadata.users`**: Identidad y cuentas de usuario (autenticación Google OAuth2).
- **`metadata.user_analyses`**: Historial de análisis ejecutados (`coordinates` como `Geometry(POINT, 4326)`, `indices` en `JSONB`, `approach`, `chart_data`).
- **`metadata.user_alerts`**: Registro de alertas automatizadas configurables.
- **`metadata.api_usage_logs`**: Logs de uso geoespaciales por coordenadas y endpoint.
- **`metadata.page_visits`**: Métricas anónimas de trafico y observabilidad.

---

## Seguridad, QA y CI/CD

- **Dependabot & Vulneraciones**: 0 alertas activas. Dependencia `@playwright/test` y contenedores CI sincronizados a versión `v1.56.0` (CVE-2025-59288 resuelto).
- **Suite de Pruebas**: 49 tests unitarios y de integración en FastAPI (`pytest tests/`).
- **Control de Calidad UI/UX**: Tests E2E de regresión visual y accesibilidad WCAG 2.1 AA en Playwright Container.
- **Protocolo Git (AGENTS.md)**: Integración continua estricta mediante ramas de feature (`feat/`, `fix/`, `chore/`), semántica de commits y PR merge vía `gh pr merge --squash --delete-branch`.

---

_Última actualización: Julio de 2026_
