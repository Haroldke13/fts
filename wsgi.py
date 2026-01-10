# WSGI entry
import os
import logging
from app import create_app, socketio

# Create the app (without running it)
app = create_app()

# Configure logging
logging.basicConfig(level=logging.INFO)

# For development, run separately with: python wsgi.py
if __name__ == "__main__":
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    try:
        socketio.run(app, debug=debug, host=host, port=port)
    except Exception as e:
        logging.error(f"Error starting server: {e}")

# For production, use: gunicorn --worker-class eventlet -w 1 wsgi:app
# Ensure eventlet is installed: pip install eventlet
