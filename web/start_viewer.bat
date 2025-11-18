@echo off
echo ========================================
echo   Visor Web - Riesgo de Inundacion
echo   Papudo, Region de Valparaiso
echo ========================================
echo.
echo Iniciando servidor HTTP en puerto 8000...
echo.

cd /d "%~dp0"
python -m http.server 8000

echo.
echo Servidor detenido.
pause
