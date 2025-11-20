# Guía de Despliegue en Railway - GeoFeedback Papudo

Esta guía te llevará paso a paso para desplegar el proyecto completo en Railway.app usando una combinación de Railway CLI y Dashboard.

---

## 📊 Estado Actual del Despliegue

### ✅ Completado

- [x] Cuenta Railway creada y autenticada (`railway login`)
- [x] Proyecto Railway creado y linked: `thorough-emotion`
- [x] Servicio inicial: `Demo_geofeedback` (linked)
- [x] PostgreSQL 18 instalado localmente (para comando `psql`)
- [x] Configuración `railway.toml` corregida:
  - Root `railway.toml` → `railway.toml.backup` (eliminado)
  - Creado `api/railway.toml` con healthcheck `/api/v1/health`
  - Creado `web/railway.toml` con healthcheck `/health`
- [x] Cambios commiteados y pusheados a GitHub:
  - Commit `20a4302`: Railway configuration files
  - Commit `496f1e8`: Add CLI setup guide
- [x] Railway CLI linked a proyecto:
  - Workspace: `thechosen16's Projects`
  - Project: `thorough-emotion`
  - Environment: `production`
  - Service: `Demo_geofeedback`
- [x] **Base de datos configurada:** Usando Supabase PostgreSQL con PostGIS
  - Host: `db.gskrrpduiqabnzzbbtbw.supabase.co:5432`
  - DATABASE_URL configurada en Railway apuntando a Supabase
- [x] **Migración de base de datos ejecutada exitosamente:**
  - ✅ Extensiones PostGIS creadas
  - ✅ 5 schemas creados
  - ✅ Tablas creadas con índices espaciales
  - ✅ 20 instalaciones cargadas
  - ✅ 3 funciones API creadas
  - ✅ Metadata insertada

### 🔄 En Progreso

- [x] **Servicio API configurado y corregido**:
  - ✅ Root Directory: `api`
  - ✅ Variables de entorno configuradas
  - ✅ Dominio público: `demogeofeedback-production.up.railway.app`
  - ✅ Dockerfile corregido para usar `$PORT` dinámico
  - ✅ **CRÍTICO**: Dockerfile corregido para copiar `config.py` (faltaba)
  - 🔄 Redesplegando con todas las correcciones
- [x] **Frontend actualizado**:
  - ✅ Conectado con API en producción
  - ✅ Fallback a datos locales si API falla
  - ✅ Detección automática de entorno (dev/prod)

### 🐛 Problemas Resueltos

