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
        
        /* Navigation */
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
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        .nav-links a {
            color: var(--text);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }
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
        .btn-secondary {
            background: var(--primary);
            color: white;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }

        /* Hero */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 8rem 2rem 4rem;
            background: linear-gradient(135deg, var(--primary) 0%, #0f2744 100%);
            position: relative;
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
        .hero-text p {
            font-size: 1.25rem;
            color: rgba(255,255,255,0.8);
            margin-bottom: 2rem;
        }
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

        /* Sections */
        .section { padding: 6rem 2rem; }
        .section-dark { background: var(--primary); color: white; }
        .section-light { background: var(--white); }
        .container { max-width: 1200px; margin: 0 auto; }
        .section-header { text-align: center; margin-bottom: 4rem; }
        .section-header h2 { font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem; }
        .section-header p { font-size: 1.1rem; color: var(--text-light); max-width: 600px; margin: 0 auto; }
        .section-dark .section-header p { color: rgba(255,255,255,0.7); }

        /* Cards Grid */
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
        
        .card-light {
            background: var(--background);
            border: 1px solid var(--border);
        }
        .card-light:hover { box-shadow: var(--shadow-lg); }
        .card-light i { color: var(--secondary); }
        .card-light h3 { color: var(--primary); }
        .card-light p { color: var(--text-light); }

        /* Demo Section */
        .demo-section {
            background: linear-gradient(180deg, var(--background) 0%, #e2e8f0 100%);
            padding: 6rem 2rem;
        }
        .demo-container { max-width: 1400px; margin: 0 auto; }
        .demo-layout {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 1.5rem;
            margin-top: 2rem;
        }

        /* Map */
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

        /* Sidebar */
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

        /* Search Input */
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
            transition: border-color 0.3s;
        }
        .search-input:focus { outline: none; border-color: var(--secondary); }

        /* Selected Location Badge */
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

        /* Approach Selector */
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

        /* Indices Panel */
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
        .index-color {
            width: 12px; height: 12px;
            border-radius: 3px;
        }
        .index-name {
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--primary);
        }
        .index-desc {
            font-size: 0.8rem;
            color: var(--text-light);
            line-height: 1.4;
        }

        /* Analyze Button */
        #analyze-btn {
            width: 100%;
            padding: 1rem;
            font-size: 1rem;
            margin-top: 0.5rem;
        }

        /* Status Indicator */
        .status-bar {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .status-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.8rem;
            color: var(--text-light);
        }
        .status-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--border);
        }
        .status-dot.ready { background: var(--secondary); }

        /* Results Grid */
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
        .result-icon { font-size: 2rem; }
        .result-content h4 { font-size: 1rem; color: var(--primary); margin-bottom: 0.25rem; }
        .result-content p { font-size: 0.85rem; color: var(--text-light); margin: 0; }

        /* Footer */
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
        .footer-logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 700;
        }
        .footer-logo i { color: var(--secondary); }
        .footer-links { display: flex; gap: 2rem; }
        .footer-links a {
            color: rgba(255,255,255,0.7);
            text-decoration: none;
        }
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

        /* Responsive */
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

        /* Google Autocomplete Styles */
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
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <a href="#" class="logo">
                <i class="fas fa-globe-americas"></i>
                GeoFeedback
            </a>
            <div class="nav-links">
                <a href="#problema">Problema</a>
                <a href="#solucion">Solucion</a>
                <a href="#demo">Demo</a>
                <a href="/api/docs" class="btn btn-primary">
                    <i class="fas fa-code"></i> API
                </a>
            </div>
        </div>
    </nav>

    <section class="hero">
        <div class="hero-content">
            <div class="hero-text">
                <h1>Democratizando la <span>Inteligencia Territorial</span></h1>
                <p>Plataforma open source que transforma datos satelitales en mapas de riesgo y herramientas de gestion hidrica para Chile.</p>
                <div class="hero-buttons">
                    <a href="#demo" class="btn btn-primary">
                        <i class="fas fa-map-marked-alt"></i> Explorar Demo
                    </a>
                    <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank" class="btn btn-secondary">
                        <i class="fab fa-github"></i> GitHub
                    </a>
                </div>
            </div>
            <div class="hero-visual">
                <i class="fas fa-satellite satellite-icon"></i>
            </div>
        </div>
    </section>

    <section id="problema" class="section section-dark">
        <div class="container">
            <div class="section-header">
                <h2>El Problema</h2>
                <p>Chile enfrenta desafios criticos en gestion territorial</p>
            </div>
            <div class="cards-grid">
                <div class="card">
                    <i class="fas fa-balance-scale"></i>
                    <h3>Ley 21.364</h3>
                    <p>Municipios deben elaborar planes de emergencia y mapas de riesgo, pero carecen de herramientas accesibles.</p>
                </div>
                <div class="card">
                    <i class="fas fa-tint-slash"></i>
                    <h3>Mega-sequia</h3>
                    <p>15 anios de deficit hidrico. Agricultores necesitan datos para optimizar uso del agua.</p>
                </div>
                <div class="card">
                    <i class="fas fa-dollar-sign"></i>
                    <h3>Alto Costo</h3>
                    <p>Estudios geoespaciales profesionales son costosos para municipios rurales.</p>
                </div>
            </div>
        </div>
    </section>

    <section id="solucion" class="section section-light">
        <div class="container">
            <div class="section-header">
                <h2>Nuestra Solucion</h2>
                <p>Inteligencia territorial accesible mediante tecnologia satelital</p>
            </div>
            <div class="cards-grid">
                <div class="card card-light">
                    <i class="fab fa-google"></i>
                    <h3>Google Earth Engine</h3>
                    <p>Procesamiento de datos satelitales en la nube</p>
                </div>
                <div class="card card-light">
                    <i class="fab fa-python"></i>
                    <h3>Python + QGIS</h3>
                    <p>Scripts automatizados para analisis reproducible</p>
                </div>
                <div class="card card-light">
                    <i class="fas fa-satellite"></i>
                    <h3>Sentinel-2</h3>
                    <p>Imagenes multiespectrales gratuitas cada 5 dias</p>
                </div>
                <div class="card card-light">
                    <i class="fas fa-code-branch"></i>
                    <h3>Open Source</h3>
                    <p>Codigo abierto para replicar en cualquier territorio</p>
                </div>
            </div>
        </div>
    </section>

    <section id="demo" class="demo-section">
        <div class="demo-container">
            <div class="section-header">
                <h2>Demo Interactivo</h2>
                <p>Selecciona ubicacion y enfoque en cualquier orden para explorar el analisis territorial</p>
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
                        <button class="map-control-btn" onclick="centerMap()" title="Centrar en Chile">
                            <i class="fas fa-home"></i>
                        </button>
                    </div>
                </div>

                <div class="sidebar">
                    <!-- Status -->
                    <div class="panel">
                        <div class="status-bar">
                            <div class="status-item">
                                <span class="status-dot" id="status-location"></span>
                                Ubicacion
                            </div>
                            <div class="status-item">
                                <span class="status-dot" id="status-approach"></span>
                                Enfoque
                            </div>
                        </div>
                    </div>

                    <!-- Location Search -->
                    <div class="panel">
                        <div class="panel-header">
                            <i class="fas fa-search"></i> Buscar Ubicacion
                        </div>
                        <div class="search-wrapper">
                            <i class="fas fa-map-marker-alt"></i>
                            <input type="text" id="location-search" class="search-input" placeholder="Ej: Papudo, Valparaiso">
                        </div>
                        <div class="location-badge" id="location-badge">
                            <h4 id="location-name">-</h4>
                            <p id="location-coords">-</p>
                        </div>
                    </div>

                    <!-- Approach Selector -->
                    <div class="panel">
                        <div class="panel-header">
                            <i class="fas fa-crosshairs"></i> Seleccionar Enfoque
                        </div>
                        <select id="approach-select" class="approach-select" onchange="onApproachChange()">
                            <option value="">-- Elige un enfoque de analisis --</option>
                            <option value="flood-risk">Riesgo de Inundacion</option>
                            <option value="water-management">Gestion Hidrica</option>
                            <option value="drought">Sequia y Desertificacion</option>
                            <option value="land-planning">Planificacion Territorial</option>
                        </select>

                        <div class="indices-panel" id="indices-panel">
                            <div class="indices-title">Indices y capas del analisis:</div>
                            <div id="indices-list"></div>
                        </div>
                    </div>

                    <!-- Analyze Button -->
                    <div class="panel">
                        <button class="btn btn-primary" id="analyze-btn" onclick="analyzeTerritory()" disabled>
                            <i class="fas fa-satellite-dish"></i> Iniciar Analisis
                        </button>
                        <p style="font-size: 0.8rem; color: var(--text-light); margin-top: 0.5rem; text-align: center;">
                            Requiere ubicacion y enfoque seleccionados
                        </p>
                    </div>
                </div>
            </div>

            <div class="results-grid">
                <div class="result-card" id="result-location">
                    <div class="result-icon">📍</div>
                    <div class="result-content">
                        <h4>Ubicacion</h4>
                        <p>Busca o haz clic en el mapa</p>
                    </div>
                </div>
                <div class="result-card" id="result-approach">
                    <div class="result-icon">🎯</div>
                    <div class="result-content">
                        <h4>Enfoque</h4>
                        <p>Selecciona el tipo de analisis</p>
                    </div>
                </div>
                <div class="result-card">
                    <div class="result-icon">🛰️</div>
                    <div class="result-content">
                        <h4>Fuente</h4>
                        <p>Sentinel-2 + SRTM via Google Earth Engine</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <footer>
        <div class="footer-content">
            <div class="footer-logo">
                <i class="fas fa-globe-americas"></i>
                GeoFeedback Chile
            </div>
            <div class="footer-links">
                <a href="#demo">Demo</a>
                <a href="/api/docs">API</a>
                <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank">GitHub</a>
            </div>
            <div class="social-links">
                <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank">
                    <i class="fab fa-github"></i>
                </a>
                <a href="https://www.linkedin.com/in/alejandro-olivares-verdugo/" target="_blank">
                    <i class="fab fa-linkedin-in"></i>
                </a>
            </div>
        </div>
    </footer>

    <script>
        // ====== GLOBAL STATE ======
        var map = null;
        var marker = null;
        var autocomplete = null;
        var selectedPlace = null;
        var selectedApproach = null;

        // ====== APPROACH DEFINITIONS ======
        var approaches = {
            "flood-risk": {
                name: "Riesgo de Inundacion",
                icon: "🌊",
                indices: [
                    {
                        name: "NDWI",
                        color: "#3b82f6",
                        desc: "Indice de Agua Normalizado. Detecta cuerpos de agua y humedad superficial usando bandas verde e infrarrojo cercano."
                    },
                    {
                        name: "Pendientes SRTM",
                        color: "#f59e0b",
                        desc: "Modelo de elevacion de 30m. Identifica zonas bajas donde el agua tiende a acumularse."
                    },
                    {
                        name: "Flow Accumulation",
                        color: "#ef4444",
                        desc: "Calcula rutas de escorrentia y zonas de acumulacion de flujo hidrico."
                    },
                    {
                        name: "Red Hidrica",
                        color: "#06b6d4",
                        desc: "Cauces, quebradas y cuerpos de agua permanentes del territorio."
                    }
                ]
            },
            "water-management": {
                name: "Gestion Hidrica",
                icon: "💧",
                indices: [
                    {
                        name: "NDWI Temporal",
                        color: "#3b82f6",
                        desc: "Serie temporal del indice de agua para detectar variaciones estacionales."
                    },
                    {
                        name: "NDMI",
                        color: "#8b5cf6",
                        desc: "Indice de Humedad. Mide contenido de agua en vegetacion usando SWIR."
                    },
                    {
                        name: "NDVI",
                        color: "#10b981",
                        desc: "Indice de Vegetacion. Indica vigor vegetal y correlaciona con disponibilidad hidrica."
                    },
                    {
                        name: "Estres Hidrico",
                        color: "#ef4444",
                        desc: "Combinacion de indices que identifica zonas con deficit de agua."
                    }
                ]
            },
            "drought": {
                name: "Sequia y Desertificacion",
                icon: "🏜️",
                indices: [
                    {
                        name: "NDVI Historico",
                        color: "#10b981",
                        desc: "Tendencia de vegetacion en los ultimos 5-10 anios para detectar degradacion."
                    },
                    {
                        name: "Cambio de Cobertura",
                        color: "#f59e0b",
                        desc: "Comparacion multitemporal de uso de suelo y cobertura vegetal."
                    },
                    {
                        name: "Indice de Aridez",
                        color: "#dc2626",
                        desc: "Relacion precipitacion/evapotranspiracion que indica nivel de sequia."
                    },
                    {
                        name: "Albedo Superficial",
                        color: "#78716c",
                        desc: "Reflectividad del suelo. Suelos desnudos tienen mayor albedo."
                    }
                ]
            },
            "land-planning": {
                name: "Planificacion Territorial",
                icon: "🏗️",
                indices: [
                    {
                        name: "MDE",
                        color: "#78716c",
                        desc: "Modelo Digital de Elevacion. Base para analisis topografico."
                    },
                    {
                        name: "Pendientes",
                        color: "#f59e0b",
                        desc: "Clasificacion de pendientes para aptitud constructiva y agricola."
                    },
                    {
                        name: "Orientacion",
                        color: "#fbbf24",
                        desc: "Aspecto o exposicion solar de laderas. Afecta microclima y uso."
                    },
                    {
                        name: "Uso de Suelo",
                        color: "#10b981",
                        desc: "Clasificacion supervisada del territorio: urbano, agricola, natural."
                    }
                ]
            }
        };

        // ====== INIT MAP FUNCTION ======
        function initMap() {
            console.log("initMap called");
            
            var placeholder = document.getElementById("map-placeholder");
            if (placeholder) {
                placeholder.style.display = "none";
            }

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

            // Setup autocomplete
            var input = document.getElementById("location-search");
            autocomplete = new google.maps.places.Autocomplete(input, {
                componentRestrictions: { country: "cl" },
                fields: ["place_id", "geometry", "name", "formatted_address"]
            });

            autocomplete.addListener("place_changed", function() {
                var place = autocomplete.getPlace();
                console.log("Place changed:", place);
                
                if (place.geometry && place.geometry.location) {
                    handlePlaceSelection(place);
                }
            });

            // Map click
            map.addListener("click", function(e) {
                placeMarker(e.latLng);
                reverseGeocode(e.latLng);
            });

            console.log("Map initialized successfully");
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
            map.setZoom(13);
            marker.setPosition(loc);
            marker.setVisible(true);

            updateLocationUI();
            checkReadyState();
        }

        function placeMarker(latLng) {
            marker.setPosition(latLng);
            marker.setVisible(true);
            if (map.getZoom() < 10) {
                map.setZoom(13);
            }
            map.panTo(latLng);
        }

        function reverseGeocode(latLng) {
            var geocoder = new google.maps.Geocoder();
            
            geocoder.geocode({ location: latLng }, function(results, status) {
                if (status === "OK" && results[0]) {
                    var place = results[0];
                    var name = "Ubicacion";
                    
                    // Try to find locality name
                    for (var i = 0; i < place.address_components.length; i++) {
                        var comp = place.address_components[i];
                        if (comp.types.indexOf("locality") >= 0 || 
                            comp.types.indexOf("administrative_area_level_3") >= 0) {
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
                    checkReadyState();
                }
            });
        }

        function updateLocationUI() {
            var badge = document.getElementById("location-badge");
            badge.classList.add("active");
            document.getElementById("location-name").textContent = selectedPlace.name;
            document.getElementById("location-coords").textContent = 
                selectedPlace.lat.toFixed(4) + ", " + selectedPlace.lng.toFixed(4);

            document.getElementById("status-location").classList.add("ready");
            
            document.getElementById("result-location").innerHTML = 
                '<div class="result-icon">📍</div>' +
                '<div class="result-content">' +
                '<h4>' + selectedPlace.name + '</h4>' +
                '<p>' + selectedPlace.address + '</p>' +
                '</div>';
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

            // Update status
            document.getElementById("status-approach").classList.add("ready");

            // Build indices list
            var html = "";
            for (var i = 0; i < config.indices.length; i++) {
                var idx = config.indices[i];
                html += '<div class="index-item">' +
                    '<div class="index-header">' +
                    '<div class="index-color" style="background:' + idx.color + '"></div>' +
                    '<span class="index-name">' + idx.name + '</span>' +
                    '</div>' +
                    '<div class="index-desc">' + idx.desc + '</div>' +
                    '</div>';
            }

            document.getElementById("indices-list").innerHTML = html;
            document.getElementById("indices-panel").classList.add("active");

            // Update result card
            document.getElementById("result-approach").innerHTML = 
                '<div class="result-icon">' + config.icon + '</div>' +
                '<div class="result-content">' +
                '<h4>' + config.name + '</h4>' +
                '<p>' + config.indices.length + ' capas de datos</p>' +
                '</div>';

            checkReadyState();
        }

        function checkReadyState() {
            var btn = document.getElementById("analyze-btn");
            if (selectedPlace && selectedApproach) {
                btn.disabled = false;
            } else {
                btn.disabled = true;
            }
        }

        function centerMap() {
            if (map) {
                map.setCenter({ lat: -33.4489, lng: -70.6693 });
                map.setZoom(5);
            }
        }

        function analyzeTerritory() {
            if (!selectedPlace || !selectedApproach) return;

            var config = approaches[selectedApproach];
            var indices = [];
            for (var i = 0; i < config.indices.length; i++) {
                indices.push(config.indices[i].name);
            }

            alert(
                "Analisis: " + config.name + "\n" +
                "Ubicacion: " + selectedPlace.name + "\n\n" +
                "Indices a procesar:\n- " + indices.join("\n- ") + "\n\n" +
                "Coordenadas: " + selectedPlace.lat.toFixed(4) + ", " + selectedPlace.lng.toFixed(4) + "\n\n" +
                "Esta funcionalidad conectara con Google Earth Engine."
            );
        }

        // Make initMap global
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
    return jsonify({"total_analyses": 147, "municipalities_served": 12})

@app.route('/api/v1/infrastructure')
def infrastructure():
    return jsonify({"features": [
        {"type": "school", "name": "Escuela Papudo", "lat": -32.5127, "lng": -71.4469}
    ]})

@app.route('/api/v1/risk-zones')
def risk_zones():
    return jsonify({"zones": [
        {"level": "high", "area_ha": 45.2, "description": "Quebrada El Frances"}
    ]})

@app.route('/api/docs')
def api_docs():
    return '''<!DOCTYPE html>
<html><head><title>GeoFeedback API</title>
<style>body{font-family:sans-serif;max-width:800px;margin:50px auto;padding:20px}
h1{color:#1e3a5f}.endpoint{background:#f8fafc;padding:20px;border-radius:8px;margin:20px 0;border-left:4px solid #10b981}
code{background:#e5e7eb;padding:2px 8px;border-radius:4px}.method{background:#10b981;color:white;padding:4px 12px;border-radius:4px}</style>
</head><body>
<h1>GeoFeedback API v1</h1>
<div class="endpoint"><span class="method">GET</span> <code>/api/v1/health</code><p>Estado del servicio</p></div>
<div class="endpoint"><span class="method">GET</span> <code>/api/v1/stats</code><p>Estadisticas</p></div>
<div class="endpoint"><span class="method">GET</span> <code>/api/v1/infrastructure</code><p>Infraestructura</p></div>
<div class="endpoint"><span class="method">GET</span> <code>/api/v1/risk-zones</code><p>Zonas de riesgo</p></div>
<p><a href="/">Volver</a></p>
</body></html>'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
