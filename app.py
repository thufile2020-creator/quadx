"""Run the entire four-member hackathon project: python app.py.

One Flask process serves the QUADx frontend and all Member 2/3/4 APIs.
"""
import os
import sys
from pathlib import Path

from flask import send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from carbon_api import create_app

app = create_app()
FRONTEND = PROJECT_ROOT / "frontend"


@app.get("/")
def home():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/styles.css")
def stylesheet():
    return send_from_directory(FRONTEND, "styles.css")


@app.get("/script.js")
def javascript():
    return send_from_directory(FRONTEND, "script.js")


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
