from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import GreenMission
from ..validation import fail, json_body, text_field
from .helpers import owned_business

bp = Blueprint("missions", __name__, url_prefix="/api/businesses/<int:business_id>/missions")
VALID_STATUSES = {"todo", "in_progress", "done"}


@bp.get("")
@jwt_required()
def list_missions(business_id):
    owned_business(business_id)
    items = db.session.execute(db.select(GreenMission).filter_by(business_id=business_id).order_by(GreenMission.id)).scalars().all()
    return jsonify({"missions": [item.to_dict() for item in items]})


@bp.post("")
@jwt_required()
def create_mission(business_id):
    owned_business(business_id)
    data = json_body()
    item = GreenMission(business_id=business_id, title=text_field(data.get("title"), "title", 200))
    db.session.add(item)
    db.session.commit()
    return jsonify({"mission": item.to_dict()}), 201


@bp.patch("/<int:mission_id>")
@jwt_required()
def update_mission(business_id, mission_id):
    owned_business(business_id)
    item = db.session.get(GreenMission, mission_id)
    if item is None or item.business_id != business_id:
        fail("Mission not found", 404)
    data = json_body()
    status = data.get("status")
    if status not in VALID_STATUSES:
        fail("status must be todo, in_progress or done")
    item.status = status
    db.session.commit()
    return jsonify({"mission": item.to_dict()})
