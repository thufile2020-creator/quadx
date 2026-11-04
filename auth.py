import re
from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import User
from ..validation import json_body, text_field, fail

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    data = json_body()
    name = text_field(data.get("name"), "name", 100)
    email = text_field(data.get("email"), "email", 255).lower()
    password = data.get("password")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        fail("Enter a valid email")
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        fail("Password must contain 8-128 characters")
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        fail("An account with this email already exists", 409)
    return jsonify({"user": user.to_dict(), "access_token": create_access_token(identity=str(user.id))}), 201


@bp.post("/login")
def login():
    data = json_body()
    email = text_field(data.get("email"), "email", 255).lower()
    password = data.get("password")
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if user is None or not isinstance(password, str) or not user.verify_password(password):
        fail("Invalid email or password", 401)
    return jsonify({"user": user.to_dict(), "access_token": create_access_token(identity=str(user.id))})


@bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        fail("User no longer exists", 401)
    return jsonify({"user": user.to_dict()})
