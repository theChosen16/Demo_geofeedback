# GeoFeedback Chile 🌎

**Plataforma de Inteligencia Territorial con IA**

[![Demo](https://img.shields.io/badge/Demo-geofeedback.cl-blue)](https://demogeofeedback-production.up.railway.app)
[![License](https://img.shields.io/badge/License-All%20Rights%20Reserved-red)](#)
[![Security](https://img.shields.io/badge/Security-0%20alertas%20activas-brightgreen)](./SECURITY_AUDIT.md)
[![CI](https://github.com/theChosen16/Demo_geofeedback/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/theChosen16/Demo_geofeedback/actions/workflows/ci.yml)

---

## 🚀 Demo en Vivo

**https://geofeedback.cl**

---

## ✨ Características

- 🛰️ **Análisis Satelital** - Índices NDVI, NDWI, NDMI con Sentinel-2
- 🤖 **IA Integrada** - Interpretación automática con Google Gemini
- 🗺️ **13 APIs de Google** - Maps, Elevation, Air Quality, Solar, Pollen
- 🏢 **Google Earth Engine™ Enterprise** - Potencia de cómputo comercial sin barreras
- 📱 **100% Mobile Optimized** - Diseño responsivo full-width y controles táctiles
- 💬 **Chat Asistente** - Pregunta sobre tus análisis en tiempo real
- 🛡️ **Resiliente** - Retry automático y manejo de errores de red
- 📊 **8 Enfoques de Análisis** - Minería, Agricultura, Energía, y más

---

## ✅ Cambios Abril 2026

- Contador público de métricas reforzado: ahora renderiza `0` explícitamente cuando no hay datos.
- Fetch de `/api/v1/stats` endurecido con validación de respuesta HTTP y fallback seguro.
- `api/database.py` ahora autocrea las tablas de analytics en caliente si Railway responde con `undefined_table`, y reintenta la operación una vez.
- Nuevo endpoint `GET /api/v1/observability` con checks críticos de BD, analytics, GEE y Maps; devuelve `503` cuando el estado está degradado.
- Nuevo `GET /robots.txt` para eliminar ruido de `404` en logs de Railway.
- `scripts/monitor_deploy.py` ya no depende de `requests`: usa librería estándar, URL configurable y modo `--once` para smoke checks.
- UX de rutas mejorada: `/api` redirige a `/api/docs` y `/contact` redirige a `/#contacto`.
- Bootstrap de base de datos en Railway actualizado para crear tablas de analytics (`06_create_analytics_tables.sql`).
- Pipeline de CI reforzado con regresión dedicada de observability, validación de la CLI de monitoreo y smoke check contra el deployment productivo en `.github/workflows/ci.yml`.

---

## 📚 Documentación

Ver [DOCS.md](./DOCS.md) para documentación técnica completa:

- Arquitectura del sistema
- APIs integradas y su uso
- Índices satelitales y fórmulas
- Configuración de Railway
- Operación del contador público y analytics
- Endpoint de observability y monitor operativo
- Pipeline CI (`.github/workflows/ci.yml`) y pruebas de regresión

---

## 🔒 Licencia

**© 2025 Alejandro Hernández Aguirre - Todos los derechos reservados**

Este proyecto es una demo técnica. Ver [LICENSE](./LICENSE) para detalles.

---

## 👤 Autor

**Alejandro Hernández Aguirre**

- [LinkedIn](https://www.linkedin.com/in/alejandro-hern%C3%A1ndez-aguirre-bb8967246/)
- [GitHub](https://github.com/theChosen16)

---

_Última actualización: 24 de Abril de 2026_
