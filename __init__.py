# Member 3 AI and Member 4 reports now live inside backend/ for GitHub grouping.
import sys
from pathlib import Path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env BEFORE importing Config (Config reads environment at import time).
load_dotenv()
from .config import Config
from .extensions import db, jwt
from .models import seed_demo_factors
from .validation import register_error_handlers


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)
    origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})
    register_error_handlers(app)

    from .routes import auth, businesses, activities, emissions, missions, ai_integration, report_integration
    for blueprint in (auth.bp, businesses.bp, activities.bp, emissions.bp, missions.bp, ai_integration.bp, report_integration.bp):
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()   # Hackathon MVP. Use Alembic/Flask-Migrate later.
        seed_demo_factors()
    return app
