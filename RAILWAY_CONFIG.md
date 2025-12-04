# 🚂 Configuración de Despliegue en Railway

Para que la aplicación funcione correctamente en producción con la nueva integración de Google Earth Engine, debes configurar las siguientes variables de entorno en tu proyecto de Railway.

## 1. Variables de Entorno Requeridas

Ve a la pestaña **Variables** de tu servicio en Railway y agrega:

| Variable                              | Descripción                              | Valor / Instrucción                                       |
| ------------------------------------- | ---------------------------------------- | --------------------------------------------------------- |
| `GOOGLE_MAPS_API_KEY`                 | Llave para Maps JS, Elevation, etc.      | Tu API Key actual (empieza con `AIza...`)                 |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Credenciales de Service Account para GEE | **Ver instrucciones abajo**                               |
| `PORT`                                | Puerto del servidor                      | (Automático) Railway lo gestiona, no necesitas agregarlo. |

### 🔑 Cómo obtener `GOOGLE_APPLICATION_CREDENTIALS_JSON`

1. Abre el archivo `api/service-account-key.json` que se generó en tu proyecto local.
2. Copia **todo** el contenido del archivo (el JSON completo).
3. En Railway, crea la variable `GOOGLE_APPLICATION_CREDENTIALS_JSON` y pega el contenido como valor.

> **Por qué hacemos esto**: Es más seguro inyectar el archivo de credenciales como una variable de entorno que subirlo al repositorio.

## 2. Configuración de Build y Deploy

He actualizado el archivo `railway.toml` para asegurar que se ejecute la aplicación correcta.

- **Servicio**: `api`
- **Dockerfile**: `api/Dockerfile`
- **Comando de Inicio**: Se usará el definido en el Dockerfile (`gunicorn app:app ...`), que está optimizado para producción.

> **Nota**: Antes, la configuración apuntaba a `start.sh` que ejecutaba una versión "simple" de la app. Con el cambio realizado, ahora se ejecutará la versión completa con Google Earth Engine.

## 3. Verificación

Una vez configuradas las variables y desplegado el cambio:

1. Ve a la URL de tu servicio (ej. `https://...up.railway.app/api/v1/gee-test`).
2. Deberías ver un mensaje de éxito: `{"status": "success", "message": "Conexión a GEE exitosa", ...}`.
