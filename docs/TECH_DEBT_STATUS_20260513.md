# Technical Debt Status — 2026-05-13

本文件針對截圖中的「已確認的技術債」逐項核對目前程式碼狀態，並記錄本次修復。

## 結論

| 項目 | 判定 | 現況 / 本次處理 |
|------|------|-----------------|
| T3：`strategy_fusion.py` 的 `EventContext` 未從 RAG 知識庫完整填充 | 部分屬實，已修復 | `TradingEngine` 已會把 `NewsAdapter.get_event_context()` 傳入策略層，但 adapter 原本未在此路徑自動初始化事件評估器。本次補上初始化，並讓 `EventContext` 帶入事件分數、類型、衰減、可信度、來源、標題、情緒分數與 RAG metadata。 |
| T4：`analysis/news/analyzer.py` 過大 | 屬實，暫不阻塞 staging | 目前檔案約 1200 行，確實應拆為 fetcher / sentiment / aggregator，但現有公開入口穩定。此項屬中低優先級重構，不應在上線前混入大範圍搬移。 |
| T5：新聞抓取硬編碼 `hours=24`，缺少增量邏輯 | 截圖過期 | `CryptoNewsAnalyzer.analyze_news(symbol, hours=None)` 已有自適應時間窗、`news_fetch_state.json`、上次抓取時間與 overlap；`hours=24` 只剩範例 / 明確覆蓋用法。 |
| 策略層：`PhaseRouter` 未接正式 `TradingEngine` | 截圖過期 | `TradingEngine(strategy_type="phase_router")` 已可選接 `TradingPhaseRouter`，並在 `_generate_strategy_signal()` 先走 PhaseRouter。預設仍是 `fusion`。 |
| 策略層：`PortfolioOptimizer` 未接主線 | 屬實但非 live blocker | `StrategyPortfolioOptimizer` 是離線研究 / 優化器，已可用正式 replay 聚合評估，不應直接插入 live 交易主線。 |
| 策略層：`PairTradingStrategy` 需次資產資料 | 屬實，已有 replay 支援 | 單資產 fusion 主線刻意排除 PairTradingStrategy；`backtest/service.py` 已會為 pair template 載入 secondary OHLCV。live 主線若要啟用 pair trading，仍需獨立多資產資料流設計。 |
| 回測門檻：正式交易前需 BTC/ETH 多時間框架矩陣與通過門檻 | 屬實，已修復為 gate | 新增 `python main.py readiness-gate` 與 `config/trading_readiness_gate.json`，以 `backtest/` replay service 執行矩陣並輸出 `PASS` / `FAIL`；gate 路徑不會更新 Golden Profile。 |

## 新增 Gate

```bash
python main.py readiness-gate --dry-run
python main.py readiness-gate --output output/readiness_gate.json
```

目前本機資料檢查結果顯示：

- `BTCUSDT 1h`：存在，2020-01-01 ~ 2023-12-31
- `ETHUSDT 1h`：存在，2020-01-01 ~ 2023-12-31
- `BTCUSDT 4h`：缺失
- `ETHUSDT 4h`：缺失

因此預設 readiness matrix 目前會阻擋正式上線，直到 `4h` 歷史資料下載完成，且完整 gate 執行結果達到設定門檻。

## 已驗證命令

```bash
python -m py_compile src/schemas/rag.py src/rag/services/news_adapter.py backtest/readiness_gate.py backtest/__init__.py src/bioneuronai/cli/main.py
python main.py readiness-gate --dry-run --json
python main.py readiness-gate --symbols BTCUSDT --intervals 1h --start-date 2020-01-01 --end-date 2020-01-03 --json
```

短區間實跑 gate 可正常執行並回報 `FAIL`，原因是該短區間有效 K 線不足、最佳策略交易次數為 0；這是 gate 正確阻擋，不是 CLI 失效。
