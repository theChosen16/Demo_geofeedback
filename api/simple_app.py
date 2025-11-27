import os
import logging
import sys
from flask import Flask, jsonify

# Setup minimal logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    logger.info("Root endpoint hit")
    return "Hello from Minimal GeoFeedback App"

@app.route('/api/v1/health')
def health():
    logger.info("Health check hit")
    return jsonify({"status": "healthy", "type": "minimal"})

if __name__ == '__main__':
    print("="*50)
    print("STARTING SIMPLE APP")
    print("Environment:")
    for k, v in os.environ.items():
        if "SECRET" not in k:
            print(f"{k}={v}")
    print("="*50)
    
    port = int(os.environ.get('PORT', 8080))
    print(f"Binding to 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)
