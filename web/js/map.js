// Global variables
let map;
let riskLayer;
let infrastructureLayer;
let infrastructureData;
let markerClusterGroup;

// Category icons and colors
const categoryStyles = {
    'Educación': { icon: 'graduation-cap', color: '#2E86AB' },
    'Salud': { icon: 'hospital', color: '#A23B72' },
    'Emergencias': { icon: 'fire-extinguisher', color: '#F18F01' },
    'Gobierno': { icon: 'landmark', color: '#C73E1D' },
    'Comercio': { icon: 'shopping-cart', color: '#6A4C93' }
};

// Risk level colors
const riskColors = {
    3: { color: '#FF6B6B', name: 'Alto' },
    2: { color: '#FFD700', name: 'Medio' },
    1: { color: '#90EE90', name: 'Bajo' },
    0: { color: '#CCCCCC', name: 'Sin Datos' }
};

// Initialize map on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    loadData();
    setupEventListeners();
});

// Initialize Leaflet map
function initializeMap() {
    // Create map centered on Papudo
    map = L.map('map', {
        center: [-32.5067, -71.4492],
        zoom: 13,
        zoomControl: true
    });

    // Add base layer - OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    // Add scale control
    L.control.scale({ position: 'bottomright' }).addTo(map);

    // Initialize marker cluster group
    markerClusterGroup = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    });
}

