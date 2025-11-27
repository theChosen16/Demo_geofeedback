#!/bin/sh
set -e

# Log startup info
echo "Starting application..."
echo "Current user: $(whoami)"
echo "Environment variables:"
env | grep -v "SECRET" | sort

# Ensure PORT is set
PORT="${PORT:-8080}"
echo "Using PORT: $PORT"

# Start Gunicorn
# --bind 0.0.0.0:$PORT : Bind to all interfaces on the specified port
# --workers 1 : Keep memory usage low
# --timeout 120 : Allow long requests
# --access-logfile - : Log to stdout
# --error-logfile - : Log errors to stdout
# --log-level debug : Verbose logging
exec gunicorn \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug \
    simple_app:app
