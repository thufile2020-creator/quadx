"""Member 4 carbon passport integrated with Member 2's database.

Authenticated export reads the business's actual saved activities.
Unauthenticated /preview and /pdf endpoints serve *demo* input JSON only
and should be secured before public production deployment.
"""
import calendar
import json
from datetime import date
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from reports import PassportError, build_passport, generate_passport_pdf
from ..extensions import db
from ..models import ActivityRecord
from .helpers import owned_business

bp = Blueprint("report_integration", __name__, url_prefix="/api/reports")


def _pdf(passport):
    with TemporaryDirectory(prefix="quadx_pdf_") as temp:
        path = Path(temp) / "passport.pdf"
        generate_passport_pdf(passport, str(path))
        content = path.read_bytes()
    return send_file(BytesIO(content), mimetype="application/pdf", as_attachment=True,
                     download_name=f"Carbon_Passport_{passport['report_id']}.pdf")


def _requested_passport():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise PassportError("Provide a JSON passport payload")
    return build_passport(data)


@bp.post("/preview")
def preview():
    try:
        return jsonify(_requested_passport())
    except PassportError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.post("/pdf")
def export_demo_pdf():
    try:
        return _pdf(_requested_passport())
    except PassportError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.get("/businesses/<int:business_id>/pdf")
@jwt_required()
def export_business_pdf(business_id):
    """Generate report from a user's saved database records, not browser claims."""
    business = owned_business(business_id)
    records = db.session.execute(
        db.select(ActivityRecord).filter_by(business_id=business_id)
        .order_by(ActivityRecord.period, ActivityRecord.id)
    ).scalars().all()
    if not records:
        return jsonify({"error": "Save at least one activity first"}), 400
    periods = [row.period for row in records]
    first = min(periods)
    last = max(periods)
    last_y, last_m = (int(n) for n in last.split("-"))
    items = []
    for row in records:
        details = {}
        try:
            details = json.loads(row.note or "{}")
            if not isinstance(details, dict):
                details = {}
        except (ValueError, TypeError):
            pass
        unit = "kWh" if row.activity_type == "electricity" else "litres"
        items.append({
            "id": f"REC-{row.id}", "source": row.activity_type.title(),
            "scope": "Scope 2" if row.activity_type == "electricity" else "Scope 1",
            "quantity": row.quantity, "unit": unit,
            "emission_factor": row.factor_kg_co2e_per_unit,
            "factor_unit": f"kg CO2e/{unit}",
            "factor_source": row.factor_source,
            "factor_year": date.today().year,
            "evidence_file": str(details.get("sourceName") or "")[:160],
        })
    payload = {
        "report_id": f"QUADX-{business_id}-{date.today():%Y%m%d}",
        "business": {
            "name": business.name,
            "industry": business.industry or "Unspecified",
            "location": business.city or "Unspecified",
            "supplier_id": f"QUADX-{business.id}",
        },
        "period": {
            "start": f"{first}-01",
            "end": f"{last}-{calendar.monthrange(last_y, last_m)[1]:02d}",
        },
        "activities": items,
        "quality_notes": [
            "Self-entered figures require checking against source records.",
            "Demo emission-factor values are not suitable for official reporting.",
            "Source factor-year column uses export year for demonstration only; not a verified factor publication year.",
        ],
    }
    try:
        return _pdf(build_passport(payload))
    except PassportError as exc:
        return jsonify({"error": str(exc)}), 400
