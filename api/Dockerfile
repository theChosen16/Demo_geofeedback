FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Instalar dependencias
RUN pip install --no-cache-dir flask flask-cors gunicorn

# Copiar archivos
COPY app.py .
COPY simple_app.py .
COPY start.sh .

# Dar permisos de ejecución
RUN chmod +x start.sh

# Puerto (informativo, Railway inyecta PORT)
EXPOSE 8080

# Usar el script de inicio
CMD ["./start.sh"]
