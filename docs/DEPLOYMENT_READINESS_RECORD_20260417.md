# BioNeuronai 部署準備紀錄

> 更新日期：2026-04-17  
> 後續驗證：2026-04-18 / 2026-04-19 / 2026-04-22 / 2026-04-23
> 範圍：前端選型、部署前盤點、分析模組、策略模組、AI/模型主鏈、環境阻塞  
> 結論：目前可準備內部 staging / testnet 驗證；尚未達正式交易部署標準。
>
> 註記：本檔為 2026-04-17 當下的部署盤點快照。2026-04-21 之後已完成的程式修復與文件同步，請以 `README.md`、`docs/TECH_DEBT_AND_ROADMAP.md`、`docs/API_INTEGRATION_BASELINE.md` 與各子模組 README 作為現況依據。

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

- `model/my_100m_model.pth` 是主交易模型，checkpoint 仍是 legacy MLP 格式；相容模型類別已遷移到 `src/bioneuronai/models/legacy.py`，不再依賴 `archived/` 路徑。
- `model/tiny_llm_100m.pth` 本機存在，但目前未被 git 追蹤；乾淨部署環境可能缺 chat/NLP 權重。
- ✅ `strategy_fusion.py` `EventContext` dict/object 型別落差已修正（2026-04-19）：`_adjust_weights_by_event()` 與 `generate_fusion_signal()` 現已支援 dict→EventContext 自動轉換；`NewsAdapter.get_event_context()` 已回傳 `EventContext` 物件。
- 仍需補 pretrade / strategy fusion 的端到端事件調權測試，確認 RAG / news event context 實際消費鏈。
- 2026-04-18 已完成 `InferenceEngine(warmup=False).load_model("my_100m_model")` 實測，CPU 可載入 111.2M 參數模型。

AI 模組部署判斷：模型載入與單筆 mock 推論已通過；仍需用真實 K 線與策略主線做端到端驗收。

---

## 6. 環境與部署阻塞

目前本機狀態：

| 項目 | 狀態 | 影響 |
|------|------|------|
| Python | `Python 3.13.9` 可用 | 已可跑 CLI、pytest、API import、模型載入 |
| Docker CLI | 已安裝 | 可查版本 |
| Docker daemon | ✅ 可用（v29.4.0） | `docker compose build` / `up` 全通 |
| Node/npm | 可用 | `frontend/devops-d` 已完成 install/build |
| 測試目錄 | 已新增 `tests/test_smoke.py` | 2026-04-18 smoke tests 全部通過 |
| `.env` | 存在敏感憑證 | 不可提交或分享；若曾外流需輪換 |

Docker compose 已完成驗證：

- ✅ `logs/` 與 `data/` 目錄已建立並納入 git，bind mount 連同容器啟動已驗證。
- ✅ Dockerfile pip 清單補齊 `python-dotenv`、`regex`、`schedule`，与 `pyproject.toml` 已對齊。
- ✅ `docker compose build` 全部 8 個 images 建立成功（2026-04-22）。

---

## 7. 部署前驗收門檻

### 內部 staging / testnet 前必做

1. 啟動 Docker daemon，完成 Docker build / container healthcheck。
2. 執行 backend smoke：
   - `status`（2026-04-18 已通過）
   - `news`（2026-04-18 可執行，但 CryptoPanic 免費模式回 404 / 0 articles）
   - `pretrade`
   - `backtest/simulate`
   - `chat`
3. 實測 `TradingEngine(enable_ai_model=True)` 初始化。
4. `load_ai_model("my_100m_model")`（2026-04-18 已通過）。
5. ✅ `EventContext` dict/object 型別落差已修正（2026-04-19）；仍需補端到端事件調權測試。
6. ✅ `logs/` 與 `data/` 已建立並納入 git；啟動 Docker daemon 後需完成實際 bind mount / healthcheck 驗證。
7. 依 staging / production 實際網域設定 `ALLOWED_ORIGINS`。
8. 擴充 `tests/`，加入 API route、pretrade、backtest、model predict smoke。

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

---

## 10. 2026-04-22 Docker 部署驗收結果

