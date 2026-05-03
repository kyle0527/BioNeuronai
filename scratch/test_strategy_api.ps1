$body = @{
    symbol = "BTCUSDT"
    interval = "1h"
    start_date = "2020-01-01"
    end_date = "2020-01-03"
    balance = 10000
    warmup_bars = 10
    execution_mode = "template_rules"
    close_open_positions_on_end = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/backtest/strategy-run" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120
$response | ConvertTo-Json -Depth 10
