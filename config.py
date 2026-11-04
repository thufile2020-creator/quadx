"""Configuration for the GitHub-ready CarbonEase project."""
import os
from pathlib import Path
from datetime import timedelta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = "sqlite:///" + (DATABASE_DIR / "carbonease.db").as_posix()

class Config:
    # Set DATABASE_URL in backend/.env to use an external database instead.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or DEFAULT_SQLITE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-REPLACE-before-deploy")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024
