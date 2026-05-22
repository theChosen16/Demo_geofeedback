# GeoFeedback Chile - Documentación Técnica

> **Versión:** 3.4 | **Fecha:** Mayo 2026 (UI/UX)
> **Demo en vivo:** https://geofeedback.cl

---

## Índice

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura](#arquitectura)
3. [APIs Integradas](#apis-integradas)
4. [Índices Satelitales](#índices-satelitales)
5. [Configuración de Railway](#configuración-de-railway)
6. [Seguridad y Auditoría](#seguridad-y-auditoría)
7. [Transparencia Metodológica](#transparencia-metodológica)
8. [Servicios y Licenciamiento](#servicios-y-licenciamiento)
9. [Operación Analytics y Contador Público](#operación-analytics-y-contador-público)
10. [CI/CD y Validación](#cicd-y-validación)

---

## Descripción del Proyecto

GeoFeedback Chile es una plataforma de inteligencia territorial que transforma datos satelitales en mapas de riesgo y herramientas de gestión para Chile. Ofrece capacidades de **Google Earth Engine (GEE)** para uso comercial mediante un modelo de suscripción gestionada.

### Stack Tecnológico

| Componente | Tecnología                       |
| ---------- | -------------------------------- |
| Backend    | Python 3.11 + Flask              |
| AI         | Google Gemini 3.5 Flash          |
| Satélite   | Google Earth Engine (Sentinel-2) |
| Mapas      | Google Maps JavaScript API       |
| Deploy     | Railway (Docker)                 |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                   │
│  - Google Maps con AdvancedMarkerElement                │
│  - Diseño Mobile First (Full-Width Map & Inputs)        │
│  - Modal de interpretación con escalas                  │
│  - Chat sidebar responsivo con Gemini AI                │
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

- **Uso:** Procesamiento de imágenes Sentinel-2 a escala planetaria
- **Modalidad:** Comercial (mediante suscripción GeoFeedback) y Research
- **Capacidades:** Earth Engine Compute Units (EECU) gestionadas
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

- **Modelo:** gemini-3.5-flash
- **Uso:** Interpretación de análisis, chatbot
- **SDK:** google-genai >= 1.0.0
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

### Física de los Índices Espectrales

Los índices funcionan gracias a las propiedades de absorción y reflexión de la luz:

| Índice   | Fenómeno Físico                                                              |
| -------- | ---------------------------------------------------------------------------- |
| **NDVI** | Clorofila absorbe luz roja (~680nm), estructura celular mesófilo refleja NIR |
| **NDWI** | Agua absorbe NIR, refleja luz verde                                          |
| **NDMI** | Agua en tejidos absorbe SWIR, NIR reflejado por estructura celular           |

### Sentinel-2 - Operadores y Costos

| Aspecto            | Información                                               |
| ------------------ | --------------------------------------------------------- |
| Operador           | ESA (Agencia Espacial Europea) - Programa Copernicus (UE) |
| Satélites          | Sentinel-2A (2015), 2B (2017), 2C (2024)                  |
| Costo construcción | ~€200 millones por satélite                               |
| Costo operación    | ~€25 millones/año                                         |
| Acceso datos       | **Gratuito y abierto**                                    |

> **Nota:** Sentinel-2 es multiespectral (13 bandas). ESA desarrolla CHIME con +200 bandas hiperespectrales.

---

## Configuración y Operación en Railway

La plataforma **GeoFeedback Chile** está diseñada para ejecutarse sobre una arquitectura escalable y moderna en **Railway**. El ecosistema productivo se integra de forma nativa con los siguientes servicios de Railway:

*   **Demo_geofeedback (Flask API):** El servicio de backend principal que procesa la lógica satelital y de IA.
*   **PostGIS:** Base de datos relacional PostgreSQL con extensiones espaciales PostGIS para el cálculo de riesgos geométricos.
*   **Redis:** Caché de alto rendimiento utilizado para el limitador de peticiones híbrido (*Rate Limiter*).
*   **Grafana Stack (Prometheus, Loki, Tempo, Grafana):** Pila de observabilidad y telemetría en tiempo real que ingesta de forma nativa los registros estructurados del API.

---

### Variables de Entorno Requeridas

Estas variables deben configurarse en el panel de **Railway → Service → Variables** del servicio `Demo_geofeedback`:

| Variable | Descripción | ¿Requerida? |
| :--- | :--- | :--- |
| `DATABASE_URL` | Inyectada automáticamente por Railway al conectar el servicio de PostGIS. Contiene las credenciales de conexión. | **Sí (Automática)** |
| `REDIS_URL` | Inyectada automáticamente al conectar el servicio Redis. Habilita la caché y rate-limiting centralizado. | **Sí (Automática)** |
| `GOOGLE_MAPS_API_KEY` | Clave API de Google Maps Platform con restricciones para el dominio productivo. | **Sí** |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Contenido de texto **completo** (JSON sin saltos de línea) de tu archivo `service-account-key.json` de Google Earth Engine. | **Sí** |
| `GEMINI_API_KEY` | Clave de API de Google AI Studio para las consultas automatizadas a Gemini 3. | **Sí** |
| `PORT` | Puerto asignado de forma dinámica por Railway para exponer la aplicación (por defecto `5000`). | **Sí (Automática)** |
| `RAILWAY_ENVIRONMENT` | Seteada automáticamente por Railway (ej. `production` o `staging`). | **Sí (Automática)** |

---

### Mecanismos de Compilación y Configuración (*Config as Code*)

Para brindar soporte integral ante cualquier flujo de trabajo, el repositorio incluye dos formas compatibles de despliegue:

#### A. Despliegue en la Raíz (Predeterminado y Recomendado)
Cuando Railway construye desde la raíz del repositorio, utiliza el archivo [Dockerfile](file:///c:/Users/alean/Desktop/Geofeedback/Demo/Dockerfile) y el archivo [railway.toml](file:///c:/Users/alean/Desktop/Geofeedback/Demo/railway.toml) ubicados en la raíz.
*   El `Dockerfile` de la raíz copia `api/requirements.txt`, instala todas las dependencias y traslada el código de `api/` y `scripts/` al directorio de trabajo `/app`.
*   Esto asegura una construcción inmediata sin necesidad de alterar los ajustes de ruta en el GUI de Railway.

#### B. Despliegue en Subdirectorio (`api/`)
Si has configurado explícitamente `api` como el *Root Directory* de tu servicio en el panel de Railway, la plataforma utilizará de forma aislada [api/Dockerfile](file:///c:/Users/alean/Desktop/Geofeedback/Demo/api/Dockerfile) y [api/railway.toml](file:///c:/Users/alean/Desktop/Geofeedback/Demo/api/railway.toml). Ambos están optimizados con los mismos límites de memoria para el tier gratuito (512MB RAM).

---

### Uso de la CLI de Railway para Operaciones de Producción

La CLI oficial de Railway permite interactuar de forma segura con la infraestructura de producción directamente desde tu consola local de Windows.

#### 1. Autenticación y Conexión al Proyecto
Inicia sesión en tu cuenta y vincula tu consola local con el proyecto productivo en Railway:
```powershell
# Iniciar sesión desde el navegador
railway login

# Vincular la terminal con el proyecto productivo
railway link
```
*Durante `railway link`, selecciona tu Workspace (`thechosen16's Projects`), el proyecto (`thorough-emotion`), el entorno (`production`), y el servicio (`Demo_geofeedback`).*

#### 2. Inicialización Segura de la Base de Datos (PostGIS)
El script de inicialización [init_railway_db.py](file:///c:/Users/alean/Desktop/Geofeedback/Demo/scripts/init_railway_db.py) configura todo el esquema espacial de PostGIS, funciones almacenadas y tablas de métricas de analítica.

Para ejecutar este script contra la base de datos real de producción **sin exponer credenciales ni contraseñas en texto plano**, utiliza el comando `railway run`:
```powershell
railway run python scripts/init_railway_db.py
```
> [!NOTE]
> `railway run` consulta las variables del entorno productivo asociadas (como `DATABASE_URL`), las inyecta de forma dinámica en el entorno de ejecución temporal de tu terminal de Windows y ejecuta el script local contra la base de datos remota de Railway de forma totalmente segura.

El script de inicialización realiza la carga secuencial de los siguientes recursos:
1.  `scripts/sql/01_setup_postgis_schema.sql` (Extensiones, esquemas espaciales y geometría)
2.  `scripts/sql/04_create_functions.sql` (Funciones de cruce geográfico optimizadas)
3.  `scripts/sql/06_create_analytics_tables.sql` (Tablas `metadata.page_visits` y `metadata.api_usage_logs` para el visor de visitas)

---

### Monitoreo y Observabilidad en Tiempo Real

El sistema está configurado para entregar logs enriquecidos e integrarse de manera automática con tu panel de **Grafana Stack** (Loki / Prometheus):

1.  **Logs en formato JSON:** El API no emite texto plano convencional; en su lugar, utiliza la función `log_event()` para estructurar todos los eventos significativos en strings JSON de una sola línea (ej. `{"timestamp": "...", "event": "api_usage", "status": "success"}`).
2.  **Integración con Loki:** Promtail ingesta y parsea nativamente estas líneas de JSON desde el contenedor de Railway. Esto te permite crear tableros personalizados de Grafana basados en los campos JSON (como IP enmascarada, código de respuesta HTTP, tipo de análisis y tiempo de respuesta) sin necesidad de complejos analizadores de expresiones regulares.
3.  **Endpoint de Observabilidad Dedicado:**
    El API expone la ruta `GET /api/v1/observability` que analiza de forma holística el estado del sistema. Si algún servicio crítico (como PostGIS o Google Earth Engine) sufre una degradación, el endpoint responde con código de estado HTTP `503 Service Unavailable`, permitiendo que las alertas o sistemas de orquestación de Railway detecten y manejen el incidente de inmediato.

---

## Seguridad y Auditoría

**Auditoría Abril 2026: ✅ PASADO — 0 alertas activas** ([ver historial completo](./SECURITY_AUDIT.md))

### Correcciones Aplicadas (Abril 2026)

| Vulnerabilidad | Archivo | Estado |
|----------------|---------|--------|
| Flask CVE-2026-27205 | `requirements.txt` | ✅ Upgrade `>=3.1.3` |
| SQL Injection (`lat`/`lng`) | `database.py` | ✅ Query parametrizado |
| Clear-text logging (password taint) | `config.py` | ✅ Variables descontaminadas |
| Stack trace en respuestas API | `app.py` (×3) | ✅ Mensajes genéricos |
| Google API Key expuesta en git | Historial | ✅ Reescrito con `git-filter-repo` |

### Gestión de Credenciales

- **Local:** Se usa `service-account-key.json` (protegido por `.gitignore`) y `.env`.
- **Producción:** Credenciales exclusivamente vía Variables de Entorno (ver `gee_config.py`).
- **Código:** Sin defaults inseguros en `config.py`.

### Configuración GCP - API Key Maps Platform

- **Restricciones de dominio activas:** `browserKeyRestrictions` — solo acepta requests desde `geofeedback.cl` y subdominos Railway.
- **Restricciones de API:** Sin límite (configurado vía CLI, la UI de GCP Maps Platform no expone esta opción).
- **Historial limpio:** Key rotada y commits anteriores reescritos.

### Privacidad de Datos

- Las coordenadas de usuario no se almacenan de forma persistente.
- PII (Información Personal) se maneja con logs mínimos.
- API Keys de frontend se inyectan en tiempo de ejecución (servidor-side rendering).

---

## Transparencia Metodológica

### Frecuencia de Datos (Sentinel-2)

- **Licencia Research (Demo):** Imágenes históricas recientes (no tiempo real).
- **Frecuencia de Revisita:** 5 días en el ecuador, **2-3 días en Chile** debido al solapamiento orbital.
- **Licencia Comercial:** Permite ingesta de imágenes propias o satélites de baja latencia para "Tiempo Real".

### Cálculo de Índices

Los valores presentados en el dashboard son **promedios espaciales** calculados sobre el área circular seleccionada (A = π \* r²).

- **NDVI:** Promedio de vigor vegetal en el radio de análisis.
- **Alertas:** Basadas en umbrales predefinidos sobre estos promedios.

---

---

## Servicios y Licenciamiento

### Modelo de Negocio (GEE Comercial)

Google Earth Engine requiere licencias Enterprise para uso comercial. GeoFeedback actúa como intermediario tecnológico facilitando:

1.  **Legalidad:** Licenciamiento comercial incluido en planes de suscripción.
2.  **Infraestructura:** Gestión de cuotas EECU y almacenamiento en la nube.
3.  **Privacidad:** Ingesta de datos privados (drones/satélite propio) en planes Profesional/Enterprise.

### Planes Disponibles

| Plan            | Enfoque            | GEE Capacidad       | Ideal para                |
| :-------------- | :----------------- | :------------------ | :------------------------ |
| **Monitoreo**   | Análisis estándar  | Cloud API Básico    | PyMEs agrícolas, Forestal |
| **Profesional** | Control total      | High-EECU + Ingesta | Consultoras, Minería      |
| **Ingeniería**  | Servicios a medida | Custom              | EIA/DIA, Gobierno         |

---

## Operación Analytics y Contador Público

### Endpoint público

- `GET /api/v1/stats` retorna:

```json
{
  "visits": 0,
  "analyses": 0
}
```

### Flujo de datos

1. El frontend solicita `/api/v1/stats` al cargar la home.
2. El backend consulta `metadata.page_visits` y `metadata.api_usage_logs`.
3. El contador anima valores y, si ambos son 0, renderiza `0` explícitamente (sin placeholders).
4. Si Railway devuelve `undefined_table`, `api/database.py` crea de forma lazy el schema analytics acotado y reintenta la operación una vez.

### Registro de eventos

- Visitas: se registran en la ruta `/` vía `database.log_visit(...)`.
- Análisis exitosos: se registran en `/api/v1/analyze` vía `database.log_analysis(...)`.

### Observability y monitoreo

- `GET /api/v1/observability` combina checks críticos (`database`, `analytics`, `google_earth_engine`, `google_maps_key`) con checks opcionales (`gemini`, `redis`).
- Si algún check crítico falla, el endpoint responde `503` con payload diagnóstico en vez de degradar silenciosamente.
- `scripts/monitor_deploy.py` usa librería estándar, soporta `--url` y `--once`, y falla si observability reporta estado degradado o analytics no está listo.
- `GET /robots.txt` evita ruido de `404` en logs y simplifica la lectura operativa de Railway.

## CI/CD y Validación

### Workflow de GitHub Actions

- Archivo: `.github/workflows/ci.yml`
- Triggers: `push` y `pull_request` sobre `master` y `main`
- Etapas:
  - Instalación de dependencias (`api/requirements.txt`)
  - Validación de sintaxis (`python -m compileall api scripts tests`)
  - Regresión dedicada de observability (`test_public_stats_and_routes.py`)
  - Validación de la CLI de monitoreo (`python scripts/monitor_deploy.py --help`)
  - Pruebas (`python -m unittest discover -s tests -p "test_*.py" -v`)

### Pruebas de regresión incluidas

- Contrato de `GET /api/v1/stats` (claves y tipos)
- Fallback de stats cuando falla BD
- Contrato saludable/degradado de `GET /api/v1/observability`
- Redirects de UX (`/api/` y `/contact`)
- `GET /robots.txt` sin `404`
- Presencia del fix de render en cero y del bootstrap analytics

---

_© 2025-2026 GeoFeedback Chile - Todos los derechos reservados_