// API Configuration
// En producción (Railway), usa la API. En desarrollo local, usa archivos GeoJSON
const API_BASE_URL = window.location.hostname.includes('railway.app')
    ? 'https://demogeofeedback-production.up.railway.app'
    : (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? null  // Desarrollo local: usar archivos
        : 'https://demogeofeedback-production.up.railway.app';  // Producción

// Load GeoJSON data
async function loadData() {
    try {
        // Intentar cargar desde API si está configurada
        if (API_BASE_URL) {
            await loadDataFromAPI();
        } else {
            // Modo desarrollo: cargar desde archivos locales
            await loadDataFromFile();
        }

        // Create layers
        createRiskPolygons();
        createInfrastructureMarkers();

        // Update statistics
        updateStatistics();

        // Hide loading overlay
        document.getElementById('loading').classList.add('hidden');

    } catch (error) {
        console.error('Error loading data:', error);

        // Fallback: intentar cargar desde archivo si la API falla
        if (API_BASE_URL) {
            console.warn('API falló, intentando cargar desde archivo local...');
            try {
                await loadDataFromFile();
                createRiskPolygons();
                createInfrastructureMarkers();
                updateStatistics();
                document.getElementById('loading').classList.add('hidden');
            } catch (fallbackError) {
                alert('Error al cargar los datos. Por favor verifica la conexión.');
            }
        } else {
            alert('Error al cargar los datos. Por favor verifica que los archivos GeoJSON existan.');
        }
    }
}

// Load data from API (production)
async function loadDataFromAPI() {
    console.log('Cargando datos desde API...');
    const response = await fetch(`${API_BASE_URL}/api/v1/infrastructure`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    // Convertir formato de API a GeoJSON
    infrastructureData = {
        type: 'FeatureCollection',
        features: data.facilities.map(facility => ({
            type: 'Feature',
            geometry: facility.geometry,
            properties: {
                name: facility.name,
                category: facility.category,
                address: facility.address || '',
                risk_level: facility.risk_level,
                risk_name: facility.risk_name,
                risk_color: facility.risk_color,
                distance_to_risk: facility.distance_to_risk
            }
        }))
    };

    console.log(`✓ ${data.facilities.length} instalaciones cargadas desde API`);
}

// Load data from local file (development)
async function loadDataFromFile() {
    console.log('Cargando datos desde archivo local...');
    const response = await fetch('../data/processed/infrastructure_with_risk.geojson');
    infrastructureData = await response.json();
    console.log(`✓ ${infrastructureData.features.length} instalaciones cargadas desde archivo`);
}

// Create risk polygon layer
function createRiskPolygons() {
    // For now, create simplified risk zones as circles
    // In production, load actual polygon GeoJSON from PostGIS
    const riskZones = [
        { lat: -32.51, lng: -71.45, level: 2, radius: 800 },
        { lat: -32.50, lng: -71.44, level: 2, radius: 600 },
        { lat: -32.52, lng: -71.46, level: 3, radius: 500 }
    ];

    riskLayer = L.layerGroup();

    riskZones.forEach(zone => {
        const circle = L.circle([zone.lat, zone.lng], {
            radius: zone.radius,
            fillColor: riskColors[zone.level].color,
            fillOpacity: 0.4,
            color: riskColors[zone.level].color,
            weight: 2,
            opacity: 0.7
        });

        circle.bindPopup(`
            <div class="popup-title">Zona de Riesgo ${riskColors[zone.level].name}</div>
            <div>Nivel: ${zone.level}</div>
        `);

        circle.addTo(riskLayer);
    });

    riskLayer.addTo(map);
}

// Create infrastructure markers
function createInfrastructureMarkers() {
    infrastructureLayer = L.layerGroup();

    infrastructureData.features.forEach(feature => {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;
        const category = props.category || 'Comercio';
        const style = categoryStyles[category] || categoryStyles['Comercio'];
        const riskLevel = props.risk_level || 0;

        // Create custom icon
        const iconHtml = `
            <div style="
                background-color: ${style.color};
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 3px solid ${riskColors[riskLevel].color};
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            ">
                <i class="fas fa-${style.icon}" style="color: white; font-size: 14px;"></i>
            </div>
        `;

        const customIcon = L.divIcon({
            html: iconHtml,
            className: 'custom-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16]
        });

        // Create marker
        const marker = L.marker([coords[1], coords[0]], { icon: customIcon });

        // Create popup content
        const popupContent = `
            <div class="popup-title">${props.name}</div>
            <div class="popup-category">${category}</div>
            <div class="popup-risk">
                <span>Nivel de Riesgo:</span>
                <span class="risk-badge ${riskColors[riskLevel].name.toLowerCase()}">
                    ${riskColors[riskLevel].name}
                </span>
            </div>
            ${props.addr_street ? `<div><i class="fas fa-map-marker-alt"></i> ${props.addr_street} ${props.addr_number || ''}</div>` : ''}
            <div style="margin-top: 0.5rem; font-size: 0.8rem; color: #666;">
                <i class="fas fa-info-circle"></i> Click para más detalles
            </div>
        `;

        marker.bindPopup(popupContent);

        // Add click event for details
        marker.on('click', () => {
            console.log('Facility details:', props);
        });

        // Add to cluster group
        markerClusterGroup.addLayer(marker);
    });

    infrastructureLayer.addLayer(markerClusterGroup);
    infrastructureLayer.addTo(map);
}

// Update statistics
function updateStatistics() {
    const stats = {
        total: 0,
        high: 0,
        medium: 0,
        low: 0
    };

    infrastructureData.features.forEach(feature => {
        stats.total++;
        const riskLevel = feature.properties.risk_level || 0;

        if (riskLevel === 3) stats.high++;
        else if (riskLevel === 2) stats.medium++;
        else if (riskLevel === 1) stats.low++;
    });

    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-high').textContent = stats.high;
    document.getElementById('stat-medium').textContent = stats.medium;
    document.getElementById('stat-low').textContent = stats.low;
}

// Setup event listeners
function setupEventListeners() {
    // Layer toggles
    document.getElementById('layer-risk').addEventListener('change', function(e) {
        if (e.target.checked) {
            map.addLayer(riskLayer);
        } else {
            map.removeLayer(riskLayer);
        }
    });

    document.getElementById('layer-infrastructure').addEventListener('change', function(e) {
        if (e.target.checked) {
            map.addLayer(infrastructureLayer);
        } else {
            map.removeLayer(infrastructureLayer);
        }
    });

    // Filters
    document.getElementById('filter-risk-level').addEventListener('change', applyFilters);
    document.getElementById('filter-category').addEventListener('change', applyFilters);

    // Search
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase().trim();

        if (query.length < 2) {
            searchResults.classList.remove('show');
            searchResults.innerHTML = '';
            return;
        }

        const results = infrastructureData.features.filter(feature => {
            const name = feature.properties.name.toLowerCase();
            const category = (feature.properties.category || '').toLowerCase();
            return name.includes(query) || category.includes(query);
        });

        if (results.length > 0) {
            searchResults.innerHTML = results.slice(0, 10).map(feature => `
                <div class="search-result-item" data-coords="${feature.geometry.coordinates}">
                    <strong>${feature.properties.name}</strong>
                    <small>${feature.properties.category} - ${riskColors[feature.properties.risk_level || 0].name}</small>
                </div>
            `).join('');

            searchResults.classList.add('show');

            // Add click events to results
            searchResults.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', function() {
                    const coords = JSON.parse(this.dataset.coords);
                    map.setView([coords[1], coords[0]], 16);
                    searchResults.classList.remove('show');
                    searchInput.value = '';
                });
            });
        } else {
            searchResults.innerHTML = '<div class="search-result-item">No se encontraron resultados</div>';
            searchResults.classList.add('show');
        }
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-box')) {
            searchResults.classList.remove('show');
        }
    });
}

