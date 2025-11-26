# ARREGLOS CRÍTICOS RAILWAY - 26 NOV 2025

## PROBLEMA IDENTIFICADO

**Síntomas:**
- ✅ Health check `/api/v1/health` → 200 OK
- ❌ Ruta raíz `/` → 502 Bad Gateway
- ❌ `/favicon.ico` → 502

**Causa probable:** Error en la ruta index al ejecutarse.

---

## SOLUCIÓN 1: Arreglar ruta index en app.py

### Problema
La ruta `/` está causando crash del worker, posiblemente por `gc.collect()` o error en imports.

### Fix para `api/app.py`

Reemplazar la ruta index (cerca de línea 153) con esta versión más robusta:

```python
@app.route('/')
def index():
    """API Landing - JSON only (ultra-lightweight)"""
    try:
        return jsonify({
            'service': 'GeoFeedback Papudo API',
            'version': '1.0.2',
            'status': 'running',
            'endpoints': {
                'health': '/api/v1/health',
                'docs': '/api/docs',
                'stats': '/api/v1/stats',
                'infrastructure': '/api/v1/infrastructure',
                'risk_point': '/api/v1/risk/point?lon=X&lat=Y'
            },
            'documentation': 'https://github.com/theChosen16/Demo_geofeedback',
            'memory_optimized': True,
            'database': 'connected'
        })
    except Exception as e:
        # Fallback si algo falla
        return {'error': 'Internal error', 'details': str(e)}, 500


@app.route('/favicon.ico')
def favicon():
    """Return 204 No Content for favicon to avoid 502"""
    return '', 204
```

**Cambios:**
1. Removido `gc.collect()` (puede causar problemas)
2. Agregado try-except para capturar cualquier error
3. Agregada ruta `/favicon.ico` para evitar 502

---

## SOLUCIÓN 2: Verificar que gunicorn se esté usando correctamente

### Verificar `api/Dockerfile` (línea 50+)

Asegurarse que el CMD tenga **exactamente** esto:

```dockerfile
CMD ["sh", "-c", "gunicorn \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers 1 \
    --timeout 120 \
    --max-requests 500 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level warning \
    app:app"]
```

---

## SOLUCIÓN 3: Agregar endpoint de debug

Agregar en `api/app.py` (después de la ruta index):

```python
@app.route('/debug/memory')
def debug_memory():
    """Check memory usage (development only)"""
    import sys
    import gc
    
    # Force garbage collection
    gc.collect()
    
    # Get object counts
    obj_counts = {}
    for obj in gc.get_objects():
        obj_type = type(obj).__name__
        obj_counts[obj_type] = obj_counts.get(obj_type, 0) + 1
    
    # Sort by count
    top_objects = sorted(obj_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    
    return jsonify({
        'python_version': sys.version,
        'top_objects': top_objects,
        'total_objects': len(gc.get_objects())
    })
```

---

## SOLUCIÓN 4: Verificar base de datos

### A. Conectar a Railway DB y verificar esquemas

```sql
-- Conectar a la base de datos Railway
-- Usar DATABASE_URL de Railway

-- 1. Verificar que el esquema 'api' existe
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name = 'api';

-- 2. Verificar tablas en esquema 'api'
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'api';

-- 3. Verificar función get_risk_statistics existe
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'api' 
  AND routine_name = 'get_risk_statistics';
```

### B. Si el esquema 'api' NO existe, crearlo:

```sql
-- Crear esquema api
CREATE SCHEMA IF NOT EXISTS api;

-- Crear tabla de ejemplo (risk_zones)
CREATE TABLE IF NOT EXISTS api.risk_zones (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(Polygon, 4326),
    risk_level VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Crear función get_risk_statistics
CREATE OR REPLACE FUNCTION api.get_risk_statistics()
RETURNS TABLE (
    total_zones INTEGER,
    high_risk INTEGER,
    medium_risk INTEGER,
    low_risk INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_zones,
        COUNT(*) FILTER (WHERE risk_level = 'HIGH')::INTEGER as high_risk,
        COUNT(*) FILTER (WHERE risk_level = 'MEDIUM')::INTEGER as medium_risk,
        COUNT(*) FILTER (WHERE risk_level = 'LOW')::INTEGER as low_risk
    FROM api.risk_zones;
END;
$$ LANGUAGE plpgsql;
```

---

## SOLUCIÓN 5: Variables de entorno Railway

Agregar estas variables en Railway Dashboard:

```env
# Flask
FLASK_ENV=production

# Logging
LOG_LEVEL=WARNING

# Database Pool (ya configurado en código)
DB_POOL_MIN=1
DB_POOL_MAX=5

# Railway detection
RAILWAY_ENVIRONMENT=production
```

---

## PASOS DE IMPLEMENTACIÓN

### 1. Arreglo Inmediato (app.py)

```bash
# Editar api/app.py y reemplazar la ruta index + agregar favicon
# Commit y push
git add api/app.py
git commit -m "Fix: Remove gc.collect() from index route, add favicon handler"
git push origin master
```

### 2. Verificar Database

```bash
# Conectar a Railway DB usando DATABASE_URL
psql $DATABASE_URL

# Ejecutar queries de verificación (ver SOLUCIÓN 4.A)
# Si falta algo, crear esquemas/funciones (ver SOLUCIÓN 4.B)
```

### 3. Monitorear Deploy

```bash
# Ver logs en tiempo real
railway logs -f

# Buscar errores específicos
railway logs | grep -i error
railway logs | grep -i 502
```

### 4. Test Endpoints

```bash
# Health check
curl https://demogeofeedback-production.up.railway.app/api/v1/health

# Root endpoint
curl https://demogeofeedback-production.up.railway.app/

# Debug memory (si implementaste)
curl https://demogeofeedback-production.up.railway.app/debug/memory
```

---

## VERIFICACIÓN DE ÉXITO

✅ **Todos estos deben retornar 200:**
- `/api/v1/health`
- `/` (index)
- `/favicon.ico` (204 No Content)
- `/api/docs`

✅ **NO debe haber 502 en logs**

✅ **Memoria debe estar < 200MB** (verificar en Railway dashboard)

---

## SI SIGUE FALLANDO

### Debug adicional en app.py

Agregar al inicio del archivo, después de los imports:

```python
import logging
import sys

# Configure logging más detallado temporalmente
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# Log que la app se está cargando
logging.info("=" * 50)
logging.info("LOADING APP - GeoFeedback Papudo")
logging.info("=" * 50)
```

Y en la ruta index:

```python
@app.route('/')
def index():
    """API Landing"""
    app.logger.info("Index route called")
    try:
        response = {
            'service': 'GeoFeedback Papudo API',
            'version': '1.0.2',
            'status': 'running'
        }
        app.logger.info(f"Returning response: {response}")
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error in index route: {e}", exc_info=True)
        return {'error': str(e)}, 500
```

---

## RESUMEN DE ARCHIVOS A MODIFICAR

1. **`api/app.py`** - Arreglar ruta index, quitar gc.collect(), agregar favicon
2. **`api/Dockerfile`** - Ya está optimizado (1 worker)
3. **Base de datos Railway** - Verificar esquema 'api' existe
4. **Variables Railway** - Agregar RAILWAY_ENVIRONMENT=production

---

**Prioridad de implementación:**
1. ⚠️ **URGENTE:** Arreglar ruta `/` en app.py (SOLUCIÓN 1)
2. 🔍 **IMPORTANTE:** Verificar base de datos (SOLUCIÓN 4)
3. 📊 **OPCIONAL:** Agregar endpoint debug (SOLUCIÓN 3)
