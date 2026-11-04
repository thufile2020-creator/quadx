"""Member 3 engine in the same Flask app as Member 2.

All AI recommendations here are offline/rule-based unless Member 3's
optional LLM integration is separately enabled. OCR is user-reviewed.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Blueprint, jsonify, request
from ai_engine import (
    calculate_emissions, detect_carbon_anomaly, generate_recommendations, read_bill,
)

bp = Blueprint("ai_integration", __name__, url_prefix="/api/ai")
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _json():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError("Provide a JSON object")
    return body


@bp.post("/calculate")
def calculate():
    try:
        return jsonify(calculate_emissions(_json()))
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/detect")
def detect():
    try:
        body = _json()
        records = body.get("records", [])
        if not isinstance(records, list) or len(records) > 120:
            raise ValueError("records must be a list of at most 120 months")
        return jsonify(detect_carbon_anomaly(records, body.get("threshold_pct", 20)))
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/recommend")
def recommend():
    try:
        body = _json()
        summary = calculate_emissions(body.get("activity", {}))
        detector = None
        if "records" in body:
            records = body["records"]
            if not isinstance(records, list) or len(records) > 120:
                raise ValueError("records must be a list of at most 120 months")
            detector = detect_carbon_anomaly(records)
        return jsonify({
            "emissions": summary,
            "anomaly": detector,
            "suggestions": generate_recommendations(summary, detector),
            "method": "Offline, rule-based suggestions; not a generative AI response.",
        })
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/scan")
def scan():
    uploaded = request.files.get("bill")
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "Select a file using form field 'bill'"}), 400
    ext = Path(uploaded.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Unsupported bill type"}), 400
    try:
        with TemporaryDirectory(prefix="quadx_scan_") as temp:
            path = Path(temp) / ("bill" + ext)
            uploaded.save(path)
            result = read_bill(path)
            result["original_filename"] = Path(uploaded.filename).name[:150]
            return jsonify(result)
    except (ValueError, RuntimeError, OSError) as exc:
        return jsonify({"error": str(exc)}), 422
