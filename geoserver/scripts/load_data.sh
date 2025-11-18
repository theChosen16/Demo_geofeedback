#!/bin/bash

# ============================================================================
# SCRIPT DE CARGA DE DATOS A POSTGIS DOCKER
# ============================================================================
# Este script exporta datos desde la BD local y los carga en el contenedor
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuración BD Local
LOCAL_HOST="localhost"
LOCAL_PORT="5432"
LOCAL_DB="geofeedback_papudo"
LOCAL_USER="geofeedback"

# Configuración BD Docker
DOCKER_CONTAINER="geofeedback_postgis"
DOCKER_DB="geofeedback_papudo"
DOCKER_USER="geofeedback"

# Directorio temporal
TEMP_DIR="./temp_export"
mkdir -p "${TEMP_DIR}"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Carga de Datos a PostGIS Docker${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================================================
# 1. Exportar datos desde BD local
# ============================================================================
echo -e "${YELLOW}[1/4] Exportando datos desde BD local...${NC}"

# Exportar polígonos de riesgo
echo -n "  • Exportando amenaza_poligonos... "
PGPASSWORD="Papudo2025" pg_dump -h ${LOCAL_HOST} -p ${LOCAL_PORT} -U ${LOCAL_USER} -d ${LOCAL_DB} \
  -t processed.amenaza_poligonos \
  --data-only \
  --column-inserts \
  -f "${TEMP_DIR}/amenaza_poligonos.sql" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Error${NC}"
fi

# Exportar infraestructura
echo -n "  • Exportando facilities_risk... "
PGPASSWORD="Papudo2025" pg_dump -h ${LOCAL_HOST} -p ${LOCAL_PORT} -U ${LOCAL_USER} -d ${LOCAL_DB} \
  -t infrastructure.facilities_risk \
  --data-only \
  --column-inserts \
  -f "${TEMP_DIR}/facilities_risk.sql" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗ Error${NC}"
fi

# ============================================================================
# 2. Esperar a que PostgreSQL esté listo
# ============================================================================
echo ""
echo -e "${YELLOW}[2/4] Esperando a que PostgreSQL esté listo...${NC}"

for i in {1..30}; do
    if docker exec ${DOCKER_CONTAINER} pg_isready -U ${DOCKER_USER} > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL está listo${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# ============================================================================
# 3. Copiar archivos al contenedor
# ============================================================================
echo ""
echo -e "${YELLOW}[3/4] Copiando archivos al contenedor...${NC}"

docker cp "${TEMP_DIR}/amenaza_poligonos.sql" ${DOCKER_CONTAINER}:/tmp/
docker cp "${TEMP_DIR}/facilities_risk.sql" ${DOCKER_CONTAINER}:/tmp/

echo -e "${GREEN}✓ Archivos copiados${NC}"

# ============================================================================
# 4. Cargar datos en PostgreSQL Docker
# ============================================================================
echo ""
echo -e "${YELLOW}[4/4] Cargando datos en PostgreSQL Docker...${NC}"

# Cargar polígonos de riesgo
echo -n "  • Cargando amenaza_poligonos... "
docker exec ${DOCKER_CONTAINER} psql -U ${DOCKER_USER} -d ${DOCKER_DB} \
  -f /tmp/amenaza_poligonos.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ Puede que ya existan datos${NC}"
fi

# Cargar infraestructura
echo -n "  • Cargando facilities_risk... "
docker exec ${DOCKER_CONTAINER} psql -U ${DOCKER_USER} -d ${DOCKER_DB} \
  -f /tmp/facilities_risk.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ Puede que ya existan datos${NC}"
fi

# ============================================================================
# 5. Verificar carga
# ============================================================================
echo ""
echo -e "${YELLOW}Verificando carga de datos...${NC}"

RISK_COUNT=$(docker exec ${DOCKER_CONTAINER} psql -U ${DOCKER_USER} -d ${DOCKER_DB} \
  -t -c "SELECT COUNT(*) FROM processed.amenaza_poligonos;" | tr -d ' ')

INFRA_COUNT=$(docker exec ${DOCKER_CONTAINER} psql -U ${DOCKER_USER} -d ${DOCKER_DB} \
  -t -c "SELECT COUNT(*) FROM infrastructure.facilities_risk;" | tr -d ' ')

echo -e "  • Polígonos de riesgo: ${GREEN}${RISK_COUNT}${NC}"
echo -e "  • Instalaciones: ${GREEN}${INFRA_COUNT}${NC}"

# ============================================================================
# Limpieza
# ============================================================================
echo ""
echo -e "${YELLOW}Limpiando archivos temporales...${NC}"
rm -rf "${TEMP_DIR}"
echo -e "${GREEN}✓ Limpieza completada${NC}"

# ============================================================================
# Resumen
# ============================================================================
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ CARGA DE DATOS COMPLETADA${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "Datos disponibles en PostgreSQL Docker:"
echo "  • ${RISK_COUNT} polígonos de riesgo"
echo "  • ${INFRA_COUNT} instalaciones de infraestructura"
echo ""
echo "Próximo paso: Ejecutar setup de GeoServer"
echo "  cd scripts && ./setup_geoserver.sh"
echo ""
echo -e "${BLUE}============================================${NC}"
