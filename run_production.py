#!/usr/bin/env python3
"""
Production launcher for Label Print Server
Runs Flask in production mode without debug features
"""

import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == '__main__':
    # Import Flask app
    from app import app
    
    # Run in production mode
    print("Starting Label Print Server in PRODUCTION mode...")
    print("Port: 5000")
    print("Host: 0.0.0.0")
    print("Debug: False")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        sys.exit(1)