# BioNeuronAI DevOps Dashboard

A high-performance developer operations dashboard for BioNeuronAI that enables rapid API testing, monitoring, and data inspection with minimal overhead and maximum efficiency.

## 🔌 API Connection

This dashboard connects to the local BioNeuronAI FastAPI server by default:
```
http://localhost:8000
```

### Configuration

The API base URL is configured in `src/lib/api.ts` and can be overridden using environment variables:

- **Default**: `http://localhost:8000`
- **Override**: Set `VITE_API_BASE_URL` in a `.env` file

Example `.env` file (optional):
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Available Endpoints

- `GET /api/v1/status` - System health and status
- `POST /api/v1/news` - Latest news feed
- `POST /api/v1/pretrade` - Pre-trade analysis
- `POST /api/v1/chat` - AI chat interface
- `POST /api/v1/trade/start` - Start trading operations
- `POST /api/v1/trade/stop` - Stop trading operations
- `GET /api/v1/backtest/catalog` - Backtest data catalog
- `GET /api/v1/backtest/inspect` - Backtest data inspection
- `POST /api/v1/backtest/simulate` - Backtest simulation
- `POST /api/v1/backtest/run` - Run replay backtest
- `GET /api/v1/backtest/runs` - List replay runs

## Current Project Status

As of 2026-04-17, this is the first frontend selected for deployment readiness work. `frontend/admin-da` and `frontend/trading` remain in the repository but are deferred until the backend endpoints and WebSocket paths they need are verified.

## 🚀 Features

- **System Status Monitor** - Real-time system health monitoring
- **API Playground** - Test any endpoint with custom JSON payloads
- **Chat Interface** - Interact with AI chat functionality
- **Trade Controls** - Start/stop trading operations
- **Backtest Operations** - Execute and monitor backtests
- **News Feed** - Monitor relevant news data
- **Pre-Trade Analysis** - Review pre-trade checks
- **Raw JSON Inspector** - View and copy all API responses

## 🧹 Just Exploring?
No problem! If you were just checking things out and don't need to keep this code:

- Simply delete your Spark.
- Everything will be cleaned up — no traces left behind.

## 📄 License For Spark Template Resources 

The Spark Template files and resources from GitHub are licensed under the terms of the MIT license, Copyright GitHub, Inc.
