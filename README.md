# GeoFeedback Papudo - Demo Simplificado

## 🌊 Descripción

Sistema simplificado de análisis de riesgo de inundación para la comuna de Papudo, Región de Valparaíso, Chile.

**Versión actual**: 2.0 - Deploy Mínimo (sin base de datos)

---

## 🎯 Arquitectura Actual

### Componentes Principales

1. **API Flask** (`api/`)

   - Servidor REST con datos estáticos embebidos
   - Endpoints de consulta sin dependencia de PostgreSQL
   - Landing page HTML inline con estadísticas visuales
   - Desplegado en Railway

2. **Visor Web** (`web/`)

   - Interfaz de mapa interactivo con Leaflet.js
   - Visualización de instalaciones críticas
   - Filtros por nivel de riesgo y categoría
   - Desplegado en GitHub Pages

3. **Datos Estáticos** (`data/`)
   - GeoJSON procesados de infraestructura
   - Archivos de zonas de riesgo
   - Scripts de procesamiento (Python)

---

## 🚀 Deployment

### API en Railway

La API está desplegada en: `https://demogeofeedback-production.up.railway.app`

**Endpoints disponibles**:

- `GET /` - Landing page HTML con estadísticas
- `GET /api/v1/health` - Health check del servicio
- `GET /api/v1/stats` - Estadísticas generales (20 instalaciones)
- `GET /api/v1/infrastructure` - Lista de infraestructura crítica
- `GET /api/docs` - Documentación de la API

**Desplegar cambios**:

```bash
cd c:\Users\alean\Desktop\Geofeedback\Demo
git add .
git commit -m "Tu mensaje"
git push origin main  # Railway auto-deploya
```

### Visor Web en GitHub Pages

URL pública: `https://thechosen16.github.io/Demo_geofeedback/`

**Actualizar**:

```bash
git add web/
git commit -m "Update web viewer"
git push origin main
```

---

## 📁 Estructura del Proyecto

```
Demo_geofeedback/
├── api/                        # API Flask simplificada
│   ├── app.py                  # Aplicación principal (datos estáticos)
│   ├── Dockerfile              # Configuración Docker optimizada
│   ├── requirements.txt        # Dependencias (Flask, CORS, Gunicorn)
│   └── README.md               # Documentación de la API
│
├── web/                        # Visor web (GitHub Pages)
│   ├── index.html              # Página principal
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── map.js              # Lógica del mapa
│
├── data/                       # Datos GeoJSON procesados
│   ├── processed/              # Archivos listos para usar
│   └── raw/                    # Datos originales
│
├── scripts/                    # Scripts de procesamiento
│   ├── 03_vectorize_amenaza.py
│   ├── 07_download_infrastructure.py
│   └── ...
│
├── backups/                    # Backups de versiones anteriores
│   ├── app.py.backup           # Versión con PostgreSQL
│   ├── Dockerfile.backup
│   └── requirements.txt.backup
│
├── Documentacion/              # Documentación del proyecto
│   ├── 00_INDICE_Y_RESUMEN.md
│   └── ...
│
└── README.md                   # Este archivo
```

---

## 🔧 Desarrollo Local

### Prerrequisitos

- Python 3.11+
- Git

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/theChosen16/Demo_geofeedback.git
cd Demo_geofeedback

# Instalar dependencias de la API
cd api
pip install -r requirements.txt

# Ejecutar API localmente
python app.py
```

La API estará disponible en: `http://localhost:8080`

### Probar Endpoints

```bash
# Health check
curl http://localhost:8080/api/v1/health

# Estadísticas
curl http://localhost:8080/api/v1/stats

# Infraestructura
curl http://localhost:8080/api/v1/infrastructure
```

---

## 📊 Datos Incluidos

### Área de Estudio: Papudo, Región de Valparaíso

- **Superficie**: 15.4 km²
- **Instalaciones críticas**: 20 registradas
- **Niveles de riesgo**:
  - 🔴 Alto: 5 instalaciones (25%)
  - 🟡 Medio: 8 instalaciones (40%)
  - 🟢 Bajo: 7 instalaciones (35%)

### Categorías de Infraestructura

