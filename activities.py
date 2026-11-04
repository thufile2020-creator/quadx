from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import ActivityRecord, EmissionFactor, ProductionRecord
from ..services.emissions import ACTIVITY_FIELDS, get_factor, month_summary
from ..validation import fail, json_body, number, period_field, positive_int, text_field
from .helpers import owned_business

bp = Blueprint("records", __name__, url_prefix="/api/businesses/<int:business_id>")


@bp.get("/activities")
@jwt_required()
def list_activities(business_id):
    owned_business(business_id)
    query = db.select(ActivityRecord).filter_by(business_id=business_id)
    if request.args.get("period"):
        query = query.filter_by(period=period_field(request.args["period"]))
    records = db.session.execute(query.order_by(ActivityRecord.id.desc())).scalars().all()
    return jsonify({"records": [record.to_dict() for record in records]})


@bp.post("/activities")
@jwt_required()
def add_activity(business_id):
    owned_business(business_id)
    data = json_body()
    activity_type = data.get("activity_type")
    if activity_type not in ACTIVITY_FIELDS:
        fail(f"activity_type must be one of {', '.join(ACTIVITY_FIELDS)}")
    factor = get_factor(activity_type)
    record = ActivityRecord(
        business_id=business_id, period=period_field(data.get("period")),
        activity_type=activity_type, quantity=number(data.get("quantity"), "quantity"),
        factor_kg_co2e_per_unit=factor.kg_co2e_per_unit,
        factor_source=factor.source, factor_is_demo=factor.is_demo,
        note=text_field(data.get("note"), "note", 250, required=False),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"record": record.to_dict()}), 201


@bp.delete("/activities/<int:record_id>")
@jwt_required()
def delete_activity(business_id, record_id):
    owned_business(business_id)
    record = db.session.get(ActivityRecord, record_id)
    if record is None or record.business_id != business_id:
        fail("Record not found", 404)
    db.session.delete(record)
    db.session.commit()
    return "", 204


@bp.get("/production")
@jwt_required()
def list_production(business_id):
    owned_business(business_id)
    query = db.select(ProductionRecord).filter_by(business_id=business_id)
    if request.args.get("period"):
        query = query.filter_by(period=period_field(request.args["period"]))
    items = db.session.execute(query.order_by(ProductionRecord.period.desc())).scalars().all()
    return jsonify({"production": [item.to_dict() for item in items]})


@bp.put("/production")
@jwt_required()
def upsert_production(business_id):
    owned_business(business_id)
    data = json_body()
    period = period_field(data.get("period"))
    item = db.session.execute(db.select(ProductionRecord).filter_by(business_id=business_id, period=period)).scalar_one_or_none()
    is_new = item is None
    if is_new:
        item = ProductionRecord(business_id=business_id, period=period)
        db.session.add(item)
    item.product_name = text_field(data.get("product_name"), "product_name", 120)
    item.units = positive_int(data.get("units"), "units")
    db.session.commit()
    return jsonify({"production": item.to_dict()}), (201 if is_new else 200)


@bp.get("/summary")
@jwt_required()
def summary(business_id):
    owned_business(business_id)
    return jsonify(month_summary(business_id, period_field(request.args.get("period"))))


@bp.get("/trends")
@jwt_required()
def trends(business_id):
    owned_business(business_id)
    periods = db.session.execute(
        db.select(ActivityRecord.period).filter_by(business_id=business_id).distinct().order_by(ActivityRecord.period)
    ).scalars().all()
    return jsonify({"business_id": business_id, "months": [month_summary(business_id, period) for period in periods]})
