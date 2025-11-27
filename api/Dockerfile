FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Instalar dependencias mínimas
RUN pip install --no-cache-dir flask flask-cors gunicorn

# Copiar solo app.py
COPY app.py .

# Puerto
EXPOSE 8080

# Comando de inicio - Usando sh -c para garantizar expansión de variables
# Aumentado timeout a 120s y log level a debug para diagnóstico
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 --log-level debug --access-logfile - --error-logfile - app:app"]
