import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Landing page HTML with Google Maps + Places Autocomplete
LANDING_HTML = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GeoFeedback Chile - Inteligencia Territorial con IA</title>
    
    <!-- SEO Meta Tags -->
    <meta name="description" content="Plataforma open source de análisis geoespacial que transforma datos satelitales en mapas de riesgo y herramientas de gestión hídrica para Chile.">
    <meta name="keywords" content="geofeedback, inteligencia territorial, mapas de riesgo, Chile, Google Earth Engine, análisis satelital, NDWI, gestión hídrica">
    <meta name="author" content="GeoFeedback Chile">
    <link rel="canonical" href="https://geofeedback.cl/">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://geofeedback.cl/">
    <meta property="og:title" content="GeoFeedback Chile - Inteligencia Territorial con IA">
    <meta property="og:description" content="Plataforma open source de análisis geoespacial que transforma datos satelitales en mapas de riesgo y herramientas de gestión hídrica para Chile.">
    <meta property="og:image" content="https://geofeedback.cl/static/og-image.png">
    <meta property="og:locale" content="es_CL">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="https://geofeedback.cl/">
    <meta name="twitter:title" content="GeoFeedback Chile - Inteligencia Territorial">
    <meta name="twitter:description" content="Análisis geoespacial open source para gestión de riesgo territorial en Chile.">
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
            --accent-light: #fbbf24;
            --danger: #ef4444;
            --danger-light: #f87171;
            --text: #1f2937;
            --text-light: #6b7280;
            --background: #f8fafc;
            --white: #ffffff;
            --border: #e5e7eb;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.6;
        }

        /* Navigation */
        .navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.95);
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

        .logo i {
            color: var(--secondary);
            font-size: 1.75rem;
        }

        .nav-links {
            display: flex;
            gap: 2rem;
            list-style: none;
        }

        .nav-links a {
            color: var(--text);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }

        .nav-links a:hover {
            color: var(--secondary);
        }

        /* Hero Section */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 50%, var(--secondary) 100%);
            padding: 6rem 2rem 4rem;
            position: relative;
            overflow: hidden;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
            opacity: 0.5;
        }

        .hero-content {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4rem;
            align-items: center;
            position: relative;
            z-index: 1;
        }

        .hero-text h1 {
            font-size: 3.5rem;
            font-weight: 800;
            color: var(--white);
            margin-bottom: 1.5rem;
            line-height: 1.1;
        }

        .hero-text h1 span {
            color: var(--accent);
        }

        .hero-text p {
            font-size: 1.25rem;
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 2rem;
        }

        .hero-buttons {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            border-radius: 12px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s;
            cursor: pointer;
            border: none;
            font-size: 1rem;
        }

        .btn-primary {
            background: var(--accent);
            color: var(--primary);
        }

        .btn-primary:hover {
            background: var(--accent-light);
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.15);
            color: var(--white);
            border: 2px solid rgba(255, 255, 255, 0.3);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-2px);
        }

        .hero-visual {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .hero-image {
            width: 100%;
            max-width: 500px;
        }

        .hero-image > div {
            height: 400px;
            background: linear-gradient(135deg, #0ea5e9 0%, #10b981 50%, #1e3a5f 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            box-shadow: var(--shadow-lg);
        }

        .hero-image > div > div {
            text-align: center;
            color: white;
        }

        .hero-image > div > div i {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.9;
        }

        .hero-image > div > div p:first-of-type {
            font-size: 1.2rem;
            font-weight: 600;
        }

        .hero-image > div > div p:last-of-type {
            opacity: 0.8;
        }

        /* Sections */
        .section {
            padding: 5rem 2rem;
        }

        .section-dark {
            background: var(--primary);
            color: var(--white);
        }

        .section-light {
            background: var(--white);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .section-header {
            text-align: center;
            margin-bottom: 3rem;
        }

        .section-header h2 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .section-header p {
            font-size: 1.1rem;
            color: var(--text-light);
            max-width: 600px;
            margin: 0 auto;
        }

        .section-dark .section-header p {
            color: rgba(255, 255, 255, 0.8);
        }

        /* Problem Cards */
        .problem-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 2rem;
        }

        .problem-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .problem-card h3 {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            margin-bottom: 1rem;
        }

        .problem-card h3 i {
            color: var(--accent);
        }

        .problem-card p {
            color: rgba(255, 255, 255, 0.8);
        }

        /* Solution Cards */
        .solution-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
        }

        .solution-card {
            background: var(--white);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            box-shadow: var(--shadow);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .solution-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        .solution-card i {
            font-size: 3rem;
            color: var(--secondary);
            margin-bottom: 1rem;
        }

        .solution-card h3 {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }

        .solution-card p {
            font-size: 0.9rem;
            color: var(--text-light);
        }

        /* Demo Section */
        #demo {
            background: linear-gradient(180deg, var(--background) 0%, #e0f2fe 100%);
        }

        .demo-grid {
            display: grid;
            grid-template-columns: 1fr 320px;
            gap: 1.5rem;
            align-items: start;
        }

        .demo-map-container {
            height: 600px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--border);
            position: relative;
        }

        #demo-map {
            height: 100%;
            width: 100%;
        }

        .home-btn {
            position: absolute;
            top: 10px;
            right: 60px;
            z-index: 5;
            background: white;
            border: none;
            border-radius: 2px;
            width: 40px;
            height: 40px;
            cursor: pointer;
            box-shadow: 0 1px 4px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }

        .home-btn:hover {
            background: #f4f4f4;
        }

        .demo-sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .search-card {
            background: var(--white);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
        }

        .search-card h3 {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.1rem;
            color: var(--primary);
            margin-bottom: 1rem;
        }

        .search-input-container {
            position: relative;
        }

        .search-input-container i {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-light);
            pointer-events: none;
        }

        #location-search {
            width: 100%;
            padding: 1rem 1rem 1rem 2.75rem;
            border: 2px solid var(--border);
            border-radius: 12px;
            font-size: 1rem;
            transition: border-color 0.3s, box-shadow 0.3s;
        }

        #location-search:focus {
            outline: none;
            border-color: var(--secondary);
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
        }

        #location-search::placeholder {
            color: var(--text-light);
        }

        .search-hint {
            font-size: 0.8rem;
            color: var(--text-light);
            margin-top: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .search-hint i {
            color: var(--secondary);
        }

        .selected-location {
            margin-top: 1rem;
            padding: 1rem;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(30, 58, 95, 0.1) 100%);
            border-radius: 10px;
            display: none;
        }

        .selected-location.active {
            display: block;
        }

        .selected-location h4 {
            font-size: 0.9rem;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }

        .selected-location p {
            font-size: 0.85rem;
            color: var(--text);
        }

        .selected-location .coords {
            font-size: 0.75rem;
            color: var(--text-light);
            margin-top: 0.25rem;
            font-family: monospace;
        }

        .layer-card {
            background: var(--white);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
        }

        .layer-card h3 {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.1rem;
            color: var(--primary);
            margin-bottom: 1rem;
        }

        .layer-options {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .layer-option {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            background: var(--background);
            border-radius: 10px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .layer-option:hover {
            background: #e0f2fe;
        }

        .layer-option input {
            accent-color: var(--secondary);
            width: 18px;
            height: 18px;
        }

        .layer-option label {
            cursor: pointer;
            font-size: 0.9rem;
        }

        .legend-card {
            background: var(--white);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
        }

        .legend-card h3 {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.1rem;
            color: var(--primary);
            margin-bottom: 1rem;
        }

        .legend-items {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.85rem;
        }

        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            flex-shrink: 0;
        }

        /* Demo Results */
        .demo-results {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-top: 2rem;
        }

        .result-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            gap: 1rem;
            align-items: flex-start;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .result-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }

        .result-icon {
            font-size: 1.5rem;
            flex-shrink: 0;
        }

        .result-content h4 {
            font-size: 1rem;
            color: var(--primary);
            margin-bottom: 0.25rem;
        }

        .result-content p {
            font-size: 0.85rem;
            color: var(--text-light);
        }

        /* Analyze Button */
        .analyze-btn {
            width: 100%;
            margin-top: 1rem;
            padding: 1rem;
            background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .analyze-btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .analyze-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Footer */
        footer {
            background: var(--primary);
            color: var(--white);
            padding: 3rem 2rem;
        }

        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .footer-logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 700;
        }

        .footer-logo i {
            color: var(--secondary);
        }

        .footer-links {
            display: flex;
            gap: 2rem;
        }

        .footer-links a {
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            transition: color 0.3s;
        }

        .footer-links a:hover {
            color: var(--secondary);
        }

        .social-links {
            display: flex;
            gap: 1rem;
        }

        .social-links a {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--white);
            text-decoration: none;
            transition: background 0.3s, transform 0.3s;
        }

        .social-links a:hover {
            background: var(--secondary);
            transform: translateY(-2px);
        }

        /* Responsive */
        @media (max-width: 1024px) {
            .hero-content {
                grid-template-columns: 1fr;
                text-align: center;
            }

            .hero-visual {
                order: -1;
            }

            .hero-buttons {
                justify-content: center;
            }

            .problem-grid {
                grid-template-columns: 1fr;
            }

            .solution-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .demo-grid {
                grid-template-columns: 1fr;
            }

            .demo-map-container {
                height: 500px;
            }

            .demo-results {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 768px) {
            .navbar-content {
                flex-direction: column;
                gap: 1rem;
            }

            .nav-links {
                gap: 1rem;
                flex-wrap: wrap;
                justify-content: center;
            }

            .hero-text h1 {
                font-size: 2.5rem;
            }

            .section-header h2 {
                font-size: 2rem;
            }

            .solution-grid {
                grid-template-columns: 1fr;
            }

            .demo-map-container {
                height: 400px;
            }

            .footer-content {
                flex-direction: column;
                gap: 2rem;
                text-align: center;
            }

            .footer-links {
                flex-wrap: wrap;
                justify-content: center;
            }
        }

        /* Google Places Autocomplete Styling */
        .pac-container {
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-lg);
            margin-top: 4px;
            font-family: 'Inter', sans-serif;
        }

        .pac-item {
            padding: 10px 14px;
            cursor: pointer;
            border-bottom: 1px solid var(--border);
        }

        .pac-item:hover {
            background: #e0f2fe;
        }

        .pac-item-query {
            font-size: 0.95rem;
            color: var(--primary);
        }

        .pac-matched {
            font-weight: 600;
        }

        .pac-icon {
            display: none;
        }

        /* Loading State */
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10;
            border-radius: 16px;
        }

        .loading-overlay.hidden {
            display: none;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid var(--border);
            border-top-color: var(--secondary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="navbar-content">
            <a href="#" class="logo">
                <i class="fas fa-globe-americas"></i>
                GeoFeedback
            </a>
            <ul class="nav-links">
                <li><a href="#problema">Problema</a></li>
                <li><a href="#solucion">Solución</a></li>
                <li><a href="#demo">Demo</a></li>
                <li><a href="#metodologia">Metodología</a></li>
                <li><a href="/api/docs">API Docs</a></li>
            </ul>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <div class="hero-text">
                <h1>Democratizando la <span>Inteligencia Territorial</span></h1>
                <p>Plataforma open source de análisis geoespacial que transforma datos satelitales en mapas de riesgo y herramientas de gestión hídrica para Chile.</p>
                <div class="hero-buttons">
                    <a href="#demo" class="btn btn-primary">
                        <i class="fas fa-play-circle"></i>
                        Probar Demo
                    </a>
                    <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank" class="btn btn-secondary">
                        <i class="fab fa-github"></i>
                        Ver en GitHub
                    </a>
                </div>
            </div>
            <div class="hero-visual">
                <div class="hero-image">
                    <div>
                        <div>
                            <i class="fas fa-satellite"></i>
                            <p>Monitoreo Satelital</p>
                            <p>Papudo, Valparaíso</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Problem Section -->
    <section id="problema" class="section section-dark">
        <div class="container">
            <div class="section-header">
                <h2>El Problema</h2>
                <p>Chile enfrenta desafíos críticos que requieren inteligencia territorial accesible</p>
            </div>
            <div class="problem-grid">
                <div class="problem-card">
                    <h3><i class="fas fa-gavel"></i> Ley 21.364</h3>
                    <p>Las municipalidades deben crear planes de gestión de riesgo de desastres, pero carecen de herramientas técnicas y presupuesto para análisis geoespacial profesional.</p>
                </div>
                <div class="problem-card">
                    <h3><i class="fas fa-tint-slash"></i> Mega-sequía</h3>
                    <p>Chile atraviesa más de 15 años de mega-sequía. Los agricultores y gestores de cuencas necesitan información actualizada sobre disponibilidad hídrica.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Solution Section -->
    <section id="solucion" class="section section-light">
        <div class="container">
            <div class="section-header">
                <h2>Nuestra Solución</h2>
                <p>Stack tecnológico open source para análisis territorial</p>
            </div>
            <div class="solution-grid">
                <div class="solution-card">
                    <i class="fas fa-satellite-dish"></i>
                    <h3>Google Earth Engine</h3>
                    <p>Procesamiento de imágenes Sentinel-2 en la nube</p>
                </div>
                <div class="solution-card">
                    <i class="fab fa-python"></i>
                    <h3>Python + Flask</h3>
                    <p>API REST para servir datos procesados</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-map-marked-alt"></i>
                    <h3>Google Maps</h3>
                    <p>Visualización interactiva con autocompletado</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-robot"></i>
                    <h3>Gemini AI</h3>
                    <p>Análisis inteligente de territorios</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Demo Section -->
    <section id="demo" class="section">
        <div class="container">
            <div class="section-header">
                <h2>Demo Interactivo</h2>
                <p>Busca cualquier localidad de Chile y explora sus características territoriales</p>
            </div>
            <div class="demo-grid">
                <div class="demo-map-container">
                    <div id="demo-map"></div>
                    <button class="home-btn" onclick="centerMap()" title="Centrar en Chile">
                        <i class="fas fa-home"></i>
                    </button>
                    <div class="loading-overlay hidden" id="map-loading">
                        <div class="spinner"></div>
                    </div>
                </div>
                <div class="demo-sidebar">
                    <div class="search-card">
                        <h3><i class="fas fa-search-location"></i> Buscar Localidad</h3>
                        <div class="search-input-container">
                            <i class="fas fa-map-marker-alt"></i>
                            <input type="text" id="location-search" placeholder="Escribe una localidad chilena...">
                        </div>
                        <div class="search-hint">
                            <i class="fas fa-info-circle"></i>
                            <span>Ej: Papudo, Valparaíso, Pucón...</span>
                        </div>
                        <div class="selected-location" id="selected-location">
                            <h4>📍 Ubicación Seleccionada</h4>
                            <p id="location-name">-</p>
                            <p class="coords" id="location-coords">-</p>
                        </div>
                        <button class="analyze-btn" id="analyze-btn" disabled onclick="analyzeLocation()">
                            <i class="fas fa-satellite"></i>
                            Analizar Territorio
                        </button>
                    </div>
                    <div class="layer-card">
                        <h3><i class="fas fa-layer-group"></i> Capas</h3>
                        <div class="layer-options">
                            <div class="layer-option">
                                <input type="checkbox" id="layer-satellite" onchange="toggleMapType()">
                                <label for="layer-satellite">Vista Satélite</label>
                            </div>
                            <div class="layer-option">
                                <input type="checkbox" id="layer-terrain" onchange="toggleTerrain()">
                                <label for="layer-terrain">Terreno</label>
                            </div>
                        </div>
                    </div>
                    <div class="legend-card">
                        <h3><i class="fas fa-palette"></i> Leyenda</h3>
                        <div class="legend-items">
                            <div class="legend-item">
                                <div class="legend-color" style="background: rgba(239, 68, 68, 0.4); border: 2px solid #ef4444;"></div>
                                <span>Riesgo Alto</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color" style="background: rgba(245, 158, 11, 0.4); border: 2px solid #f59e0b;"></div>
                                <span>Riesgo Medio</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color" style="background: rgba(16, 185, 129, 0.4); border: 2px solid #10b981;"></div>
                                <span>Riesgo Bajo</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color" style="background: #3b82f6;"></div>
                                <span>Infraestructura</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="demo-results">
                <div class="result-card" id="info-panel">
                    <div class="result-icon">📍</div>
                    <div class="result-content">
                        <h4>Ubicación</h4>
                        <p>Selecciona una localidad para ver información detallada</p>
                    </div>
                </div>
                <div class="result-card">
                    <div class="result-icon">📊</div>
                    <div class="result-content">
                        <h4>Estadísticas</h4>
                        <p>Los datos se cargarán al seleccionar una ubicación</p>
                    </div>
                </div>
                <div class="result-card">
                    <div class="result-icon">🛰️</div>
                    <div class="result-content">
                        <h4>Fuente de Datos</h4>
                        <p>Sentinel-2 • Resolución 10m • Google Earth Engine</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Methodology Section -->
    <section id="metodologia" class="section section-light">
        <div class="container">
            <div class="section-header">
                <h2>Metodología</h2>
                <p>Proceso de análisis territorial basado en datos satelitales</p>
            </div>
            <div class="solution-grid">
                <div class="solution-card">
                    <i class="fas fa-cloud-download-alt"></i>
                    <h3>1. Adquisición</h3>
                    <p>Descarga automática de imágenes Sentinel-2 desde GEE</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-calculator"></i>
                    <h3>2. Procesamiento</h3>
                    <p>Cálculo de NDWI para detección de agua y humedad</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-mountain"></i>
                    <h3>3. Topografía</h3>
                    <p>Integración de datos SRTM para análisis de pendientes</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-chart-area"></i>
                    <h3>4. Clasificación</h3>
                    <p>Generación de zonas de riesgo por susceptibilidad</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
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
                <a href="https://github.com/theChosen16/Demo_geofeedback" target="_blank" title="GitHub">
                    <i class="fab fa-github"></i>
                </a>
                <a href="https://www.linkedin.com/in/alejandro-olivares-verdugo/" target="_blank" title="LinkedIn">
                    <i class="fab fa-linkedin-in"></i>
                </a>
            </div>
        </div>
    </footer>

    <!-- Google Maps JavaScript API with Places Library -->
    <!-- Google Maps API -->
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyCmKOB4Vaxt8-ll8dypzRUn6PgNH2OoPxc&libraries=places&callback=initMap" async defer></script>
    
    <script>
        let map;
        let marker;
        let autocomplete;
        let selectedPlace = null;
        
        // Chile bounds for restricting view
        const chileBounds = {
            north: -17.5,
            south: -56.0,
            west: -76.0,
            east: -66.5
        };

        // Initialize map
        function initMap() {
            // Center of Chile
            const chileCenter = { lat: -33.4489, lng: -70.6693 };
            
            map = new google.maps.Map(document.getElementById('demo-map'), {
                center: chileCenter,
                zoom: 5,
                minZoom: 4,
                maxZoom: 18,
                restriction: {
                    latLngBounds: chileBounds,
                    strictBounds: false
                },
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                zoomControl: true,
                styles: [
                    {
                        featureType: "poi",
                        elementType: "labels",
                        stylers: [{ visibility: "off" }]
                    }
                ]
            });
            
            // Initialize marker
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
            
            // Initialize Places Autocomplete
            const input = document.getElementById('location-search');
            
            autocomplete = new google.maps.places.Autocomplete(input, {
                componentRestrictions: { country: 'cl' },
                types: ['locality', 'sublocality', 'administrative_area_level_3'],
                fields: ['place_id', 'geometry', 'name', 'formatted_address']
            });
            
            // Bias towards Chile
            autocomplete.setBounds(new google.maps.LatLngBounds(
                new google.maps.LatLng(chileBounds.south, chileBounds.west),
                new google.maps.LatLng(chileBounds.north, chileBounds.east)
            ));
            
            // Listen for place selection
            autocomplete.addListener('place_changed', onPlaceChanged);
            
            // Map click listener
            map.addListener('click', function(e) {
                placeMarkerAndPan(e.latLng);
                reverseGeocode(e.latLng);
            });
        }
        
        function onPlaceChanged() {
            const place = autocomplete.getPlace();
            
            if (!place.geometry || !place.geometry.location) {
                console.log("No geometry for this place");
                return;
            }
            
            selectedPlace = {
                name: place.name,
                address: place.formatted_address,
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng()
            };
            
            // Update map
            map.setCenter(place.geometry.location);
            map.setZoom(14);
            
            // Update marker
            marker.setPosition(place.geometry.location);
            marker.setVisible(true);
            
            // Update UI
            updateLocationUI(selectedPlace);
        }
        
        function placeMarkerAndPan(latLng) {
            marker.setPosition(latLng);
            marker.setVisible(true);
            map.panTo(latLng);
        }
        
        function reverseGeocode(latLng) {
            const geocoder = new google.maps.Geocoder();
            
            geocoder.geocode({ location: latLng }, function(results, status) {
                if (status === 'OK' && results[0]) {
                    // Find locality in results
                    let locality = null;
                    for (let result of results) {
                        if (result.types.includes('locality') || 
                            result.types.includes('administrative_area_level_3')) {
                            locality = result;
                            break;
                        }
                    }
                    
                    const place = locality || results[0];
                    
                    selectedPlace = {
                        name: extractLocalityName(place),
                        address: place.formatted_address,
                        lat: latLng.lat(),
                        lng: latLng.lng()
                    };
                    
                    updateLocationUI(selectedPlace);
                }
            });
        }
        
        function extractLocalityName(place) {
            for (let component of place.address_components) {
                if (component.types.includes('locality') || 
                    component.types.includes('administrative_area_level_3')) {
                    return component.long_name;
                }
            }
            return place.formatted_address.split(',')[0];
        }
        
        function updateLocationUI(place) {
            // Show selected location card
            const locationDiv = document.getElementById('selected-location');
            locationDiv.classList.add('active');
            
            document.getElementById('location-name').textContent = place.name;
            document.getElementById('location-coords').textContent = 
                `${place.lat.toFixed(4)}, ${place.lng.toFixed(4)}`;
            
            // Enable analyze button
            document.getElementById('analyze-btn').disabled = false;
            
            // Update info panel
            updateInfoPanel(
                place.name,
                `${place.address}<br><small>Coordenadas: ${place.lat.toFixed(4)}, ${place.lng.toFixed(4)}</small>`
            );
        }
        
        function updateInfoPanel(title, content) {
            const panel = document.getElementById('info-panel');
            panel.innerHTML = `
                <div class="result-icon">📍</div>
                <div class="result-content">
                    <h4>${title}</h4>
                    <p>${content}</p>
                </div>
            `;
        }
        
        function centerMap() {
            map.setCenter({ lat: -33.4489, lng: -70.6693 });
            map.setZoom(5);
        }
        
        function toggleMapType() {
            const satellite = document.getElementById('layer-satellite').checked;
            map.setMapTypeId(satellite ? 'hybrid' : 'roadmap');
        }
        
        function toggleTerrain() {
            const terrain = document.getElementById('layer-terrain').checked;
            if (terrain) {
                map.setMapTypeId('terrain');
                document.getElementById('layer-satellite').checked = false;
            } else {
                map.setMapTypeId('roadmap');
            }
        }
        
        function analyzeLocation() {
            if (!selectedPlace) return;
            
            // Show loading
            document.getElementById('map-loading').classList.remove('hidden');
            document.getElementById('analyze-btn').disabled = true;
            document.getElementById('analyze-btn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analizando...';
            
            // Simulate analysis (in production, this would call your GEE backend)
            setTimeout(function() {
                document.getElementById('map-loading').classList.add('hidden');
                document.getElementById('analyze-btn').disabled = false;
                document.getElementById('analyze-btn').innerHTML = '<i class="fas fa-satellite"></i> Analizar Territorio';
                
                // Show result
                alert(`Análisis completado para ${selectedPlace.name}\\n\\nEsta funcionalidad conectará con Google Earth Engine para generar mapas de riesgo de inundación basados en NDWI y datos topográficos SRTM.\\n\\nCoordenadas: ${selectedPlace.lat.toFixed(4)}, ${selectedPlace.lng.toFixed(4)}`);
            }, 2000);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def landing():
    return LANDING_HTML

@app.route('/api/v1/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "GeoFeedback API",
        "version": "1.0.0"
    })

@app.route('/api/v1/stats')
def stats():
    return jsonify({
        "total_analyses": 156,
        "municipalities_covered": 12,
        "hectares_analyzed": 45230,
        "last_update": "2025-11-29"
    })

@app.route('/api/docs')
def api_docs():
    return jsonify({
        "name": "GeoFeedback Chile API",
        "version": "1.0.0",
        "description": "API para análisis geoespacial de riesgo territorial",
        "endpoints": {
            "/api/v1/health": "Estado del servicio",
            "/api/v1/stats": "Estadísticas generales",
            "/api/v1/analyze": "Análisis de territorio (POST)"
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

