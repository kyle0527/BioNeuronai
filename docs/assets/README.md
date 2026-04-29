# Visual Evidence Assets

This directory is the public evidence shelf for README visuals and demo artifacts.

## Required Assets

| Asset | Target file | How to produce | Status |
|---|---|---|---|
| Architecture diagram | `architecture.mmd` and exported `architecture.png` | Render Mermaid with GitHub or `mmdc` | Source ready |
| TinyLLM inference flow | `tinyllm_inference_flow.mmd` and exported `tinyllm_inference_flow.png` | Render Mermaid with GitHub or `mmdc` | Source ready |
| CLI + Dashboard demo | `demo_30s.gif` | Record `docker compose up api`, status curl, dashboard | TODO |
| Equity curve | `equity_curve.png` | Run fixed walk-forward backtest and export matplotlib chart | TODO |
| Drawdown curve | `drawdown.png` | Same backtest run as equity curve | TODO |
| Signal vs price | `signal_vs_price.png` | Plot model signal timestamps over BTCUSDT close | TODO |

## Recording Checklist

1. Start API: `docker compose up api`.
2. Verify API: `curl http://localhost:8000/api/v1/status`.
3. Open dashboard: `docker compose up frontend`.
4. Capture 30 seconds: API startup, status response, dashboard first view.
5. Save the final GIF as `docs/assets/demo_30s.gif`.

Do not publish performance charts until the command, dataset range, commit SHA, and generated files can be reproduced.
