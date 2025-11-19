# ============================================================================
# Dockerfile para Visor Web - GeoFeedback Papudo
# Servidor nginx sirviendo contenido estático
# ============================================================================

FROM nginx:alpine

# Metadata
LABEL maintainer="GeoFeedback Chile"
LABEL description="Visor web interactivo de riesgo de inundación en Papudo"
LABEL version="1.0.0"

# Copiar archivos de la aplicación
COPY index.html /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/
COPY data/ /usr/share/nginx/html/data/

# Copiar configuración personalizada de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# nginx se inicia automáticamente con la imagen base
