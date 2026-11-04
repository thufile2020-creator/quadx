"""Isolated in-memory database for every test."""
import pytest
from carbon_api import create_app
from carbon_api.extensions import db


@pytest.fixture
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "testing-secret-only",
    })
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth(client):
    response = client.post("/api/auth/register", json={
        "name": "Asha", "email": "asha@example.test", "password": "StrongPass123!"
    })
    assert response.status_code == 201
    return {"Authorization": "Bearer " + response.json["access_token"]}


@pytest.fixture
def business_id(client, auth):
    response = client.post("/api/businesses", headers=auth, json={
        "name": "Example Manufacturing", "industry": "Plastic components", "city": "Chennai"
    })
    assert response.status_code == 201
    return response.json["business"]["id"]
