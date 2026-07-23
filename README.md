# GeoFeedback Chile 🌎

**Plataforma de Inteligencia Territorial e Teledetección Satelital con IA**

[![Demo](https://img.shields.io/badge/Demo-geofeedback.cl-blue)](https://geofeedback.cl)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-red)](#)
[![Security](https://img.shields.io/badge/Security-0%20alertas%20activas-brightgreen)](./SECURITY.md)
[![CI](https://github.com/theChosen16/Demo_geofeedback/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/theChosen16/Demo_geofeedback/actions/workflows/ci.yml)

---

## 🚀 Demo en Vivo

👉 **[https://geofeedback.cl](https://geofeedback.cl)**

---

## ✨ Características Principales

- 🛰️ **Motor Geoespacial Comercial**: Integración nativa con **Google Earth Engine™ Enterprise** y constelación **Sentinel-2 MSI (Level-2A)** y **Copernicus DEM GLO-30**.
- 🎯 **Rediseño "Enfoques Primero"**: Interfaz optimizada centrada en 9 enfoques territoriales con selección y conmutación automática de capas satelitales.
- 📊 **Catálogo de 15 Capas e Índices Satelitales/Topográficos**: `NDVI`, `NDWI`, `MNDWI`, `NDMI`, `NBR`, `NDBI`, `SAVI`, `EVI`, `BSI`, `NDRE`, `DEM GLO-30`, `Slope`, `Aspect`, `AQI`, `LST`.
- 🤖 **GeoBot AI Assistant 2.0**: Diagnósticos estructurados en 4 secciones impulsados por **Google Gemini 2.5 Flash**.
- 📈 **Pulso Territorial**: Evolución histórica mensual de índices espectrales (NDVI, NDWI, NDMI).
- 🗄️ **Base de Datos Geoespacial PostGIS en Railway**: Almacenamiento relacional (`metadata` schema) con PostGIS 3.7.
- 📱 **100% Mobile & Touch Optimized**: UI con glassmorphism, modo oscuro y micro-animaciones fluidas.
- 🛡️ **Seguridad & Calidad Auditada**: 0 alertas activas en Dependabot, pruebas E2E en Playwright y presupuestos de rendimiento en Lighthouse CI.

---

## 🏛️ Enfoques de Análisis

| Enfoque | Descripción | Capas e Índices Auto-seleccionados |
| :--- | :--- | :--- |
| 🌾 **Agroindustria** | Monitoreo de vigor, nitrógeno y estrés hídrico en cultivos. | `NDVI`, `NDMI`, `SAVI`, `NDRE`, `BSI` |
| ⛏️ **Minería Sostenible** | Control de expansión de faenas, polvo y huella hídrica. | `NDVI`, `NDWI`, `BSI`, `NDBI`, `DEM` |
| ⚡ **Energías Renovables** | Factibilidad de parques solares y gradientes topográficos. | `SOLAR`, `DEM`, `ASPECT`, `NDBI` |
| 🏢 **Desarrollo Inmobiliario** | Análisis de uso de suelo, islas de calor y expansión urbana. | `NDBI`, `DEM`, `LST`, `MNDWI` |
| 🔥 **Riesgo de Incendio** | Evaluación de severidad de fuego y estrés de vegetación. | `NBR`, `NDMI`, `NDVI`, `DEM`, `LST` |
| 🌊 **Riesgo de Inundación** | Identificación de cuerpos de agua y zonas bajas de acumulación. | `MNDWI`, `NDWI`, `DEM`, `NDBI` |
| 💧 **Gestión Hídrica** | Monitoreo de reservorios, embalses y humedad en suelos. | `NDWI`, `MNDWI`, `NDMI`, `NDVI` |
| 🌿 **Calidad Ambiental** | Auditoría ambiental, calidad del aire y cobertura foliar. | `EVI`, `NDVI`, `NDMI`, `AQI`, `BSI` |
| 🗺️ **Planificación Territorial** | Catastro topográfico, pendientes y aptitud de suelos. | `DEM`, `NDBI`, `BSI`, `NDVI` |

---

## 📚 Documentación Técnica

Consulte **[DOCS.md](./docs/DOCS.md)** para la documentación técnica completa:
- Arquitectura del Backend FastAPI y Celery Worker
- Integración con Google Earth Engine Enterprise API y fórmulas espectrales
- Estructura de esquemas y tablas PostGIS en Railway
- Marco Multi-Capa de QA, Regresión Visual y Accesibilidad
- Protocolo de seguridad y despliegue en Railway

---

## 👤 Autor

**Alejandro Hernández Aguirre**
- [LinkedIn](https://www.linkedin.com/in/alejandro-hern%C3%A1ndez-aguirre-bb8967246/)
- [GitHub](https://github.com/theChosen16)

---

_Última actualización: Julio de 2026_
