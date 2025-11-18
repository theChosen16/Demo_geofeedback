#!/bin/bash

# ============================================================================
# Script de inicio completo para GeoServer + PostGIS
# ============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  GeoFeedback Papudo - GeoServer Stack${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠  Docker no está instalado${NC}"
    exit 1
fi

# Iniciar servicios
echo -e "${YELLOW}[1/4] Iniciando servicios Docker...${NC}"
docker-compose up -d

# Esperar a que PostgreSQL esté listo
echo ""
echo -e "${YELLOW}[2/4] Esperando a que PostgreSQL esté listo...${NC}"
for i in {1..30}; do
    if docker exec geofeedback_postgis pg_isready -U geofeedback > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL está listo${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Cargar datos (opcional, solo si no existen)
echo ""
echo -e "${YELLOW}[3/4] Verificando datos...${NC}"

COUNT=$(docker exec geofeedback_postgis psql -U geofeedback -d geofeedback_papudo \
  -t -c "SELECT COUNT(*) FROM processed.amenaza_poligonos;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$COUNT" -eq "0" ]; then
    echo -e "${YELLOW}No hay datos, ejecutando carga...${NC}"
    cd scripts && ./load_data.sh && cd ..
else
    echo -e "${GREEN}✓ Datos ya existen (${COUNT} polígonos)${NC}"
fi

# Configurar GeoServer (opcional, solo si no está configurado)
echo ""
echo -e "${YELLOW}[4/4] Verificando configuración de GeoServer...${NC}"
sleep 5  # Dar tiempo a GeoServer para iniciar

WORKSPACE_EXISTS=$(curl -s -u admin:GeoFeedback2025 \
  http://localhost:8080/geoserver/rest/workspaces/geofeedback.json 2>/dev/null || echo "")

if [ -z "$WORKSPACE_EXISTS" ]; then
    echo -e "${YELLOW}Configurando GeoServer...${NC}"
    cd scripts && ./setup_geoserver.sh && cd ..
else
    echo -e "${GREEN}✓ GeoServer ya está configurado${NC}"
fi

# Resumen
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ SERVICIOS INICIADOS${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "🌐 GeoServer Web UI:"
echo "   http://localhost:8080/geoserver/web"
echo "   Usuario: admin"
echo "   Password: GeoFeedback2025"
echo ""
echo "🗺️  WMS GetCapabilities:"
echo "   http://localhost:8080/geoserver/geofeedback/wms?service=WMS&request=GetCapabilities"
echo ""
echo "📊 PostgreSQL:"
echo "   Host: localhost"
echo "   Port: 5433"
echo "   Database: geofeedback_papudo"
echo "   User: geofeedback"
echo ""
echo "Para detener: docker-compose down"
echo ""
echo -e "${BLUE}============================================${NC}"
