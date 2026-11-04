from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from ..extensions import db
from ..models import Business
from ..validation import json_body, text_field
from .helpers import owned_business

bp = Blueprint("businesses", __name__, url_prefix="/api/businesses")


@bp.get("")
@jwt_required()
def list_businesses():
    items = db.session.execute(db.select(Business).filter_by(owner_id=int(get_jwt_identity())).order_by(Business.id)).scalars().all()
    return jsonify({"businesses": [item.to_dict() for item in items]})


@bp.post("")
@jwt_required()
def create_business():
    data = json_body()
    item = Business(
        owner_id=int(get_jwt_identity()),
        name=text_field(data.get("name"), "name", 120),
        industry=text_field(data.get("industry"), "industry", 100, required=False),
        city=text_field(data.get("city"), "city", 100, required=False),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"business": item.to_dict()}), 201


@bp.get("/<int:business_id>")
@jwt_required()
def get_business(business_id):
    return jsonify({"business": owned_business(business_id).to_dict()})


@bp.patch("/<int:business_id>")
@jwt_required()
def update_business(business_id):
    item = owned_business(business_id)
    data = json_body()
    if "name" in data:
        item.name = text_field(data["name"], "name", 120)
    if "industry" in data:
        item.industry = text_field(data["industry"], "industry", 100, required=False)
    if "city" in data:
        item.city = text_field(data["city"], "city", 100, required=False)
    db.session.commit()
    return jsonify({"business": item.to_dict()})
