import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Landing page HTML with Google Maps + Places Autocomplete + Approach Flow
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
            --info: #3b82f6;
            --info-light: #60a5fa;
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
        }

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

        .nav-links a:hover {
            color: var(--secondary);
        }

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

        .btn-secondary:hover {
            background: var(--primary-light);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }

        /* Hero Section */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding: 8rem 2rem 4rem;
            background: linear-gradient(135deg, var(--primary) 0%, #0f2744 100%);
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
            background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%2310b981' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
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
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 2rem;
            max-width: 500px;
        }

        .hero-buttons {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .hero-visual {
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .satellite-icon {
            font-size: 15rem;
            color: var(--secondary);
            opacity: 0.3;
            animation: float 6s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(5deg); }
        }

        /* Sections */
        .section {
            padding: 6rem 2rem;
        }

        .section-dark {
            background: var(--primary);
            color: white;
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
            margin-bottom: 4rem;
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
            color: rgba(255, 255, 255, 0.7);
        }

        /* Problem Cards */
        .problem-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }

        .problem-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 2rem;
            transition: transform 0.3s, border-color 0.3s;
        }

        .problem-card:hover {
            transform: translateY(-5px);
            border-color: var(--secondary);
        }

        .problem-card i {
            font-size: 2.5rem;
            color: var(--accent);
            margin-bottom: 1rem;
        }

        .problem-card h3 {
            font-size: 1.25rem;
            margin-bottom: 0.75rem;
        }

        .problem-card p {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.95rem;
        }

        /* Solution Cards */
        .solution-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
        }

        .solution-card {
            background: var(--background);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 1px solid var(--border);
        }

        .solution-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        .solution-card i {
            font-size: 2.5rem;
            color: var(--secondary);
            margin-bottom: 1rem;
        }

        .solution-card h3 {
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
            color: var(--primary);
        }

        .solution-card p {
            color: var(--text-light);
            font-size: 0.9rem;
        }

        /* Demo Section */
        .demo-section {
            background: linear-gradient(180deg, var(--background) 0%, #e2e8f0 100%);
            padding: 6rem 2rem;
        }

        .demo-container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .demo-layout {
            display: grid;
            grid-template-columns: 1fr 380px;
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

        #demo-map {
            width: 100%;
            height: 550px;
        }

        .map-controls {
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            z-index: 10;
        }

        .map-control-btn {
            background: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }

        .map-control-btn:hover {
            background: var(--secondary);
            color: white;
        }

        .map-loading {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 20;
        }

        .map-loading.hidden {
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

        /* Sidebar Panel */
        .sidebar-panel {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .panel-card {
            background: white;
            border-radius: 12px;
            padding: 1.25rem;
            box-shadow: var(--shadow);
        }

        .panel-card h3 {
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .search-input-wrapper {
            position: relative;
        }

        .search-input-wrapper i {
            position: absolute;
            left: 1rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-light);
        }

        #location-search {
            width: 100%;
            padding: 0.875rem 1rem 0.875rem 2.75rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 0.95rem;
            transition: border-color 0.3s;
        }

        #location-search:focus {
            outline: none;
            border-color: var(--secondary);
        }

        /* Selected Location */
        .selected-location {
            display: none;
            background: linear-gradient(135deg, var(--secondary), var(--secondary-light));
            color: white;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 0.75rem;
        }

        .selected-location.active {
            display: block;
        }

        .selected-location h4 {
            font-size: 1.1rem;
            margin-bottom: 0.25rem;
        }

        .selected-location p {
            font-size: 0.85rem;
            opacity: 0.9;
        }

        /* Approach Selection Panel */
        .approach-panel {
            display: none;
        }

        .approach-panel.active {
            display: block;
        }

        .approach-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .approach-grid {
            display: grid;
            gap: 0.75rem;
        }

        .approach-card {
            background: var(--background);
            border: 2px solid var(--border);
            border-radius: 10px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
        }

        .approach-card:hover {
            border-color: var(--secondary);
            transform: translateX(5px);
        }

        .approach-card.selected {
            border-color: var(--secondary);
            background: rgba(16, 185, 129, 0.1);
        }

        .approach-card.selected::after {
            content: '✓';
            position: absolute;
            top: 0.75rem;
            right: 0.75rem;
            width: 24px;
            height: 24px;
            background: var(--secondary);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
        }

        .approach-icon {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
        }

        .approach-card h4 {
            font-size: 0.95rem;
            color: var(--primary);
            margin-bottom: 0.25rem;
        }

        .approach-card p {
            font-size: 0.8rem;
            color: var(--text-light);
            margin: 0;
        }

        /* Layers Panel */
        .layers-panel {
            display: none;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }

        .layers-panel.active {
            display: block;
        }

        .layers-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-light);
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .layer-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .layer-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0.75rem;
            background: var(--background);
            border-radius: 6px;
            font-size: 0.85rem;
        }

        .layer-color {
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }

        .layer-item span {
            flex: 1;
        }

        .layer-status {
            font-size: 0.7rem;
            padding: 0.15rem 0.5rem;
            border-radius: 10px;
            background: var(--secondary);
            color: white;
        }

        /* Analyze Button */
        .analyze-section {
            display: none;
            margin-top: 1rem;
        }

        .analyze-section.active {
            display: block;
        }

        #analyze-btn {
            width: 100%;
            padding: 1rem;
            font-size: 1rem;
        }

        /* Results Panel */
        .demo-results {
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
            transition: transform 0.3s;
        }

        .result-card:hover {
            transform: translateY(-3px);
        }

        .result-icon {
            font-size: 2rem;
        }

        .result-content h4 {
            font-size: 1rem;
            color: var(--primary);
            margin-bottom: 0.25rem;
        }

        .result-content p {
            font-size: 0.85rem;
            color: var(--text-light);
            margin: 0;
        }

        /* Layer Toggles */
        .layer-toggles {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .layer-toggle {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            cursor: pointer;
        }

        .layer-toggle input {
            accent-color: var(--secondary);
        }

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

        .footer-logo i {
            color: var(--secondary);
        }

        .footer-links {
            display: flex;
            gap: 2rem;
        }

        .footer-links a {
            color: rgba(255, 255, 255, 0.7);
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
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            transition: all 0.3s;
        }

        .social-links a:hover {
            background: var(--secondary);
        }

        /* Step Indicator */
        .step-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .step {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .step-number {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: var(--border);
            color: var(--text-light);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .step.active .step-number {
            background: var(--secondary);
            color: white;
        }

        .step.completed .step-number {
            background: var(--secondary);
            color: white;
        }

        .step.completed .step-number::after {
            content: '✓';
        }

        .step-label {
            font-size: 0.8rem;
            color: var(--text-light);
        }

        .step.active .step-label {
            color: var(--primary);
            font-weight: 500;
        }

        .step-line {
            width: 30px;
            height: 2px;
            background: var(--border);
        }

        .step.completed + .step-line {
            background: var(--secondary);
        }

        /* Responsive */
        @media (max-width: 1024px) {
            .demo-layout {
                grid-template-columns: 1fr;
            }
            
            .sidebar-panel {
                order: -1;
            }
            
            #demo-map {
                height: 400px;
            }
            
            .demo-results {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 768px) {
            .hero-content {
                grid-template-columns: 1fr;
                text-align: center;
            }
            
            .hero-text h1 {
                font-size: 2.5rem;
            }
            
            .hero-buttons {
                justify-content: center;
            }
            
            .hero-visual {
                display: none;
            }
            
            .nav-links {
                display: none;
            }
            
            .step-indicator {
                flex-wrap: wrap;
            }
        }

        /* Google Places Autocomplete Dropdown Style */
        .pac-container {
            border-radius: 8px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-lg);
            margin-top: 4px;
            font-family: 'Inter', sans-serif;
        }

        .pac-item {
            padding: 10px 14px;
            cursor: pointer;
            font-size: 0.9rem;
        }

        .pac-item:hover {
            background: var(--background);
        }

        .pac-item-selected {
            background: rgba(16, 185, 129, 0.1);
        }

        .pac-icon {
            display: none;
        }

        .pac-item-query {
            font-weight: 500;
            color: var(--primary);
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
            <div class="nav-links">
                <a href="#problema">Problema</a>
                <a href="#solucion">Solución</a>
                <a href="#demo">Demo</a>
                <a href="#metodologia">Metodología</a>
                <a href="/api/docs" class="btn btn-primary">
                    <i class="fas fa-code"></i> API Docs
                </a>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
        <div class="hero-content">
            <div class="hero-text">
                <h1>
                    Democratizando la <span>Inteligencia Territorial</span>
                </h1>
                <p>
                    Plataforma open source que transforma datos satelitales en mapas de riesgo 
                    y herramientas de gestión hídrica para Chile.
                </p>
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

    <!-- Problem Section -->
    <section id="problema" class="section section-dark">
        <div class="container">
            <div class="section-header">
                <h2>El Problema</h2>
                <p>Chile enfrenta desafíos críticos en gestión territorial y recursos hídricos</p>
            </div>
            <div class="problem-grid">
                <div class="problem-card">
                    <i class="fas fa-balance-scale"></i>
                    <h3>Ley 21.364</h3>
                    <p>Municipios deben elaborar planes de emergencia y mapas de riesgo, pero carecen de herramientas técnicas accesibles.</p>
                </div>
                <div class="problem-card">
                    <i class="fas fa-tint-slash"></i>
                    <h3>Mega-sequía</h3>
                    <p>15 años consecutivos de déficit hídrico. Agricultores necesitan datos precisos para optimizar el uso del agua.</p>
                </div>
                <div class="problem-card">
                    <i class="fas fa-dollar-sign"></i>
                    <h3>Alto Costo</h3>
                    <p>Estudios geoespaciales profesionales son costosos y poco accesibles para municipios rurales y pequeños agricultores.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Solution Section -->
    <section id="solucion" class="section section-light">
        <div class="container">
            <div class="section-header">
                <h2>Nuestra Solución</h2>
                <p>Inteligencia territorial accesible mediante tecnología satelital</p>
            </div>
            <div class="solution-grid">
                <div class="solution-card">
                    <i class="fab fa-google"></i>
                    <h3>Google Earth Engine</h3>
                    <p>Procesamiento de petabytes de datos satelitales en la nube</p>
                </div>
                <div class="solution-card">
                    <i class="fab fa-python"></i>
                    <h3>Python + QGIS</h3>
                    <p>Scripts automatizados para análisis reproducible</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-satellite"></i>
                    <h3>Sentinel-2</h3>
                    <p>Imágenes multiespectrales gratuitas cada 5 días</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-code-branch"></i>
                    <h3>Open Source</h3>
                    <p>Código abierto para replicar en cualquier territorio</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Demo Section -->
    <section id="demo" class="demo-section">
        <div class="demo-container">
            <div class="section-header">
                <h2>Demo Interactivo</h2>
                <p>Selecciona una ubicación, elige tu enfoque de análisis y descubre qué podemos analizar</p>
            </div>

            <div class="demo-layout">
                <!-- Map Container -->
                <div class="map-container">
                    <div id="demo-map"></div>
                    <div class="map-controls">
                        <button class="map-control-btn" onclick="centerMap()" title="Centrar en Chile">
                            <i class="fas fa-home"></i>
                        </button>
                    </div>
                    <div class="map-loading hidden" id="map-loading">
                        <div class="spinner"></div>
                        <p style="margin-top: 1rem; color: var(--text-light);">Procesando análisis...</p>
                    </div>
                </div>

                <!-- Sidebar Panel -->
                <div class="sidebar-panel">
                    <!-- Step Indicator -->
                    <div class="panel-card">
                        <div class="step-indicator">
                            <div class="step active" id="step-1">
                                <span class="step-number">1</span>
                                <span class="step-label">Ubicación</span>
                            </div>
                            <div class="step-line"></div>
                            <div class="step" id="step-2">
                                <span class="step-number">2</span>
                                <span class="step-label">Enfoque</span>
                            </div>
                            <div class="step-line"></div>
                            <div class="step" id="step-3">
                                <span class="step-number">3</span>
                                <span class="step-label">Analizar</span>
                            </div>
                        </div>
                    </div>

                    <!-- Location Search -->
                    <div class="panel-card">
                        <h3><i class="fas fa-search"></i> Buscar Localidad</h3>
                        <div class="search-input-wrapper">
                            <i class="fas fa-map-marker-alt"></i>
                            <input type="text" id="location-search" placeholder="Ej: Papudo, Valparaíso">
                        </div>
                        <div class="selected-location" id="selected-location">
                            <h4 id="location-name">-</h4>
                            <p id="location-coords">-</p>
                        </div>
                    </div>

                    <!-- Approach Selection -->
                    <div class="panel-card approach-panel" id="approach-panel">
                        <div class="approach-title">
                            <i class="fas fa-crosshairs"></i>
                            ¿Qué deseas analizar?
                        </div>
                        <div class="approach-grid">
                            <div class="approach-card" data-approach="flood-risk" onclick="selectApproach(this)">
                                <div class="approach-icon">🌊</div>
                                <h4>Riesgo de Inundación</h4>
                                <p>Zonas susceptibles a inundaciones y anegamientos</p>
                            </div>
                            <div class="approach-card" data-approach="water-management" onclick="selectApproach(this)">
                                <div class="approach-icon">💧</div>
                                <h4>Gestión Hídrica</h4>
                                <p>Disponibilidad de agua y estrés hídrico agrícola</p>
                            </div>
                            <div class="approach-card" data-approach="drought" onclick="selectApproach(this)">
                                <div class="approach-icon">🏜️</div>
                                <h4>Sequía y Desertificación</h4>
                                <p>Evolución de cobertura vegetal y degradación</p>
                            </div>
                            <div class="approach-card" data-approach="land-planning" onclick="selectApproach(this)">
                                <div class="approach-icon">🏗️</div>
                                <h4>Planificación Territorial</h4>
                                <p>Aptitud del suelo y análisis de pendientes</p>
                            </div>
                        </div>

                        <!-- Layers for selected approach -->
                        <div class="layers-panel" id="layers-panel">
                            <div class="layers-title">
                                <i class="fas fa-layer-group"></i>
                                Capas de datos disponibles
                            </div>
                            <div class="layer-list" id="layer-list">
                                <!-- Populated dynamically -->
                            </div>
                        </div>
                    </div>

                    <!-- Analyze Button -->
                    <div class="analyze-section" id="analyze-section">
                        <button class="btn btn-primary" id="analyze-btn" onclick="analyzeLocation()" disabled>
                            <i class="fas fa-satellite-dish"></i> Iniciar Análisis
                        </button>
                    </div>

                    <!-- Map Layers -->
                    <div class="panel-card">
                        <h3><i class="fas fa-layer-group"></i> Capas del Mapa</h3>
                        <div class="layer-toggles">
                            <label class="layer-toggle">
                                <input type="checkbox" id="layer-satellite" onchange="toggleMapType()">
                                Satélite
                            </label>
                            <label class="layer-toggle">
                                <input type="checkbox" id="layer-terrain" onchange="toggleTerrain()">
                                Terreno
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Results -->
            <div class="demo-results">
                <div class="result-card" id="info-panel">
                    <div class="result-icon">📍</div>
                    <div class="result-content">
                        <h4>Ubicación</h4>
                        <p>Selecciona una localidad para comenzar</p>
                    </div>
                </div>
                <div class="result-card" id="approach-info">
                    <div class="result-icon">🎯</div>
                    <div class="result-content">
                        <h4>Enfoque</h4>
                        <p>Elige qué tipo de análisis necesitas</p>
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
                    <p>Cálculo de índices espectrales (NDWI, NDVI, etc.)</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-mountain"></i>
                    <h3>3. Topografía</h3>
                    <p>Integración de datos SRTM para análisis de pendientes</p>
                </div>
                <div class="solution-card">
                    <i class="fas fa-chart-area"></i>
                    <h3>4. Clasificación</h3>
                    <p>Generación de zonas según el enfoque seleccionado</p>
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
    <script src="https://maps.googleapis.com/maps/api/js?key={google_maps_key}&libraries=places&callback=initMap" async defer></script>
    
    <script>
        let map;
        let marker;
        let autocomplete;
        let selectedPlace = null;
        let selectedApproach = null;
        
        // Approach configurations with their associated layers
        const approachConfig = {
            'flood-risk': {
                name: 'Riesgo de Inundación',
                icon: '🌊',
                description: 'Análisis de susceptibilidad a inundaciones basado en topografía e índices de agua',
                layers: [
                    { name: 'NDWI - Índice de Agua', color: '#3b82f6', status: 'Disponible' },
                    { name: 'Pendientes SRTM', color: '#f59e0b', status: 'Disponible' },
                    { name: 'Zonas de Acumulación', color: '#ef4444', status: 'Disponible' },
                    { name: 'Red Hídrica', color: '#06b6d4', status: 'Disponible' }
                ]
            },
            'water-management': {
                name: 'Gestión Hídrica',
                icon: '💧',
                description: 'Monitoreo de disponibilidad hídrica para optimización agrícola',
                layers: [
                    { name: 'NDWI Temporal', color: '#3b82f6', status: 'Disponible' },
                    { name: 'Humedad del Suelo', color: '#8b5cf6', status: 'Beta' },
                    { name: 'NDVI - Vegetación', color: '#10b981', status: 'Disponible' },
                    { name: 'Estrés Hídrico', color: '#ef4444', status: 'Disponible' }
                ]
            },
            'drought': {
                name: 'Sequía y Desertificación',
                icon: '🏜️',
                description: 'Evaluación temporal de degradación de suelos y vegetación',
                layers: [
                    { name: 'NDVI Histórico', color: '#10b981', status: 'Disponible' },
                    { name: 'Cambio de Cobertura', color: '#f59e0b', status: 'Disponible' },
                    { name: 'Índice de Aridez', color: '#dc2626', status: 'Beta' },
                    { name: 'Tendencia 5 años', color: '#6366f1', status: 'Disponible' }
                ]
            },
            'land-planning': {
                name: 'Planificación Territorial',
                icon: '🏗️',
                description: 'Caracterización del territorio para ordenamiento y uso de suelo',
                layers: [
                    { name: 'Modelo de Elevación', color: '#78716c', status: 'Disponible' },
                    { name: 'Clasificación Pendientes', color: '#f59e0b', status: 'Disponible' },
                    { name: 'Exposición Solar', color: '#fbbf24', status: 'Disponible' },
                    { name: 'Uso de Suelo', color: '#10b981', status: 'Beta' }
                ]
            }
        };
        
        // Chile bounds
        const chileBounds = {
            north: -17.5,
            south: -56.0,
            west: -76.0,
            east: -66.5
        };

        // Initialize map
        function initMap() {
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
            
            // Set bounds bias
            autocomplete.setBounds(new google.maps.LatLngBounds(
                new google.maps.LatLng(chileBounds.south, chileBounds.west),
                new google.maps.LatLng(chileBounds.north, chileBounds.east)
            ));
            
            // Listen for place selection from autocomplete
            autocomplete.addListener('place_changed', onPlaceChanged);
            
            // Also handle Enter key explicitly
            input.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    // The place_changed event should fire automatically
                    // But we can also try to get the first prediction
                    const firstPrediction = document.querySelector('.pac-item');
                    if (firstPrediction) {
                        // Simulate click on first item
                        google.maps.event.trigger(autocomplete, 'place_changed');
                    }
                }
            });
            
            // Map click listener
            map.addListener('click', function(e) {
                placeMarkerAndPan(e.latLng);
                reverseGeocode(e.latLng);
            });
        }
        
        function onPlaceChanged() {
            const place = autocomplete.getPlace();
            
            console.log('Place changed:', place);
            
            if (!place.geometry || !place.geometry.location) {
                console.log("No geometry for this place - trying search");
                // If user just typed and hit enter without selecting
                const input = document.getElementById('location-search');
                if (input.value) {
                    searchPlace(input.value);
                }
                return;
            }
            
            selectedPlace = {
                name: place.name,
                address: place.formatted_address,
                lat: place.geometry.location.lat(),
                lng: place.geometry.location.lng()
            };
            
            // Update map - move to location
            map.setCenter(place.geometry.location);
            map.setZoom(13);
            
            // Update marker
            marker.setPosition(place.geometry.location);
            marker.setVisible(true);
            
            // Update UI
            updateLocationUI(selectedPlace);
            showApproachPanel();
            updateStep(2);
        }
        
        // Fallback search using Geocoding
        function searchPlace(query) {
            const geocoder = new google.maps.Geocoder();
            
            geocoder.geocode({ 
                address: query + ', Chile',
                componentRestrictions: { country: 'cl' }
            }, function(results, status) {
                if (status === 'OK' && results[0]) {
                    const result = results[0];
                    const location = result.geometry.location;
                    
                    selectedPlace = {
                        name: extractLocalityName(result) || query,
                        address: result.formatted_address,
                        lat: location.lat(),
                        lng: location.lng()
                    };
                    
                    // Update map
                    map.setCenter(location);
                    map.setZoom(13);
                    
                    // Update marker
                    marker.setPosition(location);
                    marker.setVisible(true);
                    
                    // Update UI
                    updateLocationUI(selectedPlace);
                    showApproachPanel();
                    updateStep(2);
                }
            });
        }
        
        function placeMarkerAndPan(latLng) {
            marker.setPosition(latLng);
            marker.setVisible(true);
            map.panTo(latLng);
            if (map.getZoom() < 10) {
                map.setZoom(13);
            }
        }
        
        function reverseGeocode(latLng) {
            const geocoder = new google.maps.Geocoder();
            
            geocoder.geocode({ location: latLng }, function(results, status) {
                if (status === 'OK' && results[0]) {
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
                    showApproachPanel();
                    updateStep(2);
                }
            });
        }
        
        function extractLocalityName(place) {
            if (!place.address_components) return place.formatted_address.split(',')[0];
            
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
            
            // Update info panel
            document.getElementById('info-panel').innerHTML = `
                <div class="result-icon">📍</div>
                <div class="result-content">
                    <h4>${place.name}</h4>
                    <p>${place.address}</p>
                </div>
            `;
        }
        
        function showApproachPanel() {
            document.getElementById('approach-panel').classList.add('active');
            document.getElementById('analyze-section').classList.add('active');
        }
        
        function selectApproach(element) {
            // Remove selected class from all
            document.querySelectorAll('.approach-card').forEach(card => {
                card.classList.remove('selected');
            });
            
            // Add selected to clicked
            element.classList.add('selected');
            
            // Get approach key
            selectedApproach = element.dataset.approach;
            const config = approachConfig[selectedApproach];
            
            // Show layers panel
            const layersPanel = document.getElementById('layers-panel');
            layersPanel.classList.add('active');
            
            // Populate layers
            const layerList = document.getElementById('layer-list');
            layerList.innerHTML = config.layers.map(layer => `
                <div class="layer-item">
                    <div class="layer-color" style="background: ${layer.color}"></div>
                    <span>${layer.name}</span>
                    <span class="layer-status">${layer.status}</span>
                </div>
            `).join('');
            
            // Enable analyze button
            document.getElementById('analyze-btn').disabled = false;
            
            // Update approach info card
            document.getElementById('approach-info').innerHTML = `
                <div class="result-icon">${config.icon}</div>
                <div class="result-content">
                    <h4>${config.name}</h4>
                    <p>${config.description}</p>
                </div>
            `;
            
            updateStep(3);
        }
        
        function updateStep(step) {
            for (let i = 1; i <= 3; i++) {
                const stepEl = document.getElementById(`step-${i}`);
                stepEl.classList.remove('active', 'completed');
                
                if (i < step) {
                    stepEl.classList.add('completed');
                } else if (i === step) {
                    stepEl.classList.add('active');
                }
            }
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
            if (!selectedPlace || !selectedApproach) return;
            
            const config = approachConfig[selectedApproach];
            
            // Show loading
            document.getElementById('map-loading').classList.remove('hidden');
            document.getElementById('analyze-btn').disabled = true;
            document.getElementById('analyze-btn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
            
            // Simulate analysis (in production, this would call your GEE backend)
            setTimeout(function() {
                document.getElementById('map-loading').classList.add('hidden');
                document.getElementById('analyze-btn').disabled = false;
                document.getElementById('analyze-btn').innerHTML = '<i class="fas fa-satellite-dish"></i> Iniciar Análisis';
                
                // Show results
                alert(`Análisis "${config.name}" para ${selectedPlace.name}\n\nEsta funcionalidad conectará con Google Earth Engine para procesar:\n\n${config.layers.map(l => '• ' + l.name).join('\n')}\n\nCoordenadas: ${selectedPlace.lat.toFixed(4)}, ${selectedPlace.lng.toFixed(4)}`);
            }, 2000);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def landing():
    google_maps_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    return LANDING_HTML.replace('{google_maps_key}', google_maps_key)

# API Routes
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
        "total_analyses": 147,
        "municipalities_served": 12,
        "data_sources": ["Sentinel-2", "SRTM", "ERA5"],
        "coverage_area_km2": 45000
    })

