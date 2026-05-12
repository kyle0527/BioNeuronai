# BioNeuronai Full Operation Validation Report
> Date: 2026-05-11  
> Scope: trained checkpoint integrated runtime, CLI, REST API, WebSocket, and frontend build.  
> Exclusion: real order submission and real position close were intentionally not executed.

## Summary

This validation used the trained checkpoint registered in `config/active_model.json`:

```text
model/my_100m_model_trained_20260510.pth
```

Result: core trained-weight loading, signal inference, safe monitor-only trading flow, backtest/replay, strategy suite, signal sample collection, evolution, REST API, WebSocket, and frontend build are operational.

The main issue found during validation was fixed in `src/bioneuronai/core/inference_engine.py`: model warmup incorrectly called `model(dummy_input)` for signal-capable TinyLLM checkpoints during the benchmark loop. It now routes warmup through `forward_signal()` when the loaded model supports signal inference.

## Direct Operation Results

| Area | Operation | Result |
|---|---|---|
| Active trained model | `InferenceEngine(warmup=False).load_model("my_100m_model")` | Passed. Resolved to trained checkpoint and produced finite `(1, 512)` output. |
| Warmup after fix | `InferenceEngine(warmup=True).load_model("my_100m_model")` | Passed. Warmup latency measured on CPU. |
| CLI status | `python main.py status` | Passed. Core modules available. |
| CLI historical data | `python main.py backtest-data --symbol BTCUSDT --interval 1h` | Passed. BTCUSDT 1h historical data available for 2020-01-01 to 2023-12-31. |
| CLI backtest | `python main.py backtest ...` | Passed. Run id `20260511_000428_00a8ed7e`. |
| CLI simulate | `python main.py simulate ...` | Passed. Run id `20260511_000428_0dd54cef`. |
| CLI strategy suite | `python main.py strategy-backtest ...` | Passed. 10 templates executed, 0 failures. |
| CLI plan | `python main.py plan ...` | Passed. Plan id `plan_20260511_000506`, `execution_ready=true`. |
| CLI pretrade | `python main.py pretrade ...` | Controlled reject. Endpoint ran, but account-dependent risk step cannot complete without valid Binance Futures credentials. |
| CLI news | `python main.py news ...` | Passed with provider fallback. CryptoPanic free/public provider degraded, other feeds succeeded. |
| CLI signal data | `python main.py collect-signal-data ...` | Passed after warmup fix. 3 signal samples written. |
| CLI evolve | `python main.py evolve ...` | Passed. Best strategy score recorded in validation output. |
| CLI chat | piped prompt into `python main.py chat --language zh --symbol BTCUSDT` | Passed operationally. Response remained low-confidence by design. |

## API Validation

An isolated API service was started on `127.0.0.1:8020`; the existing service on port 8000 was not touched.

Validated REST endpoints: 24/24 passed or safely rejected where expected.

Covered endpoints:

```text
GET  /api/v1/status
POST /api/v1/binance/validate
POST /api/v1/news
GET  /api/v1/backtest/catalog
GET  /api/v1/backtest/inspect
POST /api/v1/backtest/simulate
POST /api/v1/backtest/run
POST /api/v1/backtest/strategy-run
GET  /api/v1/backtest/runs
POST /api/v1/pretrade
POST /api/v1/trade/start
GET  /api/v1/trade/status
POST /api/v1/trade/stop
POST /api/v1/training/start
GET  /api/v1/training
GET  /api/v1/training/{job_id}
GET  /api/v1/model/status
POST /api/v1/model/promote
POST /api/v1/chat
GET  /api/v1/dashboard
GET  /api/v1/risk/config
GET  /api/v1/data/catalog
GET  /backtest/ui
```

`POST /api/v1/trade/start` was executed only as:

```json
{
  "testnet": true,
  "mode": "monitor_only",
  "auto_trade": false,
  "load_ai_model": true,
  "model_name": "my_100m_model"
}
```

The API log confirms the trained checkpoint was loaded by the trading engine:

```text
C:\D\E\BioNeuronai\model\my_100m_model_trained_20260510.pth
```

## WebSocket Validation

Validated WebSocket endpoints: 3/3 passed.

| Endpoint | First message |
|---|---|
| `/ws/dashboard` | Dashboard snapshot keys received. |
| `/ws/trade` | `price_update` received. |
| `/ws/analytics` | `portfolio_update` received. |

## Frontend Validation

Frontend commands executed in `frontend/devops-d`:

```text
npm run build
npm run lint
npm run dev -- --host 127.0.0.1 --port 5175
```

Results:

- Production build passed.
- ESLint passed with 7 existing Fast Refresh warnings in shared UI/context files.
- No TypeScript/Vite integration break was found for the current dashboard/API client changes.
- Vite dev server was started with `VITE_API_BASE_URL=http://127.0.0.1:8020`; `http://127.0.0.1:5175` returned HTTP 200. The temporary API and frontend processes were stopped after validation.

## Evidence Files

Validation artifacts:

```text
output/validation_api_summary_20260511.json
output/validation_ws_summary_20260511.json
output/validation_plan_20260511.json
output/validation_pretrade_20260511.json
output/validation_signal_samples_20260511.jsonl
output/validation_strategy_backtest_20260511.json
output/validation_evolve_20260511.json
output/validation_api_8020.log
output/validation_api_8020.err.log
output/validation_ui_api_8020.log
output/validation_ui_api_8020.err.log
output/validation_frontend_vite_5175.log
output/validation_frontend_vite_5175.err.log
```

Runtime backtest outputs were also generated under:

```text
backtest/runtime/20260511_*
```

## Remaining Gaps

1. Real order and close-position endpoints were not executed by request:
   - `POST /api/v1/orders`
   - `DELETE /api/v1/positions/{position_id}`

2. Binance account-dependent validation is not fully verified without valid Futures credentials:
   - `pretrade` executes and safely rejects.
   - `binance/validate` correctly reports missing credentials when none are injected.

3. Chat uses `model/tiny_llm_100m.pth`, not the promoted trading checkpoint. The trained trading checkpoint is integrated into signal inference and trading monitor paths, while chat QA quality remains low-confidence unless the chat model itself is trained or replaced.

4. News providers can degrade externally. During validation, CryptoPanic public/free access returned degraded responses, while fallback feeds still allowed news/pretrade flows to complete.

5. Windows console encoding produced a non-fatal `cp950` logging warning when emoji/log symbols were emitted. It did not stop the trading monitor or API validation.

## Conclusion

For the requested scope, the project is operational with the trained checkpoint loaded in the AI trading/signal path. The safe non-ordering workflows are verified end to end across CLI, API, WebSocket, and frontend build. The remaining blockers are credential-dependent production exchange checks and real order operations, which were intentionally excluded.
