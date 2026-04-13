# Backend Integration Guide

This dashboard is designed to connect to a FastAPI backend. Below are the expected API responses for proper integration.

## API Endpoint Specifications

### 1. System Status
**Endpoint**: `GET /api/v1/status`

**Expected Response**:
```json
{
  "status": "healthy",
  "modules": {
    "database": true,
    "trading_engine": "online",
    "data_feed": true,
    "ai_service": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Backtest Catalog
**Endpoint**: `GET /api/v1/backtest/catalog`

**Expected Response**:
```json
{
  "dataset_count": 42,
  "root": "/data/backtests",
  "datasets": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
}
```

### 3. Backtest Runs
**Endpoint**: `GET /api/v1/backtest/runs?limit=10`

**Expected Response**:
```json
{
  "runs": [
    {
      "id": "run_123456",
      "symbol": "BTCUSDT",
      "interval": "1h",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "balance": 10000,
      "status": "completed",
      "created_at": "2024-01-15T08:00:00Z",
      "result": { "pnl": 1250, "trades": 45 }
    }
  ],
  "total": 156
}
```

### 4. News Sentiment
**Endpoint**: `POST /api/v1/news`

**Request Body**:
```json
{
  "symbol": "BTCUSDT"
}
```

**Expected Response**:
```json
{
  "symbol": "BTCUSDT",
  "sentiment": "positive",
  "score": 0.72,
  "highlights": [
    "Strong institutional buying pressure",
    "Technical breakout above resistance",
    "Positive regulatory news"
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 5. Pretrade Checklist
**Endpoint**: `POST /api/v1/pretrade`

**Request Body**:
```json
{
  "symbol": "BTCUSDT",
  "action": "buy"
}
```

**Expected Response**:
```json
{
  "symbol": "BTCUSDT",
  "action": "buy",
  "checks": [
    {
      "name": "Liquidity Check",
      "status": "pass",
      "message": "Sufficient liquidity available"
    },
    {
      "name": "Risk Limits",
      "status": "pass",
      "message": "Within risk parameters"
    },
    {
      "name": "Technical Indicators",
      "status": "warning",
      "message": "RSI approaching overbought"
    }
  ],
  "overall_status": "pass"
}
```

### 6. Backtest Inspect
**Endpoint**: `GET /api/v1/backtest/inspect`

**Expected Response**:
```json
{
  "symbol": "BTCUSDT",
  "data_points": 720,
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "warnings": [
    "Low trading volume detected on weekends"
  ]
}
```

### 7. Backtest Simulate
**Endpoint**: `POST /api/v1/backtest/simulate`

**Request Body**:
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "balance": 10000,
  "warmup_bars": 50,
  "bars": 1000
}
```

**Expected Response**:
```json
{
  "symbol": "BTCUSDT",
  "trades_count": 45,
  "final_balance": 11250,
  "pnl": 1250,
  "pnl_percentage": 12.5,
  "max_drawdown": 8.3
}
```

### 8. Backtest Run
**Endpoint**: `POST /api/v1/backtest/run`

**Request Body**: Same as Simulate

**Expected Response**:
```json
{
  "run_id": "run_789012",
  "status": "pending",
  "message": "Backtest queued for execution"
}
```

### 9. Chat
**Endpoint**: `POST /api/v1/chat`

**Request Body**:
```json
{
  "message": "What's the market outlook for BTC?",
  "conversation_id": "conv_1234567890",
  "language": "auto",
  "symbol": "BTCUSDT"
}
```

**Expected Response**:
```json
{
  "response": "Based on current market analysis, BTC shows bullish momentum with strong support at $42,000. Technical indicators suggest potential upward movement, but watch for resistance at $48,000.",
  "conversation_id": "conv_1234567890",
  "latency_ms": 1250,
  "confidence": 0.85
}
```

### 10. Trade Start
**Endpoint**: `POST /api/v1/trade/start`

**Expected Response**:
```json
{
  "status": "started",
  "message": "Trading operations initiated successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 11. Trade Stop
**Endpoint**: `POST /api/v1/trade/stop`

**Expected Response**:
```json
{
  "status": "stopped",
  "message": "Trading operations halted successfully",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### 12. Analytics Portfolio
**Endpoint**: `GET /api/v1/analytics/portfolio`

**Expected Response**:
```json
{
  "portfolio": [
    {
      "symbol": "BTCUSDT",
      "quantity": 0.5,
      "avg_price": 42000.00,
      "current_price": 45000.00,
      "value": 22500.00,
      "pnl": 1500.00,
      "pnl_percent": 7.14,
      "allocation": 45.0
    },
    {
      "symbol": "ETHUSDT",
      "quantity": 5.0,
      "avg_price": 2200.00,
      "current_price": 2400.00,
      "value": 12000.00,
      "pnl": 1000.00,
      "pnl_percent": 9.09,
      "allocation": 24.0
    }
  ],
  "total_value": 50000.00,
  "total_pnl": 5000.00,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### 13. Analytics Trades
**Endpoint**: `GET /api/v1/analytics/trades?limit=100`

**Expected Response**:
```json
{
  "trades": [
    {
      "id": "trade_123456",
      "timestamp": "2024-01-15T10:30:00Z",
      "symbol": "BTCUSDT",
      "type": "buy",
      "quantity": 0.1,
      "price": 42000.00,
      "pnl": 300.00,
      "status": "completed"
    },
    {
      "id": "trade_123457",
      "timestamp": "2024-01-15T09:15:00Z",
      "symbol": "ETHUSDT",
      "type": "sell",
      "quantity": 2.0,
      "price": 2400.00,
      "pnl": -150.00,
      "status": "completed"
    }
  ],
  "total": 248
}
```

### 14. Analytics Performance
**Endpoint**: `GET /api/v1/analytics/performance?days=30`

**Expected Response**:
```json
{
  "performance": [
    {
      "date": "2024-01-01",
      "pnl": 1250.00,
      "daily_pnl": 250.00,
      "value": 51250.00
    },
    {
      "date": "2024-01-02",
      "pnl": 1450.00,
      "daily_pnl": 200.00,
      "value": 51450.00
    }
  ],
  "metrics": {
    "total_return": 12.5,
    "win_rate": 65.4,
    "sharpe_ratio": 1.8,
    "max_drawdown": 8.3
  }
}
```

## CORS Configuration

Your FastAPI backend should allow requests from the frontend origin:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

All endpoints should return proper HTTP status codes:

- **200**: Success
- **400**: Bad Request (validation error)
- **401**: Unauthorized
- **404**: Not Found
- **500**: Internal Server Error

Error response format:
```json
{
  "detail": "Error message here",
  "code": "ERROR_CODE"
}
```

## Testing Without Backend

The dashboard will show appropriate error toasts if the backend is unavailable. You can test the UI by:

1. Starting the frontend only (it will attempt to connect to `http://localhost:8000`)
2. Observing error toasts when API calls fail
3. Using browser DevTools Network tab to see attempted requests

For full functionality, implement the FastAPI backend with the endpoints specified above.
