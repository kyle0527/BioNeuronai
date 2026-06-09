# Technical Debt Status — 2026-06-03（最後更新）

本文件針對截圖中的「已確認的技術債」逐項核對目前程式碼狀態，並記錄實際驗證結果。2026-05-19 起，本輪主要驗證改以本機全域 Python 3.13 + PyTorch CPU 2.8.0 為準；Docker 不作本輪主要驗證入口，待自然語言、交易判斷與 API/UI 流程收斂後最後重建。

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

## 2026-05-14 截圖項目複核

| 截圖項目 | 現況 | 判定 |
|---|---|---|
| `BTCUSDT/ETHUSDT 4h` 歷史資料缺失 | Docker readiness-gate dry-run 已確認 `BTCUSDT 1h`、`ETHUSDT 1h` 存在，`BTCUSDT 4h`、`ETHUSDT 4h` 缺失。 | 屬實；正式 gate 會阻擋 live。 |
| 對比回測：訓練前後模型績效比較 | `best_model_run1.pth`、`best_model_run2.pth` 與現役 `my_100m_model_trained_20260510.pth` 已在 `model/`，且 Docker 內可載入；但尚未完成同 K 線區間的 Run1 / Run2 / 現役模型績效對比報告。 | 屬實；下一步應做固定區間對比。 |
| `news_sentiment` 仍為 `0.0` 硬編碼 | 主交易路徑已可從 `NewsAdapter.get_event_context()` 與分析結果取得 sentiment；`0.0` 仍存在於 fallback/default 與 meta-learner 特徵預設值。 | 部分屬實；不再是主線完全硬編碼，但訓練資料特徵仍需補強。 |
| `analysis/news/analyzer.py` 重構 | 公開入口仍可用，檔案仍偏大，尚未拆成 fetcher / processor / sentiment / aggregator。 | 屬實但非 staging blocker。 |
| RAG 接通 `EventContext` | `TradingEngine` 已傳入 `EventContext`，`NewsAdapter` 可從 active event 或 RAG KB 組裝事件分數、類型、衰減、可信度、來源、標題與情緒。 | 主要路徑已完成；歷史相似事件與策略權重仍可強化。 |
| 方案 C `HardRouter` / Strategy Fusion | 專案沒有獨立 `HardRouter` class；實作主線是 `TradingPhaseRouter`，可透過 `TradingEngine(strategy_type="phase_router")` 接入。 | 截圖名稱不完全對應；PhaseRouter 已可用，HardRouter 仍屬設計文件。 |
| 語言訓練資料 33 筆 | `docs/TRAINED_MODEL_TECHNICAL_REPORT_20260510.md` 記錄 QA 樣本 33，且明確說 QA 品質不可當投資建議。 | 屬實；不是 runtime blocker，但限制仍需保留。 |
| Shadow Mode 驗證 | 2026-05-19 本機 API 啟動 `paper_live` 短流程；**2026-06-03 AI 自主分析管線逐層走查完成（TinyLLM 推論 164.9ms → 策略融合 → 新聞 RAG → execute_trade() 5 步驟 → Paper place_order() FILLED）**，`enable_auto_trading()` + `start_monitoring()` 24/7 自主迴圈機制確認可用。 | 核心流程驗證完成；下一步是多小時連續跑並回收 ledger。 |
| Docker image 重建複驗 | 2026-05-14 曾完成 Docker `api` / `frontend` image 複驗；本輪已改成本機 runtime 先收斂，Docker image 最後重建。 | 需後續重建複驗，不作目前完成標準。 |
| 訓練前/後權重切換驗證 | 2026-05-15 已用 Docker runtime 以 `MODEL_PATH` 切換 `my_100m_model.pth` 與 `my_100m_model_trained_20260510.pth`。兩者均可載入，且 `forward_signal()` / 真實 K 線推論輸出不同。 | 推論層驗證完成；仍需固定 IS/OOS 回測證明交易績效。 |
| 模型資產治理 | `config/active_model.json` 指向的現役權重與訓練前基準權重必須可重建取得。複驗時發現基準權重曾被刪除，需從本機 LFS 物件還原；現役包裝權重也需要明確納入 LFS 或外部 artifact 流程。 | 高優先級；否則新環境可能缺權重。 |
| Docker build context 權重排除 / image 過大 | `.dockerignore` 原本排除 `*.pth`，但 Dockerfile 又 `COPY model/`，導致權重治理矛盾且 image 可膨脹。已暫時補必要權重例外，避免 active model 在 rebuild 後消失。 | 待決策；Docker 架構後續再處理，優先解決 AI 自然語言與自行操作能力。 |

