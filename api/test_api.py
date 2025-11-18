#!/usr/bin/env python3
"""
Script de prueba para la API GeoFeedback
Ejecuta pruebas básicas en todos los endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

print("\n" + "="*80)
print("  PRUEBA DE API - GeoFeedback Papudo")
print("="*80 + "\n")

# Test 1: Root endpoint
print("[1/8] Test endpoint raíz...")
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    if response.status_code == 200:
        print(f"  ✓ Status: {response.status_code}")
        data = response.json()
        print(f"  ✓ API Name: {data.get('name')}")
        print(f"  ✓ Version: {data.get('version')}")
    else:
        print(f"  ✗ Error: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 2: Health check
print("\n[2/8] Test health check...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Status: {data.get('status')}")
        print(f"  ✓ Database: {data.get('database', {}).get('connected', 'N/A')}")
    else:
        print(f"  ✗ Error: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 3: Statistics
print("\n[3/8] Test statistics...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/stats", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Statistics retrieved")
        for stat in data.get('statistics', []):
            print(f"    - {stat['risk_name']}: {stat['num_polygons']} polígonos ({stat['percentage']}%)")
    else:
        print(f"  ✗ Error: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 4: Risk at point
print("\n[4/8] Test risk at point...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/risk/point?lon=-71.4492&lat=-32.5067", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Risk Level: {data.get('risk_level')}")
        print(f"  ✓ Risk Name: {data.get('risk_name')}")
        print(f"  ✓ Area: {data.get('area_km2')} km²")
    else:
        print(f"  ✗ Error: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 5: Infrastructure
print("\n[5/8] Test infrastructure...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/infrastructure", timeout=5)
    if response.status_code == 200:
        data = response.json()
        count = data.get('count', 0)
        print(f"  ✓ Total facilities: {count}")
        if count > 0:
            facility = data['facilities'][0]
            print(f"  ✓ Example: {facility['name']} ({facility['category']})")
    else:
        print(f"  ✗ Error: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 6: Infrastructure by ID
print("\n[6/8] Test infrastructure by ID...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/infrastructure/1", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Facility: {data.get('name')}")
        print(f"  ✓ Category: {data.get('category')}")
        print(f"  ✓ Risk: {data.get('risk_name')}")
    else:
        print(f"  ✗ Error: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 7: Infrastructure by risk level
print("\n[7/8] Test infrastructure by risk level...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/infrastructure/risk/2", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Risk Level: {data.get('risk_level')}")
        print(f"  ✓ Facilities in risk: {data.get('count')}")
    else:
        print(f"  ✗ Error: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test 8: Infrastructure by category
print("\n[8/8] Test infrastructure by category...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/infrastructure/category/Educación", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Category: {data.get('category')}")
        print(f"  ✓ Facilities: {data.get('count')}")
        for facility in data.get('facilities', [])[:3]:
            print(f"    - {facility['name']} ({facility['risk_name']})")
    else:
        print(f"  ✗ Error: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "="*80)
print("  PRUEBAS COMPLETADAS")
print("="*80 + "\n")
