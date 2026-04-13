# BioNeuronAI DevOps Dashboard

A high-performance developer operations dashboard for BioNeuronAI that enables rapid API testing, monitoring, and data inspection with minimal overhead and maximum efficiency.

## 🔌 API Connection

This dashboard connects to the **real BioNeuronAI API** at:
```
https://api.bioneuronai.com
```

### Configuration

The API base URL is configured in `src/lib/api.ts` and can be overridden using environment variables:

- **Default**: `https://api.bioneuronai.com`
- **Override**: Set `VITE_API_BASE_URL` in a `.env` file

Example `.env` file (optional):
```env
VITE_API_BASE_URL=https://api.bioneuronai.com
```

### Available Endpoints

- `GET /status` - System health and status
- `GET /news` - Latest news feed
- `POST /pretrade` - Pre-trade analysis
- `POST /chat` - AI chat interface
- `POST /trade/start` - Start trading operations
- `POST /trade/stop` - Stop trading operations
- `POST /backtest/*` - Backtesting operations

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
