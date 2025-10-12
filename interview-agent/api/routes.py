from .upload import upload_bp
from .cases import cases_bp
from .search import search_bp
from .config import config_bp
from .health import health_bp

def register_routes(app):
    """Register all blueprint routes with the Flask app"""
    app.register_blueprint(health_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(cases_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(config_bp)