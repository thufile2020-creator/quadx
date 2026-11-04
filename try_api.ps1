# On Windows PowerShell. Start server with python app.py first.
# WARNING: uses a demo account / demo password. Local development only!
$base = "http://127.0.0.1:5000/api"
$randomEmail = "demo_" + [guid]::NewGuid().ToString("N").Substring(0, 8) + "@example.test"
$registered = Invoke-RestMethod -Uri "$base/auth/register" -Method Post -ContentType 'application/json' -Body (@{
    name = "Factory Owner"; email = $randomEmail; password = "DemoPass123!"
} | ConvertTo-Json)
$headers = @{ Authorization = "Bearer $($registered.access_token)" }
$business = Invoke-RestMethod -Uri "$base/businesses" -Method Post -Headers $headers -ContentType 'application/json' -Body (@{
    name = "Sample Supplier"; industry = "Manufacturing"; city = "Chennai"
} | ConvertTo-Json)
$id = $business.business.id
$activity = Invoke-RestMethod -Uri "$base/businesses/$id/activities" -Method Post -Headers $headers -ContentType 'application/json' -Body (@{
    period = '2026-11'; activity_type = 'electricity'; quantity = 500; note = 'Sample electricity bill'
} | ConvertTo-Json)
Invoke-RestMethod -Uri "$base/businesses/$id/activities" -Method Post -Headers $headers -ContentType 'application/json' -Body (@{
    period = '2026-11'; activity_type = 'diesel'; quantity = 30
} | ConvertTo-Json)
Invoke-RestMethod -Uri "$base/businesses/$id/production" -Method Put -Headers $headers -ContentType 'application/json' -Body (@{
    period = '2026-11'; product_name = 'Plastic bottles'; units = 1000
} | ConvertTo-Json)
$summary = Invoke-RestMethod -Uri "$base/businesses/$id/summary?period=2026-11" -Method Get -Headers $headers
Write-Host "Business ID: $id"
Write-Host "Total demo emissions (kg CO2e): $($summary.total_kg_co2e)"
Write-Host "Per-product demo emissions (kg CO2e): $($summary.operational_kg_co2e_per_unit)"