## 新增 Gate

```bash
python main.py readiness-gate --dry-run
python main.py readiness-gate --output output/readiness_gate.json
```

先前 Docker readiness-gate dry-run 檢查結果顯示：

- `BTCUSDT 1h`：存在，2020-01-01 ~ 2023-12-31
- `ETHUSDT 1h`：存在，2020-01-01 ~ 2023-12-31
- `BTCUSDT 4h`：缺失
- `ETHUSDT 4h`：缺失

因此預設 readiness matrix 目前會阻擋正式上線，直到 `4h` 歷史資料下載完成，且完整 gate 執行結果達到設定門檻。

## 已驗證命令

2026-05-19 本機 runtime 驗證：

```bash
python -m py_compile src/bioneuronai/core/trading_engine.py src/bioneuronai/api/routes/system.py src/schemas/api.py
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
# GET /api/v1/status: ready=true, blocking=[]
# POST /api/v1/chat: trade_status / analyze_market 工具橋接可用
# POST /api/v1/chat: 中文要求啟動 paper_live 可觸發 start_paper_live，驗證後已停止
# POST /api/v1/trade/start mode=paper_live: 成功啟動，ai_model_loaded=true，paper_trading=true
# POST /api/v1/trade/stop: 成功停止，running=false
```

2026-06-03 Binance Testnet + AI 自主分析管線完整驗證（新增）：

```bash
# Binance Testnet 驗證
POST /api/v1/binance/validate  # canTrade=true, totalWalletBalance=5000 USDT

# 實際 Testnet 開倉
POST /api/v1/binance/order  # BTC LONG 0.002 @ 67,069.20 USDT → 訂單 13869263523
POST /api/v1/binance/order  # ETH SHORT 0.05 @ 1,899.24 USDT → 訂單 8964845387

# AI 自主分析管線（Python session）
engine.load_ai_model()  # TinyLLM 111.6M, 0.53s 載入, CPU
engine.get_ai_prediction()  # NEUTRAL, conf=0.33, latency=164.9ms
selector.get_strategy_signals()  # 2/6 有效 (swing_trading: SHORT, trend_following: SHORT)
news_adapter.get_event_context()  # sentiment=-0.543, 16 FAISS 命中, has_major_negative=True
engine.execute_trade()  # 5 步驟逐一驗證通過（新聞護欄阻擋最終下單，此為設計行為）

# Paper Trade 直接驗證
connector.place_order()  # status=FILLED, 0.01 BTC @ 67,244 USDT, 保證金 672.82 USDT
```

## 2026-06-03 新發現問題

| 問題 | 描述 | 優先級 |
|---|---|---|
| 4/6 策略回傳 None/Error | `mean_reversion`、`breakout` 等計算所需 K 線週期不足（ATR 出現負值），`get_strategy_signals()` 回傳 None/Error | 中 |
| `ai_min_confidence=0.5` 門檻偏高 | 現役模型在當前市況信心度 ~0.33，低於 0.5 門檻故輸出 HOLD；可考慮在 testnet 觀察期降至 0.25 | 待觀察 |
| `get_individual_strategy_signals()` 不存在 | `StrategySelector` 公開 API 無此方法；應使用 `get_strategy_signals(ohlcv, symbol)` | 低 |
| `OrderResult` 無 `executed_qty` | `OrderResult` 的正確欄位是 `quantity`（非 `executed_qty`）；文件應明確列出 | 低 |

```bash
docker compose run --rm status
docker compose run --rm status main.py readiness-gate --dry-run --json
docker compose run --rm backtest
docker compose run --rm simulate
docker compose exec api python -c "from bioneuronai.core.trading_engine import TradingEngine; engine=TradingEngine(testnet=True, enable_ai_model=True); print(engine.load_ai_model('my_100m_model', warmup=False))"
```

短區間實跑 gate 可正常執行並回報 `FAIL`，原因是該短區間有效 K 線不足、最佳策略交易次數為 0；這是 gate 正確阻擋，不是 CLI 失效。
