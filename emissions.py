from flask import Blueprint, jsonify
from ..extensions import db
from ..models import EmissionFactor
from ..services.emissions import calculate_preview
from ..validation import json_body

bp = Blueprint("emissions", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    return jsonify({"status": "ok", "service": "CarbonEase backend", "api_version": "1.0"})


@bp.get("/emission-factors")
def factors():
    items = db.session.execute(db.select(EmissionFactor).order_by(EmissionFactor.activity_type)).scalars().all()
    return jsonify({"factors": [factor.to_dict() for factor in items], "important": "Initial values are demo placeholders, NOT official factors"})


@bp.post("/calculate")
def calculate():
    return jsonify(calculate_preview(json_body()))
