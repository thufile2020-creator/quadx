"""Database tables owned by backend member (Member 2)."""
from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Business(db.Model):
    __tablename__ = "businesses"
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "industry": self.industry, "city": self.city}


class EmissionFactor(db.Model):
    __tablename__ = "emission_factors"
    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(30), nullable=False, unique=True)
    kg_co2e_per_unit = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(30), nullable=False)
    scope = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(250), nullable=False)
    reference_year = db.Column(db.String(20), nullable=False)
    is_demo = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "activity_type": self.activity_type,
            "kg_co2e_per_unit": self.kg_co2e_per_unit,
            "unit": self.unit,
            "scope": self.scope,
            "source": self.source,
            "reference_year": self.reference_year,
            "is_demo": self.is_demo,
        }


class ActivityRecord(db.Model):
    __tablename__ = "activity_records"
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    period = db.Column(db.String(7), nullable=False, index=True)  # YYYY-MM
    activity_type = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    # Snapshot the factor for auditability; later factor updates cannot silently rewrite history.
    factor_kg_co2e_per_unit = db.Column(db.Float, nullable=False)
    factor_source = db.Column(db.String(250), nullable=False)
    factor_is_demo = db.Column(db.Boolean, nullable=False)
    note = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "business_id": self.business_id, "period": self.period,
            "activity_type": self.activity_type, "quantity": self.quantity,
            "factor_kg_co2e_per_unit": self.factor_kg_co2e_per_unit,
            "factor_source": self.factor_source, "factor_is_demo": self.factor_is_demo,
            "kg_co2e": round(self.quantity * self.factor_kg_co2e_per_unit, 3),
            "note": self.note,
        }


class ProductionRecord(db.Model):
    __tablename__ = "production_records"
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    period = db.Column(db.String(7), nullable=False)
    # MVP assumes one homogeneous product type per business per month.
    product_name = db.Column(db.String(120), nullable=False)
    units = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint("business_id", "period", name="uq_production_business_period"),)

    def to_dict(self):
        return {"id": self.id, "period": self.period, "product_name": self.product_name, "units": self.units}


class GreenMission(db.Model):
    __tablename__ = "green_missions"
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="todo")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "status": self.status}


def seed_demo_factors():
    """INITIAL DEMO VALUES ONLY! Member 3 must replace with sourced factors."""
    defaults = (
        ("electricity", 0.7, "kWh", 2),
        ("diesel", 2.7, "litre", 1),
        ("petrol", 2.31, "litre", 1),
    )
    for activity_type, value, unit, scope in defaults:
        if db.session.execute(db.select(EmissionFactor).filter_by(activity_type=activity_type)).scalar_one_or_none() is None:
            db.session.add(EmissionFactor(
                activity_type=activity_type, kg_co2e_per_unit=value,
                unit=unit, scope=scope, source="DEMO PLACEHOLDER - NOT FOR OFFICIAL REPORTING",
                reference_year="demo", is_demo=True,
            ))
    db.session.commit()
