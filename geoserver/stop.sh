#!/bin/bash

# ============================================================================
# Script para detener servicios GeoServer + PostGIS
# ============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Deteniendo GeoServer Stack${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

echo -e "${YELLOW}¿Qué deseas hacer?${NC}"
echo "1) Detener servicios (mantener datos)"
echo "2) Detener servicios y eliminar volúmenes (BORRAR TODOS LOS DATOS)"
echo "3) Cancelar"
echo ""
read -p "Opción [1-3]: " option

case $option in
    1)
        echo ""
        echo -e "${YELLOW}Deteniendo servicios...${NC}"
        docker-compose down
        echo -e "${GREEN}✓ Servicios detenidos (datos preservados)${NC}"
        ;;
    2)
        echo ""
        echo -e "${RED}⚠  ADVERTENCIA: Esto eliminará TODOS los datos${NC}"
        read -p "¿Estás seguro? [y/N]: " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo ""
            echo -e "${YELLOW}Deteniendo servicios y eliminando volúmenes...${NC}"
            docker-compose down -v
            echo -e "${GREEN}✓ Servicios detenidos y datos eliminados${NC}"
        else
            echo -e "${YELLOW}Operación cancelada${NC}"
        fi
        ;;
    3)
        echo -e "${YELLOW}Operación cancelada${NC}"
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}============================================${NC}"
