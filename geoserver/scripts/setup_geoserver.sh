#!/bin/bash

# ============================================================================
# SCRIPT DE CONFIGURACIÓN AUTOMÁTICA DE GEOSERVER
# ============================================================================
# Este script configura GeoServer usando la REST API para:
# - Crear workspace
# - Crear datastore PostGIS
# - Publicar capas
# - Aplicar estilos SLD
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
GEOSERVER_URL="http://localhost:8080/geoserver"
GEOSERVER_USER="admin"
GEOSERVER_PASS="GeoFeedback2025"

WORKSPACE="geofeedback"
DATASTORE="papudo_postgis"

# Configuración PostGIS (contenedor Docker)
PG_HOST="postgis"
PG_PORT="5432"
PG_DATABASE="geofeedback_papudo"
PG_USER="geofeedback"
PG_PASSWORD="Papudo2025"
PG_SCHEMA="processed"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  GeoServer Setup - GeoFeedback Papudo${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Esperar a que GeoServer esté listo
echo -e "${YELLOW}[1/7] Esperando a que GeoServer esté listo...${NC}"
for i in {1..30}; do
    if curl -s -f "${GEOSERVER_URL}/rest/about/version.json" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ GeoServer está listo${NC}"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# ============================================================================
# 1. Crear Workspace
# ============================================================================
echo -e "${YELLOW}[2/7] Creando workspace '${WORKSPACE}'...${NC}"

WORKSPACE_JSON=$(cat <<EOF
{
  "workspace": {
    "name": "${WORKSPACE}",
    "isolated": false
  }
}
EOF
)

curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "${WORKSPACE_JSON}" \
  "${GEOSERVER_URL}/rest/workspaces" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Workspace creado${NC}"
else
    echo -e "${YELLOW}⚠ Workspace ya existe o error (continuando...)${NC}"
fi

# ============================================================================
# 2. Crear DataStore PostGIS
# ============================================================================
echo -e "${YELLOW}[3/7] Creando datastore PostGIS...${NC}"

DATASTORE_JSON=$(cat <<EOF
{
  "dataStore": {
    "name": "${DATASTORE}",
    "type": "PostGIS",
    "enabled": true,
    "connectionParameters": {
      "entry": [
        {"@key": "host", "$": "${PG_HOST}"},
        {"@key": "port", "$": "${PG_PORT}"},
        {"@key": "database", "$": "${PG_DATABASE}"},
        {"@key": "user", "$": "${PG_USER}"},
        {"@key": "passwd", "$": "${PG_PASSWORD}"},
        {"@key": "schema", "$": "${PG_SCHEMA}"},
        {"@key": "dbtype", "$": "postgis"},
        {"@key": "namespace", "$": "http://${WORKSPACE}"},
        {"@key": "Expose primary keys", "$": "true"},
        {"@key": "Estimated extends", "$": "true"}
      ]
    }
  }
}
EOF
)

curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "${DATASTORE_JSON}" \
  "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/datastores" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ DataStore creado${NC}"
else
    echo -e "${YELLOW}⚠ DataStore ya existe o error (continuando...)${NC}"
fi

# ============================================================================
# 3. Publicar Capa de Polígonos de Riesgo
# ============================================================================
echo -e "${YELLOW}[4/7] Publicando capa de polígonos de riesgo...${NC}"

RISK_LAYER_JSON=$(cat <<EOF
{
  "featureType": {
    "name": "amenaza_poligonos",
    "nativeName": "amenaza_poligonos",
    "title": "Zonas de Riesgo de Inundación - Papudo",
    "abstract": "Polígonos de amenaza de inundación clasificados por nivel de riesgo (Alto, Medio, Bajo)",
    "keywords": {
      "string": ["riesgo", "inundación", "Papudo", "amenaza", "Chile"]
    },
    "srs": "EPSG:32719",
    "projectionPolicy": "FORCE_DECLARED",
    "enabled": true,
    "store": {
      "@class": "dataStore",
      "name": "${WORKSPACE}:${DATASTORE}"
    }
  }
}
EOF
)

curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "${RISK_LAYER_JSON}" \
  "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/datastores/${DATASTORE}/featuretypes" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Capa de riesgo publicada${NC}"
else
    echo -e "${YELLOW}⚠ Capa ya existe o error (continuando...)${NC}"
fi

# ============================================================================
# 4. Publicar Capa de Infraestructura
# ============================================================================
echo -e "${YELLOW}[5/7] Publicando capa de infraestructura...${NC}"

# Crear datastore para schema infrastructure
INFRA_DATASTORE="${DATASTORE}_infrastructure"

INFRA_DS_JSON=$(cat <<EOF
{
  "dataStore": {
    "name": "${INFRA_DATASTORE}",
    "type": "PostGIS",
    "enabled": true,
    "connectionParameters": {
      "entry": [
        {"@key": "host", "$": "${PG_HOST}"},
        {"@key": "port", "$": "${PG_PORT}"},
        {"@key": "database", "$": "${PG_DATABASE}"},
        {"@key": "user", "$": "${PG_USER}"},
        {"@key": "passwd", "$": "${PG_PASSWORD}"},
        {"@key": "schema", "$": "infrastructure"},
        {"@key": "dbtype", "$": "postgis"},
        {"@key": "namespace", "$": "http://${WORKSPACE}"}
      ]
    }
  }
}
EOF
)

curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "${INFRA_DS_JSON}" \
  "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/datastores" > /dev/null 2>&1

INFRA_LAYER_JSON=$(cat <<EOF
{
  "featureType": {
    "name": "facilities_risk",
    "nativeName": "facilities_risk",
    "title": "Infraestructura Crítica - Papudo",
    "abstract": "Instalaciones de infraestructura crítica con nivel de riesgo asignado",
    "keywords": {
      "string": ["infraestructura", "crítica", "Papudo", "OSM", "riesgo"]
    },
    "srs": "EPSG:32719",
    "projectionPolicy": "FORCE_DECLARED",
    "enabled": true,
    "store": {
      "@class": "dataStore",
      "name": "${WORKSPACE}:${INFRA_DATASTORE}"
    }
  }
}
EOF
)

curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "${INFRA_LAYER_JSON}" \
  "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/datastores/${INFRA_DATASTORE}/featuretypes" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Capa de infraestructura publicada${NC}"
else
    echo -e "${YELLOW}⚠ Capa ya existe o error (continuando...)${NC}"
fi

# ============================================================================
# 5. Subir Estilos SLD
# ============================================================================
echo -e "${YELLOW}[6/7] Subiendo estilos SLD...${NC}"

# Estilo para polígonos de riesgo
if [ -f "../styles/risk_polygons.sld" ]; then
    curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
      -X POST \
      -H "Content-Type: application/vnd.ogc.sld+xml" \
      --data-binary @../styles/risk_polygons.sld \
      "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/styles?name=risk_style" > /dev/null 2>&1

    # Aplicar estilo a la capa
    curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
      -X PUT \
      -H "Content-Type: text/xml" \
      -d "<layer><defaultStyle><name>risk_style</name><workspace>${WORKSPACE}</workspace></defaultStyle></layer>" \
      "${GEOSERVER_URL}/rest/layers/${WORKSPACE}:amenaza_poligonos" > /dev/null 2>&1

    echo -e "${GREEN}✓ Estilo de riesgo aplicado${NC}"
fi

# Estilo para infraestructura
if [ -f "../styles/infrastructure.sld" ]; then
    curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
      -X POST \
      -H "Content-Type: application/vnd.ogc.sld+xml" \
      --data-binary @../styles/infrastructure.sld \
      "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/styles?name=infrastructure_style" > /dev/null 2>&1

    # Aplicar estilo a la capa
    curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
      -X PUT \
      -H "Content-Type: text/xml" \
      -d "<layer><defaultStyle><name>infrastructure_style</name><workspace>${WORKSPACE}</workspace></defaultStyle></layer>" \
      "${GEOSERVER_URL}/rest/layers/${WORKSPACE}:facilities_risk" > /dev/null 2>&1

    echo -e "${GREEN}✓ Estilo de infraestructura aplicado${NC}"
fi

# ============================================================================
# 6. Configurar Layer Groups (opcional)
# ============================================================================
echo -e "${YELLOW}[7/7] Creando grupo de capas...${NC}"

LAYER_GROUP_JSON=$(cat <<EOF
{
  "layerGroup": {
    "name": "geofeedback_complete",
    "title": "GeoFeedback Papudo - Vista Completa",
    "abstractTxt": "Vista completa con zonas de riesgo e infraestructura crítica",
    "mode": "SINGLE",
    "workspace": {
      "name": "${WORKSPACE}"
    },
    "publishables": {
      "published": [
        {
          "@type": "layer",
          "name": "${WORKSPACE}:amenaza_poligonos"
        },
        {
          "@type": "layer",
          "name": "${WORKSPACE}:facilities_risk"
        }
      ]
    },
    "bounds": {
      "minx": -71.50,
      "miny": -32.54,
      "maxx": -71.42,
      "maxy": -32.47,
      "crs": "EPSG:4326"
    }
  }
}
EOF
)

curl -s -u "${GEOSERVER_USER}:${GEOSERVER_PASS}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "${LAYER_GROUP_JSON}" \
  "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/layergroups" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Grupo de capas creado${NC}"
else
    echo -e "${YELLOW}⚠ Grupo ya existe o error (continuando...)${NC}"
fi

# ============================================================================
# Resumen
# ============================================================================
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ CONFIGURACIÓN COMPLETADA${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "GeoServer está configurado y listo para usar:"
echo ""
echo "🌐 Web Interface:"
echo "   ${GEOSERVER_URL}/web"
echo "   Usuario: ${GEOSERVER_USER}"
echo "   Password: ${GEOSERVER_PASS}"
echo ""
echo "📊 Capas publicadas:"
echo "   • ${WORKSPACE}:amenaza_poligonos (Zonas de Riesgo)"
echo "   • ${WORKSPACE}:facilities_risk (Infraestructura Crítica)"
echo ""
echo "🗺️  Servicios OGC:"
echo "   WMS GetCapabilities:"
echo "   ${GEOSERVER_URL}/${WORKSPACE}/wms?service=WMS&request=GetCapabilities"
echo ""
echo "   WFS GetCapabilities:"
echo "   ${GEOSERVER_URL}/${WORKSPACE}/wfs?service=WFS&request=GetCapabilities"
echo ""
echo "📍 Ejemplo WMS GetMap:"
echo "   ${GEOSERVER_URL}/${WORKSPACE}/wms?service=WMS&version=1.1.0&request=GetMap&layers=${WORKSPACE}:amenaza_poligonos&bbox=-71.50,-32.54,-71.42,-32.47&width=800&height=600&srs=EPSG:4326&format=image/png"
echo ""
echo -e "${BLUE}============================================${NC}"
