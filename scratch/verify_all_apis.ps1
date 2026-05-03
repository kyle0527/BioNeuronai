# BioNeuronAI Full API Verification Script

$baseUrl = "http://localhost:8000"

Write-Host "============================================================"
Write-Host "BioNeuronAI API Complete Verification"
Write-Host "============================================================"

# 1. STATUS
Write-Host "`n[1/8] GET /api/v1/status"
try {
    $r = Invoke-RestMethod -Uri "$baseUrl/api/v1/status"
    Write-Host "  all_ok=$($r.all_ok)  version=$($r.version)"
    Write-Host "  PASS: $(if($r.all_ok){'YES'}else{'NO - not all_ok'})"
} catch { Write-Host "  FAIL: $_" }

# 2. CATALOG
Write-Host "`n[2/8] GET /api/v1/backtest/catalog"
try {
    $r = Invoke-RestMethod -Uri "$baseUrl/api/v1/backtest/catalog?symbol=BTCUSDT&interval=1h"
    $cnt = $r.data.dataset_count
    Write-Host "  dataset_count=$cnt  start=$($r.data.datasets[0].start_date) end=$($r.data.datasets[0].end_date)"
    Write-Host "  PASS: $(if($cnt -gt 0){'YES - data found'}else{'NO - empty'})"
} catch { Write-Host "  FAIL: $_" }

# 3. BACKTEST RUNS
Write-Host "`n[3/8] GET /api/v1/backtest/runs"
try {
    $r = Invoke-RestMethod -Uri "$baseUrl/api/v1/backtest/runs?limit=3"
    $cnt = $r.data.runs.Count
    Write-Host "  runs_returned=$cnt"
    Write-Host "  PASS: $(if($cnt -ge 0){'YES'}else{'NO'})"
} catch { Write-Host "  FAIL: $_" }

# 4. NEWS
Write-Host "`n[4/8] POST /api/v1/news"
try {
    $body = @{ symbol = "BTCUSDT"; max_items = 5 } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$baseUrl/api/v1/news" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 20
    Write-Host "  sentiment_score=$($r.data.sentiment_score)  articles=$($r.data.total_articles)"
    Write-Host "  PASS: YES (responded)"
} catch { Write-Host "  FAIL: $_" }

# 5. PRETRADE
Write-Host "`n[5/8] POST /api/v1/pretrade"
try {
    $body = @{ symbol = "BTCUSDT"; action = "long"; capital = 10000.0; leverage = 5 } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$baseUrl/api/v1/pretrade" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
    Write-Host "  is_approved=$($r.data.is_approved)  status=$($r.data.overall_assessment.status)"
    Write-Host "  PASS: YES (responded with assessment)"
} catch { Write-Host "  FAIL: $_" }

# 6. SIMULATE
Write-Host "`n[6/8] POST /api/v1/backtest/simulate"
try {
    $body = @{ symbol = "BTCUSDT"; interval = "1h"; balance = 10000; bars = 20; start_date = "2020-01-01"; end_date = "2020-01-03" } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$baseUrl/api/v1/backtest/simulate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30
    Write-Host "  run_id=$($r.data.run_id)  bars_processed=$($r.data.bars_processed)"
    Write-Host "  PASS: $(if($r.data.run_id){'YES - has run_id'}else{'NO - no run_id'})"
} catch { Write-Host "  FAIL: $_" }

# 7. STRATEGY-RUN
Write-Host "`n[7/8] POST /api/v1/backtest/strategy-run"
try {
    $body = @{ symbol = "BTCUSDT"; interval = "1h"; start_date = "2020-01-01"; end_date = "2020-01-03"; balance = 10000; warmup_bars = 10; execution_mode = "template_rules"; close_open_positions_on_end = $true } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$baseUrl/api/v1/backtest/strategy-run" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 120
    $execCnt = $r.data.result.executable_count
    Write-Host "  executable_count=$execCnt  mode=$($r.data.result.execution_mode)"
    Write-Host "  PASS: $(if($execCnt -gt 0){'YES - strategies ran'}else{'NO - none ran'})"
} catch { Write-Host "  FAIL: $_" }

# 8. PLAN
Write-Host "`n[8/8] POST /api/v1/plan"
try {
    $body = @{ symbol = "BTCUSDT" } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$baseUrl/api/v1/plan" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 60
    Write-Host "  success=$($r.success)"
    Write-Host "  PASS: YES (responded)"
} catch { Write-Host "  FAIL: $_" }

Write-Host "`n============================================================"
Write-Host "Verification Complete"
Write-Host "============================================================"