| 項目 | 結果 | 備註 |
|------|------|------|
| Docker daemon | ✅ | v29.4.0 |
| `docker compose build` | ✅ | 8/8 images 成功 |
| `docker compose run --rm status` | ✅ | 7 模組 `[OK]`，版本 v2.1 |
| `docker compose run --rm pretrade` | ✅ | 5/5 步驟完整執行 |
| Binance 401 | 預期 | testnet key 未設定，不影響架構正確性 |
| `GET /api/v1/status` | ✅ | HTTP 200，`{"success":true,...}` |
| `GET http://localhost:3000` | ✅ | HTTP 200，前端 nginx 正常回應 |
| `python main.py chat --symbol BTCUSDT --language zh` | ✅ | 可完成一輪對話；目前多為低信心保守回應 |
| `POST /api/v1/chat` | ✅ | HTTP 200；回傳 `success=true`、conversation_id、latency_ms |
| `bioneuron-api` container | ✅ Started | port 8000 |
| `bioneuron-frontend` container | ✅ Started | port 3000；healthcheck 改走 `127.0.0.1`，避免容器內 `localhost -> ::1` 誤判 |

更新後判斷：**Docker 部署驗收完成**。內部 staging / testnet 端從連線面已可就緒。剩餘工作項：
- Binance testnet API key 設定（`.env` 補入）
- 正式 CORS origins / 交易 API auth 設定
- chat 權重品質與低信心回應仍需後續校正
- 長區間 replay / testnet 下持續觀察事件權重是否符合預期

---

## 11. 2026-04-23 後續部署與驗收更新

| 項目 | 結果 | 備註 |
|------|------|------|
| `frontend` healthcheck | ✅ 修正 | `docker-compose.yml` 改為 `wget http://127.0.0.1:80`，避免容器內 `localhost -> ::1` 誤判 |
| `docker compose ps` | ✅ | `bioneuron-api` 與 `bioneuron-frontend` 目前皆為 `healthy` |
| `python main.py chat --symbol BTCUSDT --language zh` | ✅ | 可完成一輪對話；目前多回低信心保守答案 |
| `POST /api/v1/chat` | ✅ | HTTP 200；回傳 `success=true`、`conversation_id`、`latency_ms` |
| Chat runtime bug | ✅ 修正 | `ChatEngine` 已改用 `HonestGenerator.generate_with_honesty()` |
| live event-context 消費鏈 | ✅ 驗證 | `news_adapter -> trading_engine -> selector -> strategy_fusion` smoke 已通過 |
| smoke tests | ✅ | `python -m pytest tests/test_smoke.py -q` = `23 passed` |

更新後判斷：

- Docker 啟動、API、前端、chat CLI、chat API、以及 live event-context 消費鏈都已完成基本驗收。
- 當前剩餘部署前阻塞已收斂為：
  - Binance testnet key 與帳戶權限
  - 正式環境的 CORS / auth 設定
  - chat 模型品質與低信心回應校正

---

## 9. 2026-04-18 後續驗證結果

| 項目 | 結果 | 備註 |
|------|------|------|
| Git 工作樹 | clean | 最新 commit `2b7cd6a` 已包含前端、文件與 smoke test 更新 |
| Python runtime | 通過 | `Python 3.13.9` |
| pytest smoke | 通過 | `python -m pytest tests/ -v`，6 passed |
| CLI status | 通過 | `python main.py status` 顯示核心模組 OK |
| API status handler | 通過 | FastAPI `TestClient` 呼叫 `/api/v1/status` 回 200 |
| CORS 預設 | 通過 | 預設 origins 為 localhost 白名單，不含 `*` |
| `frontend/devops-d` build | 通過 | `npm.cmd run build` 成功，仍有 3 個 CSS optimizer warning |
| 主交易模型載入 | 通過 | `my_100m_model.pth` CPU 載入成功，111.2M 參數 |
| mock AI predict | 通過 | 單筆 mock K 線推論成功，CPU latency 約 58ms |
| news CLI | 可執行但無資料 | CryptoPanic 免費模式回 404，結果為 0 articles |
| Docker compose config | 可展開 | 但會把 `.env` secrets 展開到輸出，不可分享原文 |
| Docker daemon | ✅ 通過 | v29.4.0，`bioneuron-api` + `bioneuron-frontend` 啟動成功 |

更新後判斷：Docker 阻塞已解除，pretrade / chat / live event-context 消費鏈 smoke 均已完成；主要剩餘阻塞為 Binance testnet key 與模型品質校正。
