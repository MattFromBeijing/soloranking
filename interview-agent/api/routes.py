from .upload import upload_bp
from .health import health_bp

def register_routes(app):
    """Register all blueprint routes with the Flask app"""
    app.register_blueprint(health_bp)
    app.register_blueprint(upload_bp)