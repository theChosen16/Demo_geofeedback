# GeoFeedback Chile 🌎

**Plataforma de Inteligencia Territorial e Teledetección Satelital con IA**

[![Demo](https://img.shields.io/badge/Demo-geofeedback.cl-blue)](https://geofeedback.cl)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-red)](#)
[![Security](https://img.shields.io/badge/Security-0%20alertas%20activas-brightgreen)](./SECURITY_AUDIT.md)
[![CI](https://github.com/theChosen16/Demo_geofeedback/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/theChosen16/Demo_geofeedback/actions/workflows/ci.yml)

---

## 🚀 Demo en Vivo

**https://geofeedback.cl**

---

## ✨ Características Principales

- 🛰️ **Motor Geoespacial Comercial**: Integración nativa con **Google Earth Engine™ Enterprise** y constelación **Sentinel-2 MSI (Level-2A)** y **Copernicus DEM GLO-30**.
- 🎯 **Rediseño "Enfoques Primero"**: Interfaz optimizada centrada en 9 enfoques territoriales con selección y conmutación automática de capas satelitales.
- 📊 **Catálogo de 15 Capas e Índices Satelitales/Topográficos**:
  1. **NDVI**: Índice de Vegetación
  2. **NDWI**: Agua Superficial
  3. **MNDWI**: Agua Modificada Urbana
  4. **NDMI**: Humedad Canopia
  5. **NBR**: Severidad de Incendio Forestal
  6. **NDBI**: Huella de Suelo Construido/Urbano
  7. **SAVI**: Vegetación Ajustada para Zonas Áridas
  8. **EVI**: Vegetación de Dosel Denso
  9. **BSI**: Suelo Desnudo / Exposición y Erosión
  10. **NDRE**: Clorofila / Agricultura de Precisión
  11. **DEM GLO-30**: Elevación Topográfica
  12. **Slope**: Pendiente del Terreno (°)
  13. **Aspect**: Orientación de Ladera (Aspect °)
  14. **AQI**: Calidad del Aire (Google Air Quality API)
  15. **LST**: Temperatura Superficial Terrestre
- 🤖 **GeoBot AI Assistant 2.0**: Asistente con diagnósticos estructurados en 4 secciones (Ficha Resumen, Matriz Técnica con badges 🟢🟡🔴, Explicación Limpia Territorial y Recomendaciones Tácticas).
- 🗄️ **Base de Datos PostGIS en Railway**: Almacenamiento geoespacial relacional (`metadata` schema, `user_analyses`, `users`, `user_alerts`, `api_usage_logs`).
- 📱 **100% Mobile & Touch Optimized**: UI ultra-moderna con glassmorphism, modo oscuro y animaciones fluidas.
- 🛡️ **Seguridad & Calidad Auditada**: 0 alertas activas en Dependabot (Playwright v1.56.0), suite de tests E2E y presupuesto de rendimiento en Lighthouse CI.

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

Consulte [DOCS.md](./DOCS.md) para acceder a la documentación técnica detallada:
- Arquitectura del Backend y Worker Asíncrono
- Integración con Google Earth Engine Enterprise API
- Fórmulas matemáticas de los 15 índices espectrales
- Estructura de esquemas y tablas PostGIS en Railway
- Protocolo de seguridad y automatización CI/CD

---

## 🛠️ Despliegue en Railway

El proyecto está listo para despliegue de cero-configuración en Railway:

1. **Servicio Principal**: Vincula el repositorio a Railway. El proyecto detectará automáticamente el `Dockerfile` y `railway.toml`.
2. **Bases de Datos**: Conecta los servicios oficiales de **PostGIS** (`POSTGRES_URL`) y **Redis** (`REDIS_URL`).
3. **Verificación de Base de Datos**:
   ```powershell
   railway run python scripts/init_railway_db.py
   ```

---

## 👤 Autor

**Alejandro Hernández Aguirre**
- [LinkedIn](https://www.linkedin.com/in/alejandro-hern%C3%A1ndez-aguirre-bb8967246/)
- [GitHub](https://github.com/theChosen16)

---

_Última actualización: Julio de 2026_
