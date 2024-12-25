# api/app.py
from flask import Flask, Blueprint
from flask_cors import CORS
from common.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    # Register blueprints
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")
    return app
