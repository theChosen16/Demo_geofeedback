#!/bin/sh
set -e

# =============================================================================
# Production entrypoint for the GeoFeedback API.
#
# Mirrors the Dockerfile CMD: launches the WSGI app under Gunicorn.
#
# SECURITY NOTES (why this script no longer does what it used to):
#   * It NO LONGER runs `python -u simple_app.py`. That file does not exist and
#     the invocation started Flask's *development* server, which must never be
#     exposed to production traffic (debugger, single-threaded, no hardening).
#   * It NO LONGER dumps the process environment to stdout. The previous
#     `env | grep -viE "SECRET|KEY|PASSWORD|TOKEN|CREDENTIALS"` filter did NOT
#     mask DATABASE_URL, REDIS_URL or IP_HASH_SALT — all of which embed
#     credentials/secrets — so it leaked them into the centralized log stream.
# =============================================================================

cd "$(dirname "$0")"

PORT="${PORT:-5000}"
echo "Starting GeoFeedback API on port ${PORT} (gunicorn)..."

exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WORKERS:-2}" \
    --threads "${THREADS:-2}" \
    --timeout "${TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app
