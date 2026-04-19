# BioNeuronai 部署準備紀錄

> 更新日期：2026-04-17  
> 範圍：前端選型、部署前盤點、分析模組、策略模組、AI/模型主鏈、環境阻塞  
> 結論：目前可準備內部 staging / testnet 驗證；尚未達正式交易部署標準。

---

## 1. 本次決策

本次不再同時推進三個前端。部署前端先選定：

| 前端 | 狀態 | 決策 |
|------|------|------|
| `frontend/devops-d/` | 已修補並完成 build 驗證 | 作為第一個前端主線 |
| `frontend/admin-da/` | 保留原始碼，未進一步修補 | 暫緩 |
| `frontend/trading/` | 保留原始碼，未進一步修補 | 暫緩 |

選擇 `frontend/devops-d/` 的原因：

- 對應現有後端 API 較直接：`status`、`news`、`pretrade`、`backtest`、`chat`、`trade/start`、`trade/stop`。
- 比 `admin-da`、`trading` 少依賴尚未確認的 WebSocket 與高階後端端點。
- 適合先做部署前的系統監控、API 驗證與人工操作入口。

---

## 2. 已完成的前端更新

### `frontend/devops-d/`

已補齊 Vite build 需要的本地 library：

| 檔案 | 用途 |
|------|------|
| `frontend/devops-d/src/lib/utils.ts` | 提供 `cn()`，整合 `clsx` 與 `tailwind-merge` |
| `frontend/devops-d/src/lib/api.ts` | 統一 REST API client、endpoint helper、request logger hook 入口 |
| `frontend/devops-d/src/lib/RequestLoggerContext.tsx` | 提供 request logger context/provider |
| `frontend/devops-d/package-lock.json` | 鎖定 npm dependency 版本 |
| `frontend/devops-d/.gitignore` | 忽略 `.npm-cache` |

同時修正根目錄 `.gitignore`：

- 原本 `lib/`、`lib64/` 會誤忽略 `frontend/devops-d/src/lib/`。
- 已改成 `/lib/`、`/lib64/`，只忽略 repo root 的 Python venv 目錄。

### 驗證結果

在 `frontend/devops-d/`：

- `npm.cmd install --cache .npm-cache --ignore-scripts`：成功。
- `npm.cmd run build`：成功。
- Vite build 產出：
  - `dist/index.html`
  - `dist/assets/*.css`
  - `dist/assets/*.js`
- build 期間有 3 個 CSS optimizer warning，與 Tailwind/container query 解析有關，未阻擋 build。
- dev server 已可由 `http://127.0.0.1:5173` 回應 200。

後端 API 預設仍需在 `http://localhost:8000` 啟動。

---

## 3. 分析模組盤點

目前分析層不是空殼，主要能力已存在：

| 能力 | 代表位置 | 狀態 |
|------|----------|------|
| 新聞分析 | `src/bioneuronai/analysis/news/analyzer.py` | 主體完成，已接 `NewsDataFetcher` 與 RAG ingest |
| 關鍵字與事件評估 | `src/bioneuronai/analysis/keywords/`、`analysis/news/evaluator.py` | 可用，但事件時效學習仍需補強 |
| 特徵工程 | `src/bioneuronai/analysis/feature_engineering.py` | 主體完成 |
| 市場 regime | `src/bioneuronai/analysis/market_regime.py` | 主體完成 |
| daily report / SOP | `src/bioneuronai/analysis/daily_report/` | 可用，但 backtest 驗證步驟仍未完成 |
| pretrade 新聞檢查 | `src/bioneuronai/planning/pretrade_automation.py` | 已走 `NewsAdapter` / RAG 路徑，失敗時不做 legacy fallback |

仍需處理：

- `UnifiedRetriever.retrieve_for_trading()` 尚未成為 pretrade / strategy fusion 的正式消費入口。
- `strategy_fusion.py` 的 `EventContext` 還未完全由 RAG knowledge base 填充。
- daily report 尚未將每日報告寫回 knowledge base。
- `analysis/news/analyzer.py` 仍偏大，後續應拆分以降低維護成本。

分析模組部署判斷：可進入 staging 驗證，但不應視為正式交易前全部完成。

---

## 4. 策略模組盤點

正式交易主線目前是：

```text
TradingEngine
  -> StrategySelector
  -> AIStrategyFusion
  -> 基礎策略 signal
  -> risk / execution
```

已接主線：

- `src/bioneuronai/core/trading_engine.py`
- `src/bioneuronai/strategies/selector/core.py`
- `src/bioneuronai/strategies/strategy_fusion.py`

策略層現有能力：

| 能力 | 狀態 |
|------|------|
| 6 種基礎策略 | 策略本體存在 |
| StrategySelector | 已是正式主線 |
| AIStrategyFusion | 已接 StrategySelector / TradingEngine |
| StrategyArena | 已改用正式 replay，不再使用隨機假績效 |
| PortfolioOptimizer | 已改用 replay 聚合，但未接正式交易主線 |
| PhaseRouter | 框架存在，但未接正式 TradingEngine 主線 |
| RL Fusion Agent | 研究型能力，未接正式主線 |

