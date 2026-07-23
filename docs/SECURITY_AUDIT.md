# Auditoría de Seguridad y Privacidad - GeoFeedback Demo

## Historial de Auditorías

| Fecha | Estatus | Responsable |
|-------|---------|-------------|
| 20 de Enero, 2026 | ✅ PASADO (Con observaciones) | Interno |
| 9 de Abril, 2026 | ✅ PASADO — 0 alertas activas | Automatizado (GitHub CodeQL + Dependabot) |
| 30 de Mayo, 2026 | ✅ RESUELTO — 8 hallazgos corregidos | Claude Code (revisión arquitectónica completa) |
| 31 de Mayo, 2026 | ✅ RESUELTO — 6 hallazgos de seguimiento corregidos | Claude Code (auditoría completa post-merge PR #11) |
| 10 de Junio, 2026 | ✅ RESUELTO — 7 hallazgos corregidos | Claude Code (PR #13) |
| 13 de Junio, 2026 | ✅ RESUELTO — 4 hallazgos corregidos | Claude Code (auditoría arquitectónica completa, PR #14) |
| 20 de Junio, 2026 | ✅ RESUELTO — 2 hallazgos corregidos | Claude Code (rutina de auditoría programada) |
| 27 de Junio, 2026 | ✅ RESUELTO — 5 hallazgos corregidos | Claude Code (auditoría arquitectónica de scripts, infra y backend) |
| 4 de Julio, 2026 | ✅ RESUELTO — 2 hallazgos corregidos | Claude Code (auditoría de disponibilidad/DoS en runtime Flask) |
| 11 de Julio, 2026 | ✅ RESUELTO — 2 hallazgos corregidos | Claude Code (auditoría de entrypoint de despliegue y superficie de lectura no autenticada) |
| 18 de Julio, 2026 | ✅ RESUELTO — 3 hallazgos corregidos | Claude Code (auditoría arquitectónica del backend FastAPI actual) |

---

## Auditoría Julio 2026 — Backend FastAPI Actual (18 de Julio)

**Fecha:** 18 de Julio, 2026
**Estatus:** ✅ **RESUELTO — 3 hallazgos corregidos**

Revisión arquitectónica del **runtime FastAPI en producción** (`backend/app/`: `main.py`,
`core/security.py`, `core/config.py`, `api/endpoints/*`, `tasks/worker.py`, `db/*`) más el
frontend React (`frontend/src/`), `Dockerfile`, `docker-compose.yml`, `railway.toml` y CI.

Las auditorías previas de este documento describen la arquitectura **Flask** ya retirada
(`api/app.py`, `api/start.sh`, `templates/index.html`, `static/js/app.js`). El backend
vigente es **FastAPI + Celery**, por lo que esta auditoría revalida la postura sobre el
código realmente desplegado. Se **reconfirmó** lo ya endurecido:

- **Sin sinks XSS:** el frontend React no usa `dangerouslySetInnerHTML`; todo se renderiza
  como texto vía JSX. El legacy `static/js/app.js` mantiene el patrón "escapar primero".
- **Sin inyección SQL:** todas las lecturas usan el ORM de SQLModel/SQLAlchemy con
  parámetros; las escrituras de coordenadas usan `WKTElement` con SRID fijo.
- **Sin inyección de cabeceras de email:** el endpoint `/contact` valida el remitente con
  `EmailStr` y solo lo coloca en el campo JSON `reply_to` de la API de Resend; `to` es fijo.
- **CORS fail-closed en producción, cabeceras de seguridad + CSP, secretos fuera del repo,
  anonimización de IP con HMAC-SHA256, `/observability` con token en tiempo constante**, y
  **rate limiting** en `/analyze`, `/interpret`, `/chat`, `/contact`, `/stats` y `/visit`.
- **Timeout wall-clock en GEE:** el residual de la auditoría del 11 de Julio ya está
  resuelto en `tasks/worker.py` (`get_info_with_timeout` con `ThreadPoolExecutor`).

Se hallaron **tres vectores residuales**, todos de agotamiento de recursos / configuración.

### Hallazgos y Correcciones

#### 🟠 MEDIO — `GET /api/v1/analyze/status/{task_id}` sin rate limiting

| Aspecto | Detalle |
|---------|---------|
| **Archivo** | `backend/app/api/endpoints/analyze.py` |
| **Problema** | Único endpoint público **sin** limitador. Un cliente anónimo podía sondear el backend de resultados de Celery/Redis de forma ilimitada (el frontend lo consulta cada 2 s durante cada análisis). Misma clase de DoS de lectura no autenticada que ya se corrigió para `/stats` el 11 de Julio. |
| **Impacto** | Agotamiento de recursos de Redis/Celery por peticiones baratas y anónimas. |
| **Corrección** | Nuevo `status_limiter` (90/min/IP, reutilizando la clase `RateLimiter` Redis-first con fallback en memoria). 90/min deja holgura para varios análisis concurrentes por IP (~30 req/min cada uno) sin degradar el sondeo legítimo. Cubierto por `AnalyzeStatusRateLimitTests`. |
| **Fuera de alcance (a propósito)** | Este límite mitiga **agotamiento de recursos**, no autorización: `task_id` es un uuid4 de Celery (~122 bits de entropía, no derivable de lat/lng/approach), así que la fuerza bruta ya era inviable con o sin límite. El endpoint sigue sin verificar quién originó la tarea — quien obtenga un `task_id` válido (filtrado por logs, `Referer`, o un futuro enlace "compartir resultados" en la URL) puede leer ese análisis completo. Es el modelo de acceso aceptado para una demo pública sin sesiones de usuario (el `task_id` funciona como bearer-token no autenticado); documentado explícitamente en `backend/app/core/security.py` junto a `status_limiter` para que quede claro que un cambio futuro que reduzca esa entropía o exponga el `task_id` en una ruta del SPA rompería esta invariante. |

#### 🟠 MEDIO — CORS: origen comodín combinado con credenciales

| Aspecto | Detalle |
|---------|---------|
| **Archivo** | `backend/app/main.py` |
| **Problema** | El middleware CORS se registraba siempre con `allow_credentials=True`. En despliegues **no productivos** sin `ALLOWED_ORIGINS` (dev y el `docker-compose.yml` incluido), `cors_origins` devuelve `["*"]`; Starlette entonces **refleja cualquier `Origin`** y emite `Access-Control-Allow-Credentials: true`, habilitando peticiones autenticadas cross-origin desde cualquier sitio. En Railway la postura fail-closed ya lo impedía, pero el path de docker-compose es un despliegue soportado y alcanzable. |
| **Impacto** | Lectura cross-origin con credenciales desde orígenes arbitrarios en despliegues self-hosted/dev. |
| **Corrección** | `allow_credentials` se deriva de los orígenes vía `resolve_cors_allow_credentials()`: con comodín las credenciales quedan deshabilitadas (Starlette responde `Access-Control-Allow-Origin: *` sin reflejar el `Origin`). Con `ALLOWED_ORIGINS` explícito el comportamiento no cambia. La comprobación usa **pertenencia** (`"*" in origins`), no igualdad de listas — una revisión adversarial detectó que la primera versión (`origins != ["*"]`) no cubría una lista mixta como `["https://geofeedback.cl", "*"]` (p.ej. `ALLOWED_ORIGINS` mal configurado), donde Starlette igual trata el comodín como wildcard total y habría colado `allow_credentials=True`. Cubierto por `CorsCredentialedWildcardTests` (integración) y `ResolveCorsAllowCredentialsTests` (las 3 ramas de la función pura, incluida la regresión de lista mixta). |

#### 🟡 BAJO — `log_event` hasheaba innecesariamente cada registro estructurado a stdout

| Aspecto | Detalle |
|---------|---------|
| **Archivo** | `backend/app/core/security.py` |
| **Problema** | `log_event` ejecutaba `print(hashlib.sha256(str(log_data)...).hexdigest()[:0], ...)` — un "dummy flush" que calculaba un SHA-256 completo del registro (incluyendo IP ya anonimizada y metadatos) para luego truncarlo a cadena vacía en cada evento. Trabajo criptográfico muerto y confuso en un camino caliente. |
| **Impacto** | Desperdicio de CPU por evento y ruido de mantenibilidad (código engañoso en el módulo de seguridad). |
| **Corrección** | Reemplazado por `print(import_json_dumps(log_data), flush=True)`, que emite el registro como JSON de una sola línea (formato que Railway/Loki parsean directamente) preservando el flush explícito a stdout. |

### Recomendaciones residuales (no corregidas — mayor riesgo de regresión o fuera de alcance de código)

- **Confianza en `X-Forwarded-For`.** `get_client_ip` toma la última IP del encabezado, correcto tras un único proxy de confianza (el edge de Railway lo antepone). En un despliegue sin proxy (docker-compose expuesto directamente) el encabezado es controlable por el cliente y permitiría evadir el rate limiting rotándolo. Conviene hacer configurable el número de saltos de proxy de confianza si se soporta ese modo de despliegue.
- **`docker-compose.yml` con `POSTGRES_PASSWORD: password123` e `IP_HASH_SALT` de desarrollo.** Aceptable para desarrollo local, pero debería documentarse que no se use en despliegues accesibles.
- **CSP `script-src 'unsafe-inline'`.** Requiere nonces/refactor del bootstrap de Google Maps para eliminarse; ya documentado.

---

## Auditoría Julio 2026 — Entrypoint de Despliegue y Lectura No Autenticada (11 de Julio)

**Fecha:** 11 de Julio, 2026
**Estatus:** ✅ **RESUELTO — 2 hallazgos corregidos**

Revisión arquitectónica completa (backend `api/app.py`, `database.py`, `config.py`, `gee_config.py`; frontend `templates/index.html` + `static/js/app.js`; despliegue `Dockerfile`, `railway.toml`, scripts de arranque; CI). Se **reconfirmó** la postura ya endurecida por auditorías previas:

- **Sin sinks XSS explotables:** el frontend aplica el patrón "escapar primero, formatear después" en todos los renders de datos no confiables (respuestas del servidor, salida de Gemini, entrada de usuario). Todos los `target="_blank"` llevan `rel="noopener noreferrer"`.
- **Inyección SQL:** todas las queries en `database.py` son parametrizadas; los identificadores dinámicos usan `psycopg2.sql`.
- **CORS fail-closed** en producción, **cabeceras de seguridad + CSP** aplicadas, **secretos fuera del repo** (`.gitignore` cubre `.env` y `service-account-key.json`), **anonimización de IP con HMAC**, **`/observability`** protegido por token en tiempo constante, y **rate limiting** en `/analyze`, `/interpret`, `/chat`, `/contact` y el logging de visitas.

Se hallaron **dos vectores residuales**, ambos de agotamiento de recursos / exposición de secretos operativa.

### Hallazgos y Correcciones

#### 🟠 MEDIO — `api/start.sh` filtraba secretos a los logs y arrancaba el servidor de desarrollo

| Aspecto | Detalle |
|---------|---------|
| **Archivo** | `api/start.sh` |
| **Problema** | Script huérfano (no referenciado por `Dockerfile`/`railway.toml`, que despliegan vía Gunicorn `app:app`) pero peligroso si alguien lo invoca: (1) volcaba el entorno con `env \| grep -viE "SECRET\|KEY\|PASSWORD\|TOKEN\|CREDENTIALS"`, filtro que **NO** enmascara `DATABASE_URL`, `REDIS_URL` ni `IP_HASH_SALT` — todos con credenciales/secretos — hacia el stream centralizado de logs; (2) lanzaba `python -u simple_app.py`, un archivo inexistente, invocando el **servidor de desarrollo de Flask** (con debugger, sin hardening) en un contexto de producción. |
| **Impacto** | Exposición de credenciales de base de datos/Redis y del salt de anonimización en logs; ejecución del servidor de desarrollo si el entrypoint se reactivara. |
| **Corrección** | Reescrito como entrypoint de producción correcto que hace `exec gunicorn ... app:app` (espejo del `Dockerfile`), sin volcado de entorno y sin servidor de desarrollo. |

#### 🟡 BAJO/MEDIO — `GET /api/v1/stats` sin límite: lectura no autenticada que castiga la BD

| Aspecto | Detalle |
|---------|---------|
| **Archivo** | `api/app.py` (`stats()`) |
| **Problema** | El endpoint público ejecutaba **dos `COUNT(*)`** contra el Postgres del free-tier en **cada** petición, sin autenticación ni rate limiting. Un flood de `GET /api/v1/stats` se traduce en carga de BD no acotada (DoS de disponibilidad/costo) — el análogo de lectura al flood de escritura de visitas que ya estaba mitigado en `GET /`. |
| **Impacto** | Agotamiento de recursos de la base de datos gratuita mediante peticiones baratas y anónimas. |
| **Corrección** | Nuevo `stats_limiter` (60/min/IP, reutilizando la clase `RateLimiter` Redis-first). Al superar el límite se devuelve `429` con el mismo payload seguro `{"visits":0,"analyses":0}` que el frontend ya tolera ante respuestas no-OK, protegiendo la BD sin degradar la experiencia legítima. Cubierto por `StatsRateLimitTests`. |

### Recomendaciones residuales (no corregidas en este PR — mayor riesgo de regresión)

- **Timeout wall-clock en el camino GEE de `/analyze`.** Las llamadas síncronas `.getInfo()` no tienen timeout a nivel de aplicación (solo el `--timeout 120` de Gunicorn, que mata el worker completo). Conviene aplicar el mismo patrón de `_GEMINI_EXECUTOR` (`future.result(timeout=...)`) ya usado para Gemini, para no fijar los 2 workers ante respuestas lentas de Earth Engine.
- **CSP `script-src 'unsafe-inline'`.** Requiere refactor de plantilla (mover handlers inline y bloques `<script>`) para eliminarse; documentado ya en el código.

---

## Auditoría Julio 2026 — Disponibilidad y DoS en el Runtime Flask (4 de Julio)

**Fecha:** 4 de Julio, 2026
**Estatus:** ✅ **RESUELTO — 2 hallazgos corregidos**

Revisión arquitectónica del *runtime* de peticiones (`api/app.py`) con foco en superficies de **denegación de servicio y agotamiento de recursos** que las auditorías previas —centradas en secretos, CORS, XSS y anonimización— no habían cubierto. Se reconfirmó que el frontend sigue sin sinks XSS explotables (patrón "escapar primero, formatear después") y que las entradas de `/analyze`, `/interpret`, `/chat` y `/contact` están validadas y acotadas. Se hallaron **dos vectores de disponibilidad**.

### Hallazgos y Correcciones

#### 🟠 MEDIO — Escritura no acotada en analytics + envenenamiento de métricas vía `GET /` (`api/app.py`)

| Función | Descripción |
|---------|-------------|
| `landing()` | Cada visita a la landing ejecutaba `database.log_visit()` → un `INSERT` en `metadata.page_visits` **sin rate limiting** (a diferencia de `/analyze` y `/contact`, que sí lo tenían). Un atacante no autenticado podía inundar `GET /` para: (a) hacer crecer sin límite la Postgres del *free tier* de Railway (agotamiento de almacenamiento / costo → DoS), y (b) inflar arbitrariamente el contador público de "visitas" que muestra el sitio (integridad de datos). |

**Corrección:** Se añadió un `RateLimiter` dedicado (`visit_limiter`, 30 req/min/IP, respaldado por Redis igual que los demás). Solo se **gatea la escritura** de analytics; la página se sirve siempre, incluso cuando el logging queda throttleado, por lo que la UX de usuarios legítimos no cambia mientras los floods quedan acotados. Cubierto por `VisitLoggingRateLimitTests`.

#### 🟠 MEDIO — Timeout de Gemini no se aplica realmente; un worker de Gunicorn puede bloquearse (`api/app.py`)

| Función | Descripción |
|---------|-------------|
| `call_gemini_with_retry()` | Usaba `with concurrent.futures.ThreadPoolExecutor() as executor:` por llamada. Aunque `future.result(timeout=...)` lanza `TimeoutError`, **salir del bloque `with` ejecuta `executor.shutdown(wait=True)`, que bloquea el hilo de la petición hasta que la llamada HTTP lenta termina** — anulando el *wall-clock limit* que el propio docstring prometía. Con solo 2 workers en el *free tier*, unas pocas respuestas lentas/colgadas de la API de Gemini podían fijar todos los workers (DoS de disponibilidad). |

**Corrección:** Se reemplazó el executor por-llamada por un **executor persistente a nivel de módulo** (`_GEMINI_EXECUTOR`) que nunca se apaga por petición. Ahora `future.result(timeout)` retorna de inmediato al vencer el timeout y el hilo de la petición (y el worker de Gunicorn) queda libre; el hilo colgado termina en segundo plano sin retener la petición. Verificado por `GeminiTimeoutTests` (la llamada retorna en <2 s ante un upstream de 5 s; el código anterior bloqueaba ~5 s).

### Verificación

- `python -m unittest discover -s tests -p "test_*.py"` → **21/21 OK** (2 tests nuevos de regresión).
- `python -m compileall api scripts tests` → OK.

---

## Auditoría Junio 2026 — Scripts de Datos, Infraestructura y Backend (27 de Junio)

**Fecha:** 27 de Junio, 2026
**Estatus:** ✅ **RESUELTO — 5 hallazgos corregidos**

Revisión arquitectónica completa con foco en la capa de **scripts de inicialización/datos** (no cubierta en profundidad por auditorías previas centradas en `app.py`), además de una pasada de seguimiento sobre el backend Flask. Se confirmó que el frontend (`app.js`, `index.html`) sigue sin sinks XSS explotables: el patrón "escapar primero, formatear con regex después" es seguro porque `insertAdjacentHTML` no des-escapa entidades, y el `color` del AQI proviene de una whitelist ternaria, no de la API. Se hallaron **secretos versionados** y dos debilidades de defensa en profundidad.

### Hallazgos y Correcciones

#### 🔴 ALTO — Contraseña de rol de BD hardcodeada en SQL versionada (`scripts/sql/01_setup_postgis_schema.sql`)

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `scripts/sql/01_setup_postgis_schema.sql` | `CREATE ROLE geofeedback_api ... PASSWORD 'api_readonly_2025'` | El rol de base de datos de la API se creaba con una contraseña en texto plano **commiteada al repositorio**. `scripts/init_railway_db.py` ejecuta esta SQL contra la **base de datos de producción de Railway**, por lo que cualquiera con acceso de lectura al repo obtiene una credencial de BD potencialmente válida. Si el puerto de Postgres es alcanzable (Railway expone proxies TCP públicos para bases de datos), permite conexión y lectura de datos. |

**Corrección:** Eliminada la contraseña literal. El rol ahora lo crean los *runners* (`init_railway_db.py` vía parámetro enlazado de psycopg2; `run_postgis_setup.sh` vía `psql -v ... \gexec`) leyendo la contraseña desde la variable de entorno `GEOFEEDBACK_API_DB_PASSWORD`. Los `GRANT` al rol en `01/04/05/06_*.sql` se hicieron **condicionales** (`IF EXISTS (SELECT FROM pg_roles ...)`) para que los scripts no fallen cuando el rol aún no se ha provisto. Documentada la nueva variable en `api/.env.example`.

#### 🟠 MEDIO — Contraseña de BD `Papudo2025` hardcodeada en múltiples scripts (`scripts/*.sh`, `scripts/*.py`, `api/README.md`)

| Archivo | Descripción |
|---------|-------------|
| `scripts/02_load_raster_data.sh`, `scripts/run_postgis_setup.sh` | `export PGPASSWORD="Papudo2025"`. Estos scripts además se copian a la imagen Docker de producción (`COPY scripts/ ./scripts/`), enviando el secreto dentro del contenedor. |
| `scripts/08_analyze_infrastructure_risk.py`, `scripts/06_test_postgis.py` | `'password': 'Papudo2025'` en el dict de conexión. |
| `scripts/03_vectorize_amenaza.py` | `os.getenv('DB_PASSWORD', 'Papudo2025')` — default inseguro. |
| `api/README.md` | Documentaba la contraseña real en el bloque `.env`. |

**Corrección:** Eliminadas todas las contraseñas literales. Los `.sh` exigen `PGPASSWORD` por entorno (`${PGPASSWORD:?...}`, falla si no está). Los `.py` leen `os.getenv('DB_PASSWORD')` sin default. `README.md` usa `your-password-here`.

#### 🟠 MEDIO — CORS abierto (wildcard) en producción si `ALLOWED_ORIGINS` no está configurado (`api/app.py`)

| Función | Descripción |
|---------|-------------|
| Configuración CORS a nivel de módulo | Cuando `ALLOWED_ORIGINS` estaba vacío/`*`, el código caía a `CORS(app)` (cualquier origen) emitiendo solo un `warnings.warn` — incluso con `RAILWAY_ENVIRONMENT` presente. Una mala configuración dejaba las respuestas legibles por cualquier sitio web cross-origin. |

**Corrección:** *Fail-closed* en producción, coherente con el hard-fail de `SECRET_KEY` en `config.py`: si `RAILWAY_ENVIRONMENT` está presente y `ALLOWED_ORIGINS` no, **no se habilita CORS** (la app se sirve same-origin, así que el frontend sigue operando y los lectores cross-origin quedan bloqueados por el navegador). En local se mantiene el wildcard. Verificado: en producción sin orígenes, no se emite `Access-Control-Allow-Origin`.

#### 🟡 BAJO — Anonimización de IP reversible: SHA-256 sin sal (`api/app.py`)

| Función | Descripción |
|---------|-------------|
| `hash_ip()` | Usaba `hashlib.sha256(ip)` sin clave. El espacio IPv4 (~4.3 mil millones) es suficientemente pequeño para revertir cualquier hash sin sal con una tabla precomputada, anulando el propósito de privacidad de los logs/analytics. |

**Corrección:** Migrado a `hmac.new(_IP_HASH_KEY, ip, sha256)` con clave secreta (`IP_HASH_SALT`, con fallback a `SECRET_KEY`). El digest ya no es reversible sin el secreto. Documentada `IP_HASH_SALT` en `api/.env.example`.

#### 🔵 INFO — Campo `approach` sin cota antes de interpolar en el prompt de Gemini (`api/app.py`)

| Endpoint | Descripción |
|----------|-------------|
| `/api/v1/interpret` | `approach` se interpolaba en el prompt sin truncar, a diferencia de `location` (200) y `meta_date` (30) — superficie inconsistente de inyección de prompt / costo de tokens (acotada solo por `MAX_CONTENT_LENGTH`). |

**Corrección:** `approach` truncado a 50 caracteres.

### Verificación post-fix

- Suite de tests (`tests/`): **19/19 ✅**
- `python -m compileall api scripts tests`: ✅
- `python scripts/monitor_deploy.py --help`: ✅
- CORS producción sin `ALLOWED_ORIGINS` → sin header `Access-Control-Allow-Origin` (fail-closed) ✅
- `hash_ip()` produce digest HMAC distinto al SHA-256 simple ✅

### Resumen Consolidado (Junio 2026 — 27 de Junio)

| Hallazgo | Severidad | Estado |
|----------|-----------|--------|
| Contraseña de rol de BD hardcodeada en SQL | 🔴 ALTO | ✅ Resuelto |
| Contraseña `Papudo2025` en scripts/README | 🟠 MEDIO | ✅ Resuelto |
| CORS wildcard en producción (fail-open) | 🟠 MEDIO | ✅ Resuelto |
| Anonimización de IP reversible (SHA-256 sin sal) | 🟡 BAJO | ✅ Resuelto |
| `approach` sin cota en prompt de Gemini | 🔵 INFO | ✅ Resuelto |

### Acción manual pendiente (fuera del código)

- [ ] **Rotar** la credencial del rol `geofeedback_api`: la contraseña `api_readonly_2025` quedó en el historial de git; debe considerarse comprometida. Definir `GEOFEEDBACK_API_DB_PASSWORD` en Railway/entorno y re-ejecutar `init_railway_db.py` para aplicar la nueva contraseña (`ALTER ROLE`).
- [ ] **Rotar** cualquier base de datos local/compartida que aún use `Papudo2025`.
- [ ] (Recomendado) Considerar `git-filter-repo` para purgar las contraseñas del historial, o asumirlas comprometidas y rotarlas (suficiente si las bases ya no son alcanzables).
- [ ] (Opcional) Definir `IP_HASH_SALT` dedicado en producción en lugar de reutilizar `SECRET_KEY`.

---

## Auditoría Junio 2026 — Revisión Arquitectónica Completa (PR #14)

**Fecha:** 13 de Junio, 2026 (Completada el 21 de Junio, 2026)
**Estatus:** ✅ **RESUELTO — 4 hallazgos corregidos**

Revisión integral del repositorio tras mergear los PRs #12 y #13. Cubrió backend Flask (`app.py`, `config.py`, `database.py`), frontend JS (`app.js`), template HTML, Dockerfile, `railway.toml`, CI/CD, `.env.example` y dependencias.

### Hallazgos y Correcciones

#### 🟠 MEDIO — Inconsistencia de variable CORS: `CORS_ORIGINS` vs `ALLOWED_ORIGINS` (`api/app.py`, `api/.env.example`)

| Archivo | Descripción |
|---------|-------------|
| `api/app.py` | Lee `ALLOWED_ORIGINS` para configurar Flask-CORS. |
| `api/.env.example` | Documentaba `CORS_ORIGINS=*` como variable a configurar. |

Las dos variables son distintas. Si un operador seguía la documentación del `.env.example` y configuraba solo `CORS_ORIGINS` en Railway, `app.py` no la leía → CORS permanecía abierto (wildcard) en producción sin advertencia.

**Corrección:** `app.py` ahora lee `ALLOWED_ORIGINS` con fallback a `CORS_ORIGINS` para compatibilidad con deployments existentes:
```python
ALLOWED_ORIGINS = (
    os.environ.get('ALLOWED_ORIGINS', '') or
    os.environ.get('CORS_ORIGINS', '')
)
```
`.env.example` actualizado para mostrar `ALLOWED_ORIGINS` como variable primaria con el valor de producción de ejemplo.

---

#### 🟡 BAJO — `SECRET_KEY` de Flask calculada pero nunca aplicada al app (`api/app.py`)

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/config.py` | `Config.SECRET_KEY` | Calcula la clave y en producción lanza `RuntimeError` si no está configurada (correcto). |
| `api/app.py` | Post-creación de `app` | Nunca hacía `app.config['SECRET_KEY'] = Config.SECRET_KEY` → Flask usaba `None` como llave secreta. |

Con `SECRET_KEY = None`, cualquier intento de usar sesiones Flask firmaría cookies con una llave nula (inseguro). Aunque las sesiones no se usan actualmente, el patrón establece una base incorrecta y la validación de producción en `config.py` sería inútil si nunca se aplica el valor.

**Corrección:** `app.py` importa `Config` y aplica la llave inmediatamente después de crear la instancia Flask:
```python
from config import Config as _AppConfig
app.config['SECRET_KEY'] = _AppConfig.SECRET_KEY
```

---

#### 🔵 INFO — `location` del lugar no enviado desde el frontend a `/api/v1/analyze` (`api/static/js/app.js`)

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/static/js/app.js` | `analyzeTerritory()` payload | El PR #13 corrigió el backend para extraer `location` del body JSON, pero el frontend nunca lo incluía en el payload → la BD registraba `"Unknown"` como `location_name` en cada análisis. |

**Corrección:** `analyzeTerritory()` ahora incluye `location: selectedPlace.name` en el payload enviado a `/api/v1/analyze`, completando el circuito de analytics.

---

#### 🔵 INFO — Sin Subresource Integrity (SRI) en recursos CDN (`api/templates/index.html`)

| Recurso | URL | Estado |
|---------|-----|--------|
| Font Awesome 6.4.0 | `cdnjs.cloudflare.com/.../all.min.css` | ✅ Añadida integridad sha512 |
| Chart.js 4.4.1 | `cdnjs.cloudflare.com/.../chart.umd.min.js` | ✅ Añadida integridad sha512 |

Un proveedor CDN comprometido o un ataque de red (MITM) podría servir JavaScript/CSS malicioso. La CSP actual permite `cdnjs.cloudflare.com` explícitamente sin validación de contenido.

**Corrección:** Se añadieron los atributos `integrity` y `crossorigin="anonymous"` usando los hashes SHA-512 publicados en cdnjs para cada recurso:
```html
<link
  rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
  integrity="sha512-iecdLmaskl7CVkqkXNQ/ZH/XLlvWZOJyj7Yy7tcenmpD1ypASozpmT/E0iPtmFIB46ZmdtAc9eNBvH0H/ZpiBw=="
  crossorigin="anonymous"
/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js" integrity="sha512-CQBWl4fJHWbryGE+Pc7UAxWMUMNMWzWxF4SQo9CgkJIN1kx6djDQZjh3Y8SZ1d+6I+1zze6Z7kHXO7q3UyZAWw==" crossorigin="anonymous"></script>
```

### Resumen Consolidado (Junio 2026 - Auditoría PR #14)

| Hallazgo | Severidad | Estado |
|----------|-----------|--------|
| CORS env var inconsistente | 🟠 MEDIO | ✅ Resuelto en código |
| SECRET_KEY no aplicada a Flask app | 🟡 BAJO | ✅ Resuelto en código |
| location no enviado en payload analyze | 🔵 INFO | ✅ Resuelto en código |
| SRI ausente en recursos CDN | 🔵 INFO | ✅ Resuelto en código |

---

## Auditoría Junio 2026 (Rutina Programada)

**Fecha:** 20 de Junio, 2026
**Estatus:** ✅ **RESUELTO — 2 hallazgos corregidos**

Revisión arquitectónica de seguimiento (backend Flask, configuración, variables de entorno y logging). Las correcciones de PRs anteriores (#11, #12, #13) se verificaron vigentes; se encontraron dos hallazgos nuevos.

### Hallazgos y Correcciones

#### 🔴 ALTO — Desalineación de variable de entorno deja CORS abierto en producción (`api/.env.example`, `api/config.py`)

| Archivo | Descripción |
|---------|-------------|
| `api/app.py` | El gate de CORS (`CORS(app, origins=...)`) lee **únicamente** `ALLOWED_ORIGINS`. |
| `api/.env.example` | Documentaba `CORS_ORIGINS` como la variable a configurar — nombre **distinto** al que realmente lee `app.py`. |
| `api/config.py` | Definía `Config.CORS_ORIGINS` (leyendo `CORS_ORIGINS`), pero ningún módulo lo importaba: código muerto que reforzaba la documentación incorrecta. |

Un operador que siguiera el `.env.example` oficial y configurara `CORS_ORIGINS` en Railway creería haber restringido CORS, pero `app.py` seguiría sin ver `ALLOWED_ORIGINS` definida y abriría CORS a **cualquier origen** en producción (`CORS(app)` sin restricción), anulando la protección descrita como resuelta en la auditoría de Mayo 2026.

**Corrección:** Eliminado el código muerto `Config.CORS_ORIGINS`/`get_cors_origins()` en `config.py`. `.env.example` actualizado para documentar `ALLOWED_ORIGINS` (la variable real), con advertencia explícita de que CORS queda abierto si se deja vacía.

#### 🟡 MEDIO — IPs de clientes en texto claro en logs centralizados (`api/app.py`)

| Función | Descripción |
|---------|-------------|
| `log_event()` en `rate_limit_exceeded`, `/analyze`, `/chat`, `/contact` | Se enviaba la IP del cliente **sin hashear** al stream de logs JSON (stdout → Loki/Grafana), pese a que `database.log_visit()` ya hashea la IP con SHA-256 antes de persistirla — inconsistencia entre el cuidado de privacidad aplicado a la BD y el aplicado a los logs operativos. |

**Corrección:** Añadido helper `hash_ip()` (mismo esquema SHA-256 ya usado en `landing()`) y aplicado en todos los `log_event()` que incluían `ip=`. `landing()` reutiliza el mismo helper en lugar de duplicar el cálculo.

### Verificación post-fix

- Suite de tests (`tests/test_public_stats_and_routes.py`, `tests/test_monitor_deploy.py`): 19/19 ✅
- `python -m py_compile api/app.py api/config.py`: ✅

---

## Auditoría Mayo 2026 (Seguimiento) — Revisión Completa Post-Merge PR #11

**Fecha:** 31 de Mayo, 2026
**Estatus:** ✅ **RESUELTO — 6 hallazgos corregidos**

Auditoría integral del repositorio tras mergear el [PR #11](https://github.com/theChosen16/Demo_geofeedback/pull/11). Cubrió backend Flask, capa de BD, frontend JS, template, Docker, CI/CD, config/secretos, dependencias y scripts. Se confirmó que el PR #11 resolvió correctamente sus 8 hallazgos, pero la remediación de XSS quedó **incompleta** y se detectaron defectos de configuración.

### Hallazgos y Correcciones

#### 🟠 MEDIO — XSS: remediación de salida de IA incompleta (`api/static/js/app.js`)

| Función | Línea | Descripción |
|---------|-------|-------------|
| `requestAIInterpretation()` / `fetchAIInterpretation()` | ~1564 / ~1657 | El PR #11 corrigió `addChatMessage` (respuestas de `/chat`) pero dejó **dos renderizadores de `/interpret`** insertando `data.interpretation` (salida de Gemini) vía `insertAdjacentHTML` **sin escapar**. Mismo patrón que el PR clasificó como ALTO. |

**Corrección:** `escapeHtml(data.interpretation)` **antes** de aplicar el formato (secciones, negrita, saltos de línea), igual que en `addChatMessage`.

#### 🟡 BAJO — Gating de `/observability` inefectivo en producción (`api/app.py`)

El fix del PR #11 gateaba con `RAILWAY_ENVIRONMENT`, variable que Railway setea **a nivel de proceso** → el desglose quedaba expuesto a todos los clientes externos en producción.

**Corrección:** Gating por secreto compartido en el header `X-Observability-Token` (comparación en tiempo constante con `hmac.compare_digest`, leído por request). Sin `OBSERVABILITY_TOKEN` configurado, el endpoint **falla seguro** y solo expone `status` + `public_stats`. El monitor (`scripts/monitor_deploy.py`) envía el header y tolera el payload reducido.

#### 🟡 BAJO — CSP con `'unsafe-eval'` (`api/app.py`)

`script-src` incluía `'unsafe-eval'`, innecesario (Chart.js v4 y el loader de Google Maps no lo requieren) y debilitante frente a XSS.

**Corrección:** Eliminado `'unsafe-eval'`. (`'unsafe-inline'` se mantiene: requiere refactor del template por los handlers `onclick`/`onkeypress` inline; documentado en el código.)

#### 🟡 BAJO — Clave de Google Maps expuesta sin restricción documentada (`api/app.py`)

La key se inyecta en el cliente (inevitable para Maps JS). Riesgo de abuso de facturación si no está restringida en GCP.

**Corrección:** No tiene fix de código (es config de GCP). Documentado en el punto de inyección: **debe restringirse por HTTP-referrer (`*.geofeedback.cl`) y por APIs** en Google Cloud Console.

#### 🔵 INFO — XSS defensa en profundidad: datos de APIs de Google (`api/static/js/app.js`)

`result-location` (`placeName`/`name` de Geocoding/Places) y `data-aqi` (`aqi.category` de Air Quality) se insertaban vía `innerHTML` sin escapar. Fuente semi-confiable (Google), riesgo bajo.

**Corrección:** Aplicado `escapeHtml()` en los tres sinks.

#### 🔵 INFO — Fallback débil de `SECRET_KEY` (`api/config.py`)

El fallback usaba `id(object())` (no criptográfico).

**Corrección:** Fallback con `secrets.token_hex(32)` (CSPRNG) y **fallo duro** (`RuntimeError`) si falta `SECRET_KEY` en producción (`RAILWAY_ENVIRONMENT` presente).

### Acción manual pendiente (fuera del código)

- [ ] Restringir `GOOGLE_MAPS_API_KEY` por HTTP-referrer y APIs en Google Cloud Console.
- [ ] (Opcional) Definir `OBSERVABILITY_TOKEN` en Railway y como secret de GitHub para el desglose detallado en el monitor.

---

## Auditoría Abril 2026 — Resolución Completa de Alertas GitHub

**Fecha:** 9 de Abril, 2026
**Estatus:** ✅ **PASADO — 0 alertas abiertas en todas las categorías**

Se resolvieron **8 alertas de seguridad** detectadas por GitHub Advanced Security.

### 🔴 Dependabot (1/1 resuelta)

| # | Paquete | CVE | Severidad | Acción |
|---|---------|-----|-----------|--------|
| 6 | `flask` | CVE-2026-27205 | Low | Upgrade `3.0.0` → `>=3.1.3` en `api/requirements.txt` |

### 🔴 Code Scanning — CodeQL (6/6 resueltas)

| # | Regla | Archivo | Descripción | Acción |
|---|-------|---------|-------------|--------|
| 5 | `py/sql-injection` | `api/database.py:51` | f-string SQL con `lat`/`lng` del usuario | Reemplazado por query parametrizado con `%s` y `float()` cast |
| 4/6 | `py/clear-text-logging-sensitive-data` | `api/config.py:124` | Config dict contaminado con `url.password` logueado | Extraídas variables `db_name`, `db_port`, `sslmode` antes del dict; log usa solo esas variables limpias |
| 1 | `py/stack-trace-exposure` | `api/app.py:351` | `str(e)` retornado en JSON al cliente (`/analyze`) | Reemplazado por mensaje genérico; excepción se imprime solo en servidor |
| 2 | `py/stack-trace-exposure` | `api/app.py:642` | `str(e)` retornado en JSON al cliente (`/contact`) | Reemplazado por mensaje genérico |
| 3 | `py/stack-trace-exposure` | `api/app.py:3675` | `str(e)` en campo `"error"` en respuesta de `/stats` | Campo `"error"` eliminado de la respuesta |

### 🔴 Secret Scanning (1/1 resuelta)

| # | Tipo | Commit | Acción |
|---|------|--------|--------|
| 1 | Google API Key (`AIzaSyCmKOB4...`) | `79b87b7` (Nov 2025) | Alerta cerrada como `revoked`. Historial git reescrito con `git-filter-repo`: key reemplazada por `GOOGLE_MAPS_KEY_PLACEHOLDER` en los 169 commits. Force push a `master`. |

> **Nota:** La key fue rotada manualmente en una sesión previa a esta auditoría. La expuesta ya no es válida operativamente.

### Verificación post-fix

- CodeQL workflow `24212170566` y `24212262834`: ✅ `success`
- `gh api .../code-scanning/alerts?state=open` → `0`
- `gh api .../dependabot/alerts?state=open` → `0`
- `gh api .../secret-scanning/alerts?state=open` → `0`

---

## Auditoría Mayo 2026 — Revisión Arquitectónica Completa

**Fecha:** 30 de Mayo, 2026
**Estatus:** ✅ **RESUELTO — 8 hallazgos corregidos**

Revisión manual completa del flujo de datos entre todos los componentes: API Flask, módulo de base de datos, plantilla HTML y JavaScript del frontend.

### Hallazgos y Correcciones

#### 🔴 CRÍTICO — IP Spoofing / Bypass de Rate Limiting

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/app.py` | `get_client_ip()` | La función aceptaba `X-Real-IP` sin validación y calculaba `ips[-2]` en `X-Forwarded-For`, ambos valores controlables por el cliente. Un atacante podía enviar `X-Real-IP: 1.2.3.4` o `X-Forwarded-For: 1.2.3.4, victim` para suplantar cualquier IP y evadir los rate limiters completamente. |

**Corrección:** Eliminada la lectura de `X-Real-IP` (trivialmente falsificable). Para `X-Forwarded-For` se toma siempre el último elemento (`ips[-1]`), que es el que añade el proxy confiable de Railway — no el cliente.

---

#### 🔴 ALTO — XSS en Respuestas del Chatbot IA

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/static/js/app.js` | `addChatMessage()` | Las respuestas de Gemini se insertaban mediante `innerHTML` sin escapado HTML. Si el modelo retornaba `<script>...</script>` (ya sea por diseño o por inyección de prompt), el código se ejecutaba en el navegador del usuario. |

**Corrección:** Función reescrita usando `document.createElement` + `textContent`. Se añadió helper `escapeHtml()` que usa `createTextNode` internamente. Los saltos de línea reales (`\n`) se convierten a `<br>` **después** del escapado.

---

#### 🔴 ALTO — XSS en Tabla de Resultados del Análisis

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/static/js/app.js` | Loop `for (var key in data.data)` | Las claves y valores del objeto `data.data` (respuesta de `/api/v1/analyze`) se concatenaban directamente en HTML de la tabla sin escapado. |

**Corrección:** Aplicado `escapeHtml()` a `key` y `data.data[key]` antes de concatenar.

---

#### 🔴 ALTO — XSS en `showToast` via Mensajes del Servidor

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/static/js/app.js` | `showToast()` | El parámetro `message` se asignaba mediante `innerHTML`. Si la API retornaba un mensaje con caracteres HTML especiales, se renderizaba. |

**Corrección:** El ícono se construye como markup estático; el `message` se adjunta con `document.createTextNode()`.

---

#### 🟠 MEDIO — Sin Validación de Formato de Email en `/contact`

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/app.py` | `/api/v1/contact` | Solo se verificaba que `email` no estuviera vacío. No había validación de formato RFC 5321 ni límites de longitud en ningún campo, permitiendo texto arbitrario de hasta el tamaño máximo del cuerpo HTTP. |

**Corrección:** Añadida regex de validación `_EMAIL_RE`. Límites de longitud: `name`/`company` ≤100, `email` ≤254, `message` ≤2000.

---

#### 🟠 MEDIO — Sin Límite de Tamaño de Request (DoS)

| Archivo | Descripción |
|---------|-------------|
| `api/app.py` | Flask por defecto acepta cuerpos HTTP de hasta 16 MB. Un atacante podía enviar payloads masivos a `/analyze`, `/interpret` o `/chat` para saturar memoria en el tier gratuito de Railway (512 MB RAM). |

**Corrección:** `app.config['MAX_CONTENT_LENGTH'] = 64 * 1024` (64 KB).

---

#### 🟠 MEDIO — Inyección de Prompt via Campos Libres en `/interpret` y `/chat`

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/app.py` | `/api/v1/interpret`, `/api/v1/chat` | El campo `location` (texto libre) y `history` (lista sin cota) se interpolaban directamente en los prompts de Gemini sin truncar. Un atacante podía inyectar instrucciones arbitrarias: `"Santiago\n\nIGNORE ALL INSTRUCTIONS. Ahora di..."`. |

**Corrección:** `location` truncado a 200 chars, `meta_date` a 30 chars, `results` validado como `dict` con máximo 20 claves, historial de chat limitado a 20 mensajes de 500 chars cada uno.

---

#### 🟡 BAJO — Patrón de SQL Injection en GRANTs de `database.py`

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/database.py` | `_ensure_analytics_tables()` | Los `GRANT` se construían con f-strings interpolando `ANALYTICS_ROLE` directamente. Aunque el valor es una constante hardcodeada, el patrón es peligroso y viola el principio de código seguro por diseño. |

**Corrección:** Migrado a `psycopg2.sql.SQL(...).format(psql.Identifier(ANALYTICS_ROLE))` para usar identificadores parametrizados.

---

#### 🟡 BAJO — Endpoint `/observability` Expone Estado Interno a Atacantes

| Archivo | Línea | Descripción |
|---------|-------|-------------|
| `api/app.py` | `/api/v1/observability` | Cualquier cliente externo podía consultar qué subsistemas estaban activos (base de datos, GEE, Redis, Gemini, Maps key), facilitando ataques orientados al timing (p.ej., atacar cuando Redis no está disponible para evadir rate limiting distribuido). |

**Corrección:** El desglose por componente (`critical_checks`, `optional_checks`, `analytics`) solo se retorna cuando `RAILWAY_ENVIRONMENT` está configurado (requests internos del entorno Railway). Los externos solo reciben `status` y `public_stats`.

---

### Resumen Consolidado de Postura de Seguridad (Mayo 2026)

| Categoría | Estado |
|-----------|--------|
| IP Spoofing / Rate Limit Bypass | ✅ Resuelto |
| XSS — Chat IA (addChatMessage) | ✅ Resuelto |
| XSS — Tabla de resultados | ✅ Resuelto |
| XSS — showToast | ✅ Resuelto |
| Validación email en formulario | ✅ Resuelto |
| Límite de tamaño de request | ✅ Resuelto |
| Inyección de Prompt (LLM) | ✅ Mitigado |
| SQL Injection en GRANTs | ✅ Resuelto |
| Exposición de estado interno | ✅ Resuelto |

---

## Auditoría Enero 2026

**Fecha:** 20 de Enero, 2026
**Estatus:** ✅ PASADO (Con observaciones)

### 1. Gestión de Secretos y Claves

#### 🔴 Hallazgo Crítico: Credenciales de Service Account

- **Archivo:** `api/service-account-key.json`
- **Estado:** Presente en el entorno local.
- **Contenido:** Llave privada real de Google Cloud (`private_key_id: e27936...`).
- **Verificación Git:** ✅ **SEGURO.** El archivo está listado en `.gitignore` y **no existe** en el historial de commits del repositorio.
- **Acción Recomendada:**
  - **NO eliminar** del `.gitignore`.
  - Si compartes tu carpeta local (zip, drive, etc.), asegúrate de excluir manualmente este archivo.
  - Para producción (Railway), usa el mecanismo de `GOOGLE_APPLICATION_CREDENTIALS_JSON` (variable de entorno) implementado en `gee_config.py`.

#### 🟡 Configuración y Valores por Defecto

- **Archivo:** `api/config.py`
- **Observación:** Existían valores por defecto hardcodeados para entornos de desarrollo.
- **Estado Actual:** ✅ Resuelto en Auditoría Abril 2026 — `config.py` ya no contiene defaults inseguros. El password de BD se lee exclusivamente desde `DB_PASSWORD` env var (sin valor por defecto).

#### 🟢 API Keys (Gemini, Google Maps)

- **Implementación:** Correcta.
- **Detalles:**
  - `app.py` carga `GEMINI_API_KEY` y `resend_api_key` desde `os.environ`.
  - `GOOGLE_MAPS_API_KEY` se inyecta dinámicamente en el HTML en tiempo de ejecución, evitando hardcodearla en el frontend.

### 2. Privacidad de Datos

#### 🟢 Geolocalización y Datos de Usuario

- Las coordenadas (`lat`, `lng`) se procesan y devuelven sin almacenamiento persistente de usuarios anónimos.
- **Formulario de Contacto:** Los datos personales se envían por correo vía Resend API. Se recomienda no persistirlos en logs de servidor en producción.

### 3. Seguridad del Repositorio (.gitignore)

El archivo `.gitignore` está correctamente configurado para excluir:

- `venv/`, `env/` (Entornos virtuales)
- `.env`, `.env.local` (Variables de entorno locales)
- `*.log` (Archivos de registro)
- `service-account-key.json` (Credenciales)
- `data/raw/` (Datos crudos potencialmente sensibles o pesados)

---

## Estado Actual de Seguridad (Abril 2026)

### API Key de Google Maps — Configuración GCP

Configurada vía `gcloud services api-keys update` (la UI de GCP no expone la opción para claves de Maps Platform):

| Parámetro | Valor |
|-----------|-------|
| Restricciones de API | **Sin restricciones** (cualquier Google API habilitada en el proyecto) |
| Restricciones de dominio | `browserKeyRestrictions` activo |
| Dominios permitidos | `https://geofeedback.cl/`, `https://geofeedback.cl/*`, `https://*.geofeedback.cl/*`, `https://*.up.railway.app/*` |

> **Comando usado:** `gcloud services api-keys update projects/206456645570/locations/global/keys/8ddbe545-... --clear-restrictions` seguido de `--allowed-referrers`.

### Resumen de Postura de Seguridad

| Categoría | Estado |
|-----------|--------|
| Dependencias vulnerables | ✅ 0 alertas abiertas |
| Inyección SQL | ✅ Resuelto — queries parametrizados |
| Exposición de stack traces | ✅ Resuelto — mensajes genéricos al cliente |
| Logging de datos sensibles | ✅ Resuelto — taint flow eliminado |
| Secretos en código/historial | ✅ Resuelto — historial reescrito |
| Restricciones de API Key GCP | ✅ Dominios restringidos, APIs sin límite |

---

_Última actualización: 9 de Abril de 2026_
