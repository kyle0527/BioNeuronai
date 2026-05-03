$ErrorActionPreference = 'Stop'

function Test-Endpoint {
    param ($Name, $Method, $Uri, $Body)
    Write-Host "--- Testing $Name ---"
    try {
        if ($Body) {
            $response = Invoke-RestMethod -Uri $Uri -Method $Method -Body $Body -ContentType "application/json" -TimeoutSec 60
        } else {
            $response = Invoke-RestMethod -Uri $Uri -Method $Method -TimeoutSec 60
        }
        $responseJson = $response | ConvertTo-Json -Depth 5 -Compress
        Write-Host "SUCCESS: $responseJson"
    } catch {
        Write-Host "FAILED: $_"
    }
}

Test-Endpoint "Status" "GET" "http://localhost:8000/api/v1/status"
Test-Endpoint "Catalog" "GET" "http://localhost:8000/api/v1/backtest/catalog"
Test-Endpoint "Dashboard" "GET" "http://localhost:8000/api/v1/dashboard"

Test-Endpoint "News" "POST" "http://localhost:8000/api/v1/news" '{"symbol":"BTCUSDT","max_items":3}'
Test-Endpoint "Pretrade" "POST" "http://localhost:8000/api/v1/pretrade" '{"symbol":"BTCUSDT","action":"long"}'
Test-Endpoint "Simulate" "POST" "http://localhost:8000/api/v1/backtest/simulate" '{"symbol":"BTCUSDT","interval":"1h","bars":20}'
Test-Endpoint "Runs" "GET" "http://localhost:8000/api/v1/backtest/runs?limit=3"

Write-Host "Tests finished."
