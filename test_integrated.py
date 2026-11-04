"""Integration tests of code supplied by all four teammates."""
from io import BytesIO


def test_member3_calculator_and_detective(client):
    calc = client.post('/api/ai/calculate', json={
        'electricity_kwh': 500, 'diesel_litres': 30,
    })
    assert calc.status_code == 200
    assert calc.json['total_kg_co2e'] == 431.0
    detective = client.post('/api/ai/detect', json={'records': [
        {'electricity_kwh': 1000, 'products': 500},
        {'electricity_kwh': 1100, 'products': 550},
        {'electricity_kwh': 1500, 'products': 500},
    ]})
    assert detective.status_code == 200
    assert detective.json['alert'] is True
    assert detective.json['change_percent'] == 50.0


def test_member3_txt_ocr(client):
    uploaded = client.post('/api/ai/scan', data={
        'bill': (BytesIO(b'Consumption in kWh: 850\n'), 'electric_bill.txt')
    }, content_type='multipart/form-data')
    assert uploaded.status_code == 200
    assert uploaded.json['extracted']['electricity_kwh'] == 850
    assert uploaded.json['needs_manual_review'] is True


def test_member4_report_pdf_from_db(client, auth, business_id):
    saved = client.post(f'/api/businesses/{business_id}/activities', headers=auth, json={
        'period': '2026-11', 'activity_type':'electricity','quantity':500,
        'note':'{"name":"Electricity bill","date":"2026-11-04"}',
    })
    assert saved.status_code == 201
    pdf = client.get(f'/api/reports/businesses/{business_id}/pdf', headers=auth)
    assert pdf.status_code == 200
    assert pdf.data.startswith(b'%PDF')
    assert pdf.mimetype == 'application/pdf'
    unauthorized = client.get(f'/api/reports/businesses/{business_id}/pdf')
    assert unauthorized.status_code == 401


def test_member4_preview(client):
    payload={
        'report_id':'TEST-2026',
        'business':{'name':'Demo','industry':'Manufacturing','location':'Chennai','supplier_id':'DEMO-1'},
        'period':{'start':'2026-11-01','end':'2026-11-30'},
        'activities':[{'id':'ELEC-1','source':'Electricity','scope':'Scope 2',
            'quantity':500,'unit':'kWh','emission_factor':0.7,'factor_unit':'kg CO2e/kWh',
            'factor_source':'DEMO ONLY','factor_year':2026,'evidence_file':'example.txt'}]
    }
    result=client.post('/api/reports/preview',json=payload)
    assert result.status_code == 200
    assert result.json['total_kg_co2e'] == 350.0
    assert 'NOT VERIFIED' in result.json['status']
