# Auditoría de Seguridad y Privacidad - GeoFeedback Demo

## Historial de Auditorías

| Fecha | Estatus | Responsable |
|-------|---------|-------------|
| 20 de Enero, 2026 | ✅ PASADO (Con observaciones) | Interno |
| 9 de Abril, 2026 | ✅ PASADO — 0 alertas activas | Automatizado (GitHub CodeQL + Dependabot) |
| 30 de Mayo, 2026 | ✅ RESUELTO — 8 hallazgos corregidos | Claude Code (revisión arquitectónica completa) |
| 31 de Mayo, 2026 | ✅ RESUELTO — 6 hallazgos de seguimiento corregidos | Claude Code (auditoría completa post-merge PR #11) |

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
