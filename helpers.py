from flask_jwt_extended import get_jwt_identity
from ..extensions import db
from ..models import Business
from ..validation import fail


def owned_business(business_id):
    business = db.session.get(Business, business_id)
    if business is None or business.owner_id != int(get_jwt_identity()):
        fail("Business not found", 404)
    return business
