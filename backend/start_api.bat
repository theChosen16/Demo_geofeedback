@echo off
echo ========================================
echo   GeoFeedback Papudo API
echo   REST API Server
echo ========================================
echo.
echo Iniciando API Flask en puerto 5000...
echo.
echo API disponible en: http://localhost:5000
echo Documentacion: http://localhost:5000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

cd /d "%~dp0"
python app.py

pause
