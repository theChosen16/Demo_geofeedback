#!/bin/bash
# ============================================================================
# CARGA DE DATOS RASTER A POSTGIS
# ============================================================================
# Importa los resultados del análisis (rasters) a PostGIS
# Usa raster2pgsql con configuración optimizada
# Autor: GeoFeedback Chile
# Fecha: Noviembre 2025
# ============================================================================

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

PROJECT_DIR=~/geofeedback-papudo
DATA_DIR="$PROJECT_DIR/data/processed"

# Credenciales PostgreSQL
DB_NAME="geofeedback_papudo"
DB_USER="geofeedback"
DB_HOST="localhost"
export PGPASSWORD="Papudo2025"

# Opciones de raster2pgsql
# -s SRID: Sistema de coordenadas
# -I: Crear índice espacial
# -C: Aplicar constraints
# -M: Vacuum analyze después de cargar
# -t: Tamaño de tile (100x100 píxeles para web mapping)
# -F: Agregar columna con nombre del archivo

RASTER2PGSQL_OPTS="-s 32719 -I -C -M -t 100x100 -F"

echo ""
echo "============================================================================"
echo "CARGA DE DATOS RASTER A POSTGIS"
echo "============================================================================"
echo ""

# ============================================================================
# VERIFICAR PRERREQUISITOS
# ============================================================================

echo -e "${YELLOW}[1/6] Verificando prerrequisitos...${NC}"

# Verificar que existen los archivos
if [ ! -f "$DATA_DIR/Amenaza_Clasificada.tif" ]; then
    echo -e "${RED}✗ Error: Amenaza_Clasificada.tif no encontrado${NC}"
    exit 1
fi

if [ ! -f "$DATA_DIR/Amenaza_Score_Continuo.tif" ]; then
    echo -e "${RED}✗ Error: Amenaza_Score_Continuo.tif no encontrado${NC}"
    exit 1
fi

if [ ! -f "$DATA_DIR/Pendiente.tif" ]; then
    echo -e "${RED}✗ Error: Pendiente.tif no encontrado${NC}"
    exit 1
fi

