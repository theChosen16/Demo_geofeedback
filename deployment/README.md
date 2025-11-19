# Despliegue - GeoFeedback Papudo

Este directorio contiene todos los archivos necesarios para desplegar el proyecto en producción.

## 📁 Contenidos

```
deployment/
├── RAILWAY_DEPLOYMENT.md    # Guía completa de despliegue en Railway
├── migrate_database.py      # Script de migración de base de datos
├── docker-compose.prod.yml  # Docker Compose para producción (opcional)
└── README.md               # Este archivo
```

## 🚀 Despliegue Rápido

### Railway (Recomendado)

Railway es la forma más fácil de desplegar el proyecto completo:

```bash
# 1. Instalar CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Crear proyecto
railway init

# 4. Agregar PostgreSQL
railway add

# 5. Desplegar
railway up
```

**Documentación completa:** [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

### Otros Proveedores Cloud

El proyecto también es compatible con:

- **Heroku** - Similar a Railway, requiere buildpacks para PostGIS
- **DigitalOcean App Platform** - Dockerfile nativo
- **Google Cloud Run** - Serverless con containers
- **AWS ECS/Fargate** - Más control, más complejidad
- **Azure Container Instances** - Windows-friendly

## 🗄️ Migración de Base de Datos

El script `migrate_database.py` inicializa PostgreSQL con:

- ✅ Extensiones PostGIS
- ✅ Schemas organizados (raw, processed, infrastructure, metadata, api)
- ✅ Tablas con índices espaciales
- ✅ Funciones PL/pgSQL para API
- ✅ Datos iniciales de infraestructura

### Uso

**En Railway:**

```bash
# Automático con variable de entorno
RUN_MIGRATIONS=true

# Manual
railway run python deployment/migrate_database.py
```

**En local:**

```bash
# Con variables de entorno
export DATABASE_URL="postgresql://user:pass@localhost:5432/geofeedback_papudo"
python deployment/migrate_database.py

# O con variables individuales
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=geofeedback_papudo
export DB_USER=geofeedback
export DB_PASSWORD=your-password
python deployment/migrate_database.py
```

## 🐳 Docker Compose (Producción)

Para despliegue self-hosted con Docker Compose:

```bash
# Build
docker-compose -f deployment/docker-compose.prod.yml build

# Up
docker-compose -f deployment/docker-compose.prod.yml up -d

# Logs
docker-compose -f deployment/docker-compose.prod.yml logs -f

# Down
docker-compose -f deployment/docker-compose.prod.yml down
```

## 🔐 Seguridad

### Variables de Entorno Requeridas

**API Flask:**

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<generar-con-secrets.token_hex(32)>
DATABASE_URL=postgresql://user:pass@host:port/db
CORS_ORIGINS=https://tu-dominio.com
```

**Web (si usa API):**

```env
API_URL=https://api.tudominio.com
```

### Generar SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Checklist de Seguridad

- [ ] SECRET_KEY único y aleatorio
- [ ] CORS limitado a dominios específicos
- [ ] HTTPS habilitado (automático en Railway)
- [ ] Credenciales de BD seguras
- [ ] Rate limiting configurado
- [ ] Variables de entorno no commiteadas
- [ ] `.env` en `.gitignore`

## 📊 Monitoreo

### Health Checks

**API:**
```bash
curl https://api.tudominio.com/api/v1/health
```

**Web:**
```bash
curl https://tudominio.com/health
```

**PostgreSQL:**
```bash
# Desde Railway CLI
railway connect postgres

# Verificar
SELECT postgis_version();
SELECT COUNT(*) FROM infrastructure.facilities_risk;
```

### Logs

**Railway:**
```bash
railway logs -s api
railway logs -s web
railway logs -s postgres
```

**Docker Compose:**
```bash
docker-compose logs -f api
docker-compose logs -f web
docker-compose logs -f postgis
```

## 🔄 CI/CD

El proyecto está configurado para despliegue automático:

**Railway:**
- Push a `master` → Deploy automático
- Health checks antes de routing
- Zero-downtime deployments
- Rollback con un click

**GitHub Actions** (opcional):

```yaml
# .github/workflows/deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [master]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## 🐛 Troubleshooting

### Error de conexión a BD

```bash
# Verificar DATABASE_URL
echo $DATABASE_URL

# Test de conexión
python3 -c "
import psycopg2
from urllib.parse import urlparse
url = urlparse('$DATABASE_URL')
conn = psycopg2.connect(
    dbname=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
print('✓ Conexión exitosa')
conn.close()
"
```

### CORS errors

1. Verificar `CORS_ORIGINS` en variables de entorno
2. Incluir protocolo: `https://dominio.com`
3. Sin trailing slash
4. Múltiples: separar con comas

### Migración falla

```bash
# Ver logs detallados
python deployment/migrate_database.py

# Verificar extensiones
psql $DATABASE_URL -c "SELECT * FROM pg_extension;"

# Verificar permisos
psql $DATABASE_URL -c "\du"
```

### Out of memory

1. Reducir workers de Gunicorn
2. Optimizar queries SQL
3. Implementar cache
4. Upgrade plan

## 📚 Documentación Adicional

- [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) - Guía completa de Railway
- [../api/README.md](../api/README.md) - Documentación de API
- [../web/README.md](../web/README.md) - Documentación de frontend
- [../geoserver/README.md](../geoserver/README.md) - GeoServer con Docker

## 🆘 Soporte

- **Issues:** https://github.com/theChosen16/Demo_geofeedback/issues
- **Email:** geofeedback@tudominio.cl
- **Railway Discord:** https://discord.gg/railway

---

**GeoFeedback Chile** - Noviembre 2025
