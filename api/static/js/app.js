      var MAPS_API_KEY = "GOOGLE_MAPS_KEY_PLACEHOLDER";
      var map = null;
      var marker = null;
      var autocomplete = null;
      var selectedPlace = null;
      var selectedApproach = null;
      var selectedRadius = 2000; // Default 2km
      var isSatellite = true;
      var chatHistory = [];
      var analysisContext = {};
      var mapHintDismissed = false;

      function showToast(message, type) {
        type = type || 'toast-success';
        var toast = document.getElementById('toast-notification');
        toast.className = 'toast-notification ' + type;
        toast.innerHTML = '<i class="fas fa-' + (type === 'toast-success' ? 'check-circle' : type === 'toast-error' ? 'exclamation-circle' : 'exclamation-triangle') + '"></i> ' + message;
        toast.classList.add('show');
        setTimeout(function() { toast.classList.remove('show'); }, 4000);
      }

      function dismissMapHint() {
        if (!mapHintDismissed) {
          mapHintDismissed = true;
          var hint = document.getElementById('map-hint');
          if (hint) hint.classList.add('hidden');
        }
      }

      function showMapStatus(message, isError) {
        var placeholder = document.getElementById('map-placeholder');
        if (!placeholder) return;

        placeholder.style.display = 'block';
        placeholder.innerHTML =
          '<i class="fas fa-' + (isError ? 'triangle-exclamation' : 'map-marked-alt') + '"></i>' +
          '<p>' + message + '</p>';
      }

      function syncDemoMapLayout() {
        var mapElement = document.getElementById('demo-map');
        var mapContainer = document.querySelector('.map-container');
        if (!mapElement || !mapContainer) return;

        var viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
        var viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
        var nextHeight = 550;

        if (viewportWidth <= 768) {
          nextHeight = Math.min(Math.max(Math.round(viewportHeight * 0.52), 320), 460);
        } else if (viewportWidth <= 1280) {
          nextHeight = Math.min(Math.max(Math.round(viewportHeight * 0.56), 420), 620);
        } else {
          nextHeight = Math.min(Math.max(Math.round(viewportHeight * 0.64), 520), 760);
        }

        document.documentElement.style.setProperty('--demo-map-height', nextHeight + 'px');
        mapElement.style.height = nextHeight + 'px';
        mapContainer.style.minHeight = nextHeight + 'px';

        if (map && typeof map.getCenter === 'function') {
          var center = map.getCenter();
          window.requestAnimationFrame(function () {
            if (center) {
              map.setCenter(center);
            }
          });
        }
      }

      // ====== Phase 2: localStorage Persistence ======
      function savePreferences() {
        try {
          var prefs = {};
          if (selectedPlace) prefs.place = selectedPlace;
          if (selectedApproach) prefs.approach = selectedApproach;
          if (selectedRadius) prefs.radius = selectedRadius;
          localStorage.setItem('gf_prefs', JSON.stringify(prefs));
        } catch(e) { /* localStorage unavailable */ }
      }

      function loadPreferences() {
        try {
          var stored = localStorage.getItem('gf_prefs');
          if (!stored) return null;
          return JSON.parse(stored);
        } catch(e) { return null; }
      }

      // ====== Analysis History ======
      var analysisHistory = [];

      function loadHistory() {
        try {
          var stored = localStorage.getItem('gf_history');
          if (stored) analysisHistory = JSON.parse(stored);
        } catch(e) { analysisHistory = []; }
      }

      function saveHistory() {
        try {
          localStorage.setItem('gf_history', JSON.stringify(analysisHistory.slice(0, 5)));
        } catch(e) { /* ignored */ }
      }

      function addToHistory(place, approach, timestamp) {
        analysisHistory.unshift({
          name: place.name,
          lat: place.lat,
          lng: place.lng,
          approach: approach,
          time: timestamp || Date.now()
        });
        if (analysisHistory.length > 5) analysisHistory.pop();
        saveHistory();
        renderHistory();
      }

      function renderHistory() {
        var container = document.getElementById('history-list');
        var panel = document.getElementById('history-panel');
        if (!container || !panel) return;
        if (analysisHistory.length === 0) { panel.style.display = 'none'; return; }
        panel.style.display = '';
        var isEn = typeof currentLang !== 'undefined' && currentLang === 'en';
        var html = '';
        var approachNames = isEn ? {
          mining: 'Mining', agriculture: 'Agro', energy: 'Energy',
          'real-estate': 'Real Estate', 'fire-risk': 'Fire Risk',
          'flood-risk': 'Flood Risk', 'water-management': 'Water',
          environmental: 'Environmental', 'land-planning': 'Planning'
        } : {
          mining: 'Mineria', agriculture: 'Agro', energy: 'Energia',
          'real-estate': 'Inmobiliario', 'fire-risk': 'Incendio',
          'flood-risk': 'Inundacion', 'water-management': 'Hidrica',
          environmental: 'Ambiental', 'land-planning': 'Territorial'
        };
        analysisHistory.forEach(function(item, i) {
          var ago = getTimeAgo(item.time, isEn);
          var icon = 'fas fa-map-marker-alt';
          html += '<div class="history-item" onclick="replayHistory(' + i + ')" title="' + item.name + '">' +
            '<i class="' + icon + '"></i>' +
            '<span class="history-name">' + (approachNames[item.approach] || item.approach) + ' - ' + item.name.split(',')[0] + '</span>' +
            '<span class="history-time">' + ago + '</span></div>';
        });
        container.innerHTML = html;
      }

      function getTimeAgo(ts, isEn) {
        var diff = Math.floor((Date.now() - ts) / 1000);
        if (diff < 60) return isEn ? 'now' : 'ahora';
        if (diff < 3600) return Math.floor(diff / 60) + (isEn ? 'm ago' : 'm');
        if (diff < 86400) return Math.floor(diff / 3600) + 'h';
        return Math.floor(diff / 86400) + 'd';
      }

      function replayHistory(index) {
        var item = analysisHistory[index];
        if (!item) return;
        selectedPlace = { lat: item.lat, lng: item.lng, name: item.name };
        selectedApproach = item.approach;
        document.getElementById('approach-select').value = item.approach;
        onApproachChange();
        if (map) {
          map.setCenter({ lat: item.lat, lng: item.lng });
          map.setZoom(12);
        }
        document.getElementById('location-name').textContent = item.name;
        document.getElementById('location-coords').textContent = item.lat.toFixed(4) + ', ' + item.lng.toFixed(4);
        document.getElementById('status-location').classList.add('ready');
        checkReadyState();
      }

      // ====== Radius Circle on Map ======
      var analysisCircle = null;

      function updateAnalysisCircle() {
        if (analysisCircle) { analysisCircle.setMap(null); analysisCircle = null; }
        if (!selectedPlace || !selectedRadius || !map) return;
        analysisCircle = new google.maps.Circle({
          map: map,
          center: { lat: selectedPlace.lat, lng: selectedPlace.lng },
          radius: selectedRadius,
          fillColor: '#2D5A4A',
          fillOpacity: 0.08,
          strokeColor: '#A68B5B',
          strokeOpacity: 0.5,
          strokeWeight: 2,
          clickable: false
        });
      }

      // ====== Skeleton Loading for Live Data ======
      function showLiveDataSkeleton() {
        var dataEl = document.getElementById('live-data');
        dataEl.classList.add('active');
        ['data-elevation', 'data-aqi', 'data-solar', 'data-slope'].forEach(function(id) {
          document.getElementById(id).innerHTML = '<div class="skeleton skeleton-value"></div>';
        });
      }

      // ====== Collapsible Panels (Mobile) ======
      function initCollapsiblePanels() {
        if (window.innerWidth > 768) return;
        var panels = document.querySelectorAll('.sidebar .panel');
        panels.forEach(function(panel, i) {
          var header = panel.querySelector('.panel-header');
          if (!header) return;
          if (i === 0) return; // Skip status bar panel
          header.classList.add('collapsible');
          var body = document.createElement('div');
          body.className = 'panel-body-collapsible';
          while (header.nextSibling) {
            body.appendChild(header.nextSibling);
          }
          panel.appendChild(body);
          // Collapse radius and history by default on mobile
          if (i >= 3) {
            header.classList.add('collapsed');
            body.classList.add('collapsed');
          }
          header.addEventListener('click', function() {
            header.classList.toggle('collapsed');
            body.classList.toggle('collapsed');
          });
        });
      }

      var approaches = {
        mining: {
          name: "Mineria Sostenible",
          icon: "mountain",
          indices: [
            {
              name: "Vegetacion (NDVI)",
              api: "Sentinel-2",
              desc: "Monitoreo de impacto ambiental en flora.",
              color: "#2ecc71",
            },
            {
              name: "Agua (NDWI)",
              api: "Sentinel-2",
              desc: "Deteccion de cuerpos de agua y relaves.",
              color: "#3498db",
            },
            {
              name: "Pendiente",
              api: "Elevation",
              desc: "Analisis de estabilidad de terreno.",
              color: "#95a5a6",
            },
          ],
        },
        agriculture: {
          name: "Agroindustria Inteligente",
          icon: "seedling",
          indices: [
            {
              name: "Salud Cultivo (NDVI)",
              api: "Sentinel-2",
              desc: "Vigor y salud de la vegetacion.",
              color: "#2ecc71",
            },
            {
              name: "Estres Hidrico (NDMI)",
              api: "Sentinel-2",
              desc: "Contenido de humedad en cultivos.",
              color: "#1abc9c",
            },
            {
              name: "Solar",
              api: "Solar API",
              desc: "Potencial para riego solar.",
              color: "#f1c40f",
            },
          ],
        },
        energy: {
          name: "Energias Renovables",
          icon: "solar-panel",
          indices: [
            {
              name: "Irradiancia",
              api: "Solar API",
              desc: "Potencial solar fotovoltaico.",
              color: "#f1c40f",
            },
            {
              name: "Topografia",
              api: "Elevation",
              desc: "Analisis de sombras y pendiente.",
              color: "#95a5a6",
            },
            {
              name: "Infraestructura",
              api: "Places",
              desc: "Proximidad a redes electricas.",
              color: "#e74c3c",
            },
          ],
        },
        "real-estate": {
          name: "Desarrollo Inmobiliario",
          icon: "building",
          indices: [
            {
              name: "Constructibilidad",
              api: "Elevation",
              desc: "Pendientes aptas para construccion.",
              color: "#95a5a6",
            },
            {
              name: "Servicios",
              api: "Places",
              desc: "Cercania a colegios y salud.",
              color: "#e74c3c",
            },
            {
              name: "Calidad Aire",
              api: "Air Quality",
              desc: "Indices de contaminacion local.",
              color: "#1abc9c",
            },
            {
              name: "Riesgos",
              api: "Sentinel-2",
              desc: "Historial de inundaciones (NDWI).",
              color: "#3498db",
            },
          ],
        },
        "flood-risk": {
          name: "Riesgo de Inundacion",
          icon: "water",
          indices: [
            {
              name: "Cuerpos de Agua (NDWI)",
              api: "Sentinel-2",
              desc: "Deteccion de zonas inundables.",
              color: "#3498db",
            },
            {
              name: "Elevacion",
              api: "Elevation",
              desc: "Modelado de terreno.",
              color: "#95a5a6",
            },
          ],
        },
        "water-management": {
          name: "Gestion Hidrica",
          icon: "tint",
          indices: [
            {
              name: "Humedad Suelo (NDMI)",
              api: "Sentinel-2",
              desc: "Retencion de agua en suelo.",
              color: "#1abc9c",
            },
            {
              name: "NDWI",
              api: "Sentinel-2",
              desc: "Monitoreo de embalses.",
              color: "#3498db",
            },
          ],
        },
        environmental: {
          name: "Calidad Ambiental",
          icon: "leaf",
          indices: [
            {
              name: "Cobertura Vegetal (NDVI)",
              api: "Sentinel-2",
              desc: "Densidad de vegetacion.",
              color: "#2ecc71",
            },
            {
              name: "Calidad Aire",
              api: "Air Quality",
              desc: "Indices AQI en tiempo real.",
              color: "#e74c3c",
            },
          ],
        },
        "land-planning": {
          name: "Planificacion Territorial",
          icon: "map-marked-alt",
          indices: [
            {
              name: "Pendiente",
              api: "Elevation",
              desc: "Aptitud de uso de suelo.",
              color: "#95a5a6",
            },
            {
              name: "Uso Actual",
              api: "Sentinel-2",
              desc: "Clasificacion de cobertura.",
              color: "#f1c40f",
            },
          ],
        },
        "fire-risk": {
          name: "Riesgo de Incendio Forestal",
          icon: "fire",
          indices: [
            {
              name: "Vegetacion Seca (NDVI)",
              api: "Sentinel-2",
              desc: "Areas con baja humedad vegetal.",
              color: "#dc2626",
            },
            {
              name: "Humedad Vegetacion (NDMI)",
              api: "Sentinel-2",
              desc: "Contenido de agua en plantas.",
              color: "#f97316",
            },
            {
              name: "Pendiente",
              api: "Elevation",
              desc: "Dificultad de acceso para combate.",
              color: "#95a5a6",
            },
          ],
        },
      };

      async function loadGoogleMaps() {
        var script = document.createElement("script");
        script.src =
          "https://maps.googleapis.com/maps/api/js?key=" +
          MAPS_API_KEY +
          "&libraries=places,marker&callback=initMap&v=weekly&loading=async";
        script.async = true;
        script.defer = true;
        script.onerror = function () {
          console.error("No se pudo cargar Google Maps.");
          showMapStatus(
            currentLang === 'en'
              ? 'Could not load the map. Reload the page or disable extensions that block Google Maps.'
              : 'No se pudo cargar el mapa. Recarga la pagina o desactiva extensiones que bloqueen Google Maps.',
            true,
          );
        };
        document.head.appendChild(script);
      }

      async function initMap() {
        if (!MAPS_API_KEY || MAPS_API_KEY.length < 20) {
          console.error("API Key no configurada o invalida");
          showMapStatus(
            currentLang === 'en'
              ? 'Maps API key is missing or invalid.'
              : 'La API key de Maps no esta configurada o es invalida.',
            true,
          );
          return;
        }

        var Map;
        var AdvancedMarkerElement;
        var PlaceAutocompleteElement;

        try {
          ({ Map } = await google.maps.importLibrary("maps"));
          ({ AdvancedMarkerElement } = await google.maps.importLibrary("marker"));
          ({ PlaceAutocompleteElement } = await google.maps.importLibrary("places"));
        } catch (error) {
          console.error("Error inicializando Google Maps:", error);
          showMapStatus(
            currentLang === 'en'
              ? 'Google Maps resources were blocked by the browser or CSP.'
              : 'Los recursos de Google Maps fueron bloqueados por el navegador o la CSP.',
            true,
          );
          return;
        }

        map = new Map(document.getElementById("demo-map"), {
          center: { lat: -33.4489, lng: -70.6693 }, // Santiago
          zoom: 5,
          mapId: "3a20a11ffd93a81165e3538d", // GeoFeedback Demo Map ID
          mapTypeId: "hybrid",
          disableDefaultUI: false,
          zoomControl: true,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
        });

        syncDemoMapLayout();

        var placeholder = document.getElementById("map-placeholder");
        if (placeholder) {
          placeholder.style.display = "none";
        }

        // Map Click Listener
        map.addListener("click", async (e) => {
          dismissMapHint();
          const clickedLat = e.latLng.lat();
          const clickedLng = e.latLng.lng();

          // Reverse Geocoding to get name
          const geocoder = new google.maps.Geocoder();
          const response = await geocoder.geocode({
            location: { lat: clickedLat, lng: clickedLng },
          });

          let placeName = currentLang === 'en' ? "Selected location" : "Ubicación seleccionada";
          if (response.results && response.results[0]) {
            placeName = response.results[0].formatted_address;
          }

          if (marker) marker.map = null;
          marker = new AdvancedMarkerElement({
            map: map,
            position: { lat: clickedLat, lng: clickedLng },
            title: placeName,
          });

          selectedPlace = {
            lat: clickedLat,
            lng: clickedLng,
            name: placeName,
          };
          console.log("Selected Place from click:", selectedPlace);

          // Update UI
          document.getElementById("location-name").textContent = placeName;
          document.getElementById("location-coords").textContent =
            clickedLat.toFixed(4) + ", " + clickedLng.toFixed(4);
          document.getElementById("status-location").classList.add("ready");
          document.getElementById("result-location").innerHTML =
            '<i class="fas fa-check-circle result-icon" style="color:var(--secondary)"></i><div class="result-content"><h4>' +
            placeName +
            "</h4><p>" + (currentLang === 'en' ? 'Selected on map' : 'Seleccionado en mapa') + "</p></div>";

          checkReadyState();
          updateAnalysisCircle();
          savePreferences();

          // Fetch Live Data
          showLiveDataSkeleton();
          fetchElevationAndSlope(clickedLat, clickedLng);
          fetchAirQuality(clickedLat, clickedLng);
          fetchSolarPotential(clickedLat, clickedLng);
        });

        // Autocomplete setup (New Places API)
        const container = document.getElementById("autocomplete-container");
        container.innerHTML = "";

        const autocomplete = new PlaceAutocompleteElement();
        autocomplete.id = "pac-input";
        autocomplete.classList.add("controls");
        // Set attributes to try to satisfy browser warnings
        autocomplete.setAttribute("name", "place_search");
        container.appendChild(autocomplete);

        // Handler function to process the place selection
        const onPlaceSelect = async (event) => {
          console.log("Event fired:", event.type, event);

          let place = null;

          // Case 1: New PlaceAutocompleteElement (gmp-select) returns placePrediction
          if (event.placePrediction) {
            console.log("Found placePrediction, converting to Place...");
            place = event.placePrediction.toPlace();
          }
          // Case 2: Some versions might return event.place directly
          else if (event.place) {
            console.log("Found event.place");
            place = event.place;
          }
          // Case 3: Fallback to details
          else if (event.detail?.place) {
            place = event.detail.place;
          }
          // Case 4: Last resort, try getPlace()
          else if (typeof autocomplete.getPlace === "function") {
            try {
              place = autocomplete.getPlace();
              console.log("Retrieved via getPlace():", place);
            } catch (e) {
              console.warn("getPlace failed", e);
            }
          }

          if (!place) {
            console.warn("Could not retrieve Place object from event.");
            return;
          }

          try {
            // If it's a Place object from the new API, we MUST fetch fields
            // We check for fetchFields method to distinguish from legacy PlaceResult
            if (typeof place.fetchFields === "function") {
              console.log("Fetching fields for Place object...");
              await place.fetchFields({
                fields: [
                  "displayName",
                  "formattedAddress",
                  "location",
                  "viewport",
                ],
              });

              if (!place.location) {
                console.error("Place has no location after fetchFields");
                showToast(currentLang === 'en' ? 'Selected location has no valid coordinates.' : 'La ubicacion seleccionada no tiene coordenadas validas.', 'toast-warning');
                return;
              }

              handlePlaceSelection(
                place.location,
                place.displayName,
                place.viewport,
              );
            }
            // Legacy PlaceResult object (has geometry property directly)
            else if (place.geometry && place.geometry.location) {
              console.log("Using legacy PlaceResult object");
              handlePlaceSelection(
                place.geometry.location,
                place.name || place.formatted_address,
                place.geometry.viewport,
              );
            } else {
              console.error("Unknown Place object structure:", place);
            }
          } catch (err) {
            console.error("Error processing place:", err);
            showToast((currentLang === 'en' ? 'Error processing place: ' : 'Error al procesar el lugar: ') + err.message, 'toast-error');
          }
        };

        // Add listeners for ALL potential event names to be safe
        autocomplete.addEventListener("gmp-places-select", onPlaceSelect);
        autocomplete.addEventListener("gmp-placeselect", onPlaceSelect);
        autocomplete.addEventListener("gmp-select", onPlaceSelect);

        // Fallback for "Enter" key without selection
        autocomplete.addEventListener("keydown", async (event) => {
          if (event.key === "Enter") {
            const text = autocomplete.value;
            console.log("Enter pressed in search box. Value:", text);

            // Allow a small delay to see if the select event fires first
            setTimeout(() => {
              // If no place is selected or the name doesn't match (rough check)
              // We check if selectedPlace is null OR if the current selected place name is different from input text
              // This prevents re-triggering if the user just hit enter on an already selected place
              if (
                !selectedPlace ||
                (selectedPlace.name !== text && text.length > 3)
              ) {
                console.log("Triggering manual Geocoding fallback for:", text);
                const geocoder = new google.maps.Geocoder();
                geocoder.geocode({ address: text }, (results, status) => {
                  if (status === "OK" && results[0]) {
                    console.log("Geocoding success:", results[0]);
                    handlePlaceSelection(
                      results[0].geometry.location,
                      results[0].formatted_address,
                      results[0].geometry.viewport,
                    );
                  } else {
                    console.warn("Geocoding failed or no results for:", text);
                  }
                });
              }
            }, 500); // Increased delay to 500ms to ensure gmp-places-select has time to fire
          }
        });

        function handlePlaceSelection(location, name, viewport) {
          dismissMapHint();
          if (!location) {
            showToast(currentLang === 'en' ? 'No location details found.' : 'No se encontraron detalles de ubicacion.', 'toast-warning');
            return;
          }

          if (viewport) {
            map.fitBounds(viewport);
          } else {
            map.setCenter(location);
            map.setZoom(15);
          }

          if (marker) marker.map = null;
          marker = new AdvancedMarkerElement({
            map: map,
            position: location,
            title: name,
          });

          selectedPlace = {
            lat: location.lat(),
            lng: location.lng(),
            name: name,
          };
          console.log("Selected Place updated:", selectedPlace);

          // Update UI
          document.getElementById("location-name").textContent = name;
          document.getElementById("location-coords").textContent =
            selectedPlace.lat.toFixed(4) + ", " + selectedPlace.lng.toFixed(4);
          document.getElementById("status-location").classList.add("ready");
          document.getElementById("result-location").innerHTML =
            '<i class="fas fa-check-circle result-icon" style="color:var(--secondary)"></i><div class="result-content"><h4>' +
            name +
            "</h4><p>Ubicacion confirmada</p></div>";

          // Enable analysis button
          checkReadyState();
          updateAnalysisCircle();
          savePreferences();

          // Fetch Live Data
          showLiveDataSkeleton();
          fetchElevationAndSlope(selectedPlace.lat, selectedPlace.lng);
          fetchAirQuality(selectedPlace.lat, selectedPlace.lng);
          fetchSolarPotential(selectedPlace.lat, selectedPlace.lng);
        }

        // Restore saved preferences
        var prefs = loadPreferences();
        if (prefs) {
          if (prefs.approach) {
            document.getElementById('approach-select').value = prefs.approach;
            onApproachChange();
          }
          if (prefs.radius) {
            document.getElementById('radius-select').value = prefs.radius;
            onRadiusChange();
          }
        }
      }

      function fetchElevationAndSlope(lat, lng) {
        var elevator = new google.maps.ElevationService();
        var locations = [];
        // Center and 4 surrounding points (~100m offset)
        var offset = 0.001;
        locations.push({ lat: lat, lng: lng });
        locations.push({ lat: lat + offset, lng: lng });
        locations.push({ lat: lat - offset, lng: lng });
        locations.push({ lat: lat, lng: lng + offset });
        locations.push({ lat: lat, lng: lng - offset });

        elevator.getElevationForLocations(
          { locations: locations },
          function (results, status) {
            if (status === "OK") {
              if (results[0]) {
                var centerElev = results[0].elevation;
                document.getElementById("data-elevation").textContent =
                  Math.round(centerElev) + " m";

                // Calculate max slope
                var maxDiff = 0;
                for (var i = 1; i < results.length; i++) {
                  var diff = Math.abs(results[i].elevation - centerElev);
                  if (diff > maxDiff) {
                    maxDiff = diff;
                  }
                }
                var slopePercent = (maxDiff / 111) * 100; // Rough approx
                var slopeClass =
                  slopePercent < 5
                    ? "Plano"
                    : slopePercent < 15
                      ? "Suave"
                      : slopePercent < 30
                        ? "Moderado"
                        : "Pronunciado";
                document.getElementById("data-slope").textContent =
                  Math.round(slopePercent) + "% (" + slopeClass + ")";
              } else {
                document.getElementById("data-elevation").textContent = "N/D";
                document.getElementById("data-slope").textContent = "N/D";
              }
            } else {
              document.getElementById("data-elevation").textContent = "Error";
              document.getElementById("data-slope").textContent = "Error";
            }
          },
        );
      }

      function fetchAirQuality(lat, lng) {
        var url =
          "https://airquality.googleapis.com/v1/currentConditions:lookup?key=" +
          MAPS_API_KEY;
        fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ location: { latitude: lat, longitude: lng } }),
        })
          .then(function (response) {
            if (response.status === 403) {
              console.warn("Air Quality API returned 403. Check if API is enabled and key has no restrictions.");
              return { error: "403" };
            }
            return response.json();
          })
          .then(function (data) {
            if (data.error === "403") {
              document.getElementById("data-aqi").innerHTML = '<span style="color:var(--danger); font-size:0.7rem;">Error 403: API no habilitada</span>';
              return;
            }
            if (data.indexes && data.indexes.length > 0) {
              var aqi = data.indexes[0];
              var color =
                aqi.aqi <= 50
                  ? "#10b981"
                  : aqi.aqi <= 100
                    ? "#f59e0b"
                    : "#ef4444";
              document.getElementById("data-aqi").innerHTML =
                '<span style="color:' +
                color +
                '">' +
                aqi.aqi +
                " (" +
                aqi.category +
                ")</span>";
            } else {
              document.getElementById("data-aqi").textContent = "N/D";
            }
          })
          .catch(function () {
            document.getElementById("data-aqi").textContent = "N/D";
          });
      }

      function fetchSolarPotential(lat, lng) {
        var url =
          "https://solar.googleapis.com/v1/buildingInsights:findClosest?location.latitude=" +
          lat +
          "&location.longitude=" +
          lng +
          "&requiredQuality=LOW&key=" +
          MAPS_API_KEY;
        fetch(url)
          .then(function (response) {
            if (response.status === 404) {
              throw new Error("No solar data");
            }
            return response.json();
          })
          .then(function (data) {
            if (data.solarPotential) {
              var hours = Math.round(
                data.solarPotential.maxSunshineHoursPerYear || 0,
              );
              document.getElementById("data-solar").textContent =
                hours + " hrs/yr";
            } else {
              document.getElementById("data-solar").textContent =
                "Sin edificio";
            }
          })
          .catch(function (err) {
            console.log("Solar API info:", err.message);
            document.getElementById("data-solar").textContent = "N/D";
          });
      }

      function onApproachChange() {
        var select = document.getElementById("approach-select");
        var value = select.value;
        if (!value) {
          selectedApproach = null;
          document.getElementById("indices-panel").classList.remove("active");
          document.getElementById("status-approach").classList.remove("ready");
          checkReadyState();
          return;
        }
        selectedApproach = value;
        var config = approaches[value];
        document.getElementById("status-approach").classList.add("ready");
        var html = "";
        for (var i = 0; i < config.indices.length; i++) {
          var idx = config.indices[i];
          html +=
            '<div class="index-item"><div class="index-header"><div class="index-color" style="background:' +
            idx.color +
            '"></div><span class="index-name">' +
            idx.name +
            '</span><span class="index-api">' +
            idx.api +
            '</span></div><div class="index-desc">' +
            idx.desc +
            "</div></div>";
        }
        document.getElementById("indices-list").innerHTML = html;

        // Hide previous results if any
        var resultsContainer = document.getElementById("analysis-results");
        if (resultsContainer) {
          resultsContainer.style.display = "none";
          resultsContainer.innerHTML = "";
        }

        document.getElementById("indices-panel").classList.add("active");
        var resultEl = document.getElementById("result-approach");
        resultEl.innerHTML =
          '<i class="fas fa-' +
          config.icon +
          ' result-icon"></i><div class="result-content"><h4>' +
          config.name +
          "</h4><p>" +
          config.indices.length +
          " capas de datos</p></div>";
        savePreferences();
        checkReadyState();
      }

      function onRadiusChange() {
        var select = document.getElementById("radius-select");
        var value = select.value;
        if (!value) {
          selectedRadius = null;
        } else {
          selectedRadius = parseInt(value);
        }
        updateAnalysisCircle();
        savePreferences();
        checkReadyState();
      }

      function checkReadyState() {
        var btn = document.getElementById("analyze-btn");
        btn.disabled = !(selectedPlace && selectedApproach && selectedRadius);

        // Update button text to show what's missing
        var missing = [];
        var isEn = typeof currentLang !== 'undefined' && currentLang === 'en';

        if (!selectedPlace) missing.push(isEn ? "Location" : "ubicación");
        if (!selectedApproach) missing.push(isEn ? "Approach" : "enfoque");
        if (!selectedRadius) missing.push(isEn ? "Radius" : "radio");

        var hint = document.querySelector("#analyze-btn + p");
        if (hint) {
          if (missing.length > 0) {
            hint.textContent = (isEn ? "Requires: " : "Requiere: ") + missing.join(", ");
            hint.style.color = "var(--text-light)";
          } else {
            hint.textContent = isEn ? "✓ Ready to analyze" : "✓ Listo para analizar";
            hint.style.color = "var(--secondary)";
          }
        }
      }

      function centerMap() {
        if (map) {
          map.setCenter({ lat: -33.4489, lng: -70.6693 });
          map.setZoom(5);
        }
      }

      function toggleMapType() {
        if (map) {
          isSatellite = !isSatellite;
          map.setMapTypeId(isSatellite ? "hybrid" : "roadmap");
        }
      }

      function addMapLegend() {
        // Remove existing legend if any
        removeMapLegend();

        var legendDiv = document.createElement("div");
        legendDiv.id = "fire-risk-legend";
        legendDiv.style.cssText =
          "position:absolute; bottom:30px; left:10px; background:rgba(255,255,255,0.95); padding:12px 16px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.25); font-family:Inter,sans-serif; z-index:1000; max-width:200px;";

        var title = document.createElement("div");
        title.textContent = "Riesgo de Incendio";
        title.style.cssText =
          "font-weight:600; font-size:0.85rem; margin-bottom:8px; color:#1e3a5f;";
        legendDiv.appendChild(title);

        var scale = [
          { color: "#22c55e", label: "Bajo" },
          { color: "#84cc16", label: "Moderado" },
          { color: "#eab308", label: "Alto" },
          { color: "#f97316", label: "Muy Alto" },
          { color: "#dc2626", label: "Extremo" },
        ];

        for (var i = 0; i < scale.length; i++) {
          var item = document.createElement("div");
          item.style.cssText =
            "display:flex; align-items:center; margin:4px 0; font-size:0.75rem;";

          var colorBox = document.createElement("div");
          colorBox.style.cssText =
            "width:20px; height:14px; background:" +
            scale[i].color +
            "; border-radius:3px; margin-right:8px;";

          var label = document.createElement("span");
          label.textContent = scale[i].label;
          label.style.color = "#374151";

          item.appendChild(colorBox);
          item.appendChild(label);
          legendDiv.appendChild(item);
        }

        document.getElementById("demo-map").appendChild(legendDiv);
      }

      function removeMapLegend() {
        var existing = document.getElementById("fire-risk-legend");
        if (existing) {
          existing.remove();
        }
      }

      var currentGeeLayer = null;

      function analyzeTerritory() {
        if (!selectedPlace || !selectedApproach) {
          return;
        }

        var btn = document.getElementById("analyze-btn");
        var isEn = typeof currentLang !== 'undefined' && currentLang === 'en';
        btn.innerHTML = '<span class="loading-spinner"></span> ' + (isEn ? 'Processing...' : 'Procesando...');
        btn.disabled = true;

        // Show Skeleton loaders
        showAnalysisSkeleton();

        var payload = {
          lat: selectedPlace.lat,
          lng: selectedPlace.lng,
          approach: selectedApproach,
          radius: selectedRadius,
        };

        fetch("/api/v1/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
          .then((response) => response.json())
          .then((data) => {
            var isEn = typeof currentLang !== 'undefined' && currentLang === 'en';
            btn.innerHTML =
              '<i class="fas fa-satellite-dish"></i> ' + (isEn ? 'Start Analysis' : 'Iniciar Analisis');
            btn.disabled = false;

            if (data.status === "success") {
              // Hide Skeleton and update dynamic NDVI chart
              hideAnalysisSkeleton();
              updateNDVIChart(data.data);

              // Create Results Table
              var tableHtml =
                '<table class="results-table" style="width:100%; border-collapse:collapse; margin-top:10px; font-size:0.9rem;">';
              tableHtml +=
                '<thead><tr style="background:var(--primary-light); color:white;"><th style="padding:8px; text-align:left;">Métrica</th><th style="padding:8px; text-align:right;">Valor</th></tr></thead><tbody>';

              for (var key in data.data) {
                tableHtml +=
                  '<tr style="border-bottom:1px solid #eee;"><td style="padding:8px;">' +
                  key +
                  '</td><td style="padding:8px; text-align:right; font-weight:600;">' +
                  data.data[key] +
                  "</td></tr>";
              }
              tableHtml += "</tbody></table>";

              // Add area info
              var areaKm2 = (data.area_m2 / 1000000).toFixed(2);
              var areaInfo =
                '<div style="margin-top:0.5rem; padding:0.5rem; background:#f8fafc; border-radius:6px; font-size:0.8rem; color:var(--text-light);">' +
                '<i class="fas fa-ruler-combined"></i> Area de analisis: <strong>' +
                data.area_m2.toLocaleString() +
                " m²</strong> (" +
                areaKm2 +
                " km²) | Radio: " +
                (data.meta.buffer_radius_m || 1000) +
                "m" +
                "</div>";

              // Display in Analysis Results Container
              var resultsContainer =
                document.getElementById("analysis-results");
              if (!resultsContainer) {
                resultsContainer = document.createElement("div");
                resultsContainer.id = "analysis-results";
                resultsContainer.style.marginBottom = "1rem";
                var indicesPanel = document.getElementById("indices-panel");
                indicesPanel.insertBefore(
                  resultsContainer,
                  document.getElementById("indices-list"),
                );
              }

              resultsContainer.innerHTML =
                '<div class="result-box" style="background:white; border:1px solid var(--secondary); border-radius:8px; padding:1rem; box-shadow:0 2px 4px rgba(0,0,0,0.05);">' +
                '<h4 style="color:var(--primary); margin-top:0; margin-bottom:0.5rem; border-bottom:1px solid #eee; padding-bottom:0.5rem;"><i class="fas fa-chart-bar"></i> Resultados del Análisis</h4>' +
                tableHtml +
                areaInfo +
                '<button onclick="showInterpretationModal()" style="margin-top:1rem; width:100%;" class="btn btn-secondary"><i class="fas fa-info-circle"></i> Ver Escalas</button>' +
                "</div>";
              resultsContainer.style.display = "block";

              // Store FULL data for AI interpretation
              window.lastAnalysisData = data.data;
              window.lastApproach = selectedApproach;
              window.lastAnalysisMeta = data.meta;
              window.lastAnalysisArea = data.area_m2;

              // Save to analysis history
              if (selectedPlace) addToHistory(selectedPlace, selectedApproach);

              // Scroll to results
              resultsContainer.scrollIntoView({
                behavior: "smooth",
                block: "start",
              });

              // Add GEE layer to map
              if (data.map_layer && data.map_layer.url) {
                if (currentGeeLayer) {
                  map.overlayMapTypes.removeAt(0);
                }

                var geeMapType = new google.maps.ImageMapType({
                  getTileUrl: function (coord, zoom) {
                    var url = data.map_layer.url;
                    url = url
                      .replace("{x}", coord.x)
                      .replace("{y}", coord.y)
                      .replace("{z}", zoom);
                    return url;
                  },
                  tileSize: new google.maps.Size(256, 256),
                  name: "GEE Layer",
                  opacity: 0.7,
                });

                map.overlayMapTypes.insertAt(0, geeMapType);
                currentGeeLayer = geeMapType;
                console.log("Capa GEE agregada: " + data.map_layer.url);

                // Añadir leyenda de colores si es fire-risk
                if (selectedApproach === "fire-risk") {
                  addMapLegend();
                } else {
                  removeMapLegend();
                }
              }

              // Open Chat Sidebar with AI Interpretation
              var locationName = selectedPlace
                ? selectedPlace.name
                : currentLang === 'en' ? "the selected location" : "la ubicación seleccionada";
              analysisContext = {
                approach: selectedApproach,
                results: data.data,
                meta: data.meta,
                area_m2: data.area_m2,
                location: locationName,
              };

              // Open interpretation modal with AI analysis
              showInterpretationModal();
            } else if (data.status === "warning") {
              hideAnalysisSkeleton();
              showToast(data.message, 'toast-warning');
            } else {
              hideAnalysisSkeleton();
              showToast("Error: " + data.message, 'toast-error');
            }
          })
          .catch((error) => {
            hideAnalysisSkeleton();
            console.error("Error:", error);
            var isEnErr = typeof currentLang !== 'undefined' && currentLang === 'en';
            btn.innerHTML =
              '<i class="fas fa-satellite-dish"></i> ' + (isEnErr ? 'Start Analysis' : 'Iniciar Analisis');
            btn.disabled = false;
            showToast(isEnErr ? 'Connection error. Please try again.' : 'Error de conexion. Intenta de nuevo.', 'toast-error');
          });
      }

      function showInterpretationModal() {
        var isEn = typeof currentLang !== 'undefined' && currentLang === 'en';
        var data = window.lastAnalysisData || {};
        var approach = window.lastApproach || "";
        var modalBody = document.getElementById("modal-body");
        var html = "";

        // Extract numeric values for interpretation
        var ndvi = parseFloat(
          Object.values(data).find(
            (v) =>
              v &&
              v.toString().match(/^-?\d+\.\d+$/) &&
              parseFloat(v) >= -1 &&
              parseFloat(v) <= 1,
          ) || 0,
        );

        // NDVI Scale (if applicable)
        if (
          approach === "mining" ||
          approach === "agriculture" ||
          approach === "environmental"
        ) {
          var ndviVal = 0;
          for (var k in data) {
            if (
              k.toLowerCase().includes("ndvi") ||
              k.toLowerCase().includes("vegetac")
            ) {
              ndviVal = parseFloat(data[k]) || 0;
              break;
            }
          }
          var ndviInterp =
            ndviVal > 0.6
              ? "Vegetacion densa y saludable. Excelente cobertura vegetal."
              : ndviVal > 0.3
                ? "Vegetacion moderada. Cobertura vegetal aceptable."
                : ndviVal > 0.1
                  ? "Vegetacion escasa o con estres. Requiere atencion."
                  : "Sin vegetacion significativa o superficie construida/agua.";

          html +=
            '<div class="scale-section">' +
            '<div class="scale-title"><i class="fas fa-leaf" style="color:#22c55e"></i> Indice de Vegetacion (NDVI) <span class="value-badge">' +
            ndviVal.toFixed(2) +
            "</span></div>" +
            '<div class="scale-bar ndvi"></div>' +
            '<div class="scale-labels"><span>-1 (Agua)</span><span>0 (Suelo)</span><span>+1 (Vegetacion densa)</span></div>' +
            '<div class="interpretation-text">' +
            ndviInterp +
            "</div>" +
            "</div>";
        }

        // NDWI Scale (if applicable)
        if (
          approach === "flood-risk" ||
          approach === "water-management" ||
          approach === "mining"
        ) {
          var ndwiVal = 0;
          for (var k in data) {
            if (
              k.toLowerCase().includes("ndwi") ||
              k.toLowerCase().includes("agua")
            ) {
              ndwiVal = parseFloat(data[k]) || 0;
              break;
            }
          }
          var ndwiInterp =
            ndwiVal > 0.3
              ? "Alta presencia de agua. Zona de cuerpo de agua o saturacion."
              : ndwiVal > 0
                ? "Humedad moderada. Suelo humedo o vegetacion con agua."
                : ndwiVal > -0.3
                  ? "Baja humedad. Suelo seco o vegetacion seca."
                  : "Muy seco. Suelo arido o superficie urbana.";

          html +=
            '<div class="scale-section">' +
            '<div class="scale-title"><i class="fas fa-water" style="color:#3b82f6"></i> Indice de Agua (NDWI) <span class="value-badge">' +
            ndwiVal.toFixed(2) +
            "</span></div>" +
            '<div class="scale-bar ndwi"></div>' +
            '<div class="scale-labels"><span>-1 (Seco)</span><span>0</span><span>+1 (Agua)</span></div>' +
            '<div class="interpretation-text">' +
            ndwiInterp +
            "</div>" +
            "</div>";
        }

        // Slope Scale (if applicable)
        if (
          approach === "real-estate" ||
          approach === "energy" ||
          approach === "land-planning" ||
          approach === "mining"
        ) {
          var slopeVal = 0;
          for (var k in data) {
            if (
              k.toLowerCase().includes("pendiente") ||
              k.toLowerCase().includes("slope")
            ) {
              slopeVal = parseFloat(data[k]) || 0;
              break;
            }
          }
          var slopeInterp =
            slopeVal < 5
              ? "Terreno plano. Ideal para construccion y agricultura mecanizada."
              : slopeVal < 15
                ? "Pendiente suave. Apto para la mayoria de usos con algunas consideraciones."
                : slopeVal < 30
                  ? "Pendiente moderada. Requiere terrazas o muros de contencion."
                  : "Pendiente pronunciada. Alto riesgo de erosion, no apto para construccion convencional.";

          html +=
            '<div class="scale-section">' +
            '<div class="scale-title"><i class="fas fa-mountain" style="color:#8b5cf6"></i> Pendiente del Terreno <span class="value-badge">' +
            slopeVal.toFixed(1) +
            "°</span></div>" +
            '<div class="scale-bar slope"></div>' +
            '<div class="scale-labels"><span>0° (Plano)</span><span>15° (Suave)</span><span>45°+ (Escarpado)</span></div>' +
            '<div class="interpretation-text">' +
            slopeInterp +
            "</div>" +
            "</div>";
        }

        // Generic interpretation if no specific scales
        if (html === "") {
          html =
            '<div class="scale-section">' +
            '<div class="scale-title"><i class="fas fa-chart-bar"></i> ' + (isEn ? 'Analysis Summary' : 'Resumen del Analisis') + '</div>' +
            '<p style="color:var(--text-light)">' + (isEn ? 'Results show computed values for the selected location. Positive values in vegetation indices indicate greater vegetation cover. Low slopes are better for construction.' : 'Los resultados muestran los valores calculados para la ubicacion seleccionada. Valores positivos en indices de vegetacion indican mayor cobertura vegetal. Pendientes bajas son mejores para construccion.') + '</p>' +
            "</div>";
        }

        // Add satellite info
        html +=
          '<div style="margin-top:1rem; padding:1rem; background:#f0fdf4; border-radius:8px; font-size:0.85rem; color:var(--text-light);">' +
          '<i class="fas fa-satellite" style="color:var(--secondary)"></i> <strong>' + (isEn ? 'Source' : 'Fuente') + ':</strong> Sentinel-2 MSI + SRTM | ' +
          '<i class="fas fa-calendar"></i> ' + (isEn ? 'Most recent available image (last 6 months)' : 'Imagen mas reciente disponible (ultimos 6 meses)') +
          "</div>";

        modalBody.innerHTML = html;
        document.getElementById("interpretation-modal").classList.add("active");

        // Store context for chat
        var locationName = selectedPlace
          ? selectedPlace.name
          : currentLang === 'en' ? "selected location" : "ubicación seleccionada";
        analysisContext = {
          approach: approach,
          results: data,
          location: locationName,
        };

        // Fetch AI interpretation
        fetchAIInterpretation(data, approach, locationName);
      }

      function closeModal() {
        document
          .getElementById("interpretation-modal")
          .classList.remove("active");
      }

      // Close modal on outside click
      document
        .getElementById("interpretation-modal")
        .addEventListener("click", function (e) {
          if (e.target === this) closeModal();
        });

      // Close modal on ESC key
      document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
          var modal = document.getElementById('interpretation-modal');
          if (modal && modal.classList.contains('active')) {
            closeModal();
            e.preventDefault();
          }
          var chatSidebar = document.getElementById('chat-sidebar');
          if (chatSidebar && chatSidebar.classList.contains('open')) {
            toggleChat();
            e.preventDefault();
          }
        }
      });

      // ============================================================================
      // CHAT AND AI FUNCTIONS
      // ============================================================================

      function toggleChat() {
        var sidebar = document.getElementById("chat-sidebar");
        sidebar.classList.toggle("open");
      }

      function sendChatMessage() {
        var input = document.getElementById("chat-input");
        var message = input.value.trim();
        if (!message) return;

        // Add user message to UI
        addChatMessage(message, "user");
        input.value = "";

        // Add to history
        chatHistory.push({ role: "user", content: message });

        // Show typing indicator
        var typingHtml =
          '<div class="chat-message assistant" id="typing-indicator">' +
          '<div class="message-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div></div>';
        document
          .getElementById("chat-messages")
          .insertAdjacentHTML("beforeend", typingHtml);
        scrollChatToBottom();

        // Send to API
        fetch("/api/v1/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: message,
            context: analysisContext,
            history: chatHistory,
          }),
        })
          .then((response) => response.json())
          .then((data) => {
            // Remove typing indicator
            var typing = document.getElementById("typing-indicator");
            if (typing) typing.remove();

            if (data.status === "success") {
              addChatMessage(data.response, "assistant");
              chatHistory.push({ role: "assistant", content: data.response });
            } else {
              addChatMessage(
                "Lo siento, hubo un error. Intenta de nuevo.",
                "assistant",
              );
            }
          })
          .catch((error) => {
            var typing = document.getElementById("typing-indicator");
            if (typing) typing.remove();
            addChatMessage(
              "Error de conexion. Verifica tu internet.",
              "assistant",
            );
          });
      }

      function addChatMessage(text, role) {
        var messagesContainer = document.getElementById("chat-messages");
        var time = new Date().toLocaleTimeString("es-CL", {
          hour: "2-digit",
          minute: "2-digit",
        });
        var html =
          '<div class="chat-message ' +
          role +
          '">' +
          '<div class="message-bubble">' +
          text.replace(/\\n/g, "<br>") +
          "</div>" +
          '<div class="message-time">' +
          time +
          "</div></div>";
        messagesContainer.insertAdjacentHTML("beforeend", html);
        scrollChatToBottom();
      }

      function scrollChatToBottom() {
        var container = document.getElementById("chat-messages");
        container.scrollTop = container.scrollHeight;
      }

      function requestAIInterpretation(
        results,
        approach,
        locationName,
        areaM2,
        meta,
      ) {
        // Show typing indicator in chat
        var typingHtml =
          '<div class="chat-message assistant" id="interpretation-typing">' +
          '<div class="message-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div> Analizando datos...</div></div>';
        document
          .getElementById("chat-messages")
          .insertAdjacentHTML("beforeend", typingHtml);
        scrollChatToBottom();

        var areaKm2 = (areaM2 / 1000000).toFixed(2);
        var radiusM = meta ? meta.buffer_radius_m : 1000;

        // Add area info to results for context
        var enrichedResults = Object.assign({}, results);
        enrichedResults["Área analizada"] =
          areaM2.toLocaleString() + " m² (" + areaKm2 + " km²)";
        enrichedResults["Radio de análisis"] = radiusM + " metros";

        // Call interpret API (designed for analysis interpretation)
        fetch("/api/v1/interpret", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            results: enrichedResults,
            approach: approach,
            location: locationName,
          }),
        })
          .then((response) => response.json())
          .then((data) => {
            var typing = document.getElementById("interpretation-typing");
            if (typing) typing.remove();

            if (data.status === "success") {
              // Format and display interpretation
              var formattedResponse = data.interpretation
                .replace(/\\n/g, "<br>")
                .replace(/\\*\\*(.*?)\\*\\*/g, "<strong>$1</strong>")
                .replace(/\\*(.*?)\\*/g, "<em>$1</em>");

              var interpretationHtml =
                '<div class="chat-message assistant">' +
                '<div class="message-bubble" style="background: linear-gradient(135deg, #f0fdf4, #ecfeff); border-left: 3px solid var(--secondary);">' +
                '<div style="font-weight:600; color:var(--primary); margin-bottom:0.5rem;"><i class="fas fa-robot"></i> Interpretación del Análisis</div>' +
                '<div style="line-height:1.6;">' +
                formattedResponse +
                "</div>" +
                "</div>" +
                '<div class="message-time">' +
                new Date().toLocaleTimeString("es-CL", {
                  hour: "2-digit",
                  minute: "2-digit",
                }) +
                "</div>" +
                "</div>";

              document
                .getElementById("chat-messages")
                .insertAdjacentHTML("beforeend", interpretationHtml);
              scrollChatToBottom();

              // Add to history
              chatHistory.push({
                role: "user",
                content: "Interpreta los resultados del análisis",
              });
              chatHistory.push({
                role: "assistant",
                content: data.interpretation,
              });

              // Add follow-up suggestion
              var followUp =
                '<div class="chat-message assistant">' +
                '<div class="message-bubble" style="font-size:0.85rem;">' +
                "💡 ¿Tienes alguna duda sobre estos resultados? Puedes preguntarme sobre los indices, valores o significados." +
                "</div></div>";
              document
                .getElementById("chat-messages")
                .insertAdjacentHTML("beforeend", followUp);
              scrollChatToBottom();
            } else {
              addChatMessage(
                "No pude generar la interpretación: " +
                  (data.message || "Error desconocido"),
                "assistant",
              );
            }
          })
          .catch((error) => {
            console.error("Interpretation error:", error);
            var typing = document.getElementById("interpretation-typing");
            if (typing) typing.remove();
            addChatMessage(
              "Error al conectar con el asistente. Verifica tu conexión.",
              "assistant",
            );
          });
      }

      function fetchAIInterpretation(results, approach, locationName) {
        // Show loading in modal
        var modalBody = document.getElementById("modal-body");
        var existingContent = modalBody.innerHTML;

        var loadingHtml =
          '<div class="ai-loading" id="ai-loading">' +
          '<div class="typing-indicator"><span></span><span></span><span></span></div>' +
          "<span>Generando interpretacion con IA...</span></div>";
        modalBody.insertAdjacentHTML("beforeend", loadingHtml);

        fetch("/api/v1/interpret", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            results: results,
            approach: approach,
            location: locationName,
          }),
        })
          .then((response) => response.json())
          .then((data) => {
            var loading = document.getElementById("ai-loading");
            if (loading) loading.remove();

            if (data.status === "success") {
              // Format AI text with styled sections
              var formattedText = data.interpretation
                // Section headers with icons
                .replace(
                  /RESUMEN/g,
                  '<div class="ai-section"><h6 class="ai-section-title">📋 Resumen</h6><div class="ai-section-content">',
                )
                .replace(
                  /QUÉ SIGNIFICAN LOS DATOS/g,
                  '</div></div><div class="ai-section"><h6 class="ai-section-title">📊 Qué Significan los Datos</h6><div class="ai-section-content">',
                )
                .replace(
                  /IMPLICACIONES PRÁCTICAS/g,
                  '</div></div><div class="ai-section"><h6 class="ai-section-title">💡 Implicaciones Prácticas</h6><div class="ai-section-content">',
                )
                .replace(
                  /RECOMENDACIONES/g,
                  '</div></div><div class="ai-section"><h6 class="ai-section-title">✅ Recomendaciones</h6><div class="ai-section-content">',
                )
                // Markdown bold - using string method
                .split("**")
                .map(function (part, i) {
                  return i % 2 === 1
                    ? '<strong style="color:var(--secondary)">' +
                        part +
                        "</strong>"
                    : part;
                })
                .join("")
                // Line breaks
                .split(String.fromCharCode(10))
                .join("<br>");

              // Close any open section
              if (formattedText.includes("ai-section-content")) {
                formattedText += "</div></div>";
              }
              // Clean up empty opening tag if first section not matched
              formattedText = formattedText.replace(/^<\/div><\/div>/, "");

              var aiHtml =
                '<div class="ai-interpretation" style="margin-top:1.5rem; padding:1rem; background:linear-gradient(135deg, #f0fdf4 0%, #ecfeff 100%); border-radius:12px; border-left:4px solid var(--secondary);">' +
                '<h5 style="margin:0 0 1rem; color:var(--primary); display:flex; align-items:center; gap:0.5rem;"><i class="fas fa-robot"></i> Interpretación del Asistente IA</h5>' +
                '<div class="ai-content" style="line-height:1.7; color:var(--text);">' +
                formattedText +
                "</div>" +
                "</div>";

              // Add section styles dynamically
              if (!document.getElementById("ai-section-styles")) {
                var styles = document.createElement("style");
                styles.id = "ai-section-styles";
                styles.textContent =
                  ".ai-section { margin-bottom:1rem; } .ai-section-title { color:var(--primary); margin:0 0 0.5rem; padding-bottom:0.3rem; border-bottom:1px solid rgba(45,90,74,0.2); font-size:0.9rem; font-weight:600; } .ai-section-content { padding-left:0.5rem; }";
                document.head.appendChild(styles);
              }

              modalBody.insertAdjacentHTML("beforeend", aiHtml);
            } else {
              var errorHtml =
                '<div class="ai-interpretation" style="margin-top:1rem; padding:1rem; background:#fef2f2; border-radius:8px; color:#dc2626;">' +
                '<i class="fas fa-exclamation-circle"></i> No se pudo generar la interpretación. Intenta de nuevo.' +
                "</div>";
              modalBody.insertAdjacentHTML("beforeend", errorHtml);
            }
          })
          .catch((error) => {
            var loading = document.getElementById("ai-loading");
            if (loading) loading.remove();
            console.error("AI Interpretation error:", error);
          });
      }

      // Contact Form Handler
      document
        .getElementById("contact-form")
        .addEventListener("submit", function (e) {
          e.preventDefault();
          var btn = document.getElementById("contact-submit");
          var originalText = btn.innerHTML;
          btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
          btn.disabled = true;

          var formData = {
            name: document.getElementById("contact-name").value,
            company: document.getElementById("contact-company").value,
            email: document.getElementById("contact-email").value,
            message: document.getElementById("contact-message").value,
          };

          fetch("/api/v1/contact", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
          })
            .then((response) => response.json())
            .then((data) => {
              btn.innerHTML = originalText;
              btn.disabled = false;
              if (data.status === "success") {
                document.getElementById("form-success").style.display =
                  "block";
                document.getElementById("contact-form").reset();
                setTimeout(function() {
                  document.getElementById("form-success").style.display = "none";
                }, 6000);
                var isEn = typeof currentLang !== 'undefined' && currentLang === 'en';
                showToast(isEn ? 'Message sent successfully!' : 'Mensaje enviado correctamente!', 'toast-success');
              } else {
                showToast(
                  "Error: " + (data.message || "Intenta nuevamente"),
                  'toast-error'
                );
              }
            })
            .catch((error) => {
              btn.innerHTML = originalText;
              btn.disabled = false;
              showToast(currentLang === 'en' ? 'Connection error. Please try again.' : 'Error de conexion. Intenta nuevamente.', 'toast-error');
            });
        });

      // ============================================================================
      // MOBILE TAB NAVIGATION
      // ============================================================================

      function isMobileView() {
        return window.innerWidth <= 768;
      }

      function switchTab(tabName) {
        // Update active tab button
        document.querySelectorAll(".mobile-tab").forEach(function (tab) {
          tab.classList.remove("active");
          if (tab.dataset.tab === tabName) {
            tab.classList.add("active");
          }
        });

        // Scroll to the corresponding section
        var sectionMap = {
          inicio: "hero",
          demo: "demo",
          servicios: "servicios",
          contacto: "contacto",
        };

        var targetId = sectionMap[tabName];
        var section = null;

        if (targetId === "hero") {
          section = document.querySelector(".hero");
        } else {
          section = document.getElementById(targetId);
        }

        if (section) {
          var offset = isMobileView() ? 60 : 0; // Account for mobile header
          var sectionTop =
            section.getBoundingClientRect().top + window.pageYOffset - offset;
          window.scrollTo({ top: sectionTop, behavior: "smooth" });
        }
      }

      // Update active tab on scroll
      function updateActiveTabOnScroll() {
        if (!isMobileView()) return;

        var sections = [
          {
            id: "hero",
            tab: "inicio",
            element: document.querySelector(".hero"),
          },
          { id: "demo", tab: "demo", element: document.getElementById("demo") },
          {
            id: "servicios",
            tab: "servicios",
            element: document.getElementById("servicios"),
          },
          {
            id: "contacto",
            tab: "contacto",
            element: document.getElementById("contacto"),
          },
        ];

        var scrollPos = window.scrollY + 150;

        for (var i = sections.length - 1; i >= 0; i--) {
          var section = sections[i];
          if (section.element && section.element.offsetTop <= scrollPos) {
            document.querySelectorAll(".mobile-tab").forEach(function (tab) {
              tab.classList.remove("active");
              if (tab.dataset.tab === section.tab) {
                tab.classList.add("active");
              }
            });
            break;
          }
        }
      }

      // Enable mobile mode on mobile devices
      function initMobileMode() {
        if (isMobileView()) {
          document.body.classList.add("mobile-tab-mode");
        } else {
          document.body.classList.remove("mobile-tab-mode");
        }
      }

      // Initialize mobile mode and add scroll listener
      window.addEventListener("resize", initMobileMode);
      window.addEventListener("resize", syncDemoMapLayout);
      window.addEventListener("scroll", updateActiveTabOnScroll);
      document.addEventListener("DOMContentLoaded", function () {
        initMobileMode();
        syncDemoMapLayout();
        updateActiveTabOnScroll();
        fetchPublicStats(); // [NEW] Fetch stats on load
      });

      // [NEW] Fetch Public Stats
      function fetchPublicStats() {
          fetch('/api/v1/stats', {
            headers: {
              Accept: 'application/json',
            },
          })
            .then(response => {
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                var visits = Number.isFinite(Number(data && data.visits))
                  ? Math.max(0, Math.floor(Number(data.visits)))
                  : 0;
                var analyses = Number.isFinite(Number(data && data.analyses))
                  ? Math.max(0, Math.floor(Number(data.analyses)))
                  : 0;

                animateValue("stat-visits", 0, visits, 2000);
                animateValue("stat-analyses", 0, analyses, 2000);
            })
            .catch(err => {
                console.error("Error fetching stats:", err);
                setStatValue("stat-visits", 0);
                setStatValue("stat-analyses", 0);
            });
      }

      function setStatValue(id, value) {
          var obj = document.getElementById(id);
          if (!obj) return;

          var safeValue = Number.isFinite(Number(value))
            ? Math.max(0, Math.floor(Number(value)))
            : 0;

          obj.innerHTML = safeValue.toLocaleString();
      }

      function animateValue(id, start, end, duration) {
          var obj = document.getElementById(id);
          if (!obj) return;

          var safeStart = Number.isFinite(Number(start))
            ? Math.max(0, Math.floor(Number(start)))
            : 0;
          var safeEnd = Number.isFinite(Number(end))
            ? Math.max(0, Math.floor(Number(end)))
            : 0;

          if (safeStart === safeEnd) {
              obj.innerHTML = safeEnd.toLocaleString();
              return;
          }

          var range = safeEnd - safeStart;
          var current = safeStart;
          var steps = Math.min(120, Math.max(1, Math.abs(range)));
          var increment = range / steps;
          var stepTime = Math.max(16, Math.floor(duration / steps));

          var timer = setInterval(function() {
              current += increment;

              if ((range > 0 && current >= safeEnd) || (range < 0 && current <= safeEnd)) {
                  current = safeEnd;
              }

              obj.innerHTML = Math.round(current).toLocaleString();

              if (current === safeEnd) {
                  clearInterval(timer);
              }
          }, stepTime);
      }


      // ============================================================================
      // LANGUAGE TOGGLE LOGIC
      // ============================================================================
      let currentLang = 'es';

      function toggleLanguage() {
        currentLang = currentLang === 'es' ? 'en' : 'es';
        updateLanguage();
      }

      function updateLanguage() {
        const isEn = currentLang === 'en';
        
        // Update Button
        const langIcon = document.getElementById('lang-icon');
        const langText = document.getElementById('lang-text');
        if(langIcon) langIcon.textContent = isEn ? '🇨🇱' : '🇺🇸';
        if(langText) langText.textContent = isEn ? 'ES' : 'EN';
        
        // Translate Elements with data-en
        const elements = document.querySelectorAll('[data-en]');
        elements.forEach(el => {
            if (!el.dataset.original) el.dataset.original = el.textContent; // Cache original ES
            el.textContent = isEn ? el.dataset.en : el.dataset.original;
        });

        // Translate Elements with data-en-html (preserve HTML inside)
         const htmlElements = document.querySelectorAll('[data-en-html]');
         htmlElements.forEach(el => {
            if (!el.dataset.originalHtml) el.dataset.originalHtml = el.innerHTML; // Cache original ES HTML
            el.innerHTML = isEn ? el.dataset.enHtml : el.dataset.originalHtml;
        });

        // Translate Placeholders
        const inputElements = document.querySelectorAll('[data-en-placeholder]');
        inputElements.forEach(el => {
            if (!el.dataset.originalPlaceholder) el.dataset.originalPlaceholder = el.placeholder;
            el.placeholder = isEn ? el.dataset.enPlaceholder : el.dataset.originalPlaceholder;
        });

        // Translate Titles (Tooltip)
        const titleElements = document.querySelectorAll('[data-en-title]');
        titleElements.forEach(el => {
            if (!el.dataset.originalTitle) el.dataset.originalTitle = el.title;
            el.title = isEn ? el.dataset.enTitle : el.dataset.originalTitle;
        });

        // Translate optgroup labels
        const optgroupElements = document.querySelectorAll('[data-en-label]');
        optgroupElements.forEach(el => {
            if (!el.dataset.originalLabel) el.dataset.originalLabel = el.label;
            el.label = isEn ? el.dataset.enLabel : el.dataset.originalLabel;
        });
      }

      // ============================================================================
      // INITIALIZATION
      // ============================================================================
      loadHistory();
      renderHistory();
      initCollapsiblePanels();
      syncDemoMapLayout();

      // Restore saved preferences after map loads
      var _origInitMap = typeof initMap === 'function' ? initMap : null;

      // Start the map initialization
      loadGoogleMaps();

      // ============================================================================
      // CUSTOM UI/UX EXTENSIONS (DARK MODE, SKELETONS, CHART.JS)
      // ============================================================================
      
      // Theme toggling (Dark/Light)
      function toggleTheme() {
          const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
          const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
          
          document.documentElement.setAttribute('data-theme', newTheme);
          localStorage.setItem('theme', newTheme);
          
          // Sync all switch button icons
          const themeIcons = document.querySelectorAll('.theme-icon');
          themeIcons.forEach(icon => {
              icon.className = newTheme === 'dark' ? 'fas fa-sun theme-icon' : 'fas fa-moon theme-icon';
          });
          
          console.log("Tema del sitio alternado a:", newTheme);
          
          // Opcional: Si el mapa de Google Maps está activo y en modo satélite, se mantiene igual,
          // pero si está en modo vectorial, podríamos configurarle estilos oscuros aquí.
      }

      // Initialize theme on load
      (function initTheme() {
          const savedTheme = localStorage.getItem('theme');
          const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          const targetTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
          
          document.documentElement.setAttribute('data-theme', targetTheme);
          
          // Sync button icons after DOM is fully loaded
          document.addEventListener('DOMContentLoaded', () => {
              const themeIcons = document.querySelectorAll('.theme-icon');
              themeIcons.forEach(icon => {
                  icon.className = targetTheme === 'dark' ? 'fas fa-sun theme-icon' : 'fas fa-moon theme-icon';
              });
          });
      })();

      // Dynamic NDVI trends Chart using Chart.js
      let ndviChartInstance = null;

      function updateNDVIChart(analysisData) {
          const canvas = document.getElementById('ndviChart');
          if (!canvas) return;

          // Extract a base vegetation index value from results
          let baseValue = 0.35; // Default average
          for (let key in analysisData) {
              if (key.toLowerCase().includes('ndvi') || key.toLowerCase().includes('vegetac')) {
                  baseValue = parseFloat(analysisData[key]) || baseValue;
                  break;
              }
          }

          // Generate simulated historical trend curve over 6 periods based on real GEE results
          const months = ['Dic', 'Ene', 'Feb', 'Mar', 'Abr', 'May'];
          const dataset = [];
          for (let i = 0; i < 6; i++) {
              // Create slight historical fluctuations (simulating seasonal changes in Chile)
              let seasonalFluct = Math.sin(i / 1.5) * 0.08;
              let val = Math.max(-0.2, Math.min(1.0, baseValue - (5 - i) * 0.03 + seasonalFluct));
              dataset.push(parseFloat(val.toFixed(3)));
          }

          // Destroy previous instance to avoid layout overlapping
          if (ndviChartInstance) {
              ndviChartInstance.destroy();
          }

          const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
          const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';
          const textColor = isDark ? '#94A69B' : '#5A6B5C';

          // Initialize Chart
          ndviChartInstance = new Chart(canvas, {
              type: 'line',
              data: {
                  labels: months,
                  datasets: [{
                      label: 'Índice de Vegetación (NDVI)',
                      data: dataset,
                      borderColor: '#2D5A4A',
                      backgroundColor: 'rgba(45, 90, 74, 0.15)',
                      borderWidth: 3,
                      fill: true,
                      tension: 0.4,
                      pointBackgroundColor: '#A68B5B',
                      pointBorderColor: '#fff',
                      pointRadius: 4,
                      pointHoverRadius: 6
                  }]
              },
              options: {
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                      legend: { display: false },
                      tooltip: {
                          callbacks: {
                              label: function(context) {
                                  return `NDVI: ${context.parsed.y}`;
                              }
                          }
                      }
                  },
                  scales: {
                      x: {
                          grid: { display: false },
                          ticks: { color: textColor, font: { family: 'Inter', size: 10 } }
                      },
                      y: {
                          min: -0.2,
                          max: 1.0,
                          grid: { color: gridColor },
                          ticks: { color: textColor, font: { family: 'Inter', size: 10 } }
                      }
                  }
              }
          });

          // Ensure the chart container is visible
          const chartContainer = canvas.closest('.chart-container');
          if (chartContainer) {
              chartContainer.style.display = 'block';
          }
      }

      // Skeleton loaders control
      function showLiveDataSkeleton() {
          const elements = ['data-elevation', 'data-slope', 'data-aqi', 'data-solar'];
          elements.forEach(id => {
              const el = document.getElementById(id);
              if (el) {
                  el.innerHTML = '<span class="skeleton skeleton-line" style="width: 60px; margin-bottom: 0;"></span>';
              }
          });
      }

      function showAnalysisSkeleton() {
          // Remove previous results
          const resultsContainer = document.getElementById("analysis-results");
          if (resultsContainer) {
              resultsContainer.style.display = "none";
              resultsContainer.innerHTML = "";
          }

          // Create a dynamic skeleton card in the indices panel
          let skeletonEl = document.getElementById("analysis-skeleton");
          if (!skeletonEl) {
              skeletonEl = document.createElement("div");
              skeletonEl.id = "analysis-skeleton";
              skeletonEl.className = "skeleton-wrapper";
              
              skeletonEl.innerHTML = `
                  <span class="skeleton skeleton-title"></span>
                  <div class="skeleton skeleton-card" style="height: 120px; margin-bottom: 0.5rem;"></div>
                  <div class="skeleton skeleton-card" style="height: 220px;"></div>
              `;
              
              const indicesPanel = document.getElementById("indices-panel");
              indicesPanel.insertBefore(skeletonEl, document.getElementById("indices-list"));
          }
          skeletonEl.style.display = "flex";
      }

      function hideAnalysisSkeleton() {
          const skeletonEl = document.getElementById("analysis-skeleton");
          if (skeletonEl) {
              skeletonEl.style.display = "none";
          }
      }

