# Pasos para Completar la Configuración de Railway

✅ **Completado:**
- Railway configuration files creados
- Cambios pusheados a GitHub

## 📋 Pasos Siguientes (Requieren Railway Dashboard)

### Paso 1: Agregar PostgreSQL 🗄️

Railway CLI no puede agregar bases de datos, debes hacerlo desde el dashboard:

**Opción A: Con Keyboard Shortcut (Rápido)**
```bash
# Abrir dashboard
railway open
```
1. Presiona `Ctrl+K` (Windows) en el dashboard
2. Escribe "postgres"
3. Selecciona "Add PostgreSQL"
4. Espera 1-2 minutos a que se aprovisione

**Opción B: Con el Mouse**
1. En el dashboard, busca el botón **"+ New"** (superior izquierda o en el canvas)
2. Click en "Database"
3. Selecciona "PostgreSQL"
4. Click "Add PostgreSQL"

**Verificar que se agregó:**
- Deberías ver un nuevo servicio "PostgreSQL" en el canvas del proyecto
- Railway automáticamente creará la variable `DATABASE_URL` disponible para todos los servicios

---

### Paso 2: Habilitar PostGIS en PostgreSQL 🌍

Una vez que PostgreSQL esté running (ícono verde):

**Desde Railway CLI:**
```bash
# Conectar a la base de datos
railway connect postgres
```

**Si aparece error "Service 'postgres' not found", intenta:**
```bash
railway connect PostgreSQL
```

**Una vez conectado a psql, ejecutar:**
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Verificar que se instaló
SELECT postgis_version();

-- Salir
\q
```

**Deberías ver algo como:**
```
 postgis_version
-----------------
 3.4.x
```

---

### Paso 3: Reconfigurar Servicio Existente como API 🔧

El servicio "Demo_geofeedback" que falló necesita ser reconfigurado:

1. **En el dashboard**, localiza el servicio llamado "Demo_geofeedback" (el que tiene estado "Failed")

2. Click en ese servicio

3. Ve a la pestaña **"Settings"**

4. Busca la sección **"Build"** o **"Service Settings"**

5. Configura lo siguiente:
   - **Service Name**: Cambia a `api`
   - **Root Directory**: Escribe `api`
   - **Dockerfile Path**: Debe decir `Dockerfile` (relativo a api/)
   - Deja **Watch Paths** vacío o como está

6. **Guarda los cambios** (Click "Update" o "Save")

7. Ve a la pestaña **"Variables"**

8. Click **"+ New Variable"** y agrega las siguientes:

   ```env
   FLASK_ENV=production
   FLASK_DEBUG=False
   CORS_ORIGINS=*
   ```

9. **SECRET_KEY**: Genera uno nuevo:
   ```bash
   # En PowerShell local:
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copia el resultado y agrégalo como variable `SECRET_KEY`

10. Ve a **"Networking"** → Click **"Generate Domain"**
    - Anota la URL generada (algo como `api-production-xxxx.up.railway.app`)

---

### Paso 4: Crear Nuevo Servicio para Web 🌐

1. En el canvas del proyecto, click **"+ New"**

2. Selecciona **"GitHub Repo"**

3. Conecta con `theChosen16/Demo_geofeedback`

4. Railway creará un nuevo servicio

5. Click en el nuevo servicio → **"Settings"**

6. Configura:
   - **Service Name**: `web`
   - **Root Directory**: `web`
   - **Dockerfile Path**: `Dockerfile`

7. Click **"Update"** / **"Save"**

8. Ve a **"Networking"** → **"Generate Domain"**
   - Anota la URL generada (algo como `web-production-xxxx.up.railway.app`)

9. **Opcional**: Si quieres que el frontend use la API, agrega variable:
   - **Variables** tab → + New Variable:
   ```env
   API_URL=https://[tu-url-del-api-service].up.railway.app
   ```

---

### Paso 5: Ejecutar Migración de Base de Datos 📊

Una vez que:
- ✅ PostgreSQL está running con PostGIS habilitado
- ✅ El servicio API está configurado con Root Directory = `api`

**Desde PowerShell local:**

```bash
# Asegúrate de estar en el directorio del proyecto
cd C:\Users\alean\Desktop\Geofeedback\Demo

# Link al proyecto (si no lo has hecho)
railway link
# Selecciona: tu team → Demo_geofeedback → production

# Selecciona el servicio API
railway service
# Selecciona: api

# Ejecuta la migración
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

**Si aparece error "archivo no encontrado":**
```bash
# Asegúrate de estar en la raíz del proyecto
pwd  # Debería mostrar: .../Demo

# Si no, navega a la raíz
cd C:\Users\alean\Desktop\Geofeedback\Demo

# Intenta de nuevo
railway run python deployment/migrate_database.py
```

---

### Paso 6: Redesplegar Servicios 🚀

Los servicios deberían redesplegar automáticamente porque:
1. Pusheaste cambios a GitHub (los railway.toml)
2. Cambiaste configuración en el dashboard

**Pero si no se despliegan automáticamente:**

**Vía Dashboard:**
1. Click en servicio "api"
2. Pestaña "Deployments"
3. Click "Redeploy" en el último deployment

Repite para servicio "web"

**Vía CLI (Alternativa):**
```bash
# Para API
cd api
railway service  # Selecciona 'api'
railway up --detach

