import time
import requests
import sys
from datetime import datetime

# Configuration
URL = "https://demogeofeedback-production.up.railway.app"
ENDPOINTS = [
    "/",
    "/api/v1/health",
    "/api/v1/stats"
]
INTERVAL = 5  # seconds

def check_endpoint(endpoint):
    full_url = f"{URL}{endpoint}"
    try:
        start_time = time.time()
        response = requests.get(full_url, timeout=10)
        elapsed = (time.time() - start_time) * 1000
        
        status_code = response.status_code
        
        # Color coding
        if status_code == 200:
            status_str = f"\033[92m{status_code} OK\033[0m"
        elif status_code == 502:
            status_str = f"\033[91m{status_code} BAD GATEWAY\033[0m"
        else:
            status_str = f"\033[93m{status_code}\033[0m"
            
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {endpoint:<20} | {status_str} | {elapsed:.0f}ms")
        return status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {endpoint:<20} | \033[91mERROR\033[0m | {str(e)}")
        return False

def main():
    print(f"Starting monitor for {URL}")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        while True:
            all_healthy = True
            for endpoint in ENDPOINTS:
                if not check_endpoint(endpoint):
                    all_healthy = False
            
            if not all_healthy:
                print("\033[91m[!] Some endpoints are failing\033[0m")
            
            print("-" * 60)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nMonitor stopped")

if __name__ == "__main__":
    try:
        import colorama
        colorama.init()
    except ImportError:
        pass
    main()