仍需處理：

- PhaseRouter 與 `TradeSetup` 欄位對齊未完成。
- `PairTradingStrategy` 需要次資產資料，目前正式 replay 資料不足。
- 部分策略在目前 ETH replay 視窗尚未穩定觸發。
- 固定策略共同流程仍有 setup 驗證順序與出手率問題需驗證。

策略模組部署判斷：`StrategySelector + AIStrategyFusion` 可作 staging 主線；PhaseRouter / PortfolioOptimizer / RL agent 不列入第一階段部署範圍。

---

## 5. AI / 模型主鏈盤點

AI 主鏈分為兩層：

| 層級 | 位置 | 狀態 |
|------|------|------|
| 策略融合 AI | `strategies/strategy_fusion.py` | 已接正式策略主線 |
| PyTorch 推理模型 | `core/inference_engine.py` | 推理管線存在，但需 runtime 驗證 |

已存在能力：

- `FeaturePipeline` 建立 1024 維特徵。
- `InferenceEngine` 維持 16 步 rolling feature window。
- `ModelLoader` 可自動判斷 TinyLLM / legacy MLP checkpoint。
- `TradingEngine.load_ai_model("my_100m_model")` 是正式載入入口。

風險與缺口：

- `model/my_100m_model.pth` 是主交易模型，但仍依賴 `archived/pytorch_100m_model.py::HundredMillionModel` legacy 相容路徑。
- `model/tiny_llm_100m.pth` 本機存在，但目前未被 git 追蹤；乾淨部署環境可能缺 chat/NLP 權重。
- ✅ `strategy_fusion.py` `EventContext` dict/object 型別落差已修正（2026-04-19）：`_adjust_weights_by_event()` 與 `generate_fusion_signal()` 現已支援 dict→EventContext 自動轉換。
- 目前本機沒有 Python runtime，無法完成模型載入 smoke test。

AI 模組部署判斷：程式結構已有，但尚未完成模型載入、推論、latency、輸出品質的實跑驗收。

---

## 6. 環境與部署阻塞

目前本機狀態：

| 項目 | 狀態 | 影響 |
|------|------|------|
| Python | `python` / `py` 不可用 | 無法跑 CLI、pytest、API import、模型載入 |
| Docker CLI | 已安裝 | 可查版本 |
| Docker daemon | 未啟動或不可連線 | 無法 build / run backend container |
| Node/npm | 可用 | `frontend/devops-d` 已完成 install/build |
| 測試目錄 | 未找到正式 `tests/` | 部署前缺最小自動化驗收 |
| `.env` | 存在敏感憑證 | 不可提交或分享；若曾外流需輪換 |

Docker compose 仍需驗證：

- `logs/` 目錄目前不存在，但 `docker-compose.yml` 預設 bind `${LOGS_DIR:-./logs}`。
- Dockerfile 手動列 dependency，需確認與 `pyproject.toml` 完全一致。
- Docker build 尚未能在本機完成實測。

---

## 7. 部署前驗收門檻

### 內部 staging / testnet 前必做

1. 補可用 Python 或啟動 Docker daemon。
2. 執行 backend smoke：
   - `status`
   - `news`
   - `pretrade`
   - `backtest/simulate`
   - `chat`
3. 實測 `TradingEngine(enable_ai_model=True)` 初始化。
4. 實測 `load_ai_model("my_100m_model")`。
5. ✅ `EventContext` dict/object 型別落差已修正（2026-04-19）。
6. ✅ `logs/` 與 `data/` 已建立並納入 git；compose bind mount 可用（2026-04-19）。
7. 將 API CORS 從 `allow_origins=["*"]` 收斂為 staging 來源。
8. 建立最小 `tests/` 或 smoke script。

### 正式交易部署前必做

1. 回測矩陣至少涵蓋 BTCUSDT / ETHUSDT、多時間框架、足夠資料窗。
2. 明確策略通過門檻：max drawdown、profit factor、win rate、trade count。
3. 模型 artifact 建立 checksum 與交付來源。
4. 明確 testnet / mainnet 切換與防呆。
5. 交易 API 加入 auth / access control，不以公開 CORS 暴露。
6. 建立 runtime health、model health、news/RAG health 監控。

---

## 8. 時間估計

| 目標 | 預估 |
|------|------|
| 內部 staging / testnet | 3-5 個工作天，前提是 Python/Docker 環境可用 |
| 可宣稱分析/策略/AI 主鏈完成 | 2-4 週 |
| 正式 mainnet 自動交易 | 3-5+ 週，需視回測與風控驗收結果調整 |

目前不建議直接部署正式交易環境。

