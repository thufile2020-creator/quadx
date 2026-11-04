# CarbonEase Member 2 — API Contract v1

Base URL locally: `http://127.0.0.1:5000/api`

**Important:** Sample factors are DEMO ONLY. Do not use for official carbon reporting. All requests/responses are JSON unless stated otherwise. `period` is `YYYY-MM`. Quantities must be numbers (not strings), >= 0.

## Public endpoints

### `GET /health`
Returns `{"status":"ok", "service":"CarbonEase backend", "api_version":"1.0"}`.

### `GET /emission-factors`
Returns the available factors, units, scope, source, reference year and `is_demo` flag. The initial `0.7 kg CO2e/kWh` and `2.7 kg CO2e/litre` values are placeholders.

### `POST /calculate`
**Request**
```json
{"electricity_kwh": 500, "diesel_litres": 30}
```
**Response** (abbreviated)
```json
{
  "electricity_kg_co2e": 350,
  "diesel_kg_co2e": 81,
  "total_kg_co2e": 431,
  "unit": "kg CO2e",
  "contains_demo_factors": true,
  "warning": "Illustrative only. Replace demo factors with validated sources before external reporting.",
  "breakdown": [
    {"activity_type":"electricity", "quantity":500, "unit":"kWh", "scope":2, "factor_kg_co2e_per_unit":0.7, "factor_source":"DEMO PLACEHOLDER - NOT FOR OFFICIAL REPORTING", "kg_co2e":350},
    {"activity_type":"diesel", "quantity":30, "unit":"litre", "scope":1, "factor_kg_co2e_per_unit":2.7, "factor_source":"DEMO PLACEHOLDER - NOT FOR OFFICIAL REPORTING", "kg_co2e":81}
  ]
}
```
Missing electricity/diesel keys default to 0 for a quick preview. This endpoint **does not save** the values. Frontend can call it without login.

### `POST /auth/register`
`{"name":"Asha","email":"asha@example.com","password":"StrongPass123!"}`.
Returns `201` with `{"user": {...}, "access_token":"..."}`.

### `POST /auth/login`
`{"email":"asha@example.com","password":"StrongPass123!"}`.
Returns `{"user": {...}, "access_token":"..."}`.

## Authenticated endpoints

Send `Authorization: Bearer <access_token>` on every request below. Access tokens expire after 8 hours. Business resources are restricted to the logged-in owner.

| Method | Path | Request / description |
|---|---|---|
| GET | `/auth/me` | Current user profile |
| GET | `/businesses` | List businesses owned by account |
| POST | `/businesses` | `{"name":"Sample Supplier","industry":"Manufacturing","city":"Chennai"}` |
| GET | `/businesses/{id}` | One business |
| PATCH | `/businesses/{id}` | Update `name`, `industry`, `city` |
| GET | `/businesses/{id}/activities` | List consumption records, optional `?period=2026-11` |
| POST | `/businesses/{id}/activities` | Add one electricity/diesel activity |
| DELETE | `/businesses/{id}/activities/{record_id}` | Remove one record, returns 204 |
| GET | `/businesses/{id}/production` | List monthly production records, optional `?period=2026-11` |
| PUT | `/businesses/{id}/production` | Create/update production for one month |
| GET | `/businesses/{id}/summary?period=2026-11` | Breakdown, monthly total, and optional intensity |
| GET | `/businesses/{id}/trends` | Monthly summaries sorted by period |
| GET | `/businesses/{id}/missions` | List green tasks |
| POST | `/businesses/{id}/missions` | `{"title":"Check machine idle time"}` |
| PATCH | `/businesses/{id}/missions/{mission_id}` | `{"status":"done"}`; values `todo`, `in_progress`, `done` |

### POST `/businesses/{id}/activities`
```json
{"period":"2026-11", "activity_type":"electricity", "quantity":500, "note":"Bill November"}
```
`activity_type` can be `electricity` (kWh) or `diesel` (litres). Stored records include **a snapshot of the factor and source used when the record was created**, avoiding silent changes if factors are later updated. More than one record per month/type is allowed (e.g., two meter bills).

### PUT `/businesses/{id}/production`
```json
{"period":"2026-11", "product_name":"Plastic bottles", "units":1000}
```
MVP assumes a **single homogeneous product type** in each month. For multiple product types, Member 3/4 should agree on a justified emission allocation method before displaying emissions per product.

### GET `/businesses/{id}/summary?period=2026-11`
With 500 kWh, 30 L diesel, 1,000 identical products:
```json
{
  "business_id": 1,
  "period": "2026-11",
  "total_kg_co2e": 431,
  "breakdown_kg_co2e": {"electricity":350, "diesel":81},
  "scopes_kg_co2e": {"scope_2":350, "scope_1":81},
  "records_count": 2,
  "production": {"id":1,"period":"2026-11","product_name":"Plastic bottles","units":1000},
  "operational_kg_co2e_per_unit": 0.431,
  "contains_demo_factors": true,
  "warning": "Not an audited carbon footprint; factor placeholders may be in use."
}
```
The operational intensity is **not a full life-cycle product carbon footprint**.

## Error format
All handled errors return `{"error":"reason"}` with HTTP 400 (invalid data), 401 (not logged in), 404 (not found / not owned), or 409 (duplicate email). Missing/invalid JWT tokens are rejected by the auth library.

## Integration responsibility
- **Member 1, frontend:** consumes `/calculate`, `/businesses`, `/activities`, `/summary`, `/trends`, `/missions`.
- **Member 3, AI/OCR:** produces verified bill values and uses `/activities` to save them. Reads `/activities` and `/production` to calculate electricity-per-product changes; `/trends` provides monthly emissions summaries. Must provide sourced and appropriate factors before claiming real emission estimates.
- **Member 4, reports:** reads `/summary`, `/activities`, `/emission-factors`, and produces PDF / passport. Reports should display the period, factors, sources, calculation boundary, and demo warnings.

For the final production system, add rate limiting, refresh-token rotation, password recovery, audit logging, migrations, secure deployment settings and validated emission factors. This starter is designed for a hackathon demonstration, not certified reporting.
