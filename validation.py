"""Strict input helpers. Raise ApiError instead of returning misleading results."""
import math
import re
from flask import jsonify


class ApiError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status
        super().__init__(message)


def fail(message, status=400):
    raise ApiError(message, status)


def text_field(value, name, max_len=120, required=True):
    if value is None and not required:
        return None
    if not isinstance(value, str):
        fail(f"{name} must be text")
    value = value.strip()
    if (required and not value) or len(value) > max_len:
        fail(f"{name} must be 1-{max_len} characters")
    return value or None


def number(value, name, maximum=1_000_000_000):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"{name} must be a number")
    value = float(value)
    if not math.isfinite(value) or value < 0 or value > maximum:
        fail(f"{name} must be between 0 and {maximum}")
    return value


def positive_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 1_000_000_000:
        fail(f"{name} must be a positive whole number")
    return value


def period_field(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
        fail("period must be in YYYY-MM format, e.g. 2026-11")
    return value


def json_body():
    from flask import request
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        fail("Send a JSON object with Content-Type: application/json")
    return data


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({"error": error.message}), error.status

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(413)
    def handle_too_large(error):
        return jsonify({"error": "Request body too large"}), 413
