# Visor Web Interactivo - Riesgo de Inundación Papudo

Aplicación web interactiva para visualizar zonas de riesgo de inundación e infraestructura crítica en el municipio de Papudo.

## Características

- **Mapa Interactivo con Leaflet**: Visualización de datos geoespaciales
- **Capas Dinámicas**: Activar/desactivar zonas de riesgo e infraestructura
- **Filtros**: Filtrar por nivel de riesgo y categoría de infraestructura
- **Búsqueda**: Buscar instalaciones específicas por nombre
- **Estadísticas en Tiempo Real**: Panel con métricas actualizadas
- **Clustering de Marcadores**: Agrupación inteligente de puntos cercanos
- **Popups Informativos**: Detalles al hacer clic en cualquier elemento
- **Responsive**: Diseño adaptativo para móvil y escritorio

## Estructura de Archivos

```
web/
├── index.html          # Página principal
├── css/
│   └── style.css       # Estilos personalizados
├── js/
│   └── map.js          # Lógica del mapa y datos
├── data/
│   └── infrastructure_with_risk.geojson  # Datos de infraestructura
└── README.md           # Esta documentación
```

## Uso

### Opción 1: Abrir Directamente (Desarrollo)

Simplemente abrir `index.html` en un navegador web moderno:

```bash
# En Windows
start web/index.html

# En Linux/Mac
open web/index.html
```

**Nota**: Algunos navegadores pueden bloquear la carga de archivos locales por CORS. Use la Opción 2 si encuentra problemas.

### Opción 2: Servidor HTTP Local

Para evitar problemas de CORS, usar un servidor HTTP local:

**Python 3:**
```bash
cd web
python -m http.server 8000
```

**Python 2:**
```bash
cd web
python -m SimpleHTTPServer 8000
```

**Node.js (http-server):**
```bash
npm install -g http-server
cd web
http-server -p 8000
```

Luego abrir en el navegador: http://localhost:8000

## Controles del Visor

### Panel Lateral

1. **Capas**
   - ☑️ Zonas de Riesgo: Mostrar/ocultar polígonos de riesgo
   - ☑️ Infraestructura Crítica: Mostrar/ocultar instalaciones

2. **Filtros**
   - **Nivel de Riesgo**: Alto, Medio, Bajo, Todos
   - **Categoría**: Educación, Salud, Emergencias, Gobierno, Comercio, Todas

3. **Estadísticas**
   - Total de instalaciones
   - Desglose por nivel de riesgo
   - Actualización automática al filtrar

4. **Leyenda**
   - Colores de zonas de riesgo
   - Iconos por categoría de infraestructura

### Mapa

- **Zoom**: Rueda del ratón o botones +/-
- **Pan**: Arrastrar el mapa
- **Click en Marcador**: Ver detalles de la instalación
- **Clustering**: Los marcadores se agrupan automáticamente al hacer zoom out

### Búsqueda

- Buscar instalaciones por nombre o categoría
- Resultados en tiempo real mientras escribes
- Click en resultado para centrar el mapa

## Datos

Los datos provienen de:

- **Infraestructura**: OpenStreetMap (OSM)
- **Riesgo**: Análisis combinado de:
  - Pendiente del terreno (DEM SRTM)
  - Cobertura vegetal (NDVI Sentinel-2)
  - Depresiones topográficas

## Tecnologías Utilizadas

- **Leaflet 1.9.4**: Biblioteca de mapas interactivos
- **Leaflet.markercluster**: Agrupación de marcadores
- **Font Awesome 6.4**: Iconos
- **GeoJSON**: Formato de datos geoespaciales
- **HTML5/CSS3/JavaScript**: Frontend moderno

## Personalización

### Cambiar Colores de Riesgo

Editar en `js/map.js`:

```javascript
const riskColors = {
    3: { color: '#FF6B6B', name: 'Alto' },
    2: { color: '#FFD700', name: 'Medio' },
    1: { color: '#90EE90', name: 'Bajo' }
};
```

### Agregar Nueva Categoría

1. Actualizar `categoryStyles` en `js/map.js`:
```javascript
'NuevaCategoria': { icon: 'icon-name', color: '#HEXCOLOR' }
```

2. Agregar en leyenda (`index.html`)
3. Agregar en filtro de categorías

### Cambiar Mapa Base

Editar en `js/map.js`:

```javascript
L.tileLayer('URL_DEL_TILE_PROVIDER', {
    attribution: 'Atribución',
    maxZoom: 19
}).addTo(map);
```

Opciones populares:
- OpenStreetMap (actual)
- CartoDB Positron
- Esri WorldImagery
- Stamen Terrain

## Próximas Mejoras

- [ ] Integración con API REST para datos dinámicos
- [ ] Exportar resultados filtrados a CSV/GeoJSON
- [ ] Gráficos estadísticos (Chart.js)
- [ ] Modo de comparación temporal
- [ ] Análisis de rutas de evacuación
- [ ] Generación de reportes PDF
- [ ] Soporte multiidioma (ES/EN)

## Soporte

Para problemas o sugerencias, abrir un issue en el repositorio del proyecto.

## Licencia

Proyecto desarrollado por **GeoFeedback Chile** - Noviembre 2025

Datos: OpenStreetMap contributors, SRTM DEM, Sentinel-2 ESA