# Verificar conexión a PostgreSQL
if ! psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}✗ Error: No se puede conectar a PostgreSQL${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Todos los archivos encontrados${NC}"
echo -e "${GREEN}✓ Conexión a PostgreSQL OK${NC}"

# ============================================================================
# ELIMINAR TABLAS ANTERIORES SI EXISTEN
# ============================================================================

echo ""
echo -e "${YELLOW}[2/6] Limpiando tablas anteriores (si existen)...${NC}"

psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" << EOF > /dev/null 2>&1
DROP TABLE IF EXISTS processed.amenaza_clasificada CASCADE;
DROP TABLE IF EXISTS processed.amenaza_score_continuo CASCADE;
DROP TABLE IF EXISTS processed.pendiente CASCADE;
EOF

echo -e "${GREEN}✓ Tablas antiguas eliminadas${NC}"

# ============================================================================
# CARGAR AMENAZA CLASIFICADA (3 NIVELES: ROJO/AMARILLO/VERDE)
# ============================================================================

echo ""
echo -e "${YELLOW}[3/6] Cargando Amenaza Clasificada (3 niveles)...${NC}"

cd "$DATA_DIR"

# Generar SQL e importar
raster2pgsql $RASTER2PGSQL_OPTS \
    -d \
    -N -32768 \
    Amenaza_Clasificada.tif \
    processed.amenaza_clasificada \
    | psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -q

# Agregar metadatos y constraints
psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" << EOF
-- Agregar descripción
COMMENT ON TABLE processed.amenaza_clasificada IS 'Clasificación de amenaza de inundación en 3 niveles (1=Verde, 2=Amarillo, 3=Rojo)';
COMMENT ON COLUMN processed.amenaza_clasificada.rast IS 'Raster con valores: 0=NoData, 1=Bajo, 2=Medio, 3=Alto';

-- Constraint de valores válidos
ALTER TABLE processed.amenaza_clasificada
    ADD CONSTRAINT chk_amenaza_valid_values
    CHECK ((ST_BandPixelType(rast, 1) = '8BUI'));

-- Estadísticas
SELECT
    'Amenaza Clasificada' as capa,
    COUNT(*) as tiles,
    ST_Width(rast) as tile_width,
    ST_Height(rast) as tile_height
FROM processed.amenaza_clasificada
LIMIT 1;
EOF

echo -e "${GREEN}✓ Amenaza Clasificada cargada${NC}"

# ============================================================================
# CARGAR AMENAZA SCORE CONTINUO (0-100)
# ============================================================================

echo ""
echo -e "${YELLOW}[4/6] Cargando Amenaza Score Continuo (0-100)...${NC}"

raster2pgsql $RASTER2PGSQL_OPTS \
    -d \
    -N -9999 \
    Amenaza_Score_Continuo.tif \
    processed.amenaza_score_continuo \
    | psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -q

psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" << EOF
COMMENT ON TABLE processed.amenaza_score_continuo IS 'Score continuo de amenaza (0-100)';
COMMENT ON COLUMN processed.amenaza_score_continuo.rast IS 'Valores de 0 (sin riesgo) a 100 (riesgo máximo)';

SELECT
    'Score Continuo' as capa,
    COUNT(*) as tiles,
    ROUND(ST_MinPossibleValue(rast, 1)::numeric, 2) as min_value,
    ROUND((ST_SummaryStats(rast)).max::numeric, 2) as max_value
FROM processed.amenaza_score_continuo
LIMIT 1;
EOF

echo -e "${GREEN}✓ Score Continuo cargado${NC}"

# ============================================================================
# CARGAR PENDIENTE
# ============================================================================

echo ""
echo -e "${YELLOW}[5/6] Cargando Pendiente (grados)...${NC}"

raster2pgsql $RASTER2PGSQL_OPTS \
    -d \
    -N -9999 \
    Pendiente.tif \
    processed.pendiente \
    | psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" -q

psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" << EOF
COMMENT ON TABLE processed.pendiente IS 'Pendiente topográfica en grados';
COMMENT ON COLUMN processed.pendiente.rast IS 'Pendiente calculada desde DEM SRTM 30m';

SELECT
    'Pendiente' as capa,
    COUNT(*) as tiles,
    ROUND((ST_SummaryStats(rast)).mean::numeric, 2) as pendiente_media
FROM processed.pendiente
LIMIT 1;
EOF

echo -e "${GREEN}✓ Pendiente cargada${NC}"

# ============================================================================
# VERIFICACIÓN Y RESUMEN
# ============================================================================

echo ""
echo -e "${YELLOW}[6/6] Verificando carga y generando resumen...${NC}"

psql -U "$DB_USER" -d "$DB_NAME" -h "$DB_HOST" << EOF

-- Resumen de rasters cargados
SELECT
    schemaname || '.' || tablename as tabla,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamaño,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = schemaname AND table_name = tablename) as columnas
FROM pg_tables
WHERE schemaname = 'processed'
    AND tablename IN ('amenaza_clasificada', 'amenaza_score_continuo', 'pendiente')
ORDER BY tablename;

-- Verificar índices espaciales
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'processed'
    AND tablename IN ('amenaza_clasificada', 'amenaza_score_continuo', 'pendiente')
    AND indexdef LIKE '%gist%';

-- Registrar en metadata
INSERT INTO metadata.analysis_runs (
    analysis_type,
    dem_source,
    ndvi_source,
    resolution_meters,
    total_area_km2,
    crs,
    notes
) VALUES (
    'Riesgo Inundación',
    'SRTM 30m',
    'Sentinel-2',
    30,
    1925.32,
    'EPSG:32719',
    'Importación inicial de rasters - ' || CURRENT_TIMESTAMP
);

EOF

echo ""
echo "============================================================================"
echo -e "${GREEN}✅ CARGA DE RASTERS COMPLETADA EXITOSAMENTE${NC}"
echo "============================================================================"
echo ""
echo "Rasters importados a schema 'processed':"
echo "  • amenaza_clasificada (3 niveles)"
echo "  • amenaza_score_continuo (0-100)"
echo "  • pendiente (grados)"
echo ""
echo "Características:"
echo "  • Tiles: 100x100 píxeles"
echo "  • Índices espaciales: ✓"
echo "  • Constraints: ✓"
echo "  • CRS: EPSG:32719 (UTM 19S)"
echo ""
echo "Próximo paso: Vectorizar amenaza"
echo "  → python3 scripts/03_vectorize_amenaza.py"
echo "============================================================================"
