# GeoFeedback Chile - Plataforma de Inteligencia Territorial

## 🌊 Descripción

Plataforma open source de análisis geoespacial que transforma datos satelitales en mapas de riesgo y herramientas de gestión hídrica para Chile.

**Sitio en producción**: [https://geofeedback.cl](https://demogeofeedback-production.up.railway.app)

---

## 🎯 Arquitectura

### Componentes Principales

1. **API Flask** (`api/`)

   - Servidor REST con integración a Google Earth Engine
   - Landing page HTML con demo interactivo
   - Análisis de índices satelitales (NDVI, NDWI, NDMI)
   - Desplegado en Railway

2. **Datos** (`data/`)
   - GeoJSON procesados de infraestructura
   - Archivos de zonas de riesgo
   - Scripts de procesamiento (Python)

---

## 🚀 Deployment

### API en Railway

URL: `https://demogeofeedback-production.up.railway.app`

**Endpoints disponibles**:

- `GET /` - Landing page con demo interactivo
- `GET /api/v1/health` - Health check
- `POST /api/v1/analyze` - Análisis territorial con GEE
- `GET /api/docs` - Documentación de la API

**Desplegar cambios**:

```bash
cd c:\Users\alean\Desktop\Geofeedback\Demo
git add .
git commit -m "Tu mensaje"
git push origin master  # Railway auto-deploya
```

---

## 📁 Estructura del Proyecto

```
Demo_geofeedback/
├── api/                        # API Flask + Google Earth Engine
│   ├── app.py                  # Aplicación principal con landing HTML
│   ├── gee_config.py           # Configuración de Earth Engine
│   ├── Dockerfile              # Configuración Docker
│   └── requirements.txt        # Dependencias Python
│
├── data/                       # Datos GeoJSON procesados
│   ├── processed/              # Archivos listos para usar
│   └── raw/                    # Datos originales
│
├── scripts/                    # Scripts de procesamiento
│
├── Documentacion/              # Documentación técnica
│   ├── APIs_REFERENCE.md       # Referencia de APIs de Google
│   └── ...
│
├── backups/                    # Versiones anteriores
│
└── README.md                   # Este archivo
```

---

## 🔧 Desarrollo Local

### Prerrequisitos

- Python 3.11+
- Git
- Credenciales de Google Earth Engine (service-account-key.json)

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/theChosen16/Demo_geofeedback.git
cd Demo_geofeedback

# Instalar dependencias
cd api
pip install -r requirements.txt

# Configurar credenciales GEE (copiar tu archivo de credenciales)
# cp /path/to/service-account-key.json ./

# Ejecutar localmente
python app.py
```

La API estará disponible en: `http://localhost:5000`

---

## 🛰️ APIs Integradas

### Google Maps Platform

- **Maps JavaScript API** - Mapas interactivos
- **Elevation API** - Datos topográficos
- **Air Quality API** - Calidad del aire
- **Solar API** - Potencial fotovoltaico
- **Geocoding API** - Conversión dirección ↔ coordenadas
- **Geolocation API** - Ubicación del usuario
- **Places API** - Búsqueda de lugares
- **Pollen API** - Niveles de polen

### Google Earth Engine

- **Sentinel-2** - Imágenes satelitales multiespectrales
- **SRTM** - Modelo digital de elevación
- **Índices calculados**: NDVI, NDWI, NDMI

---

## 📊 Datos Incluidos

### Área de Estudio: Papudo, Región de Valparaíso

- **Superficie**: 15.4 km²
- **Instalaciones críticas**: 20 registradas
- **Niveles de riesgo**:
  - 🔴 Alto: 5 instalaciones (25%)
  - 🟡 Medio: 8 instalaciones (40%)
  - 🟢 Bajo: 7 instalaciones (35%)

---

## ⏭️ Roadmap

### Fase 1: MVP ✅ (COMPLETADO)

- [x] API con Google Earth Engine
- [x] Landing page interactiva
- [x] Múltiples enfoques de análisis (8 tipos)
- [x] Integración con APIs de Google Maps

### Fase 2: Mejoras UX (En progreso)

- [x] Panel de interpretación de datos con escalas
- [ ] Modal explicativo de índices
- [ ] Todas las APIs visibles en sección Solución

### Fase 3: Análisis Avanzado (Futuro)

- [ ] Análisis de series temporales
- [ ] Predicciones basadas en datos históricos
- [ ] Sistema de alertas automáticas

---

## 📝 Changelog

### 8 de Diciembre de 2025

- **Eliminada carpeta web/**: Consolidado todo en API Flask
- **13 APIs integradas**: Mostradas por categoría
- **Modal de interpretación**: Explicación de índices y escalas
- **Mejor manejo de errores GEE**: Mensajes amigables al usuario

### 26 de Noviembre de 2025

- Deploy mínimo en Railway funcionando
- Integración inicial con Google Earth Engine

---

## 📝 Licencia

Este proyecto es parte de una demostración técnica de GeoFeedback Chile.

---

## 👥 Contacto

- **Repositorio**: [github.com/theChosen16/Demo_geofeedback](https://github.com/theChosen16/Demo_geofeedback)
- **Demo en vivo**: [geofeedback.cl](https://demogeofeedback-production.up.railway.app)

---

_Última actualización: 8 de diciembre de 2025_
