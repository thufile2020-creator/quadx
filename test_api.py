def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_calculate_demo(client):
    response = client.post("/api/calculate", json={
        "electricity_kwh": 500, "diesel_litres": 30,
    })
    assert response.status_code == 200
    assert response.json["total_kg_co2e"] == 431
    assert response.json["contains_demo_factors"] is True
    assert len(response.json["breakdown"]) == 3


def test_invalid_calculation_rejected(client):
    for invalid in (-5, "500", True, 1e100):
        response = client.post("/api/calculate", json={"electricity_kwh": invalid})
        assert response.status_code == 400
    assert client.post("/api/calculate", json=[]).status_code == 400


def test_register_login_me(client, auth):
    response = client.get("/api/auth/me", headers=auth)
    assert response.status_code == 200
    assert response.json["user"]["email"] == "asha@example.test"
    login = client.post("/api/auth/login", json={"email": "asha@example.test", "password": "StrongPass123!"})
    assert login.status_code == 200
    assert login.json["access_token"]
    bad = client.post("/api/auth/login", json={"email": "asha@example.test", "password": "wrong"})
    assert bad.status_code == 401
    duplicate = client.post("/api/auth/register", json={"name":"Other", "email":"asha@example.test", "password":"StrongPass123!"})
    assert duplicate.status_code == 409


def test_businesses_require_auth(client):
    response = client.get("/api/businesses")
    assert response.status_code == 401


def test_activity_and_summary(client, auth, business_id):
    electricity = client.post(f"/api/businesses/{business_id}/activities", headers=auth, json={
        "period": "2026-11", "activity_type": "electricity", "quantity": 500
    })
    assert electricity.status_code == 201
    diesel = client.post(f"/api/businesses/{business_id}/activities", headers=auth, json={
        "period": "2026-11", "activity_type": "diesel", "quantity": 30
    })
    assert diesel.status_code == 201
    production = client.put(f"/api/businesses/{business_id}/production", headers=auth, json={
        "period": "2026-11", "product_name": "Identical bottles", "units": 1000
    })
    assert production.status_code == 201
    summary = client.get(f"/api/businesses/{business_id}/summary?period=2026-11", headers=auth)
    assert summary.status_code == 200
    assert summary.json["total_kg_co2e"] == 431
    assert summary.json["operational_kg_co2e_per_unit"] == 0.431
    assert summary.json["contains_demo_factors"] is True
    trends = client.get(f"/api/businesses/{business_id}/trends", headers=auth)
    assert len(trends.json["months"]) == 1
    record_id = diesel.json["record"]["id"]
    assert client.delete(f"/api/businesses/{business_id}/activities/{record_id}", headers=auth).status_code == 204
    assert client.get(f"/api/businesses/{business_id}/summary?period=2026-11", headers=auth).json["total_kg_co2e"] == 350


def test_input_errors(client, auth, business_id):
    url = f"/api/businesses/{business_id}/activities"
    assert client.post(url, headers=auth, json={"period": "2026-13", "activity_type": "electricity", "quantity": 10}).status_code == 400
    assert client.post(url, headers=auth, json={"period": "2026-11", "activity_type": "unknown", "quantity": 10}).status_code == 400
    assert client.put(f"/api/businesses/{business_id}/production", headers=auth, json={
        "period": "2026-11", "product_name": "bottles", "units": 0
    }).status_code == 400


def test_missions(client, auth, business_id):
    base = f"/api/businesses/{business_id}/missions"
    created = client.post(base, json={"title": "Check motor idle time"}, headers=auth)
    assert created.status_code == 201
    mission_id = created.json["mission"]["id"]
    done = client.patch(f"{base}/{mission_id}", json={"status":"done"}, headers=auth)
    assert done.status_code == 200
    assert done.json["mission"]["status"] == "done"
    assert len(client.get(base, headers=auth).json["missions"]) == 1
    assert client.patch(f"{base}/{mission_id}", json={"status":"unknown"}, headers=auth).status_code == 400


def test_cannot_read_another_users_business(client, auth, business_id):
    other = client.post("/api/auth/register", json={
        "name": "Other", "email": "other@example.test", "password": "VeryStrong456!"
    }).json["access_token"]
    other_headers = {"Authorization": f"Bearer {other}"}
    assert client.get(f"/api/businesses/{business_id}", headers=other_headers).status_code == 404
    assert client.get(f"/api/businesses/{business_id}/summary?period=2026-11", headers=other_headers).status_code == 404
    assert client.post(f"/api/businesses/{business_id}/activities", headers=other_headers, json={
        "period": "2026-11", "activity_type": "electricity", "quantity": 500
    }).status_code == 404
