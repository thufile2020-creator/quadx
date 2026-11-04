r"""Initialize the local CarbonEase database from SQLAlchemy models.

Windows (at the project root):
    .\backend\.venv\Scripts\python.exe database\init_db.py

Do not commit the generated .db file: it may contain real user records.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from carbon_api import create_app
from carbon_api.extensions import db

app = create_app()  # creates tables and demo emission factors
with app.app_context():
    print("Database URL:", db.engine.url.render_as_string(hide_password=True))
    print("Created/checked tables:", ", ".join(sorted(db.metadata.tables.keys())))
    print("Database initialized. Actual SQLite .db file is ignored by Git.")
