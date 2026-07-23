# GeoFeedback Chile - Documentación Técnica Completa

> **Versión:** 4.1 | **Fecha:** Julio 2026  
> **Demo en Vivo:** [https://geofeedback.cl](https://geofeedback.cl)  
> **Repositorio Oficial:** [github.com/theChosen16/Demo_geofeedback](https://github.com/theChosen16/Demo_geofeedback)

---

## 📋 Índice

1. [Descripción General del Proyecto](#1-descripción-general-del-proyecto)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Motor Satelital e Índices Espectrales (GEE)](#3-motor-satelital-e-índices-espectrales-gee)
4. [Matriz de Enfoques Territoriales ("Enfoques Primero")](#4-matriz-de-enfoques-territoriales-enfoques-primero)
5. [GeoBot AI Diagnostic Engine 2.0 & Chatbot](#5-geobot-ai-diagnostic-engine-20--chatbot)
6. [Base de Datos Geoespacial PostGIS en Railway](#6-base-de-datos-geoespacial-postgis-en-railway)
7. [Marco Multi-Capa de QA, Evaluación Visual y Auditoría UI/UX](#7-marco-multi-capa-de-qa-evaluación-visual-y-auditoría-uiux)
8. [Seguridad, Privacidad y Hardening](#8-seguridad-privacidad-y-hardening)
9. [Guía de Desarrollo y Despliegue (Local y Railway)](#9-guía-de-desarrollo-y-despliegue-local-y-railway)

---

## 1. Descripción General del Proyecto

**GeoFeedback Chile** es una plataforma avanzada de inteligencia geoespacial y teledetección satelital que procesa datos de observación de la Tierra a escala planetaria mediante **Google Earth Engine™ Enterprise**, traduciéndolos en mapas dinámicos y reportes ejecutivos impulsados por Inteligencia Artificial (**Google Gemini 2.5 Flash**).

La plataforma permite a usuarios técnicos y no técnicos analizar el estado del terreno en cualquier punto geográfico mediante 9 enfoques sectoriales, 15 capas e índices espectrales/topográficos, series temporales ("Pulso Territorial") y un asistente interactivo especializador (**GeoBot AI**).

---

## 2. Arquitectura del Sistema

El sistema adopta una arquitectura desacoplada y orientada a microservicios en contenedor:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             Frontend (React 19 + Vite)                           │
│  - Rediseño "Enfoques Primero" & Matriz Informativa Científica                    │
│  - Visor Geoespacial interactivo con Google Maps JS API                           │
│  - Renderizado Enriquecido de GeoBot (GeoBotResponseViewer)                       │
│  - Graficación de Serie Temporal (Pulso Territorial con Recharts)                 │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          │ HTTP / REST API (JSON)
┌─────────────────────────────────────────▼────────────────────────────────────────┐
│                                 Backend (FastAPI)                                │
│  - /api/v1/analyze        → Enrutamiento de análisis geoespaciales               │
│  - /api/v1/interpret      → Motor de diagnóstico de GeoBot IA                    │
│  - /api/v1/chat           → Chatbot conversacional interactivo                   │
│  - /api/v1/alerts         → Gestión de alertas territoriales                     │
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

## 3. Motor Satelital e Índices Espectrales (GEE)

La plataforma calcula **15 capas e índices satelitales y topográficos** procesando bandas multiespectrales de Sentinel-2 Harmonized (Level-2A) y el modelo de elevación digital Copernicus DEM GLO-30:

### 3.1 Índices Espectrales de Vegetación y Clorofila
- **NDVI (Normalized Difference Vegetation Index)**: `(B8 - B4) / (B8 + B4)`  
  *Evaluación de densidad foliar y salud vegetacional.*
- **EVI (Enhanced Vegetation Index)**: `2.5 * ((B8 - B4) / (B8 + 6.0*B4 - 7.5*B2 + 1.0))`  
  *Mayor sensibilidad en doseles foliares densos y corrección de efectos atmosféricos.*
- **SAVI (Soil Adjusted Vegetation Index)**: `((B8 - B4) / (B8 + B4 + 0.5)) * 1.5`  
  *Ajustado para eliminar la influencia del suelo en zonas áridas y semiáridas.*
- **NDRE (Normalized Difference Red Edge)**: `(B8 - B5) / (B8 + B5)`  
  *Medición de contenido de clorofila y nitrógeno para agricultura de precisión.*

### 3.2 Índices de Agua y Humedad
- **NDWI (Normalized Difference Water Index)**: `(B3 - B8) / (B3 + B8)`  
  *Detección de agua superficial en ríos, embalses y lagos.*
- **MNDWI (Modified NDWI)**: `(B3 - B11) / (B3 + B11)`  
  *Identificación de agua con supresión del ruido de construcciones urbanas.*
- **NDMI (Normalized Difference Moisture Index)**: `(B8 - B11) / (B8 + B11)`  
  *Estrés hídrico y contenido de humedad en la canopia vegetacional.*

### 3.3 Índices de Suelo, Incendios y Huella Urbana
- **NBR (Normalized Burn Ratio)**: `(B8 - B12) / (B8 + B12)`  
  *Severidad de cicatrices de incendios forestales y riesgo de combustión.*
- **NDBI (Normalized Difference Built-up Index)**: `(B11 - B8) / (B11 + B8)`  
  *Identificación de áreas construidas, infraestructura y pavimento.*
- **BSI (Bare Soil Index)**: `((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2))`  
  *Exposición de suelo desnudo, erosión y áreas despejadas.*

### 3.4 Capas Topográficas y Ambientales
- **DEM GLO-30**: Elevación topográfica sobre el nivel del mar (Copernicus DEM 30m).
- **Slope**: Pendiente del terreno medida en grados (°).
- **Aspect**: Orientación de ladera (Aspect en °) para potencial solar.
- **AQI**: Calidad del Aire en tiempo real (Google Air Quality API).
- **LST**: Temperatura Superficial Terrestre (Land Surface Temperature).

### 3.5 Lógica de Filtrado Temporal y Cobertura de Nubes
- **Filtro de Fechas UTC**: Las fechas de fin en consultas a GEE incorporan un margen de `+1 día UTC` (`now(UTC) + 1d`) para asegurar la inclusión de las pasadas satelitales del día de la consulta (compensando el comportamiento exclusivo de `filterDate` en GEE).
- **Umbral de Nubes Adaptativo (50%)**: Se utiliza un límite de 50% de nubes a nivel del tile regional (Granule 100km×100km), lo que garantiza seleccionar la pasada disponible más reciente sin descartar áreas de ROI despejadas.

---

## 4. Matriz de Enfoques Territoriales ("Enfoques Primero")

La interfaz opera bajo la metodología **"Enfoques Primero"**: la selección de un sector industrial activa y configura automáticamente las capas relevantes:

| Enfoque | Propósito Técnico | Capas Activadas Automáticamente |
| :--- | :--- | :--- |
| **🌾 Agroindustria** | Monitoreo de cultivos, clorofila y estrés hídrico. | `ndvi`, `ndmi`, `savi`, `ndre`, `bsi` |
| **⛏️ Minería Sostenible** | Control de expansión de faenas y erosión. | `ndvi`, `ndwi`, `bsi`, `ndbi`, `elevation` |
| **⚡ Energías Renovables** | Factibilidad solar y gradientes de ladera. | `solar`, `elevation`, `aspect`, `ndbi` |
| **🏢 Desarrollo Inmobiliario** | Uso de suelo urbano e islas de calor. | `ndbi`, `elevation`, `lst`, `mndwi` |
| **🔥 Riesgo de Incendio** | Evaluación de severidad y combustible forestal. | `nbr`, `ndmi`, `ndvi`, `elevation`, `lst` |
| **🌊 Riesgo de Inundación** | Cuerpos de agua y acumulación en zonas bajas. | `mndwi`, `ndwi`, `elevation`, `ndbi` |
| **💧 Gestión Hídrica** | Monitoreo de embalses y humedad de suelos. | `ndwi`, `mndwi`, `ndmi`, `ndvi` |
| **🌿 Calidad Ambiental** | Auditoría foliar, calidad de aire e impacto. | `evi`, `ndvi`, `ndmi`, `aqi`, `bsi` |
| **🗺️ Planificación Territorial** | Topografía, aptitud de suelos y construcción. | `elevation`, `ndbi`, `bsi`, `ndvi` |

---

## 5. GeoBot AI Diagnostic Engine 2.0 & Chatbot

El motor de diagnóstico e interpretación alimentado por **Google Gemini 2.5 Flash** estructura automáticamente sus salidas en 4 bloques:

1. **📌 FICHA RESUMEN Y CONTEXTO SATELITAL**: Presenta la ubicación, el enfoque territorial, la constelación satelital (Sentinel-2 MSI Level-2A) y la fecha real de captura.
2. **📊 MATRIZ TÉCNICA DE ÍNDICES Y ESTADOS**: Mapeo numérico de métricas espectrales con badges de nivel de riesgo (🟢 Saludable/Óptimo, 🟡 Moderado/Atención, 🔴 Crítico/Alto Riesgo).
3. **🌱 EXPLICACIÓN LIMPIA TERRITORIAL**: Explicación clara y accesible sobre la condición física del terreno.
4. **🎯 RECOMENDACIONES TÁCTICAS**: Tres acciones sugeridas para orientar la toma de decisiones.

---

## 6. Base de Datos Geoespacial PostGIS en Railway

La persistencia de datos se gestiona en PostgreSQL 16 con la extensión **PostGIS 3.7** bajo el esquema dedicado `metadata`:

- **`metadata.users`**: Cuentas e identidad de usuarios (Google OAuth2).
- **`metadata.user_analyses`**: Historial de análisis ejecutados (`coordinates` como `Geometry(POINT, 4326)`, métricas en `JSONB`, `approach`, `chart_data`).
- **`metadata.user_alerts`**: Sistema de alertas automáticas con notificaciones por correo.
- **`metadata.api_usage_logs`**: Auditoría de uso geoespacial anonimizado.
- **`metadata.page_visits`**: Métricas de uso y observabilidad del servicio.

---

## 7. Marco Multi-Capa de QA, Evaluación Visual y Auditoría UI/UX

GeoFeedback integra una infraestructura de Aseguramiento de Calidad automatizada en 4 niveles:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             Marco Multi-Capa de QA                               │
├──────────────────────────────────────────────────────────────────────────────────┤
│ 1. Auditoría Heurística & Agentes IA    → ui_ux_design_review_agent.py          │
│ 2. Regresión Visual Determinista        → Playwright (pixelmatch)                │
│ 3. Reglas Geométricas & Layout         → layout_rules.spec.ts                   │
│ 4. Accesibilidad WCAG 2.1 AA & LCI     → @axe-core/playwright & Lighthouse CI   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 7.1 Auditoría Heurística & Observador IA
- **Agentes:** `scripts/qa/ui_ux_design_review_agent.py`, `scripts/qa/uisentinel_check.js` y `scripts/qa/gemini_qa_observer.py`.
- **Propósito:** Analizar componentes TSX/CSS verificando jerarquía visual, contraste de color, contraste HSL en modo oscuro y zonas táctiles móviles.

### 7.2 Regresión Visual Determinista (Playwright)
- **Configuración:** `frontend/playwright.config.ts`
- **Pruebas:** `frontend/tests/e2e/visual_regression.spec.ts`
- **Mecanismo:** Comparación de imágenes con `pixelmatch`, enmascaramiento dinámico de elementos cambiantes (mapas, animaciones) y soporte de resoluciones (Escritorio HD, Tablet, Móvil).
- **ChatOps Snapshot Update:** Escribir `/approve-snapshots` en un PR ejecuta `.github/workflows/approve_snapshots.yml` para actualizar las imágenes de referencia automáticamente.

### 7.3 Verificación de Layout y Reglas Geométricas
- **Pruebas:** `frontend/tests/e2e/layout_rules.spec.ts`
- **Propósito:** Validar ausencia de desbordamiento horizontal (`overflow-x`), visibilidad de navegación y proporciones de contenedores sin depender de frágiles capturas de píxeles.

### 7.4 Accesibilidad WCAG 2.1 AA & Rendimiento Web
- **Accesibilidad:** `frontend/tests/e2e/accessibility.spec.ts` utilizando `@axe-core/playwright`.
- **Rendimiento:** Presupuestos Core Web Vitals en `.lighthouserc.json` integrados en CI/CD.

---

## 8. Seguridad, Privacidad y Hardening

- **0 Alertas en Dependabot**: Dependencias del proyecto sincronizadas y sin vulnerabilidades activas (CVE-2025-59288 resuelto).
- **Control de Inyección SQL & XSS**: ORM parametrizado (SQLModel/SQLAlchemy) y renderizado JSX en frontend sin `dangerouslySetInnerHTML`.
- **Protección de Datos & IP Anónima**: Anonimización de direcciones IP mediante hash HMAC-SHA256 con salt dinámico.
- **Rate Limiting**: Limitador Redis-first en endpoints críticos (`/analyze`, `/interpret`, `/chat`, `/contact`, `/status`).

---

## 9. Guía de Desarrollo y Despliegue (Local y Railway)

### 9.1 Entorno Local

#### Backend (FastAPI + Celery)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # En Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```

#### Suite de Pruebas
```bash
# Tests unitarios del backend
pytest tests/

# Pruebas E2E de frontend (Playwright)
cd frontend
npm run test:e2e
```

### 9.2 Despliegue en Railway

1. **Configuración Automática**: Railway detecta `Dockerfile` y `railway.toml`.
2. **Servicios de Base de Datos**: Vincula las instancias de **PostGIS** (`POSTGRES_URL`) y **Redis** (`REDIS_URL`).
3. **Inicialización de Base de Datos**:
   ```bash
   railway run python scripts/init_railway_db.py
   ```

---

_Última actualización: Julio de 2026_
