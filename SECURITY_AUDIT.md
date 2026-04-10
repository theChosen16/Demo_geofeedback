# Auditoría de Seguridad y Privacidad - GeoFeedback Demo

## Historial de Auditorías

| Fecha | Estatus | Responsable |
|-------|---------|-------------|
| 20 de Enero, 2026 | ✅ PASADO (Con observaciones) | Interno |
| 9 de Abril, 2026 | ✅ PASADO — 0 alertas activas | Automatizado (GitHub CodeQL + Dependabot) |

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
