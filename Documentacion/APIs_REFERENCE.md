# 📡 APIs de Google Cloud Platform - Referencia Completa

## GeoFeedback Chile - Integración de APIs para Análisis Territorial

---

## 📋 ÍNDICE

1. [APIs Habilitadas](#apis-habilitadas)
2. [Mapeo de APIs por Enfoque](#mapeo-de-apis-por-enfoque)
3. [Configuración de APIs](#configuración-de-apis)
4. [Ejemplos de Uso](#ejemplos-de-uso)
5. [Guía de Selección](#guía-de-selección)
6. [Límites y Cuotas](#límites-y-cuotas)

---

## 🔌 APIs HABILITADAS

Todas las siguientes APIs están habilitadas en Google Cloud Platform para el proyecto GeoFeedback:

### 1. **Air Quality API**

- **Propósito**: Calidad del aire en tiempo real
- **Resolución**: 500m × 500m
- **Datos**: PM2.5, PM10, O₃, NO₂, CO, AQI
- **Actualización**: Cada hora
- **Documentación**: https://developers.google.com/maps/documentation/air-quality

### 2. **Solar API**

- **Propósito**: Potencial solar fotovoltaico
- **Datos**: Radiación anual, horas de sol, área disponible
- **Cobertura**: Edificios y estructuras
- **Documentación**: https://developers.google.com/maps/documentation/solar

### 3. **Pollen API**

- **Propósito**: Niveles de polen y alérgenos
- **Datos**: Concentración de polen por tipo de planta
- **Resolución**: Variable
- **Documentación**: https://developers.google.com/maps/documentation/pollen

### 4. **Maps Datasets API**

- **Propósito**: Gestión de datasets geoespaciales personalizados
- **Uso**: Almacenar y gestionar capas de datos propias
- **Formatos**: GeoJSON, KML, CSV con coordenadas
- **Documentación**: https://developers.google.com/maps/documentation/datasets

### 5. **Map Tiles API**

- **Propósito**: Acceso a tiles de mapas base
- **Tipos**: Roadmap, Satellite, Terrain, Hybrid
- **Resolución**: Múltiples niveles de zoom
- **Documentación**: https://developers.google.com/maps/documentation/tile

### 6. **Maps JavaScript API**

- **Propósito**: Mapas interactivos en web
- **Uso**: Visualización principal del proyecto
- **Componentes**: Map, AdvancedMarkerElement, overlays
- **Documentación**: https://developers.google.com/maps/documentation/javascript

### 7. **Maps Static API**

- **Propósito**: Imágenes estáticas de mapas
- **Uso**: Mapas para informes PDF, emails
- **Formatos**: PNG, JPG
- **Documentación**: https://developers.google.com/maps/documentation/maps-static

### 8. **Maps Elevation API**

- **Propósito**: Datos de elevación topográfica
- **Precisión**: ~10m vertical
- **Cobertura**: Global
- **Documentación**: https://developers.google.com/maps/documentation/elevation

### 9. **Places UI Kit**

- **Propósito**: Componentes pre-construidos para búsqueda de lugares
- **Componentes**: PlaceAutocompleteElement, PlacePicker
- **Uso**: Búsqueda y selección de ubicaciones
- **Documentación**: https://developers.google.com/maps/documentation/places/web-service/place-autocomplete

### 10. **Geocoding API**

- **Propósito**: Conversión dirección ↔ coordenadas
- **Uso**: Geocoding directo e inverso
- **Precisión**: Nivel de calle
- **Documentación**: https://developers.google.com/maps/documentation/geocoding

### 11. **Geolocation API**

- **Propósito**: Determinar ubicación del usuario
- **Método**: WiFi, torres celulares, GPS
- **Uso**: Centrar mapa en ubicación actual
- **Documentación**: https://developers.google.com/maps/documentation/geolocation

### 12. **Places API (New)**

- **Propósito**: Información detallada de lugares
- **Datos**: Nombres, direcciones, ratings, fotos
- **Categorías**: Negocios, puntos de interés, instituciones
- **Documentación**: https://developers.google.com/maps/documentation/places/web-service/overview

### 13. **Address Validation API**

- **Propósito**: Validar y normalizar direcciones
- **Uso**: Asegurar calidad de datos de entrada
- **Funciones**: Corrección, completado, verificación
- **Documentación**: https://developers.google.com/maps/documentation/address-validation

---

## 🎯 MAPEO DE APIs POR ENFOQUE

### 🌊 **Enfoque 1: Riesgo de Inundación**

| Índice/Dato                 | API Principal         | APIs Complementarias | Propósito                            |
| --------------------------- | --------------------- | -------------------- | ------------------------------------ |
| **Elevación**               | Elevation API         | Map Tiles API        | Altura sobre nivel del mar           |
| **Pendiente**               | Elevation API         | -                    | Grado de inclinación del terreno     |
| **NDWI**                    | Google Earth Engine\* | -                    | Detección de cuerpos de agua         |
| **Flow Accumulation**       | Google Earth Engine\* | Elevation API        | Modelo de acumulación hídrica        |
| **Infraestructura Crítica** | Places API (New)      | Geocoding API        | Ubicación de instalaciones en riesgo |
| **Visualización**           | Maps JavaScript API   | Map Tiles API        | Mapa interactivo                     |

> \*Google Earth Engine requiere configuración separada (no es parte de Google Maps Platform)

### 💧 **Enfoque 2: Gestión Hídrica**

| Índice/Dato        | API Principal         | APIs Complementarias | Propósito                          |
| ------------------ | --------------------- | -------------------- | ---------------------------------- |
| **NDWI Temporal**  | Google Earth Engine\* | -                    | Serie temporal de agua superficial |
| **NDMI**           | Google Earth Engine\* | -                    | Humedad en vegetación              |
| **NDVI**           | Google Earth Engine\* | -                    | Vigor vegetal                      |
| **Elevación**      | Elevation API         | -                    | Modelar escorrentía                |
| **Cuencas**        | Maps Datasets API     | Elevation API        | Almacenar polígonos de cuencas     |
| **Pozos/Embalses** | Places API (New)      | Geocoding API        | Infraestructura hídrica            |

### 🍃 **Enfoque 3: Calidad Ambiental**

| Índice/Dato               | API Principal         | APIs Complementarias | Propósito                            |
| ------------------------- | --------------------- | -------------------- | ------------------------------------ |
| **Índice Calidad Aire**   | **Air Quality API**   | -                    | AQI en tiempo real (PM2.5, PM10, O₃) |
| **Contaminantes**         | **Air Quality API**   | -                    | Concentración de gases y partículas  |
| **Potencial Solar**       | **Solar API**         | -                    | Radiación solar anual                |
| **Cobertura Vegetal**     | Google Earth Engine\* | -                    | NDVI para áreas verdes               |
| **Elevación**             | Elevation API         | -                    | Dispersión de contaminantes          |
| **Polen**                 | **Pollen API**        | -                    | Niveles de alérgenos                 |
| **Ubicaciones Sensibles** | Places API (New)      | Geocoding API        | Escuelas, hospitales, parques        |

### 🏘️ **Enfoque 4: Planificación Territorial**

| Índice/Dato          | API Principal         | APIs Complementarias    | Propósito                  |
| -------------------- | --------------------- | ----------------------- | -------------------------- |
| **Modelo Elevación** | Elevation API         | Map Tiles API (Terrain) | DEM de alta precisión      |
| **Pendientes**       | Elevation API         | -                       | Aptitud constructiva       |
| **Potencial Solar**  | **Solar API**         | -                       | Planificación energética   |
| **Uso de Suelo**     | Google Earth Engine\* | Maps Datasets API       | Clasificación territorial  |
| **Calidad Aire**     | **Air Quality API**   | -                       | Zonificación residencial   |
| **Infraestructura**  | Places API (New)      | Address Validation API  | Servicios, comercio, salud |
| **Mapas Base**       | Map Tiles API         | Maps Static API         | Visualización y reportes   |

---

## ⚙️ CONFIGURACIÓN DE APIs

### Requisitos Previos

1. **Proyecto en Google Cloud Platform**

   - Crear proyecto en https://console.cloud.google.com
   - Habilitar facturación (las APIs tienen capa gratuita generosa)

2. **Habilitar APIs**

   ```bash
   # Usando gcloud CLI
   gcloud services enable \
     airquality.googleapis.com \
     solar.googleapis.com \
     pollen.googleapis.com \
     mapsdatasets.googleapis.com \
     mapsplatformdatasets.googleapis.com \
     tile.googleapis.com \
     maps-backend.googleapis.com \
     static-maps-backend.googleapis.com \
     elevation-backend.googleapis.com \
     places-backend.googleapis.com \
     geocoding-backend.googleapis.com \
     geolocation.googleapis.com \
     addressvalidation.googleapis.com
   ```

3. **Crear API Key**

   ```bash
   # Crear API Key
   gcloud alpha services api-keys create --display-name="GeoFeedback Demo"

   # Restringir por dominio (producción)
   # En Google Cloud Console → Credenciales → API Key → Restricciones
   ```

4. **Configurar Variable de Entorno**
   ```bash
   # En .env (no subir a GitHub)
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

### Restricciones de Seguridad Recomendadas

#### Para Desarrollo Local:

- Sin restricciones (solo en localhost)

#### Para Producción (Railway):

```
HTTP Referrers:
  - https://demogeofeedback-production.up.railway.app/*
  - https://thechosen16.github.io/*
```

#### APIs a Habilitar por Key:

```
✓ Maps JavaScript API
✓ Maps Elevation API
✓ Air Quality API
✓ Solar API
✓ Pollen API
✓ Geocoding API
✓ Geolocation API
✓ Places API (New)
✓ Address Validation API
✓ Map Tiles API
✓ Maps Static API
```

---

## 💡 EJEMPLOS DE USO

### Ejemplo 1: Obtener Calidad de Aire (Air Quality API)

```javascript
async function getAirQuality(lat, lng) {
  const url = `https://airquality.googleapis.com/v1/currentConditions:lookup?key=${API_KEY}`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      location: { latitude: lat, longitude: lng },
    }),
  });

  const data = await response.json();

  if (data.indexes && data.indexes.length > 0) {
    const aqi = data.indexes[0];
    console.log(`AQI: ${aqi.aqi} (${aqi.category})`);
    console.log(
      `PM2.5: ${
        data.pollutants.find((p) => p.code === "pm25").concentration.value
      } μg/m³`
    );
  }
}

// Uso
getAirQuality(-32.5127, -71.4469); // Papudo, Chile
```

### Ejemplo 2: Calcular Potencial Solar (Solar API)

```javascript
async function getSolarPotential(lat, lng) {
  const url =
    `https://solar.googleapis.com/v1/buildingInsights:findClosest?` +
    `location.latitude=${lat}&location.longitude=${lng}&requiredQuality=LOW&key=${API_KEY}`;

  const response = await fetch(url);
  const data = await response.json();

  if (data.solarPotential) {
    const potential = data.solarPotential;
    console.log(
      `Max sunshine hours/year: ${potential.maxSunshineHoursPerYear}`
    );
    console.log(`Max panel area: ${potential.maxArrayAreaMeters2} m²`);
    console.log(
      `Annual energy potential: ${potential.maxArrayPanelsCount * 350} kWh/year`
    );
  } else {
    console.log("No building found at this location");
  }
}

// Uso
getSolarPotential(-33.4489, -70.6693); // Santiago, Chile
```

### Ejemplo 3: Obtener Elevación y Calcular Pendiente (Elevation API)

```javascript
async function getElevationAndSlope(lat, lng) {
  const elevationService = new google.maps.ElevationService();

  // Punto central
  const centerPoint = { lat, lng };

  // Puntos cardinales (offset ~100m)
  const offset = 0.001;
  const points = [
    centerPoint,
    { lat: lat + offset, lng },
    { lat: lat - offset, lng },
    { lat, lng: lng + offset },
    { lat, lng: lng - offset },
  ];

  elevationService.getElevationForLocations(
    { locations: points },
    (results, status) => {
      if (status === "OK") {
        const centerElev = results[0].elevation;
        console.log(`Elevation: ${centerElev.toFixed(2)} m`);

        // Calcular pendiente máxima
        let maxDiff = 0;
        for (let i = 1; i < results.length; i++) {
          const diff = Math.abs(results[i].elevation - centerElev);
          if (diff > maxDiff) maxDiff = diff;
        }

        const slopePercent = (maxDiff / 111) * 100;
        console.log(`Slope: ${slopePercent.toFixed(2)}%`);
      }
    }
  );
}

// Uso
getElevationAndSlope(-32.5127, -71.4469);
```

### Ejemplo 4: Buscar Infraestructura Crítica (Places API New)

```javascript
async function findCriticalInfrastructure(lat, lng, radius = 5000) {
  const { Place, SearchNearbyRankPreference } = await google.maps.importLibrary(
    "places"
  );
  const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

  const request = {
    fields: ["displayName", "location", "types"],
    locationRestriction: {
      center: { lat, lng },
      radius: radius,
    },
    includedTypes: [
      "hospital",
      "school",
      "fire_station",
      "police",
      "government_office",
    ],
    rankPreference: SearchNearbyRankPreference.DISTANCE,
  };

  const { places } = await Place.searchNearby(request);

  places.forEach((place) => {
    console.log(`${place.displayName} - ${place.types.join(", ")}`);

    // Agregar marcador al mapa
    new AdvancedMarkerElement({
      map: map,
      position: place.location,
      title: place.displayName,
    });
  });
}

// Uso
findCriticalInfrastructure(-32.5127, -71.4469, 5000); // 5km radio
```

### Ejemplo 5: Niveles de Polen (Pollen API)

```javascript
async function getPollenLevels(lat, lng) {
  const url =
    `https://pollen.googleapis.com/v1/forecast:lookup?key=${API_KEY}&` +
    `location.latitude=${lat}&location.longitude=${lng}&days=1`;

  const response = await fetch(url);
  const data = await response.json();

  if (data.dailyInfo && data.dailyInfo.length > 0) {
    const today = data.dailyInfo[0];

    today.pollenTypeInfo.forEach((pollen) => {
      console.log(
        `${pollen.displayName}: ${pollen.indexInfo.category} (${pollen.indexInfo.value}/5)`
      );
    });
  }
}

// Uso
getPollenLevels(-33.4489, -70.6693);
```

---

## 🔍 GUÍA DE SELECCIÓN DE APIs

### ¿Qué API usar para...?

| Necesidad                       | API Recomendada        | Alternativa                      |
| ------------------------------- | ---------------------- | -------------------------------- |
| Mostrar mapa interactivo        | Maps JavaScript API    | Map Tiles API                    |
| Generar mapa para PDF           | Maps Static API        | Map Tiles API + Canvas           |
| Obtener altura de un punto      | Elevation API          | -                                |
| Calidad del aire en tiempo real | Air Quality API        | -                                |
| Potencial solar de edificio     | Solar API              | -                                |
| Buscar dirección                | Geocoding API          | Places API (New)                 |
| Autocomplete de lugares         | Places UI Kit          | Places API (New)                 |
| Validar dirección postal        | Address Validation API | Geocoding API                    |
| Detectar ubicación del usuario  | Geolocation API        | JavaScript navigator.geolocation |
| Almacenar capas personalizadas  | Maps Datasets API      | GeoServer + PostGIS              |
| Niveles de polen/alérgenos      | Pollen API             | -                                |
| Información de negocios         | Places API (New)       | -                                |

### Combinaciones Recomendadas por Caso de Uso

#### 1. **Análisis de Riesgo Ambiental**

```
✓ Air Quality API (contaminación)
✓ Pollen API (alérgenos)
✓ Elevation API (topografía)
✓ Places API (New) - hospitales, escuelas
✓ Maps JavaScript API (visualización)
```

#### 2. **Planificación Urbana Sostenible**

```
✓ Solar API (energía renovable)
✓ Elevation API (pendientes constructivas)
✓ Air Quality API (zonificación)
✓ Places API (New) - servicios básicos
✓ Address Validation API (catastro)
```

#### 3. **Gestión de Emergencias**

```
✓ Elevation API (zonas inundables)
✓ Places API (New) - refugios, hospitales, bomberos
✓ Geocoding API (direcciones exactas)
✓ Maps Static API (mapas impresos)
✓ Geolocation API (ubicación en tiempo real)
```

#### 4. **Agricultura de Precisión**

```
✓ Elevation API (micro-topografía)
✓ Pollen API (cultivos sensibles)
✓ Solar API (horas de luz)
✓ Google Earth Engine (NDVI, NDMI)
```

---

## 📊 LÍMITES Y CUOTAS

### Capa Gratuita Mensual (Google Maps Platform)

| API                 | Cuota Gratuita              | Costo Excedente |
| ------------------- | --------------------------- | --------------- |
| Maps JavaScript API | 28,000 cargas               | $7/1,000 cargas |
| Elevation API       | $200 créditos (~40,000 req) | $5/1,000 req    |
| Air Quality API     | 1,000 llamadas              | $0.05/llamada   |
| Solar API           | 1,000 llamadas              | $0.05/llamada   |
| Pollen API          | 1,000 llamadas              | $0.05/llamada   |
| Geocoding API       | $200 créditos (~40,000 req) | $5/1,000 req    |
| Places API (New)    | $200 créditos (~28,000 req) | Variable        |
| Static Maps API     | $200 créditos (~28,000 req) | $2/1,000 req    |
| Map Tiles API       | $200 créditos               | Variable        |
| Geolocation API     | $200 créditos (~40,000 req) | $5/1,000 req    |

> **Nota**: Google otorga $200 USD en créditos mensuales gratuitos que se aplican a todas las APIs.

### Optimización de Costos

#### ✅ Buenas Prácticas:

1. **Caché de Resultados**: Almacenar elevaciones, calidad de aire histórica
2. **Batch Requests**: Agrupar múltiples puntos en una sola llamada
3. **Restricción de API Keys**: Evitar uso no autorizado
4. **Zoom Levels**: Usar tiles de menor resolución cuando sea apropiado
5. **Static Maps**: Para contenido que no requiere interacción

#### ❌ Evitar:

- Llamadas innecesarias en cada movimiento del mapa
- Cargar Air Quality API sin caché (máx 1 vez/hora)
- Usar Places API cuando basta con Geocoding
- Generar Static Maps en tiempo real (pre-generarlos)

### Monitoreo de Uso

```bash
# Ver uso de APIs
gcloud services quotas list --service=maps-backend.googleapis.com

# Configurar alertas en Google Cloud Console
# Billing → Budgets & alerts → Create Budget
# Alerta al 50%, 90%, 100% de $200 USD
```

---

## 🚀 IMPLEMENTACIÓN ACTUAL EN GEOFEEDBACK

### APIs Actualmente Implementadas

En el archivo `api/app.py`, actualmente se utilizan:

1. ✅ **Maps JavaScript API** - Línea 626-641 (inicialización del mapa)
2. ✅ **Elevation API** - Línea 649, 788-800 (obtener elevación)
3. ✅ **Air Quality API** - Línea 830-847 (calidad del aire)
4. ✅ **Solar API** - Línea 850-862 (potencial solar)
5. ✅ **Places API (New)** - Línea 652-709 (autocompletado)
6. ✅ **Geocoding API** - Línea 746-769 (geocodificación inversa)
7. ✅ **Advanced Markers** - Línea 627, 644-647 (marcadores)

### APIs Pendientes de Implementar

#### Corto Plazo (Siguiente Sprint):

- [ ] **Pollen API** - Agregar al panel "Calidad Ambiental"
- [ ] **Address Validation API** - Validar direcciones ingresadas
- [ ] **Maps Datasets API** - Almacenar zonas de riesgo custom

#### Mediano Plazo:

- [ ] **Maps Static API** - Generar mapas para informes PDF
- [ ] **Geolocation API** - Botón "Usar mi ubicación"
- [ ] **Map Tiles API** - Overlays personalizados

---

## 📝 PRÓXIMOS PASOS

### Para Desarrolladores:

1. **Revisar este documento** completo
2. **Seleccionar APIs** según enfoque de análisis deseado
3. **Consultar ejemplos** en la sección "Ejemplos de Uso"
4. **Implementar gradualmente** (una API a la vez)
5. **Monitorear costos** en Google Cloud Console

### Para Usuarios:

Este sistema te permite:

- ✅ Elegir cualquier combinación de APIs según tu caso de uso
- ✅ Usar solo las APIs que necesitas (no todas son obligatorias)
- ✅ Escalar a nuevos enfoques agregando APIs incrementalmente
- ✅ Mantener costos bajos con la capa gratuita

---

## 📞 RECURSOS ADICIONALES

### Documentación Oficial:

- **Google Maps Platform**: https://developers.google.com/maps
- **Air Quality API**: https://developers.google.com/maps/documentation/air-quality
- **Solar API**: https://developers.google.com/maps/documentation/solar
- **Pollen API**: https://developers.google.com/maps/documentation/pollen

### Soporte:

- **Stack Overflow**: Tag `google-maps-api`
- **GitHub Issues**: https://github.com/googlemaps/js-samples/issues
- **Google Cloud Support**: https://cloud.google.com/support

### Código de Ejemplo:

- **Google Maps Samples**: https://github.com/googlemaps/js-samples
- **Air Quality Demo**: https://developers.google.com/maps/documentation/air-quality/samples
- **Solar API Demo**: https://developers.google.com/maps/documentation/solar/data-layers

---

**Última actualización**: Diciembre 2025  
**Versión**: 1.0  
**Mantenedor**: GeoFeedback Chile  
**Repositorio**: [github.com/theChosen16/Demo_geofeedback](https://github.com/theChosen16/Demo_geofeedback)

---

> 💡 **Tip**: Todas las APIs están integradas bajo una sola API Key. Para probar una nueva API, simplemente habilitarla en Google Cloud Console y usar la misma key que tienes en `GOOGLE_MAPS_API_KEY`.