# Para Web
cd ../web
railway service  # Selecciona 'web'
railway up --detach
```

---

### Paso 7: Verificar que Todo Funciona ✅

**1. Verificar API:**

Abre en navegador:
```
https://[tu-api-domain].up.railway.app/api/v1/health
```

**Deberías ver JSON como:**
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

**Probar endpoint de infraestructura:**
```
https://[tu-api-domain].up.railway.app/api/v1/infrastructure
```

Deberías ver array JSON con 20 instalaciones.

**2. Verificar Web:**

Abre en navegador:
```
https://[tu-web-domain].up.railway.app
```

Deberías ver:
- ✅ Mapa cargado
- ✅ Panel lateral con estadísticas
- ✅ Controles de filtros
- ⚠️ Puede que no se vean marcadores aún (porque el frontend carga desde archivo local)

---

### Paso 8 (Opcional): Conectar Frontend con API 🔗

Si quieres que el frontend use la API en vivo en lugar del archivo GeoJSON local:

**Editar `web/js/map.js`:**

Encontrar la función `loadData()` y cambiar para usar la API:

```javascript
// Al inicio del archivo
const API_BASE_URL = window.location.hostname.includes('localhost')
    ? 'http://localhost:5000'
    : 'https://[tu-api-domain].up.railway.app';  // <-- Usar tu URL real

// Modificar loadData()
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

// Función fallback para datos locales
async function loadLocalData() {
    const response = await fetch('../data/processed/infrastructure_with_risk.geojson');
    infrastructureData = await response.json();
    createRiskPolygons();
    createInfrastructureMarkers();
    updateStatistics();
    document.getElementById('loading').classList.add('hidden');
}
```

Luego commit y push:
```bash
git add web/js/map.js
git commit -m "Connect frontend to Railway API"
git push origin master
```

Railway redesplegará automáticamente el servicio web.

---

## 🎯 Resumen de URLs Finales

Una vez completados todos los pasos, tendrás:

- **PostgreSQL**: `railway` (internal only, con PostGIS habilitado)
- **API**: `https://api-production-xxxx.up.railway.app`
  - Health: `/api/v1/health`
  - Stats: `/api/v1/stats`
  - Infrastructure: `/api/v1/infrastructure`
- **Web**: `https://web-production-xxxx.up.railway.app`

---

## 🐛 Troubleshooting

### "Service not found" al hacer railway connect

**Solución:**
```bash
# Verificar servicios disponibles
railway service
# Aparecerá lista, usa el nombre exacto

# Si el servicio se llama "PostgreSQL" en lugar de "postgres":
railway connect PostgreSQL
```

### Deployment sigue fallando

**Verificar:**
1. Root Directory está configurado (`api` o `web`) en Settings
2. Dockerfile existe en esa ruta (`api/Dockerfile` o `web/Dockerfile`)
3. Ver logs de deployment:
   ```bash
   railway logs
   ```

### API no se conecta a PostgreSQL

**Verificar:**
1. PostgreSQL está running (verde en dashboard)
2. Variable `DATABASE_URL` existe (Variables tab del servicio API)
3. Migración se ejecutó exitosamente

### CORS errors en frontend

**Solución:**
En variables del servicio API, cambiar:
```env
CORS_ORIGINS=https://[tu-web-domain].up.railway.app
```
(Usar tu dominio exacto del servicio web, sin trailing slash)

---

## 📞 Comandos Útiles de Railway CLI

```bash
# Ver estado actual
railway status

# Cambiar de servicio
railway service

# Ver variables
railway variables

# Ver logs en tiempo real
railway logs

# Abrir dashboard
railway open

# Ejecutar comando con env de Railway
railway run [comando]

# Conectar a base de datos
railway connect postgres

# Desplegar
railway up

# Ver versión
railway version
```

---

## ✅ Checklist Final

Antes de considerar el despliegue completo:

- [ ] PostgreSQL agregado y running
- [ ] PostGIS habilitado (verificado con `SELECT postgis_version();`)
- [ ] Servicio API configurado (Root Directory = `api`)
- [ ] Variables de entorno de API configuradas (FLASK_ENV, SECRET_KEY, CORS_ORIGINS)
- [ ] Dominio generado para API
- [ ] Servicio Web creado y configurado (Root Directory = `web`)
- [ ] Dominio generado para Web
- [ ] Migración de BD ejecutada exitosamente
- [ ] API responde en `/api/v1/health` con status "healthy"
- [ ] API retorna datos en `/api/v1/infrastructure`
- [ ] Web carga correctamente en navegador
- [ ] (Opcional) Frontend conectado a API en vivo

---

**¡Éxito!** 🎉 Si completaste todos los pasos, tu aplicación debería estar funcionando en Railway.
