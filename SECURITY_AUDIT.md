# Auditoría de Seguridad y Privacidad - GeoFeedback Demo

**Fecha:** 20 de Enero, 2026
**Estatus:** ✅ PASADO (Con observaciones)

## 1. Gestión de Secretos y Claves

### 🔴 Hallazgo Crítico: Credenciales de Service Account

- **Archivo:** `api/service-account-key.json`
- **Estado:** Presente en el entorno local.
- **Contenido:** Llave privada real de Google Cloud (`private_key_id: e27936...`).
- **Verificación Git:** ✅ **SEGURO.** El archivo está listado en `.gitignore` y **no existe** en el historial de commits del repositorio.
- **Acción Recomendada:**
  - **NO eliminar** del `.gitignore`.
  - Si compartes tu carpeta local (zip, drive, etc.), asegúrate de excluir manualmente este archivo.
  - Para producción (Railway), usa el mecanismo de `GOOGLE_APPLICATION_CREDENTIALS_JSON` (variable de entorno) implementado en `gee_config.py` en lugar de subir este archivo.

### 🟡 Configuración y Valores por Defecto

- **Archivo:** `api/config.py`
- **Observación:** Existen valores por defecto hardcodeados para entornos de desarrollo:
  - `SECRET_KEY`: 'dev-secret-key-CHANGE-IN-PRODUCTION'
  - `DB_PASSWORD`: 'Papudo2025'
- **Riesgo:** Si se despliega en producción sin configurar las variables de entorno, la aplicación usará estos valores inseguros conocidos.
- **Acción Recomendada:** Asegurar que en el panel de Railway/Producción, todas las variables listadas en `config.py` estén explícitamente definidas.

### 🟢 API Keys (Gemini, Google Maps)

- **Implementación:** Correcta.
- **Detalles:**
  - `app.py` carga `GEMINI_API_KEY` y `resend_api_key` desde `os.environ`.
  - `GOOGLE_MAPS_API_KEY` se inyecta dinámicamente en el HTML en tiempo de ejecución (renderizado servidor), evitando hardcodearla en el código fuente del frontend.

## 2. Privacidad de Datos

### 🟢 Geolocalización y Datos de Usuario

- La aplicación solicita ubicación del navegador (API de Geolocalización).
- **Observación:** Los datos de ubicación (`lat`, `lng`) se envían al backend `/api/v1/analyze`, se procesan y se devuelven. No parece haber almacenamiento persistente de coordenadas de usuarios anónimos en la base de datos (según revisión de `app.py`).
- **Formulario de Contacto:** Los datos personales (nombre, email) enviados via `/api/v1/contact` se registran en los logs de la consola (`print`) y se envían por correo.
  - **Recomendación:** En un entorno de producción real, evita loguear PII (Información de Identificación Personal) en la consola (logs del servidor), ya que los proveedores de nube suelen guardar estos logs.

## 3. Seguridad del Repositorio (.gitignore)

El archivo `.gitignore` está correctamente configurado para excluir:

- `venv/`, `env/` (Entornos virtuales)
- `.env`, `.env.local` (Variables de entorno locales)
- `*.log` (Archivos de registro)
- `service-account-key.json` (Credenciales)
- `data/raw/` (Datos crudos potencialmente sensibles o pesados)

## Conclusión

El repositorio es **seguro para ser público** en su estado actual, siempre y cuando:

1. Mantengas el archivo `api/service-account-key.json` en tu máquina local y **nunca** fuerces su inclusión en git via `git add -f`.
2. No subas archivos `.env` manualmente.
3. Rotes (cambies) las API Keys si sospechas que alguna vez fueron expuestas antes de configurar el `.gitignore`.

**Nota Adicional:** El código fuente es limpio y sigue buenas prácticas de separación de configuración y lógica.