// Apply filters
function applyFilters() {
    const riskFilter = document.getElementById('filter-risk-level').value;
    const categoryFilter = document.getElementById('filter-category').value;

    // Clear current markers
    markerClusterGroup.clearLayers();

    // Filter and re-add markers
    infrastructureData.features.forEach(feature => {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;
        const riskLevel = props.risk_level || 0;
        const category = props.category || 'Comercio';

        // Apply filters
        if (riskFilter !== 'all' && riskLevel !== parseInt(riskFilter)) return;
        if (categoryFilter !== 'all' && category !== categoryFilter) return;

        // Create and add marker (same code as before)
        const style = categoryStyles[category] || categoryStyles['Comercio'];

        const iconHtml = `
            <div style="
                background-color: ${style.color};
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 3px solid ${riskColors[riskLevel].color};
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            ">
                <i class="fas fa-${style.icon}" style="color: white; font-size: 14px;"></i>
            </div>
        `;

        const customIcon = L.divIcon({
            html: iconHtml,
            className: 'custom-marker',
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16]
        });

        const marker = L.marker([coords[1], coords[0]], { icon: customIcon });

        const popupContent = `
            <div class="popup-title">${props.name}</div>
            <div class="popup-category">${category}</div>
            <div class="popup-risk">
                <span>Nivel de Riesgo:</span>
                <span class="risk-badge ${riskColors[riskLevel].name.toLowerCase()}">
                    ${riskColors[riskLevel].name}
                </span>
            </div>
            ${props.addr_street ? `<div><i class="fas fa-map-marker-alt"></i> ${props.addr_street} ${props.addr_number || ''}</div>` : ''}
        `;

        marker.bindPopup(popupContent);
        markerClusterGroup.addLayer(marker);
    });

    // Update statistics for filtered data
    updateFilteredStats();
}

// Update statistics for filtered results
function updateFilteredStats() {
    const riskFilter = document.getElementById('filter-risk-level').value;
    const categoryFilter = document.getElementById('filter-category').value;

    const stats = { total: 0, high: 0, medium: 0, low: 0 };

    infrastructureData.features.forEach(feature => {
        const riskLevel = feature.properties.risk_level || 0;
        const category = feature.properties.category || 'Comercio';

        if (riskFilter !== 'all' && riskLevel !== parseInt(riskFilter)) return;
        if (categoryFilter !== 'all' && category !== categoryFilter) return;

        stats.total++;
        if (riskLevel === 3) stats.high++;
        else if (riskLevel === 2) stats.medium++;
        else if (riskLevel === 1) stats.low++;
    });

    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-high').textContent = stats.high;
    document.getElementById('stat-medium').textContent = stats.medium;
    document.getElementById('stat-low').textContent = stats.low;
}