@app.route('/api/v1/infrastructure')
def infrastructure():
    return jsonify({
        "features": [
            {"type": "school", "name": "Escuela Papudo", "lat": -32.5127, "lng": -71.4469},
            {"type": "hospital", "name": "CESFAM Papudo", "lat": -32.5089, "lng": -71.4523},
            {"type": "fire_station", "name": "Bomberos Papudo", "lat": -32.5101, "lng": -71.4478}
        ]
    })

@app.route('/api/v1/risk-zones')
def risk_zones():
    return jsonify({
        "zones": [
            {"level": "high", "area_ha": 45.2, "description": "Quebrada El Francés"},
            {"level": "medium", "area_ha": 128.7, "description": "Sector costero norte"},
            {"level": "low", "area_ha": 234.1, "description": "Meseta central"}
        ]
    })

@app.route('/api/docs')
def api_docs():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>GeoFeedback API Documentation</title>
        <style>
            body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #1e3a5f; }
            .endpoint { background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981; }
            code { background: #e5e7eb; padding: 2px 8px; border-radius: 4px; }
            .method { background: #10b981; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🌍 GeoFeedback API v1</h1>
        <p>API REST para acceso a datos de inteligencia territorial.</p>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/v1/health</code>
            <p>Estado del servicio</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/v1/stats</code>
            <p>Estadísticas generales de la plataforma</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/v1/infrastructure</code>
            <p>Infraestructura crítica georreferenciada</p>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span> <code>/api/v1/risk-zones</code>
            <p>Zonas de riesgo clasificadas por nivel</p>
        </div>
        
        <p style="margin-top: 40px; color: #6b7280;">
            <a href="/">← Volver al inicio</a> | 
            <a href="https://github.com/theChosen16/Demo_geofeedback">GitHub</a>
        </p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
