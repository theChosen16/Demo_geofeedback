import sys
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed. Please install with: pip install playwright && playwright install chromium")
    print("Falling back to simple request check...")
    import requests
    sys.exit(1)

URL = "https://demogeofeedback-production.up.railway.app"

def run():
    with sync_playwright() as p:
        print(f"[{datetime.now()}] Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"[{datetime.now()}] Navigating to {URL}...")
        try:
            response = page.goto(URL, timeout=30000)
            status = response.status
            
            print(f"[{datetime.now()}] Status: {status}")
            
            if status == 200:
                print(f"[{datetime.now()}] Page loaded successfully")
                title = page.title()
                print(f"[{datetime.now()}] Title: {title}")
                
                # Check for specific content
                if "GeoFeedback" in page.content():
                    print(f"[{datetime.now()}] \033[92mSUCCESS: Content verified\033[0m")
                else:
                    print(f"[{datetime.now()}] \033[93mWARNING: Content might be missing\033[0m")
                
                # Screenshot
                page.screenshot(path="deploy_screenshot.png")
                print(f"[{datetime.now()}] Screenshot saved to deploy_screenshot.png")
                
            else:
                print(f"[{datetime.now()}] \033[91mFAILED: Status {status}\033[0m")
                print(f"[{datetime.now()}] Content preview: {page.content()[:200]}")
                
        except Exception as e:
            print(f"[{datetime.now()}] \033[91mERROR: {str(e)}\033[0m")
            
        finally:
            browser.close()

if __name__ == "__main__":
    run()