1. **Puerto Incorrecto (Build #1)**:
   - **Problema**: Dockerfile usaba puerto hardcoded `5000`, Railway asigna `$PORT` dinámico
   - **Solución**: Cambiar CMD a usar `${PORT:-5000}`
   - **Estado**: ✅ Resuelto

2. **DATABASE_URL No Encontrada (Build #2)**:
   - **Problema**: `config.py` no se copiaba al contenedor, app usaba fallback a `localhost:5432`
   - **Error**: `connection to server at "localhost" (127.0.0.1), port 5432 failed`
   - **Causa Raíz**: Dockerfile solo copiaba `app.py`, no `config.py`
   - **Solución**: Añadir `config.py` al COPY: `COPY app.py config.py ./`
   - **Estado**: ✅ Resuelto

### ⏳ Pendiente

- [ ] Verificar deployment exitoso del servicio API
- [ ] Crear servicio Web en Railway Dashboard:
  - Root Directory → `web`
  - Service Name → `web`
  - Generar dominio público
- [ ] Verificar deployment completo de API y Web

### 📝 Notas

- **PostgreSQL local**: Instalado en `C:\Program Files\PostgreSQL\18`
- **Contraseña generada**: `9e42287208d8431ebabd91b2a83e8d70` (cambiar después)
- **Archivo de guía CLI**: [RAILWAY_CLI_SETUP_STEPS.md](../RAILWAY_CLI_SETUP_STEPS.md)
- **Proyecto Railway actual**: `thorough-emotion` (production)
- **Servicio principal**: `Demo_geofeedback`
- **Dominio público API**: `https://demogeofeedback-production.up.railway.app`
- **Variables Railway configuradas**:
  - RAILWAY_SERVICE_NAME: `Demo_geofeedback`
  - RAILWAY_ENVIRONMENT_NAME: `production`
  - RAILWAY_PROJECT_NAME: `thorough-emotion`
  - RAILWAY_PUBLIC_DOMAIN: `demogeofeedback-production.up.railway.app`

---

## 📋 Requisitos Previos

- Cuenta en [Railway.app](https://railway.app) ✅
- Cuenta en GitHub con el repositorio `Demo_geofeedback` ✅
- CLI de Railway instalado: `npm install -g @railway/cli` ✅
- PostgreSQL instalado localmente (para `psql` command) ✅

## 🏗️ Arquitectura del Despliegue

```
Railway Project: geofeedback-papudo
├── PostgreSQL Service (PostGIS)    → Base de datos espacial
├── API Service (Flask)             → Backend API REST
└── Web Service (nginx)             → Frontend estático
```

---

## 🚀 Paso 1: Crear Proyecto en Railway

### 1.1 Desde la Web UI

1. Ir a [railway.app](https://railway.app) y hacer login
2. Click en "New Project"
3. Seleccionar "Deploy from GitHub repo"
4. Autorizar Railway a acceder a GitHub
5. Seleccionar el repositorio `theChosen16/Demo_geofeedback`
6. Railway detectará automáticamente el proyecto

### 1.2 Desde la CLI (Alternativa)

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Crear proyecto
cd Demo_geofeedback
railway init
```

---

## 🗄️ Paso 2: Configurar PostgreSQL con PostGIS

### 2.1 Agregar Servicio PostgreSQL ✅

**Usando Railway Dashboard:**

1. En el dashboard del proyecto, presionar `Ctrl+K` (atajo rápido)
2. Escribir "postgres" y seleccionar "Add PostgreSQL"
3. Esperar 1-2 minutos mientras se aprovisiona

**Alternativa con mouse:**

1. Click en "+ New" (superior izquierda o en el canvas)
2. Seleccionar "Database" → "PostgreSQL"
3. Click "Add PostgreSQL"

Railway creará automáticamente una instancia PostgreSQL 16 con:
- ✅ Variable `DATABASE_URL` disponible para todos los servicios
- ✅ Variables individuales: `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`

### 2.2 Instalar PostgreSQL localmente (para psql) ✅

**IMPORTANTE**: Railway CLI requiere el comando `psql` instalado localmente para conectarse.

```powershell
# En PowerShell como administrador
choco install postgresql

# Verificar instalación
psql --version
# Debería mostrar: psql (PostgreSQL) 18.x
```

**Ubicación de instalación:**
- Ruta: `C:\Program Files\PostgreSQL\18`
- PATH actualizado automáticamente

**Después de instalar:**
```powershell
# Cerrar y reabrir PowerShell, o ejecutar:
refreshenv

# Navegar al proyecto
cd C:\Users\alean\Desktop\Geofeedback\Demo
```

### 2.3 Habilitar PostGIS ⏳

**Conectar a Railway PostgreSQL:**

```powershell
# Asegúrate de estar en el directorio del proyecto
cd C:\Users\alean\Desktop\Geofeedback\Demo

# Conectar (nota la 'P' mayúscula en 'Postgres')
railway connect Postgres
```

**Dentro de psql (prompt `railway=>#`):**

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verificar instalación
SELECT postgis_version();
-- Deberías ver: 3.4.x USE_GEOS=1 USE_PROJ=1 USE_STATS=1

-- Salir
\q
```

### 2.4 Verificar Variables de Entorno

Railway crea automáticamente estas variables (visibles en Variables tab):

- `DATABASE_URL` - URL completa de conexión (usado por Flask)
- `PGHOST` - Host de PostgreSQL
- `PGPORT` - Puerto (5432)
- `PGDATABASE` - Nombre de la BD (railway)
- `PGUSER` - Usuario
- `PGPASSWORD` - Contraseña

---

## 🔧 Paso 3: Configurar Servicio API ⏳

**NOTA**: Ya existe un servicio llamado "Demo_geofeedback" en tu proyecto Railway que falló. Lo reconfiguraremos como servicio API.

### 3.1 Reconfigurar Servicio Existente como API

**En el Railway Dashboard:**

1. Click en el servicio "Demo_geofeedback" (el que tiene estado "Failed")
2. Ve a la pestaña **"Settings"**
3. En la sección **"Service"**:
   - Click en **"Service Name"** → cambiar a: `api`
4. Scroll down a la sección **"Build"**:
   - Click en **"Add Root Directory"** → escribir: `api`
   - **Dockerfile Path**: debe quedar como `Dockerfile` (relativo a api/)
   - **Builder**: debe estar en `DOCKERFILE`
5. Click **"Save Changes"** o **"Update"**

**Por qué esto funciona:**
- El `api/railway.toml` que creamos le dice a Railway que use el Dockerfile en `api/`
- El healthcheck está configurado en `/api/v1/health`
- Railway reconstruirá el servicio con la configuración correcta

### 3.2 Configurar Variables de Entorno

1. En el servicio API, ir a la pestaña **"Variables"**
2. Click **"+ New Variable"** para cada una:

```env
FLASK_ENV=production
FLASK_DEBUG=False
CORS_ORIGINS=*
```

3. Para `SECRET_KEY`, generarlo primero:

```powershell
# En PowerShell local
python -c "import secrets; print(secrets.token_hex(32))"
```

Copiar el resultado y agregarlo como variable `SECRET_KEY`

**Variables opcionales:**

```env
API_TITLE=GeoFeedback Papudo API
API_VERSION=1.0.0
LOG_LEVEL=INFO
```

**IMPORTANTE**: La variable `DATABASE_URL` ya existe automáticamente, creada por Railway cuando agregaste PostgreSQL.

### 3.3 Generar Dominio Público

1. Ve a la pestaña **"Settings"** → sección **"Networking"**
2. Click en **"Generate Domain"**
3. Railway asignará un dominio como: `api-production-xxxx.up.railway.app`
4. **¡Anota esta URL!** La necesitarás para el servicio web

### 3.4 Ejecutar Migración de Base de Datos (después de PostGIS)

**IMPORTANTE**: Solo ejecutar DESPUÉS de habilitar PostGIS en el Paso 2.3.

```powershell
# Asegúrate de estar en la raíz del proyecto
cd C:\Users\alean\Desktop\Geofeedback\Demo

# Link al proyecto (si no lo has hecho)
railway link
# Selecciona: tu team → Demo_geofeedback → production

# Seleccionar el servicio API
railway service
# Selecciona: api

# Ejecutar migración
railway run python deployment/migrate_database.py
```

**Deberías ver output como:**

```
============================================
MIGRACIÓN DE BASE DE DATOS - GEOFEEDBACK PAPUDO
============================================

[→] Usando DATABASE_URL de Railway
[✓] Conexión establecida
[→] Creando extensiones PostGIS...
[✓] Extensiones PostGIS creadas
[→] Creando schemas...
[✓] 5 schemas creados
[→] Creando tablas...
[✓] Tablas creadas con índices espaciales
[→] Cargando datos de infraestructura...
[✓] 20 instalaciones cargadas
[→] Creando funciones API...
[✓] 3 funciones API creadas
[→] Insertando metadata...
[✓] Metadata insertada

============================================
✅ MIGRACIÓN COMPLETADA EXITOSAMENTE
============================================
```

### 3.5 Verificar Deployment de API

El servicio debería redesplegar automáticamente después de cambiar la configuración.

**Verificar en navegador:**

```
https://[tu-api-domain].up.railway.app/api/v1/health
```

**Deberías ver JSON:**

```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T...",
  "database": {
    "connected": true,
    "database": "railway",
    "version": "PostgreSQL 16...",
    "postgis": "3.4..."
  }
}
```

---

## 🌐 Paso 4: Crear Servicio Web ⏳

### 4.1 Crear Nuevo Servicio para Web

**En el Railway Dashboard:**

1. En el canvas del proyecto, click en el botón **"+"** (superior izquierda de la barra lateral)
2. Seleccionar **"GitHub Repo"**
3. Conectar con el repositorio: `theChosen16/Demo_geofeedback`
4. Railway creará un nuevo servicio

### 4.2 Configurar el Servicio Web

1. Click en el servicio nuevo que se acaba de crear
2. Ve a la pestaña **"Settings"**
3. En la sección **"Service"**:
   - Click en **"Service Name"** → cambiar a: `web`
4. En la sección **"Build"**:
   - Click en **"Add Root Directory"** → escribir: `web`
   - **Dockerfile Path**: debe quedar como `Dockerfile`
   - **Builder**: debe estar en `DOCKERFILE`
5. Click **"Save Changes"** o **"Update"**

**Por qué esto funciona:**

- El `web/railway.toml` que creamos configura el servicio correctamente
- El healthcheck está en `/health` (configurado en nginx)
- Usará el Dockerfile en `web/` que sirve contenido estático

### 4.3 Generar Dominio Público

1. Ve a la pestaña **"Settings"** → sección **"Networking"**
2. Click en **"Generate Domain"**
3. Railway asignará un dominio como: `web-production-xxxx.up.railway.app`
4. **¡Anota esta URL!** Esta será tu aplicación web pública

### 4.4 (Opcional) Configurar Variables de Entorno

Si quieres que el frontend use la API en producción:

1. Ve a la pestaña **"Variables"**
2. Click **"+ New Variable"**:

```env
API_URL=https://[tu-api-domain].up.railway.app
```

Reemplaza `[tu-api-domain]` con el dominio que anotaste en el Paso 3.3.

### 4.5 (Opcional) Conectar Frontend con API

Por defecto, el frontend carga datos desde un archivo GeoJSON local. Para conectarlo con la API:

**Editar `web/js/map.js`:**

```javascript
// Al inicio del archivo
const API_BASE_URL = window.location.hostname.includes('localhost')
    ? 'http://localhost:5000'
    : 'https://[tu-api-domain].up.railway.app';  // <-- Usar tu URL real

// Modificar la función loadData()
async function loadData() {
    try {
        // Cargar desde API en lugar de archivo local
        const response = await fetch(`${API_BASE_URL}/api/v1/infrastructure`);
        const data = await response.json();

        // Adaptar formato
        infrastructureData = {
            type: 'FeatureCollection',
            features: data.facilities.map(f => ({
                type: 'Feature',
                geometry: f.geometry,
                properties: {
                    name: f.name,
                    category: f.category,
                    risk_level: f.risk_level,
                    risk_name: f.risk_name,
                    risk_color: f.risk_color
                }
            }))
        };

        createRiskPolygons();
        createInfrastructureMarkers();
        updateStatistics();
        document.getElementById('loading').classList.add('hidden');
    } catch (error) {
        console.error('Error loading data:', error);
        alert('Error al cargar los datos. Mostrando datos locales.');
        // Fallback a datos locales si la API falla
        loadLocalData();
    }
}
```

Luego commit y push:

```bash
git add web/js/map.js
git commit -m "Connect frontend to Railway API"
git push origin master
```

Railway redesplegará automáticamente el servicio web.

### 4.6 Verificar Deployment de Web

Abrir en navegador:

```text
https://[tu-web-domain].up.railway.app
```

Deberías ver:

- ✅ Mapa cargado
- ✅ Panel lateral con estadísticas
- ✅ Controles de filtros
- ⚠️ Puede que no se vean marcadores aún (si no conectaste con API)

---

## ✅ Paso 5: Verificar Despliegue Completo

### 5.1 Verificar PostgreSQL + PostGIS

```powershell
# Desde Railway CLI
railway connect Postgres
```

Dentro de psql:

```sql
-- Verificar extensiones
SELECT postgis_version();

-- Verificar schemas
\dn

-- Verificar tablas
\dt processed.*
\dt infrastructure.*

-- Ver datos de infraestructura
SELECT COUNT(*) FROM infrastructure.facilities_risk;
-- Debería retornar: 20

-- Ver datos de polígonos de riesgo
SELECT COUNT(*) FROM processed.amenaza_poligonos;
-- Debería retornar: ~2913

-- Salir
\q
```

### 5.2 Verificar API

**Test 1: Health Check**

Visitar en navegador:

```text
https://[tu-api-domain].up.railway.app/api/v1/health
```

Deberías ver:

```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T...",
  "database": {
    "connected": true,
    "database": "railway",
    "version": "PostgreSQL 16...",
    "postgis": "3.4..."
  }
}
```

**Test 2: Estadísticas**

```text
https://[tu-api-domain].up.railway.app/api/v1/stats
```

**Test 3: Infraestructura**

```text
https://[tu-api-domain].up.railway.app/api/v1/infrastructure
```

Deberías ver un array JSON con 20 instalaciones.

### 5.3 Verificar Visor Web

Abrir en navegador:

```text
https://[tu-web-domain].up.railway.app
```

Verificar:

- ✅ Mapa se carga correctamente (Leaflet)
- ✅ Marcadores de infraestructura aparecen
- ✅ Estadísticas se cargan en el panel lateral
- ✅ Búsqueda funciona
- ✅ Filtros por riesgo funcionan
- ✅ Colores de riesgo se muestran correctamente (Verde/Amarillo/Rojo)

---

## 🔐 Paso 6: Configuración de Seguridad (Producción)

### 6.1 Dominio Personalizado (Opcional)

1. Comprar dominio (ej: `geofeedback.cl`)
2. En Railway → Service → Settings → Networking
3. Click en "Custom Domain"
4. Agregar dominio: `api.geofeedback.cl` y `app.geofeedback.cl`
5. Configurar DNS con los registros que Railway proporciona

### 6.2 Variables de Entorno Sensibles

**Rotar secretos periódicamente:**

```bash
# Generar nuevo SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Actualizar en Railway Dashboard
```

### 6.3 Restricciones CORS

En variables de API, cambiar:

```env
# De:
CORS_ORIGINS=*

# A (solo dominios específicos):
CORS_ORIGINS=https://geofeedback-web.up.railway.app,https://app.geofeedback.cl
```

### 6.4 Rate Limiting (Recomendado)

Agregar a `api/app.py`:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/v1/stats')
@limiter.limit("100 per minute")
def get_stats():
    # ...
```

---

## 📊 Paso 7: Monitoreo y Logs

### 7.1 Ver Logs en Tiempo Real

**Desde Dashboard:**
- Ir al servicio → Tab "Deployments"
- Click en el deployment activo → Ver logs

**Desde CLI:**

```bash
# Logs de API
railway logs -s api

# Logs de Web
railway logs -s web

# Logs de PostgreSQL
railway logs -s postgres
```

### 7.2 Métricas

Railway proporciona métricas automáticas:
- CPU Usage
- Memory Usage
- Network In/Out
- Request Count

Ver en: Dashboard → Service → "Metrics"

### 7.3 Alertas (Pro Plan)

Configurar alertas para:
- Alto uso de CPU (>80%)
- Alto uso de memoria (>90%)
- Errores 5xx
- Downtime

---

## 💰 Paso 8: Costos y Escalabilidad

### 8.1 Plan Gratuito (Starter)

Railway ofrece:
- $5 USD de crédito mensual gratis
- Suficiente para proyectos pequeños/demo
- Límites:
  - 512 MB RAM por servicio
  - 1 GB storage
  - 100 GB network egress

### 8.2 Plan Developer ($5/mes)

- $5 USD de crédito mensual incluido
- Pago por uso adicional
- Mejor para desarrollo/staging

### 8.3 Plan Pro ($20/mes)

- $20 USD de crédito mensual
- Soporte prioritario
- Alertas personalizadas
- Mejor para producción

### 8.4 Optimizar Costos

**Reducir uso de recursos:**

1. **Optimizar queries:**
   ```python
   # Usar índices espaciales
   # Limitar resultados
   # Cache de queries frecuentes
   ```

2. **Comprimir respuestas:**
   ```python
   # En Flask
   from flask_compress import Compress
   Compress(app)
   ```

3. **CDN para assets estáticos:**
   - Cloudflare (gratis)
   - Cloudinary para imágenes

---

## 🔄 Paso 9: CI/CD Automático

Railway despliega automáticamente cuando haces push a `master`.

### 9.1 Flujo de Despliegue

```
Git Push → GitHub
    ↓
Railway detecta cambio
    ↓
Build de Dockerfile
    ↓
Run Migrations (si configurado)
    ↓
Deploy nuevo container
    ↓
Health check
    ↓
Traffic routing (zero-downtime)
```

### 9.2 Despliegues por Rama

Configurar diferentes servicios para diferentes ramas:

- `master` → Producción
- `develop` → Staging
- `feature/*` → Preview deployments

### 9.3 Rollback

Si algo sale mal:

1. Ir a "Deployments"
2. Seleccionar deployment anterior
3. Click en "Redeploy"

**Desde CLI:**

```bash
railway rollback
```

---

## 🛠️ Troubleshooting

### Problema: API no se conecta a PostgreSQL

**Solución:**

```bash
# Verificar que DATABASE_URL esté configurada
railway variables

# Verificar logs
railway logs -s api

# Conectar manualmente
railway connect postgres
```

### Problema: CORS errors en frontend

**Solución:**

```env
# En variables de API
CORS_ORIGINS=https://tu-dominio-web.railway.app

# Verificar en navegador (F12 → Console)
```

### Problema: Out of memory

**Solución:**

1. Optimizar queries SQL
2. Reducir workers de Gunicorn:
   ```dockerfile
   CMD ["gunicorn", "--workers", "2", ...]
   ```
3. Upgrade plan de Railway

### Problema: Deployment falla

**Verificar:**

```bash
# Ver logs de build
railway logs --deployment

# Verificar Dockerfile
docker build -t test-api -f api/Dockerfile api/

# Verificar variables de entorno
railway variables
```

---

## 📚 Recursos Adicionales

- [Documentación Railway](https://docs.railway.app)
- [Railway Community](https://discord.gg/railway)
- [Railway Status](https://status.railway.app)
- [Pricing Calculator](https://railway.app/pricing)

---

## 🎯 Checklist de Despliegue

Antes de poner en producción:

- [ ] PostgreSQL con PostGIS habilitado
- [ ] Migración de BD ejecutada exitosamente
- [ ] API responde en `/api/v1/health`
- [ ] Frontend carga correctamente
- [ ] CORS configurado correctamente
- [ ] Variables de entorno configuradas
- [ ] SECRET_KEY cambiado (no usar default)
- [ ] Dominios personalizados (si aplica)
- [ ] SSL/HTTPS habilitado (automático en Railway)
- [ ] Logs funcionando
- [ ] Métricas activas
- [ ] Alertas configuradas (Pro plan)
- [ ] Backups de BD configurados
- [ ] Documentación actualizada

---

## 💡 Mejores Prácticas

1. **Usar variables de entorno para TODO**
   - No hardcodear credenciales
   - Usar `.env.example` como template

2. **Implementar health checks**
   - API: `/api/v1/health`
   - Web: `/health`

3. **Monitorear logs regularmente**
   - Detectar errores temprano
   - Optimizar performance

4. **Mantener dependencias actualizadas**
   ```bash
   pip list --outdated
   npm outdated
   ```

5. **Backups automáticos**
   - Railway hace backups automáticos de PostgreSQL
   - Exportar datos críticos periódicamente

6. **Testing antes de deploy**
   ```bash
   # Local
   docker-compose up
   pytest

   # Staging
   railway run --environment staging
   ```

---

**Última actualización:** Noviembre 2025
**Versión:** 1.0.0
**Mantenedor:** GeoFeedback Chile
