"""
Production WSGI Server for Label Print Server
Uses Waitress as a production-ready WSGI server
"""

import os
import sys
import logging
from waitress import serve
from app import app

# Configure production logging for waitress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_production_app():
    """Create production-ready app instance"""
    # Set production environment
    os.environ.setdefault('FLASK_ENV', 'production')
    
    # Disable debug mode in production
    app.debug = False
    app.testing = False
    
    return app

def main():
    """Main production server entry point"""
    production_app = create_production_app()
    
    # Get configuration from environment
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    threads = int(os.environ.get('THREADS', 4))
    
    print("=" * 60)
    print("LABEL PRINT SERVER - PRODUCTION MODE")
    print("=" * 60)
    print(f"Server: {host}:{port}")
    print(f"Threads: {threads}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print("=" * 60)
    
    try:
        # Start production server
        serve(
            production_app,
            host=host,
            port=port,
            threads=threads,
            # Connection settings
            connection_limit=1000,
            cleanup_interval=30,
            channel_timeout=120,
            # Security settings
            expose_tracebacks=False,
            # Performance settings
            send_bytes=18000,
            # Logging
            _quiet=False,
            ident='LabelPrintServer/1.0'
        )
    except KeyboardInterrupt:
        print("\nShutting down Label Print Server...")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Failed to start production server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()