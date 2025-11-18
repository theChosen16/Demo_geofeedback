#!/bin/bash

echo "========================================"
echo "  Visor Web - Riesgo de Inundación"
echo "  Papudo, Región de Valparaíso"
echo "========================================"
echo ""
echo "Iniciando servidor HTTP en puerto 8000..."
echo "Abre tu navegador en: http://localhost:8000"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

cd "$(dirname "$0")"
python3 -m http.server 8000
