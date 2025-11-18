#!/bin/bash
# ============================================================================
# SCRIPT MAESTRO - CONFIGURACIÓN COMPLETA DE POSTGIS
# ============================================================================
# Ejecuta todos los pasos de configuración en orden
# Autor: GeoFeedback Chile
# Fecha: Noviembre 2025
# ============================================================================

set -e  # Salir si hay error

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directorio del proyecto
PROJECT_DIR=~/geofeedback-papudo
cd "$PROJECT_DIR"

# Credenciales
export PGPASSWORD="Papudo2025"

echo ""
echo -e "${BLUE}${BOLD}============================================================================${NC}"
echo -e "${BLUE}${BOLD}   CONFIGURACIÓN COMPLETA DE POSTGIS - GEOFEEDBACK PAPUDO${NC}"
echo -e "${BLUE}${BOLD}============================================================================${NC}"
echo ""

# ============================================================================
# PASO 1: SETUP SCHEMAS
# ============================================================================

echo -e "${YELLOW}[PASO 1/6] Configurando schemas y extensiones PostGIS...${NC}"
psql -U geofeedback -d geofeedback_papudo -h localhost -f scripts/sql/01_setup_postgis_schema.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Schemas configurados${NC}"
else
    echo -e "${RED}✗ Error en configuración de schemas${NC}"
    exit 1
fi

# ============================================================================
# PASO 2: CARGAR RASTERS
# ============================================================================

echo ""
echo -e "${YELLOW}[PASO 2/6] Cargando datos raster...${NC}"
bash scripts/02_load_raster_data.sh

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Rasters cargados${NC}"
else
    echo -e "${RED}✗ Error en carga de rasters${NC}"
    exit 1
fi

# ============================================================================
# PASO 3: VECTORIZAR AMENAZA
# ============================================================================

echo ""
echo -e "${YELLOW}[PASO 3/6] Vectorizando amenaza clasificada...${NC}"
source venv/bin/activate
python3 scripts/03_vectorize_amenaza.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Amenaza vectorizada${NC}"
else
    echo -e "${RED}✗ Error en vectorización${NC}"
    exit 1
fi

# ============================================================================
# PASO 4: CREAR FUNCIONES
# ============================================================================

echo ""
echo -e "${YELLOW}[PASO 4/6] Creando funciones personalizadas...${NC}"
psql -U geofeedback -d geofeedback_papudo -h localhost -f scripts/sql/04_create_functions.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Funciones creadas${NC}"
else
    echo -e "${RED}✗ Error en creación de funciones${NC}"
    exit 1
fi

# ============================================================================
# PASO 5: CREAR VISTAS MATERIALIZADAS
# ============================================================================

echo ""
echo -e "${YELLOW}[PASO 5/6] Creando vistas materializadas...${NC}"
psql -U geofeedback -d geofeedback_papudo -h localhost -f scripts/sql/05_create_views.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Vistas materializadas creadas${NC}"
else
    echo -e "${RED}✗ Error en creación de vistas${NC}"
    exit 1
fi

# ============================================================================
# PASO 6: TESTING Y VALIDACIÓN
# ============================================================================

echo ""
echo -e "${YELLOW}[PASO 6/6] Ejecutando tests de validación...${NC}"
python3 scripts/06_test_postgis.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Tests exitosos${NC}"
else
    echo -e "${RED}✗ Algunos tests fallaron${NC}"
    exit 1
fi

# ============================================================================
# RESUMEN FINAL
# ============================================================================

echo ""
echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✅ CONFIGURACIÓN POSTGIS COMPLETADA EXITOSAMENTE${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo "Base de datos: geofeedback_papudo"
echo "Schemas creados: raw, processed, infrastructure, metadata, api"
echo ""
echo "Tablas principales:"
echo "  • processed.amenaza_poligonos (vectorial)"
echo "  • processed.amenaza_clasificada (raster)"
echo "  • processed.amenaza_score_continuo (raster)"
echo "  • processed.pendiente (raster)"
echo ""
echo "Funciones API: 8"
echo "Vistas materializadas: 5"
echo ""
echo "Próximos pasos sugeridos:"
echo "  1. Análisis de infraestructura crítica"
echo "  2. Crear API REST con Flask"
echo "  3. Visor web con Leaflet"
echo ""
echo -e "${BLUE}============================================================================${NC}"
