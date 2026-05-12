# BioNeuronAI Operations Dashboard

`frontend/devops-d/` is the current primary UI for operating BioNeuronAI. It is no longer only an API playground: the first screen is the `Operations` view for runtime state, execution mode, model state, and paper-live account visibility.

## API Connection

Default API base URL:

```text
http://localhost:8000
```

For local development, Vite may run on `5173` or the next available port such as `5176`. The backend default CORS list allows `localhost` and `127.0.0.1` on ports `3000`, `8080`, and `5173-5180`.

Override API URL at build/dev time:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Main Views

| View | Purpose |
|---|---|
| `Operations` | Runtime overview, execution target, model status, trade control, pretrade, news |
| `Validation` | Backtest, data catalog, training/model operations |
| `Config` | System status and risk config |
| `Dev Tools` | API playground and request history |
| `Chat` | Bilingual AI chat with optional market context |

## Trading Modes

`TradeControlPanel` supports the backend modes below:

| Mode | Market data | Order execution | Notes |
|---|---|---|---|
| `monitor_only` | Testnet or selected connector | No automatic orders | AI model loads by default unless disabled |
| `paper_live` | Binance mainnet market data | Local virtual ledger only | No Binance order is sent; logs under `data/bioneuronai/trading/paper_live/` |
| `testnet_auto` | Binance testnet | Binance testnet orders | Requires testnet API credentials |
| `live_auto` | Binance mainnet | Real Binance mainnet orders | Requires `ALLOW_LIVE_TRADING=1` and confirm string |

## API Endpoints Used

- `GET /api/v1/status`
- `GET /api/v1/dashboard`
- `GET /api/v1/trade/status`
- `POST /api/v1/trade/start`
- `POST /api/v1/trade/stop`
- `GET /api/v1/model/status`
- `POST /api/v1/model/promote`
- `POST /api/v1/training/start`
- `GET /api/v1/training`
- `GET /api/v1/backtest/catalog`
- `GET /api/v1/backtest/inspect`
- `POST /api/v1/backtest/simulate`
- `POST /api/v1/backtest/run`
- `GET /api/v1/backtest/runs`
- `GET /api/v1/data/catalog`
- `GET /api/v1/risk/config`
- `PUT /api/v1/risk/config`
- `POST /api/v1/news`
- `POST /api/v1/pretrade`
- `POST /api/v1/chat`

## Local Development

```powershell
cd frontend/devops-d
npm install
npm run dev
```

Open the URL printed by Vite. If `5173` is occupied, Vite may choose another allowed port such as `5176`.

## Verification

Use the real running app/API paths rather than separate test fixtures:

```powershell
npm run build
npm run lint
```

Then open the Vite or Docker URL and confirm `Operations Overview` shows API health, runtime mode, execution target, and model loaded state.