- Salud (hospitales, centros de salud)
- Educación (escuelas, colegios)
- Emergencias (bomberos, carabineros)
- Gobierno (municipalidad, servicios públicos)
- Comercio (supermercados, farmacias)

---

## 🗑️ Limpieza Realizada (26 Nov 2025)

Se eliminaron los siguientes archivos obsoletos relacionados con PostgreSQL/PostGIS:

### Archivos Eliminados de `/api`:

- ❌ `config.py` - Configuración de base de datos
- ❌ `cache_helper.py` - Sistema de caché para queries SQL
- ❌ `test_api.py` - Tests que requerían BD
- ❌ `templates/` - Carpeta de plantillas HTML (ahora inline)
- ❌ `static/` - Archivos estáticos CSS/JS (no usados)

### Archivos Eliminados de raíz:

- ❌ `setup_database.sql` - Script de creación de esquemas PostgreSQL
- ❌ `ARREGLOS_RAILWAY.md` - Guía de troubleshooting obsoleta
- ❌ `QUICK_DEPLOY_RAILWAY.md` - Guía de deploy con BD
- ❌ `RAILWAY_CLI_SETUP_STEPS.md` - Configuración CLI obsoleta
- ❌ `railway.toml.backup` - Configuración antigua
- ❌ `deployment/` - Carpeta completa de deployment con BD

### Archivos Movidos a `/backups`:

- 📦 `app.py.backup` - Versión anterior con PostgreSQL (539 líneas)
- 📦 `Dockerfile.backup` - Dockerfile con dependencias de BD
- 📦 `requirements.txt.backup` - Requirements con psycopg2

**Resultado**: Proyecto más limpio y enfocado en la arquitectura actual sin base de datos.

---

## 🔄 Migración desde Versión con BD

Si necesitas volver a la versión con PostgreSQL/PostGIS:

```bash
# Restaurar desde backups
cd api
Copy-Item "..\backups\app.py.backup" -Destination "app.py" -Force
Copy-Item "..\backups\Dockerfile.backup" -Destination "Dockerfile" -Force
Copy-Item "..\backups\requirements.txt.backup" -Destination "requirements.txt" -Force

# Commit y push
cd ..
git add api/
git commit -m "Restore PostgreSQL version"
git push origin main
```

---

## ⏭️ Roadmap Futuro

### Fase 1: Deploy Mínimo ✅ (COMPLETADO)

- [x] API con datos estáticos sin BD
- [x] Dockerfile optimizado para Railway
- [x] Landing page HTML inline
- [x] Limpieza de archivos obsoletos

### Fase 2: Datos Dinámicos (Próximamente)

- [ ] Reconectar PostgreSQL/PostGIS con manejo robusto de errores
- [ ] Implementar connection pooling optimizado
- [ ] Cargar datos GeoJSON completos desde BD

### Fase 3: Análisis Avanzado (Futuro)

- [ ] Integración con Google Earth Engine
- [ ] Análisis de series temporales de inundaciones
- [ ] Predicciones basadas en datos históricos
- [ ] Sistema de alertas automáticas

---

## 📝 Changelog Reciente

### 8 de Diciembre de 2025

- **SEO Mejorado**: Agregados meta tags de Open Graph y Twitter Cards para mejor compartibilidad en redes sociales
- **Menú Móvil Funcional**: Implementada funcionalidad JavaScript para abrir/cerrar el menú en dispositivos móviles
- **URL API Corregida**: Actualizado el enlace de documentación API al endpoint correcto de Railway
- **Keywords SEO**: Agregadas palabras clave relevantes para mejor indexación

### 26 de Noviembre de 2025

- Limpieza de archivos obsoletos relacionados con PostgreSQL
- Deploy mínimo sin base de datos funcionando

---

## 📝 Licencia

Este proyecto es parte de una demostración técnica de GeoFeedback Chile.

---

## 👥 Contacto

- **Repositorio**: [github.com/theChosen16/Demo_geofeedback](https://github.com/theChosen16/Demo_geofeedback)
- **Demo en vivo**: [thechosen16.github.io/Demo_geofeedback](https://thechosen16.github.io/Demo_geofeedback/)
- **API**: [demogeofeedback-production.up.railway.app](https://demogeofeedback-production.up.railway.app)

---

_Última actualización: 8 de diciembre de 2025_
