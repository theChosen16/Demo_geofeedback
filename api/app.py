import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

LANDING_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoFeedback Chile - Inteligencia Territorial</title>
    <meta name="description" content="Plataforma open source de analisis geoespacial para Chile.">
    <link rel="canonical" href="https://geofeedback.cl/">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #1e3a5f;
            --primary-light: #2d5a87;
            --secondary: #10b981;
            --secondary-light: #34d399;
            --accent: #f59e0b;
            --danger: #ef4444;
            --text: #1f2937;
            --text-light: #6b7280;
            --background: #f8fafc;
            --white: #ffffff;
            --border: #e5e7eb;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.6;
        }
        .navbar {
            position: fixed;
            top: 0; left: 0; right: 0;
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            z-index: 1000;
            padding: 1rem 2rem;
            box-shadow: var(--shadow);
        }
        .navbar-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            text-decoration: none;
        }
        .logo i { color: var(--secondary); }
        .nav-links { display: flex; gap: 2rem; align-items: center; }
        .nav-links a { color: var(--text); text-decoration: none; font-weight: 500; }
        .nav-links a:hover { color: var(--secondary); }
        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            font-size: 0.95rem;
        }
        .btn-primary {
            background: linear-gradient(135deg, var(--secondary), var(--secondary-light));
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        }
        .btn-secondary { background: var(--primary); color: white; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 8rem 2rem 4rem;
            background: linear-gradient(135deg, var(--primary) 0%, #0f2744 100%);
        }
        .hero-content {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
        }
        .hero-text h1 {
            font-size: 3.5rem;
            font-weight: 800;
            color: white;
            line-height: 1.1;
            margin-bottom: 1.5rem;
        }
        .hero-text h1 span {
            background: linear-gradient(135deg, var(--secondary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero-text p { font-size: 1.25rem; color: rgba(255,255,255,0.8); margin-bottom: 2rem; }
        .hero-buttons { display: flex; gap: 1rem; flex-wrap: wrap; }
        .hero-visual { display: flex; justify-content: center; }
        .satellite-icon {
            font-size: 12rem;
            color: var(--secondary);
            opacity: 0.3;
            animation: float 6s ease-in-out infinite;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        .section { padding: 6rem 2rem; }
        .section-dark { background: var(--primary); color: white; }
        .section-light { background: var(--white); }
        .container { max-width: 1200px; margin: 0 auto; }
        .section-header { text-align: center; margin-bottom: 4rem; }
        .section-header h2 { font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; }
        .section-header p { font-size: 1.1rem; color: var(--text-light); max-width: 600px; margin: 0 auto; }
        .section-dark .section-header p { color: rgba(255,255,255,0.7); }
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 2rem;
            transition: transform 0.3s;
        }
        .card:hover { transform: translateY(-5px); }
        .card i { font-size: 2.5rem; color: var(--accent); margin-bottom: 1rem; }
        .card h3 { font-size: 1.25rem; margin-bottom: 0.75rem; }
        .card p { color: rgba(255,255,255,0.7); font-size: 0.95rem; }
        .card-light { background: var(--background); border: 1px solid var(--border); }
        .card-light:hover { box-shadow: var(--shadow-lg); }
        .card-light i { color: var(--secondary); }
        .card-light h3 { color: var(--primary); }
        .card-light p { color: var(--text-light); }
        .demo-section {
            background: linear-gradient(180deg, var(--background) 0%, #e2e8f0 100%);
            padding: 6rem 2rem;
        }
        .demo-container { max-width: 1400px; margin: 0 auto; }
        .demo-layout {
            display: grid;
            grid-template-columns: 1fr 420px;
            gap: 1.5rem;
            margin-top: 2rem;
        }
        .map-container {
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: var(--shadow-lg);
            position: relative;
        }
        #demo-map { width: 100%; height: 550px; background: #e5e7eb; }
        .map-controls {
            position: absolute;
            top: 1rem; right: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            z-index: 10;
        }
        .map-control-btn {
            background: white;
            border: none;
            width: 40px; height: 40px;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .map-control-btn:hover { background: var(--secondary); color: white; }
        .map-placeholder {
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: var(--text-light);
        }
        .map-placeholder i { font-size: 3rem; margin-bottom: 1rem; opacity: 0.5; }
        .sidebar { display: flex; flex-direction: column; gap: 1rem; }
        .panel {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: var(--shadow);
        }
        .panel-header {
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 500;
        }
        .search-wrapper { position: relative; }
        .search-wrapper i {
            position: absolute;
            left: 1rem; top: 50%;
            transform: translateY(-50%);
            color: var(--text-light);
        }
        .search-input {
            width: 100%;
            padding: 0.875rem 1rem 0.875rem 2.75rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
        }
        .search-input:focus { outline: none; border-color: var(--secondary); }
        .location-badge {
            display: none;
            background: linear-gradient(135deg, var(--secondary), var(--secondary-light));
            color: white;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-top: 0.75rem;
        }
        .location-badge.active { display: block; }
        .location-badge h4 { font-size: 1rem; margin-bottom: 0.25rem; }
        .location-badge p { font-size: 0.8rem; opacity: 0.9; margin: 0; }
        .approach-select {
            width: 100%;
            padding: 0.875rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
            cursor: pointer;
            background: white;
        }
        .approach-select:focus { outline: none; border-color: var(--secondary); }
        .indices-panel {
            display: none;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }
        .indices-panel.active { display: block; }
        .indices-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.75rem;
        }
        .index-item {
            background: var(--background);
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
        }
        .index-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.25rem;
        }
        .index-color { width: 12px; height: 12px; border-radius: 3px; }
        .index-name { font-weight: 600; font-size: 0.85rem; color: var(--primary); }
        .index-desc { font-size: 0.8rem; color: var(--text-light); line-height: 1.4; }
        .index-api {
            font-size: 0.7rem;
            background: var(--primary);
            color: white;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            margin-left: auto;
        }
        #analyze-btn { width: 100%; padding: 1rem; font-size: 1rem; margin-top: 0.5rem; }
        .status-bar { display: flex; gap: 1rem; margin-bottom: 1rem; }
        .status-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-light);
        }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--border); }
        .status-dot.ready { background: var(--secondary); }
        .results-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-top: 1.5rem;
        }
        .result-card {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            box-shadow: var(--shadow);
        }
        .result-icon { font-size: 2rem; color: var(--secondary); }
        .result-content h4 { font-size: 1rem; color: var(--primary); margin-bottom: 0.25rem; }
        .result-content p { font-size: 0.85rem; color: var(--text-light); margin: 0; }
        .live-data {
            display: none;
            margin-top: 1rem;
            padding: 1rem;
            background: linear-gradient(135deg, #1e3a5f 0%, #0f2744 100%);
            border-radius: 8px;
            color: white;
        }
        .live-data.active { display: block; }
        .live-data h4 {
            font-size: 0.85rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .live-data-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }
        .live-data-item {
            background: rgba(255,255,255,0.1);
            padding: 0.5rem;
            border-radius: 6px;
        }
        .live-data-label { font-size: 0.7rem; opacity: 0.7; }
        .live-data-value { font-size: 0.9rem; font-weight: 600; }
        footer {
            background: var(--primary);
            color: white;
            padding: 3rem 2rem;
        }
        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 2rem;
        }
        .footer-logo { display: flex; align-items: center; gap: 0.75rem; font-size: 1.25rem; font-weight: 700; }
        .footer-logo i { color: var(--secondary); }
        .footer-links { display: flex; gap: 2rem; }
        .footer-links a { color: rgba(255,255,255,0.7); text-decoration: none; }
        .footer-links a:hover { color: var(--secondary); }
        .social-links { display: flex; gap: 1rem; }
        .social-links a {
            width: 40px; height: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .social-links a:hover { background: var(--secondary); }
        @media (max-width: 1024px) {
            .demo-layout { grid-template-columns: 1fr; }
            .sidebar { order: -1; }
            #demo-map { height: 400px; }
            .results-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 768px) {
            .hero-content { grid-template-columns: 1fr; text-align: center; }
            .hero-text h1 { font-size: 2.5rem; }
            .hero-buttons { justify-content: center; }
            .hero-visual { display: none; }
            .nav-links { display: none; }
        }
        .pac-container {
            border-radius: 8px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-lg);
            margin-top: 4px;
            font-family: 'Inter', sans-serif;
        }
        .pac-item { padding: 10px 14px; cursor: pointer; }
        .pac-item:hover { background: var(--background); }
        .pac-icon { display: none; }
        .loading-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <a href="#" class="logo"><i class="fas fa-globe-americas"></i>GeoFeedback</a>
            <div class="nav-links">
                <a href="#problema">Problema</a>
                <a href="#solucion">Solucion</a>
                <a href="#demo">Demo</a>
                <a href="/api/docs" class="btn btn-primary"><i class="fas fa-code"></i> API</a>
            </div>
        </div>
    </nav>
    <section class="hero">
        <div class="hero-content">
            <div class="hero-text">
                <h1>Democratizando la <span>Inteligencia Territorial</span></h1>
                <p>Plataforma open source que transforma datos satelitales en mapas de riesgo y herramientas de gestion hidrica para Chile.</p>
                <div class="hero-buttons">
                    <a href="#demo" class="btn btn-primary"><i class="fas fa-map-marked-alt"></i> Explorar Demo</a>
                    <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank" class="btn btn-secondary"><i class="fab fa-github"></i> GitHub</a>
                </div>
            </div>
            <div class="hero-visual"><i class="fas fa-satellite satellite-icon"></i></div>
        </div>
    </section>
    <section id="problema" class="section section-dark">
        <div class="container">
            <div class="section-header">
                <h2>El Problema</h2>
                <p>Chile enfrenta desafios criticos en gestion territorial</p>
            </div>
            <div class="cards-grid">
                <div class="card"><i class="fas fa-balance-scale"></i><h3>Ley 21.364</h3><p>Municipios deben elaborar planes de emergencia y mapas de riesgo, pero carecen de herramientas accesibles.</p></div>
                <div class="card"><i class="fas fa-tint-slash"></i><h3>Mega-sequia</h3><p>15 anios de deficit hidrico. Agricultores necesitan datos para optimizar uso del agua.</p></div>
                <div class="card"><i class="fas fa-dollar-sign"></i><h3>Alto Costo</h3><p>Estudios geoespaciales profesionales son costosos para municipios rurales.</p></div>
            </div>
        </div>
    </section>
    <section id="solucion" class="section section-light">
        <div class="container">
            <div class="section-header">
                <h2>Nuestra Solucion</h2>
                <p>Inteligencia territorial con APIs de Google Maps Platform + Google Earth Engine</p>
            </div>
            <div class="cards-grid">
                <div class="card card-light"><i class="fab fa-google"></i><h3>Google Earth Engine</h3><p>Procesamiento de datos satelitales Sentinel-2</p></div>
                <div class="card card-light"><i class="fas fa-mountain"></i><h3>Elevation API</h3><p>Datos topograficos en tiempo real</p></div>
                <div class="card card-light"><i class="fas fa-wind"></i><h3>Air Quality API</h3><p>Calidad del aire resolucion 500m</p></div>
                <div class="card card-light"><i class="fas fa-sun"></i><h3>Solar API</h3><p>Potencial fotovoltaico de cubiertas</p></div>
            </div>
        </div>
    </section>
    <section id="demo" class="demo-section">
        <div class="demo-container">
            <div class="section-header">
                <h2>Demo Interactivo</h2>
                <p>Selecciona ubicacion y enfoque para explorar datos en tiempo real</p>
            </div>
            <div class="demo-layout">
                <div class="map-container">
                    <div id="demo-map">
                        <div class="map-placeholder" id="map-placeholder">
                            <i class="fas fa-map-marked-alt"></i>
                            <p>Cargando mapa...</p>
                        </div>
                    </div>
                    <div class="map-controls">
                        <button class="map-control-btn" onclick="centerMap()" title="Centrar en Chile"><i class="fas fa-home"></i></button>
                        <button class="map-control-btn" onclick="toggleMapType()" title="Cambiar vista"><i class="fas fa-layer-group"></i></button>
                    </div>
                </div>
                <div class="sidebar">
                    <div class="panel">
                        <div class="status-bar">
                            <div class="status-item"><span class="status-dot" id="status-location"></span>Ubicacion</div>
                            <div class="status-item"><span class="status-dot" id="status-approach"></span>Enfoque</div>
                        </div>
                    </div>
                    <div class="panel">
                        <div class="panel-header"><i class="fas fa-search"></i> Buscar Ubicacion</div>
                        <div class="search-wrapper">
                            <div id="autocomplete-container"></div>
                        </div>
                        <div class="location-badge" id="location-badge">
                            <h4 id="location-name">-</h4>
                            <p id="location-coords">-</p>
                        </div>
                        <div class="live-data" id="live-data">
                            <h4><i class="fas fa-broadcast-tower"></i> Datos en tiempo real</h4>
                            <div class="live-data-grid">
                                <div class="live-data-item"><div class="live-data-label">Elevacion</div><div class="live-data-value" id="data-elevation">--</div></div>
                                <div class="live-data-item"><div class="live-data-label">Calidad Aire (AQI)</div><div class="live-data-value" id="data-aqi">--</div></div>
                                <div class="live-data-item"><div class="live-data-label">Potencial Solar</div><div class="live-data-value" id="data-solar">--</div></div>
                                <div class="live-data-item"><div class="live-data-label">Pendiente</div><div class="live-data-value" id="data-slope">--</div></div>
                            </div>
                        </div>
                    </div>
                    <div class="panel">
                        <div class="panel-header"><i class="fas fa-crosshairs"></i> Seleccionar Enfoque</div>
                        <select id="approach-select" class="approach-select" onchange="onApproachChange()">
                            <option value="">-- Elige un enfoque de analisis --</option>
                            <option value="flood-risk">Riesgo de Inundacion</option>
                            <option value="water-management">Gestion Hidrica</option>
                            <option value="environmental">Calidad Ambiental</option>
                            <option value="land-planning">Planificacion Territorial</option>
                        </select>
                        <div class="indices-panel" id="indices-panel">
                            <div class="indices-title">Indices y datos del analisis:</div>
                            <div id="indices-list"></div>
                        </div>
                    </div>
                    <div class="panel">
                        <button class="btn btn-primary" id="analyze-btn" onclick="analyzeTerritory()" disabled><i class="fas fa-satellite-dish"></i> Iniciar Analisis</button>
                        <p style="font-size: 0.8rem; color: var(--text-light); margin-top: 0.5rem; text-align: center;">Requiere ubicacion y enfoque seleccionados</p>
                    </div>
                </div>
            </div>
            <div class="results-grid">
                <div class="result-card" id="result-location"><i class="fas fa-map-marker-alt result-icon"></i><div class="result-content"><h4>Ubicacion</h4><p>Busca o haz clic en el mapa</p></div></div>
                <div class="result-card" id="result-approach"><i class="fas fa-crosshairs result-icon"></i><div class="result-content"><h4>Enfoque</h4><p>Selecciona el tipo de analisis</p></div></div>
                <div class="result-card"><i class="fas fa-satellite result-icon"></i><div class="result-content"><h4>APIs Integradas</h4><p>Elevation, Air Quality, Solar, Geocoding</p></div></div>
            </div>
        </div>
    </section>
    <footer>
        <div class="footer-content">
            <div class="footer-logo"><i class="fas fa-globe-americas"></i>GeoFeedback Chile</div>
            <div class="footer-links">
                <a href="#demo">Demo</a>
                <a href="/api/docs">API</a>
                <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank">GitHub</a>
            </div>
            <div class="social-links">
                <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank"><i class="fab fa-github"></i></a>
                <a href="https://www.linkedin.com/in/alejandro-olivares-verdugo/" target="_blank"><i class="fab fa-linkedin-in"></i></a>
            </div>
        </div>
    </footer>
    <script>
        var MAPS_API_KEY = "GOOGLE_MAPS_KEY_PLACEHOLDER";
        var map = null;
        var marker = null;
        var autocomplete = null;
        var selectedPlace = null;
        var selectedApproach = null;
        var elevationService = null;
        var isSatellite = false;

        var approaches = {
            "flood-risk": {
                name: "Riesgo de Inundacion",
                icon: "water",
                indices: [
                    { name: "Elevacion", color: "#78716c", api: "Elevation API", desc: "Altura sobre nivel del mar. Zonas bajas son mas susceptibles a inundaciones." },
                    { name: "Pendiente", color: "#f59e0b", api: "Elevation API", desc: "Grado de inclinacion del terreno calculado desde puntos de elevacion." },
                    { name: "NDWI", color: "#3b82f6", api: "Earth Engine", desc: "Indice de Agua Normalizado. Detecta cuerpos de agua y humedad superficial." },
                    { name: "Flow Accumulation", color: "#ef4444", api: "Earth Engine", desc: "Modelo de acumulacion de flujo hidrico basado en topografia." }
                ]
            },
            "water-management": {
                name: "Gestion Hidrica",
                icon: "tint",
                indices: [
                    { name: "NDWI Temporal", color: "#3b82f6", api: "Earth Engine", desc: "Serie temporal del indice de agua para detectar variaciones estacionales." },
                    { name: "NDMI", color: "#8b5cf6", api: "Earth Engine", desc: "Indice de Humedad. Mide contenido de agua en vegetacion usando SWIR." },
                    { name: "NDVI", color: "#10b981", api: "Earth Engine", desc: "Indice de Vegetacion. Indica vigor vegetal, correlaciona con disponibilidad hidrica." },
                    { name: "Elevacion", color: "#78716c", api: "Elevation API", desc: "Altura del terreno para modelar escorrentia y acumulacion." }
                ]
            },
            "environmental": {
                name: "Calidad Ambiental",
                icon: "leaf",
                indices: [
                    { name: "Indice Calidad Aire", color: "#10b981", api: "Air Quality API", desc: "AQI en tiempo real. Mide PM2.5, PM10, O3, NO2, CO en resolucion 500m." },
                    { name: "Contaminantes", color: "#ef4444", api: "Air Quality API", desc: "Concentracion de particulas y gases contaminantes en el aire." },
                    { name: "Potencial Solar", color: "#f59e0b", api: "Solar API", desc: "Radiacion solar anual y potencial fotovoltaico de la zona." },
                    { name: "Cobertura Vegetal", color: "#22c55e", api: "Earth Engine", desc: "NDVI para evaluar areas verdes y su efecto en calidad ambiental." }
                ]
            },
            "land-planning": {
                name: "Planificacion Territorial",
                icon: "building",
                indices: [
                    { name: "Modelo Elevacion", color: "#78716c", api: "Elevation API", desc: "DEM de alta precision para analisis topografico del territorio." },
                    { name: "Pendientes", color: "#f59e0b", api: "Elevation API", desc: "Clasificacion de pendientes para aptitud constructiva y agricola." },
                    { name: "Potencial Solar", color: "#fbbf24", api: "Solar API", desc: "Horas de sol y potencial para instalaciones fotovoltaicas." },
                    { name: "Uso de Suelo", color: "#10b981", api: "Earth Engine", desc: "Clasificacion: urbano, agricola, natural, basada en Sentinel-2." }
                ]
            }
        };

        function initMap() {
            var placeholder = document.getElementById("map-placeholder");
            if (placeholder) { placeholder.style.display = "none"; }
            var chileCenter = { lat: -33.4489, lng: -70.6693 };
            map = new google.maps.Map(document.getElementById("demo-map"), {
                center: chileCenter,
                zoom: 5,
                minZoom: 4,
                maxZoom: 18,
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                zoomControl: true
            });
            marker = new google.maps.Marker({
                map: map,
                visible: false,
                animation: google.maps.Animation.DROP,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 12,
                    fillColor: "#10b981",
                    fillOpacity: 1,
                    strokeColor: "#ffffff",
                    strokeWeight: 3
                }
            });
            elevationService = new google.maps.ElevationService();
            
            // Initialize new PlaceAutocompleteElement
            // Requires "Places API (New)" to be enabled in GCP
            const autocomplete = new google.maps.places.PlaceAutocompleteElement({
                componentRestrictions: { country: "cl" }
            });
            
            const container = document.getElementById("autocomplete-container");
            container.appendChild(autocomplete);
            
            autocomplete.addEventListener("gmp-placeselect", async function(e) {
                try {
                    const place = e.place;
                    if (!place) {
                        console.log("No place selected");
                        return;
                    }
                    
                    console.log("Place selected, fetching fields...", place);
                    await place.fetchFields({ fields: ["displayName", "formattedAddress", "location"] });
                    console.log("Fields fetched:", place.displayName, place.formattedAddress);
                    
                    // Adapt new Place object to legacy structure expected by handlePlaceSelection
                    const compatPlace = {
                        name: place.displayName,
                        formatted_address: place.formattedAddress,
                        geometry: {
                            location: place.location
                        }
                    };
                    handlePlaceSelection(compatPlace);
                } catch (error) {
                    console.error("Error selecting place:", error);
                    alert("Error al obtener detalles de la ubicación. Por favor verifica que la API 'Places API (New)' esté habilitada en Google Cloud Console.");
                }
            });

            map.addListener("click", function(e) {
                placeMarker(e.latLng);
                reverseGeocode(e.latLng);
            });
        }

        function handlePlaceSelection(place) {
            var loc = place.geometry.location;
            selectedPlace = {
                name: place.name || "Ubicacion",
                address: place.formatted_address || "",
                lat: loc.lat(),
                lng: loc.lng()
            };
            map.setCenter(loc);
            map.setZoom(14);
            marker.setPosition(loc);
            marker.setVisible(true);
            updateLocationUI();
            fetchLiveData(loc.lat(), loc.lng());
            checkReadyState();
        }

        function placeMarker(latLng) {
            marker.setPosition(latLng);
            marker.setVisible(true);
            if (map.getZoom() < 12) { map.setZoom(14); }
            map.panTo(latLng);
        }

        function reverseGeocode(latLng) {
            var geocoder = new google.maps.Geocoder();
            geocoder.geocode({ location: latLng }, function(results, status) {
                if (status === "OK" && results[0]) {
                    var place = results[0];
                    var name = "Ubicacion";
                    for (var i = 0; i < place.address_components.length; i++) {
                        var comp = place.address_components[i];
                        if (comp.types.indexOf("locality") >= 0 || comp.types.indexOf("administrative_area_level_3") >= 0) {
                            name = comp.long_name;
                            break;
                        }
                    }
                    selectedPlace = {
                        name: name,
                        address: place.formatted_address,
                        lat: latLng.lat(),
                        lng: latLng.lng()
                    };
                    updateLocationUI();
                    fetchLiveData(latLng.lat(), latLng.lng());
                    checkReadyState();
                }
            });
        }

        function updateLocationUI() {
            var badge = document.getElementById("location-badge");
            badge.classList.add("active");
            document.getElementById("location-name").textContent = selectedPlace.name;
            document.getElementById("location-coords").textContent = selectedPlace.lat.toFixed(4) + ", " + selectedPlace.lng.toFixed(4);
            document.getElementById("status-location").classList.add("ready");
            var resultEl = document.getElementById("result-location");
            resultEl.innerHTML = '<i class="fas fa-map-marker-alt result-icon"></i><div class="result-content"><h4>' + selectedPlace.name + '</h4><p>' + selectedPlace.address + '</p></div>';
        }

        function fetchLiveData(lat, lng) {
            document.getElementById("live-data").classList.add("active");
            document.getElementById("data-elevation").innerHTML = '<span class="loading-spinner"></span>';
            document.getElementById("data-aqi").innerHTML = '<span class="loading-spinner"></span>';
            document.getElementById("data-solar").innerHTML = '<span class="loading-spinner"></span>';
            document.getElementById("data-slope").innerHTML = '<span class="loading-spinner"></span>';
            if (elevationService) {
                elevationService.getElevationForLocations({
                    locations: [{ lat: lat, lng: lng }]
                }, function(results, status) {
                    if (status === "OK" && results[0]) {
                        var elev = Math.round(results[0].elevation);
                        document.getElementById("data-elevation").textContent = elev + " m";
                        calculateSlope(lat, lng, elev);
                    } else {
                        document.getElementById("data-elevation").textContent = "N/D";
                        document.getElementById("data-slope").textContent = "N/D";
                    }
                });
            }
            fetchAirQuality(lat, lng);
            fetchSolarPotential(lat, lng);
        }

        function calculateSlope(lat, lng, centerElev) {
            var offset = 0.001;
            var points = [
                { lat: lat + offset, lng: lng },
                { lat: lat - offset, lng: lng },
                { lat: lat, lng: lng + offset },
                { lat: lat, lng: lng - offset }
            ];
            elevationService.getElevationForLocations({ locations: points }, function(results, status) {
                if (status === "OK" && results.length === 4) {
                    var maxDiff = 0;
                    for (var i = 0; i < results.length; i++) {
                        var diff = Math.abs(results[i].elevation - centerElev);
                        if (diff > maxDiff) { maxDiff = diff; }
                    }
                    var slopePercent = (maxDiff / 111) * 100;
                    var slopeClass = slopePercent < 5 ? "Plano" : slopePercent < 15 ? "Suave" : slopePercent < 30 ? "Moderado" : "Pronunciado";
                    document.getElementById("data-slope").textContent = Math.round(slopePercent) + "% (" + slopeClass + ")";
                } else {
                    document.getElementById("data-slope").textContent = "N/D";
                }
            });
        }

        function fetchAirQuality(lat, lng) {
            var url = "https://airquality.googleapis.com/v1/currentConditions:lookup?key=" + MAPS_API_KEY;
            fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ location: { latitude: lat, longitude: lng } })
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.indexes && data.indexes.length > 0) {
                    var aqi = data.indexes[0];
                    var color = aqi.aqi <= 50 ? "#10b981" : aqi.aqi <= 100 ? "#f59e0b" : "#ef4444";
                    document.getElementById("data-aqi").innerHTML = '<span style="color:' + color + '">' + aqi.aqi + ' (' + aqi.category + ')</span>';
                } else {
                    document.getElementById("data-aqi").textContent = "N/D";
                }
            })
            .catch(function() { document.getElementById("data-aqi").textContent = "N/D"; });
        }

        function fetchSolarPotential(lat, lng) {
            var url = "https://solar.googleapis.com/v1/buildingInsights:findClosest?location.latitude=" + lat + "&location.longitude=" + lng + "&requiredQuality=LOW&key=" + MAPS_API_KEY;
            fetch(url)
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.solarPotential) {
                    var hours = Math.round(data.solarPotential.maxSunshineHoursPerYear || 0);
                    document.getElementById("data-solar").textContent = hours + " hrs/yr";
                } else {
                    document.getElementById("data-solar").textContent = "Sin edificio";
                }
            })
            .catch(function() { document.getElementById("data-solar").textContent = "N/D"; });
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
                html += '<div class="index-item"><div class="index-header"><div class="index-color" style="background:' + idx.color + '"></div><span class="index-name">' + idx.name + '</span><span class="index-api">' + idx.api + '</span></div><div class="index-desc">' + idx.desc + '</div></div>';
            }
            document.getElementById("indices-list").innerHTML = html;
            document.getElementById("indices-panel").classList.add("active");
            var resultEl = document.getElementById("result-approach");
            resultEl.innerHTML = '<i class="fas fa-' + config.icon + ' result-icon"></i><div class="result-content"><h4>' + config.name + '</h4><p>' + config.indices.length + ' capas de datos</p></div>';
            checkReadyState();
        }

        function checkReadyState() {
            var btn = document.getElementById("analyze-btn");
            btn.disabled = !(selectedPlace && selectedApproach);
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

        function analyzeTerritory() {
            if (!selectedPlace || !selectedApproach) { return; }
            var config = approaches[selectedApproach];
            var indices = [];
            for (var i = 0; i < config.indices.length; i++) {
                indices.push(config.indices[i].name + " (" + config.indices[i].api + ")");
            }
            var elevText = document.getElementById("data-elevation").textContent;
            var aqiText = document.getElementById("data-aqi").textContent;
            var solarText = document.getElementById("data-solar").textContent;
            var slopeText = document.getElementById("data-slope").textContent;
            alert("ANALISIS: " + config.name + "\\nUBICACION: " + selectedPlace.name + "\\nCOORDENADAS: " + selectedPlace.lat.toFixed(4) + ", " + selectedPlace.lng.toFixed(4) + "\\n\\nDATOS EN TIEMPO REAL:\\n- Elevacion: " + elevText + "\\n- Pendiente: " + slopeText + "\\n- Calidad Aire: " + aqiText + "\\n- Potencial Solar: " + solarText + "\\n\\nCAPAS A PROCESAR:\\n- " + indices.join("\\n- ") + "\\n\\nSiguiente paso: Conectar con Google Earth Engine.");
        }

        window.initMap = initMap;
    </script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key=GOOGLE_MAPS_KEY_PLACEHOLDER&libraries=places&callback=initMap"></script>
</body>
</html>
'''

@app.route('/')
def landing():
    google_maps_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    html = LANDING_HTML.replace('GOOGLE_MAPS_KEY_PLACEHOLDER', google_maps_key)
    return html

@app.route('/api/v1/health')
def health():
    return jsonify({"status": "healthy", "service": "GeoFeedback API", "version": "1.0.0"})

@app.route('/api/v1/stats')
def stats():
    return jsonify({"total_analyses": 147, "municipalities_served": 12, "apis_integrated": ["Elevation", "Air Quality", "Solar", "Geocoding"]})

@app.route('/api/v1/infrastructure')
def infrastructure():
    return jsonify({"features": [{"type": "school", "name": "Escuela Papudo", "lat": -32.5127, "lng": -71.4469}]})

@app.route('/api/v1/risk-zones')
def risk_zones():
    return jsonify({"zones": [{"level": "high", "area_ha": 45.2, "description": "Quebrada El Frances"}]})

@app.route('/api/docs')
def api_docs():
    return '''<!DOCTYPE html><html><head><title>GeoFeedback API</title><style>body{font-family:sans-serif;max-width:800px;margin:50px auto;padding:20px}h1{color:#1e3a5f}.endpoint{background:#f8fafc;padding:20px;border-radius:8px;margin:20px 0;border-left:4px solid #10b981}code{background:#e5e7eb;padding:2px 8px;border-radius:4px}.method{background:#10b981;color:white;padding:4px 12px;border-radius:4px}</style></head><body><h1>GeoFeedback API v1</h1><p>APIs integradas: Maps JavaScript, Elevation, Air Quality, Solar, Geocoding</p><div class="endpoint"><span class="method">GET</span> <code>/api/v1/health</code><p>Estado del servicio</p></div><div class="endpoint"><span class="method">GET</span> <code>/api/v1/stats</code><p>Estadisticas</p></div><div class="endpoint"><span class="method">GET</span> <code>/api/v1/infrastructure</code><p>Infraestructura</p></div><div class="endpoint"><span class="method">GET</span> <code>/api/v1/risk-zones</code><p>Zonas de riesgo</p></div><p><a href="/">Volver</a></p></body></html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
