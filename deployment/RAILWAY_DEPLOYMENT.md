# Guía de Despliegue en Railway - GeoFeedback Papudo

Esta guía te llevará paso a paso para desplegar el proyecto completo en Railway.app.

## 📋 Requisitos Previos

- Cuenta en [Railway.app](https://railway.app)
- Cuenta en GitHub con el repositorio `Demo_geofeedback`
- CLI de Railway instalado (opcional): `npm install -g @railway/cli`

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

### 2.1 Agregar Servicio PostgreSQL

1. En el dashboard del proyecto, click en "+ New Service"
2. Seleccionar "Database" → "PostgreSQL"
3. Railway creará automáticamente una instancia PostgreSQL

### 2.2 Habilitar PostGIS

**Opción A: Desde Railway CLI**

```bash
# Conectar a la base de datos
railway connect postgres

# Dentro de psql:
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
\q
```

**Opción B: Ejecutar migración**

Railway ejecutará automáticamente el script de migración al desplegar.

### 2.3 Verificar Variables de Entorno

Railway crea automáticamente estas variables (no necesitas configurarlas):

- `DATABASE_URL` - URL completa de conexión
- `PGHOST` - Host de PostgreSQL
- `PGPORT` - Puerto
- `PGDATABASE` - Nombre de la BD
- `PGUSER` - Usuario
- `PGPASSWORD` - Contraseña

---

## 🔧 Paso 3: Desplegar API Flask

### 3.1 Crear Servicio API

1. Click en "+ New Service"
2. Seleccionar "GitHub Repo"
3. Conectar con `theChosen16/Demo_geofeedback`
4. Railway detectará automáticamente el `Dockerfile` en `/api`

### 3.2 Configurar Variables de Entorno

En el servicio API, ir a "Variables" y agregar:

```env
# Flask
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<generar-clave-segura-aqui>

# CORS - Especificar dominio del frontend
CORS_ORIGINS=https://tu-dominio-web.railway.app

# API
API_TITLE=GeoFeedback Papudo API
API_VERSION=1.0.0

# Logging
LOG_LEVEL=INFO
```

**Generar SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3.3 Configurar Build

1. En "Settings" → "Build"
2. Root Directory: `/api`
3. Dockerfile Path: `Dockerfile`
4. Builder: `DOCKERFILE`

### 3.4 Ejecutar Migración de Base de Datos

**Opción A: Automática (recomendada)**

Agregar variable de entorno:

```env
RUN_MIGRATIONS=true
```

**Opción B: Manual**

```bash
# Desde CLI de Railway
railway run python deployment/migrate_database.py
```

### 3.5 Generar Dominio Público

1. En "Settings" → "Networking"
2. Click en "Generate Domain"
3. Railway asignará un dominio como: `geofeedback-api.up.railway.app`

---

## 🌐 Paso 4: Desplegar Visor Web

### 4.1 Crear Servicio Web

1. Click en "+ New Service"
2. Seleccionar "GitHub Repo"
3. Conectar con `theChosen16/Demo_geofeedback`

### 4.2 Configurar Build

1. En "Settings" → "Build"
2. Root Directory: `/web`
3. Dockerfile Path: `Dockerfile`
4. Builder: `DOCKERFILE`

### 4.3 Configurar Variables de Entorno

```env
# API URL (usar el dominio generado en Paso 3.5)
API_URL=https://geofeedback-api.up.railway.app
```

### 4.4 Actualizar JavaScript para usar API de producción

Editar `web/js/map.js` para usar la variable de entorno:

```javascript
// Cambiar:
const API_BASE_URL = 'http://localhost:5000';

// Por:
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:5000'
    : 'https://geofeedback-api.up.railway.app';
```

### 4.5 Generar Dominio Público

1. En "Settings" → "Networking"
2. Click en "Generate Domain"
3. Railway asignará: `geofeedback-web.up.railway.app`

---

## ✅ Paso 5: Verificar Despliegue

### 5.1 Verificar PostgreSQL

```bash
# Desde Railway CLI
railway connect postgres

# Verificar extensiones
SELECT postgis_version();

# Verificar tablas
\dt processed.*
\dt infrastructure.*

# Ver datos
SELECT COUNT(*) FROM infrastructure.facilities_risk;
```

### 5.2 Verificar API

Visitar en navegador:

- Health Check: `https://geofeedback-api.up.railway.app/api/v1/health`
- Stats: `https://geofeedback-api.up.railway.app/api/v1/stats`
- Docs: `https://geofeedback-api.up.railway.app/`

**Desde terminal:**

```bash
curl https://geofeedback-api.up.railway.app/api/v1/health
```

### 5.3 Verificar Visor Web

Abrir en navegador: `https://geofeedback-web.up.railway.app`

Verificar:
- ✅ Mapa se carga correctamente
- ✅ Marcadores de infraestructura aparecen
- ✅ Estadísticas se cargan
- ✅ Búsqueda funciona
- ✅ Filtros funcionan

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
