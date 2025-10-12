from flask import Flask
from flask_cors import CORS
import os
from api.routes import register_routes

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:3000"])  # Allow your Next.js frontend
    
    # Register all routes
    register_routes(app)
    
    return app

def main():
    """Main entry point"""
    # Create necessary directories
    os.makedirs("./vector_store", exist_ok=True)
    os.makedirs("./temp_configs", exist_ok=True)
    
    # Create and run the Flask app
    app = create_app()
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True
    )

if __name__ == '__main__':
    main()