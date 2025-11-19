# 🚀 Despliegue Rápido en Railway - 10 Minutos

Esta guía te llevará del código a producción en Railway en aproximadamente 10 minutos.

## ✅ Pre-requisitos

- [x] Cuenta en GitHub (ya tienes el repo)
- [ ] Cuenta en [Railway.app](https://railway.app) (crear si no tienes)
- [ ] 10 minutos de tu tiempo

## 📋 Pasos

### 1️⃣ Crear Cuenta en Railway (2 min)

1. Ir a [railway.app](https://railway.app)
2. Click en "Login" (esquina superior derecha)
3. Seleccionar "Login with GitHub"
4. Autorizar Railway

✨ **Railway te da $5 USD gratis cada mes** - suficiente para este proyecto!

---

### 2️⃣ Crear Nuevo Proyecto (1 min)

1. En el dashboard de Railway, click en **"+ New Project"**
2. Seleccionar **"Deploy from GitHub repo"**
3. Buscar y seleccionar: **`theChosen16/Demo_geofeedback`**
4. Railway empezará a escanear el repositorio

---

### 3️⃣ Agregar Base de Datos PostgreSQL (2 min)

1. En tu proyecto nuevo, click en **"+ New"**
2. Seleccionar **"Database"**
3. Click en **"Add PostgreSQL"**
4. Railway creará automáticamente:
   - ✅ Instancia de PostgreSQL 16
   - ✅ Variable `DATABASE_URL`
   - ✅ Credenciales seguras

**Habilitar PostGIS:**

```bash
# Opción A: Desde el navegador
# 1. En el servicio PostgreSQL, ir a "Data"
# 2. Click en "Query"
# 3. Ejecutar:
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
```

```bash
# Opción B: Desde Railway CLI (si lo instalaste)
railway link
railway connect postgres

# Dentro de psql:
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
\q
```

---

### 4️⃣ Desplegar API Flask (2 min)

1. Click en **"+ New"**
2. Seleccionar **"GitHub Repo"**
3. Conectar con **`theChosen16/Demo_geofeedback`**
4. Railway detectará automáticamente el Dockerfile

**Configurar el servicio:**

1. Click en el servicio recién creado
2. Ir a **"Settings"**
3. En **"Service Name"** poner: `api`
4. En **"Root Directory"** poner: `api`
5. Scroll down → Click **"Generate Domain"**
6. Railway asignará algo como: `https://api-production-xxxx.up.railway.app`

**Copiar esta URL - la necesitarás después!**

**Configurar Variables de Entorno:**

1. En el servicio API, ir a **"Variables"**
2. Click **"+ New Variable"**
3. Agregar estas variables:

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<generar-uno-aqui>
CORS_ORIGINS=*
```

**Generar SECRET_KEY:**

```bash
# En tu terminal local
python -c "import secrets; print(secrets.token_hex(32))"
# Copiar el resultado y pegarlo en Railway
```

---

### 5️⃣ Migrar Base de Datos (1 min)

**Opción A: Automática (Recomendada)**

En las variables del servicio API, agregar:

```env
RUN_MIGRATIONS=true
```

Railway ejecutará la migración automáticamente en el próximo deploy.

**Opción B: Manual**

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Conectar al proyecto
railway link

# Ejecutar migración
railway run python deployment/migrate_database.py
```

---

### 6️⃣ Desplegar Visor Web (2 min)

1. Click en **"+ New"**
2. Seleccionar **"GitHub Repo"**
3. Conectar con **`theChosen16/Demo_geofeedback`**

**Configurar el servicio:**

1. Click en el servicio nuevo
2. En **"Settings"**:
   - **Service Name**: `web`
   - **Root Directory**: `web`
3. Click **"Generate Domain"**
4. Railway asignará: `https://web-production-xxxx.up.railway.app`

---

### 7️⃣ Conectar Frontend con API (1 min)

Necesitamos actualizar el frontend para usar la API en producción:

**Opción A: Editar localmente y push**

1. Abrir `web/js/map.js` en tu editor
2. Buscar la línea que define `fetch('../data/processed/infrastructure_with_risk.geojson')`
3. Cambiar para usar la API:

```javascript
// Al inicio del archivo, definir la URL de la API
const API_BASE_URL = window.location.hostname.includes('localhost')
    ? 'http://localhost:5000'
    : 'https://api-production-xxxx.up.railway.app'; // <-- Usar tu URL de la API

// Cambiar la función loadData():
async function loadData() {
    try:
        // Usar la API en lugar del archivo local
        const response = await fetch(`${API_BASE_URL}/api/v1/infrastructure`);
        const data = await response.json();

        // El formato es diferente, adaptar
        infrastructureData = {
            type: 'FeatureCollection',
            features: data.facilities.map(f => ({
                type: 'Feature',
                geometry: f.geometry,
                properties: f
            }))
        };

        createRiskPolygons();
        createInfrastructureMarkers();
        updateStatistics();
        document.getElementById('loading').classList.add('hidden');
    } catch (error) {
        console.error('Error loading data:', error);
        alert('Error al cargar los datos');
    }
}
```

4. Guardar, commit y push:

```bash
git add web/js/map.js
git commit -m "Update frontend to use Railway API"
git push origin master
```

Railway desplegará automáticamente los cambios!

---

## ✨ ¡Listo! Tu App Está en Producción

### 🔗 URLs Finales

Después de completar todos los pasos, tendrás:

- **API**: `https://api-production-xxxx.up.railway.app`
- **Web**: `https://web-production-xxxx.up.railway.app`
- **PostgreSQL**: Disponible internamente en Railway

### 🧪 Verificar que Todo Funciona

**1. Test de API:**

Abrir en navegador:
```
https://api-production-xxxx.up.railway.app/api/v1/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T...",
  "database": {
    "connected": true,
    "database": "railway",
    "version": "PostgreSQL 16...",
    "postgis": "3.4..."
  }
}
```

**2. Test de Infraestructura:**

```
https://api-production-xxxx.up.railway.app/api/v1/infrastructure
```

Deberías ver JSON con las 20 instalaciones.

**3. Test de Visor Web:**

Abrir:
```
https://web-production-xxxx.up.railway.app
```

Deberías ver:
- ✅ Mapa cargado
- ✅ Marcadores de infraestructura
- ✅ Estadísticas en el panel
- ✅ Filtros funcionando

---

## 🎯 Próximos Pasos Opcionales

### Dominio Personalizado (Opcional)

1. Comprar dominio (ej: `geofeedback.cl`)
2. En cada servicio → Settings → Networking → Custom Domain
3. Agregar:
   - API: `api.geofeedback.cl`
   - Web: `app.geofeedback.cl`
4. Configurar DNS según instrucciones de Railway

### HTTPS y SSL

✨ **¡Ya está configurado!** Railway proporciona SSL automático para todos los dominios.

### Monitoreo

Ver logs en tiempo real:

1. Click en el servicio
2. Ir a tab "Deployments"
3. Click en deployment actual
4. Ver logs en tiempo real

---

## 🐛 Problemas Comunes

### ❌ Error: "Failed to build"

**Solución:**
1. Verificar que Root Directory esté correcto (`api` o `web`)
2. Verificar que Dockerfile exista en ese directorio
3. Ver logs de build para detalles

### ❌ API no se conecta a PostgreSQL

**Solución:**
1. Verificar que el servicio PostgreSQL esté running (verde)
2. Verificar que `DATABASE_URL` existe en variables de API
3. Ejecutar migración si no se hizo: `railway run python deployment/migrate_database.py`

### ❌ CORS errors en frontend

**Solución:**

En variables de API, cambiar:
```env
CORS_ORIGINS=https://web-production-xxxx.up.railway.app
```
(Usar tu URL exacta del frontend)

### ❌ "Out of memory" error

**Solución:**

En `api/Dockerfile`, reducir workers:
```dockerfile
CMD ["gunicorn", "--workers", "2", ...]
```

---

## 💰 Costos

Railway free tier incluye:
- **$5 USD gratis/mes**
- Suficiente para:
  - PostgreSQL pequeño
  - API con tráfico moderado
  - Frontend estático

**Uso estimado de este proyecto:**
- PostgreSQL: ~$3/mes
- API: ~$1/mes
- Web: ~$0.50/mes
- **Total: ~$4.50/mes** ✅ Dentro del free tier!

---

## 📚 Documentación Completa

Para configuración avanzada:
- [deployment/RAILWAY_DEPLOYMENT.md](deployment/RAILWAY_DEPLOYMENT.md) - Guía completa
- [deployment/README.md](deployment/README.md) - Overview de deployment
- [Railway Docs](https://docs.railway.app)

---

## 🆘 ¿Necesitas Ayuda?

- **Railway Discord**: [https://discord.gg/railway](https://discord.gg/railway)
- **GitHub Issues**: [Demo_geofeedback/issues](https://github.com/theChosen16/Demo_geofeedback/issues)
- **Railway Docs**: [docs.railway.app](https://docs.railway.app)

---

**¡Felicidades! 🎉** Tu aplicación de análisis de riesgo de inundación está en producción.

---

**GeoFeedback Chile** - Noviembre 2025
