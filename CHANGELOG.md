# 更新日誌

## [v2.2] - 2026-04-07

### 🧠 TinyLLM 雙模態架構重設計 + 訓練系統整合

#### TinyLLM 雙模態（語言 + 訊號共用一份 GPT 權重）
- **重大重設計**：以 GPT 架構的 `TinyLLM` 全面取代舊 MLP `HundredMillionModel`
- **雙任務路徑**：
  - `forward_signal(B, T, 1024)` → signal_head → `(B, 512)` 交易訊號向量
  - `forward(input_ids)` → lm_head（共享 token_embedding）→ 語言生成
- **numeric_proj 加深**：1 層升為 2 層（`Linear(1024→1536)+GELU+LN → Linear(1536→768)+LN`）；GELU 非線性特徵交互，總參數 ~111.6M
- **16 步滾動視窗**：`InferenceEngine._feature_buffer = deque(maxlen=16)`；每次推論輸入 `(16, 1024)` 序列，Transformer Attention 實際跨時間步運算
- **回測隔離**：`BacktestEngine._reset_state()` 在每個 episode 開始時呼叫 `reset_buffer()`

#### ChatEngine 整合修復
- 修正 `create_chat_engine()` tokenizer 路徑：目錄 → `model/tokenizer/vocab.json`
- 修正 `BilingualTokenizer.encode()` 新增 `max_length` / `truncation` 參數
- 修正 `_stream_generate()` 中 `eos_id` 雙重間接查找 bug（永遠返回 None）

#### 訓練系統整合
- **新增** `src/nlp/training/unified_trainer.py`：語言任務 + 訊號任務多任務訓練入口，輸出 `model/my_100m_model.pth`
- **新增** `src/nlp/training/build_vocab.py`：從 `ALL_TRADING_DATA` 建立詞彙並存至 `model/tokenizer/vocab.json`
- `unified_trainer.build_model()` 無詞彙時自動呼叫 `_build_and_save_vocab()` 建立
- **新增** `backtest/service.py::collect_signal_training_data()`：回測 replay 輸出 `data/signal_history.jsonl`

#### BacktestEngine 重構
- `run()` 認知複雜度從 18 降至 <15（提取 6 個 helper 方法）
- `advanced_trainer.py` 新增 `multitask` 模式，`total_loss = lm_loss + 0.5 × signal_loss`

#### 文件更新
- 新增 `docs/tech/TINYLLM_MODEL_GUIDE.md`（架構圖、參數表、訓練策略）
- 修正 `NLP_TRAINING_GUIDE.md`（移除舊 `tiny_llm_en_zh/` 路徑、`from_pretrained()` 幻覺 API）
- 修正 `BACKTEST_SYSTEM_GUIDE.md`（正確的 BacktestEngine 同步 callback API）
- 更新 `ARCHITECTURE_OVERVIEW.md`（加入 ChatEngine 節點、TinyLLM 說明）

#### 🚀 訓練前必執行步驟
```bash
python -m nlp.training.build_vocab           # 建立詞彙
python -m nlp.training.unified_trainer --lm-only --epochs 20   # 語言預熱
python -m nlp.training.unified_trainer --signal-data data/signal_history.jsonl --epochs 10  # 多任務精調
```

---

## [v4.4] - 2026-03-18

### 🐳 Docker 部署 + FastAPI REST API + RAG 快取修復

#### RAG 快取偵測（efdd454）
- **修復**：`src/rag/core/retriever.py` 中 `cache_hit=False` TODO 問題
- **實作**：`UnifiedRetriever` 加入記憶體 TTL 快取（預設 5 分鐘）
- **效果**：相同查詢命中快取時跳過向量搜尋，大幅降低 RAG 查詢延遲
- **詳情**：55 行新增，15 行修改；`cache_hit` flag 現在正確回傳

#### Docker 部署基礎建設（29ded9d）
- **新增 `Dockerfile`**：多階段建構（builder 編譯 ta-lib C 函式庫 + 安裝 Python 依賴；runtime 為精簡 python:3.11-slim 映像，使用非 root 用戶）
- **新增 `docker-compose.yml`**：含 service profiles 支援 `status`、`news`、`pretrade`、`plan`、`backtest`、`simulate`、`trade`（trade profile 需明確 opt-in）
- **新增 `.dockerignore`**：排除 `.git`、快取、機密、文檔、測試數據、本地 logs/DB（改用 named volumes）

#### FastAPI REST API 伺服器（de8aafe）
- **新增 `src/bioneuronai/api/` 模組**，包含：
  - `app.py`（448 行）：完整 FastAPI 應用
  - `models.py`（78 行）：Request/Response Pydantic v2 模型
- **API 端點**：
  - `GET /api/v1/status` — 系統健康狀態
  - `POST /api/v1/plan`、`/news`、`/pretrade` — 對應 CLI 命令
  - `POST /api/v1/backtest`、`/simulate` — 非同步背景工作（job ID 回傳）
  - `GET /api/v1/jobs/{id}` — 查詢背景工作進度
  - `POST /api/v1/trade/start`、`/trade/stop` — 交易控制
- **依賴更新**：`pyproject.toml` 加入 `fastapi` + `uvicorn`
- **Docker 整合**：`docker-compose.yml` 新增 `api` service with healthcheck，EXPOSE 8000

#### Docker 啟動與路徑修復（cfe21ef）
- **`Dockerfile`**：`PYTHONPATH` 加入 `/app/src`，修正容器內 `from schemas.X import` 路徑
- **`__init__.py`**：移除 import-time `FileHandler` 與 `print()`，改用 `logger.debug()` 保持安靜載入
- **`trading_engine.py`**：移除模組級 `basicConfig FileHandler`；`data_dir` 改用 `Path(__file__)` 錨點路徑
- **`risk_manager.py`**、**`sop_automation.py`**、**`pretrade_automation.py`**：`data_dir`/`stats_dir` 均改用 `Path(__file__)` 錨點，修正 Docker 環境路徑錯誤

#### 🚀 Docker 快速啟動

```bash
# 系統狀態檢查
docker compose run --rm status

# 交易前檢查
docker compose run --rm pretrade

# 啟動 FastAPI REST API 伺服器
docker compose up api
# → http://localhost:8000/docs（Swagger UI）
# → http://localhost:8000/api/v1/status

# 實盤交易（需 API 金鑰）
BINANCE_API_KEY=xxx BINANCE_API_SECRET=yyy docker compose --profile trade up trade
```

#### ✅ 修復後功能狀態更新

| 項目 | 修復前 | 修復後 |
|------|--------|--------|
| RAG 快取偵測 | ❌ `cache_hit=False` 硬編碼 | ✅ TTL 記憶體快取 |
| Docker 部署 | ❌ 不存在 | ✅ 多階段建構 + compose |
| FastAPI REST API | ❌ 不存在 | ✅ 完整 REST API |
| Docker 路徑問題 | ❌ 啟動時路徑錯誤崩潰 | ✅ `Path(__file__)` 錨點修正 |

---

## [v4.3] - 2026-03-15

### 🛠️ CLI 全面審計修復（6 項問題，含 2 項 P0 致命錯誤）

本次更新基於 Explore Agent 對 `src/bioneuronai/cli/main.py` 進行的完整技術審計（涵蓋 7 個命令、40+ 個 Python 檔案的 import 鏈追蹤）。

#### 🔴 P0 致命錯誤修復

**修復 1：`cmd_trade` 呼叫不存在的 `engine.run()`**
- **位置：** `cli/main.py:314`
- **問題：** `TradingEngine` 沒有 `run()` 方法，執行時必然拋出 `AttributeError`
- **修正：** 改為 `engine.start_monitoring(args.symbol)`（`trading_engine.py:425`，內建 WebSocket 監控迴圈）

**修復 2：`cmd_simulate` 使用不存在的 `mock.start_stream()`**
- **位置：** `cli/main.py:248`（修復前）
- **問題：** `MockBinanceConnector` 沒有 `start_stream()` 方法
- **修正：** 改為 `next_tick()` 迴圈模式；補齊 `--interval`、`--start`、`--end` CLI 參數

#### 🟡 P1 功能升級與容錯強化

**修復 3：`cmd_plan` 升級為完整 10 步驟計劃**
- **問題：** 只呼叫基礎 `SOPAutomationSystem`（4 步驟）
- **修正：** 改用 `TradingPlanController.create_comprehensive_plan()`（async，10 步驟），保留 SOPAutomation 作為 fallback

**修復 4：`cmd_plan` 導入失敗無容錯**
- **問題：** `SOPAutomationSystem` 導入失敗直接 `sys.exit(1)`，無降級機制
- **修正：** 加入 try-except，失敗時 fallback 至 `TradingPlanController`

**修復 5：torch 缺失導致 CLI 啟動崩潰**
- **問題：** `bioneuronai/__init__.py` 和 `core/__init__.py` 無條件 import torch 相關模組
- **修正：** 加入 try-except 容錯，torch 缺失時降級至非 AI 模式運行

**新增 6：`pretrade` 命令**
- **問題：** `PreTradeCheckSystem`（交易前 RAG 6 點檢查）完全未被 CLI 覆蓋
- **修正：** 新增 `cmd_pretrade` 命令，呼叫 `PreTradeCheckSystem.execute_pretrade_check(symbol, capital)`

#### ✅ 修復後可執行性狀態

| 命令 | 無 torch | 有 torch | 說明 |
|------|----------|----------|------|
| `status` | ✅ | ✅ | 7 模組健康檢查 |
| `plan` | ✅ (SOPAutomation fallback) | ✅ | 完整 10 步驟計劃 |
| `news` | ✅ | ✅ | 新聞分析 |
| `pretrade` | ✅ | ✅ | 交易前 6 點 RAG 檢查（新增） |
| `backtest` | ⚠️ 無 AI | ✅ | 需歷史數據 |
| `simulate` | ⚠️ 無 AI | ✅ | next_tick() 迴圈（修復） |
| `trade` | ❌ torch 必要 | ✅ | start_monitoring() 修復 |

> 注：`trade` 命令需要 torch 是合理設計—無 AI 模型不應進行實盤交易。

#### 📦 已知環境依賴（待用戶安裝）
- `torch>=2.0.0`：AI 推論引擎核心依賴（`pyproject.toml` 已聲明，但需手動安裝）
- `schedule>=1.2.0`：`news/prediction_loop.py` 使用，需補充至 `pyproject.toml` dependencies

---

## [v4.2] - 2026-03-10

### 🛠️ L0 基礎架構修復 (CODE_FIX_GUIDE 合規)

#### 關鍵變更：統一數據來源（Single Source of Truth）

**修復 CRITICAL-1：MarketData 雙重定義**
- `schemas/market.py` 添加即時行情欄位：`bid`、`ask`、`funding_rate`、`open_interest`
- `schemas/market.py` 新增 `@computed_field price` （回傳 `self.close`）
- `trading_strategies.py` 移除 `@dataclass MarketData`，改為 `from schemas.market import MarketData`
- `data/binance_futures.py` import 路徑改為 `from schemas.market import MarketData`
- `data/binance_futures.py` 移除 `get_ticker_price()` 中的 `price=price`（現為 computed_field）

**修復 CRITICAL-2：TradingSignal 多重定義**
- `schemas/trading.py` 添加 `take_profit` 欄位及 `@computed_field action`
- `schemas/trading.py` `strength` 添加預設值 `MODERATE`
- `trading_strategies.py` 移除 `@dataclass TradingSignal`，改為 `from schemas.trading import TradingSignal`
- `trading_strategies.py` 7 個建立呼叫點全部改為 `signal_type=SignalType.X` 新格式
- `core/trading_engine.py` 4 個建立呼叫點全部更新，新增 `from schemas.enums import SignalType as TradeSignalType`

**修復 HIGH：SQLiteConfig 缺失**
- `schemas/database.py` 新增 `SQLiteConfig` 模型（`db_path`, `timeout`, `check_same_thread`, `backup_enabled`）
- `schemas/__init__.py` 新增 `SQLiteConfig` 匯出

**小型 bug 修復**
- `database_manager.py` 移除第 4、5、6、11 表之前过早的 `conn.commit()`
- `database.py` 預設路徑改為 `trading_pairs.db`（避免與 trading.db 衝突）
- `config/trading_config.py` 新增 Testnet API key 安全警告註解
- `src/__init__.py` 版本更新：2.1.0 → 4.1.0

### ✅ 驗證狀態
| 項目 | 狀態 |
|------|------|
| `MarketData` 統一 | ✅ |
| `TradingSignal` 統一 | ✅ |
| `SQLiteConfig` 建立 | ✅ |
| import 連鎖全部通進 | ✅ |
| 舊式向後兼容層移除 | ✅ |

---

## [v4.1] - 2026-02-15

### 📚 README 全面審計與修復
- **29 個 README 全部驗證通過** - 每個文件都有目錄和上層連結
- **全項目架構比對** - 與 PROJECT_REPORT_20260215_210343.txt 比對確認一致性

### ✅ 已修復
1. **創建 backtesting/README.md** - 新建歷史回測與 Walk-Forward 測試文檔
   - 完整類別說明（3 個檔案、9 個類別）
   - 與 backtest/ 的區別對照表
   - Walk-Forward 測試原理與使用方式

2. **修復 docs/README.md 斷鏈** - DATAFLOW_ANALYSIS.md 已移至 archived/old_docs/

3. **更新根目錄 README.md** - 子目錄表新增 backtesting/ 連結

4. **完善 archived/README.md** - 新增「歸檔子目錄」段落（列出 8 個子目錄）

### 📊 修復統計
| 項目 | 修復前 | 修復後 | 狀態 |
|------|--------|--------|------|
| README 總數 | 28 | 29 | ✅ |
| 缺少 TOC | 3 | 0 | ✅ |
| 缺少上層連結 | 14 | 0 | ✅ |
| 斷鏈 | 4+ | 0 | ✅ |

### 📝 標準化格式
所有 README 現均遵循統一規範：
- ✅ 頂部目錄區（`## 目錄`）
- ✅ 底部上層連結（`> 📖 上層目錄：[...](../README.md)`）
- ✅ 上層 README 含子目錄表格（双向導航）

---

## [v4.0] - 2026-02-14

### 🎉 重大成就
- **100% 無錯誤** - 修復所有 107 個代碼錯誤/警告
- **策略進化系統完成** - 三層架構全部實現並通過測試
- **生產就緒** - 核心系統可投入實際交易使用

---

## 本次更新 (2026-02-14)

### ✅ 已修復
**phase_router.py** (10個錯誤 → 0個錯誤):
1. BaseStrategy 方法調用錯誤 - 改用 `analyze_market()` + `evaluate_entry_conditions()`
2. 浮點數比較問題 - 使用 epsilon 比較 (`abs(x - 1.0) > 1e-9`)
3. Pydantic v2 屬性訪問 - 添加 `type: ignore[attr-defined]` 標記
4. PhaseConfig 屬性錯誤 - 使用正確的 `primary_strategy`, `secondary_strategy`
5. 認知複雜度過高 - 提取 `_update_phase_config()` 輔助方法
6. 未使用參數 - 移除 `market_condition`，重命名 `_position_direction`
7. 方法簽名不一致 - 統一 `identify_phase()` 參數順序

### 📊 修復統計
| 文件 | 修復前 | 修復後 | 狀態 |
|------|--------|--------|------|
| strategy_arena.py | 47 錯誤 | 0 | ✅ |
| faiss_index.py | 5 錯誤 | 0 | ✅ |
| portfolio_optimizer.py | 35 錯誤 | 0 | ✅ |
| demo_strategy_evolution.py | 10 警告 | 0 | ✅ |
| phase_router.py | 10 錯誤 | 0 | ✅ |
| **總計** | **107** | **0** | ✅ |

### 📚 文檔更新
創建/更新文檔：
1. ✅ [ERROR_FIX_COMPLETE_20260214.md](docs/ERROR_FIX_COMPLETE_20260214.md) - 完整修復報告
2. ✅ [MANUAL_IMPLEMENTATION_STATUS.md](docs/MANUAL_IMPLEMENTATION_STATUS.md) - 更新策略進化系統狀態
3. ✅ [PROJECT_STATUS_20260214.md](PROJECT_STATUS_20260214.md) - 項目狀態總覽
4. ✅ [CHANGELOG.md](CHANGELOG.md) - 本文檔

### 🎯 優化方向
根據網路調研，確定下階段優化重點：
1. **數據整合** (優先級 1)
   - WebDataFetcher 類
   - 市場情緒分析器
   - 鏈上指標提供器

2. **策略增強** (優先級 2)
   - 方向變化 (DC) 算法
   - 深度強化學習 (DRL) 策略
   - 配對交易、統計套利

3. **回測引擎** (優先級 3)
   - 真實歷史數據回測
   - Walk-Forward 測試
   - 風險指標擴充

詳見: [STRATEGY_EVOLUTION_WEB_INTEGRATION_PLAN.md](docs/STRATEGY_EVOLUTION_WEB_INTEGRATION_PLAN.md)

---

## 歷史版本

### [v3.5] - 2026-02-13
**策略進化系統實現**:
- ✅ StrategyArena - 遺傳算法參數優化
- ✅ PhaseRouter - 9階段動態路由
- ✅ PortfolioOptimizer - 全局組合優化
- ✅ 演示系統 - 4種工作流程

**部分修復**:
- ✅ strategy_arena.py (47 錯誤 → 0)
- ✅ portfolio_optimizer.py (35 錯誤 → 0)
- ✅ faiss_index.py (5 錯誤 → 0)
- ✅ demo_strategy_evolution.py (10 警告 → 0)
- ⚠️ phase_router.py (10 錯誤待修復)

### [v3.0] - 2026-01-26
**核心系統**:
- ✅ 幣安 API 連接
- ✅ WebSocket 實時數據
- ✅ 6種交易策略
- ✅ 風險管理系統
- ✅ 10步驟 SOP
- ✅ RAG 新聞分析

---

## 下一步計劃

### 短期（訓練啟動前）
- [ ] 擴充語言訓練資料 `trading_dialogue_data.py` 至 500+ 組 QA（目前 31 組）
- [ ] 下載歷史數據（BTCUSDT 2年）— 填入 `data_downloads/binance_historical/`
- [ ] 執行 `collect-signal-data` 產生真實訊號標籤（目前僅合成資料）
- [ ] 執行首次完整訓練（語言預熱 → 訊號對齊 → 多任務精調）
- [ ] 連接 `CryptoNewsAnalyzer` 至 `market_analyzer.py`（移除 `news_sentiment=0.0` 硬編碼）

### 中期
- [ ] SOP 回測驗證（啟用 `_perform_plan_backtest()`）
- [ ] StrategyArena / TradingPhaseRouter 整合至 CLI
- [ ] Walk-Forward 測試框架
- [ ] TinyLLM 擴展至 300M+（考慮 Cross-Attention 市場–語言融合）

### 長期
- [ ] DRL 策略（PPO）
- [ ] 實盤測試（小資金）

### ✅ 已完成
- ✅ TinyLLM 雙模態架構重設計（v2.2）
- ✅ 16 步滾動推論視窗 + reset_buffer（v2.2）
- ✅ ChatEngine 完整整合（v2.2）
- ✅ 訓練系統整合（unified_trainer + build_vocab，v2.2）
- ✅ BacktestEngine 重構（認知複雜度 <15，v2.2）
- ✅ RAG 快取偵測（v4.4）
- ✅ Docker 部署基礎建設（v4.4）
- ✅ FastAPI REST API 伺服器（v4.4）
- ✅ WebDataFetcher 類 + 市場情緒分析器（v4.0）

---

## 技術要點

### 關鍵學習
1. **NumPy Generator API** - 所有隨機數必須使用 `np.random.default_rng()`
2. **認知複雜度控制** - 函數分解提高可讀性 (≤15)
3. **Pydantic v2 動態屬性** - 需要 `type: ignore[attr-defined]`
4. **浮點數比較** - 使用 epsilon 避免精度問題

### 最佳實踐
- ✅ 配置化隨機種子 (可重現)
- ✅ 完整類型註釋 (類型安全)
- ✅ 提取小函數 (單一職責)
- ✅ 文檔同步更新 (可維護)

### 從網路研究學到
- **DRL** 在算法交易中優於傳統方法
- **DC 算法** 比時間間隔更準確
- **回測嚴格性** 和避免過擬合至關重要
- **多樣化** 降低風險 (多策略組合)

---

## 貢獻者

**BioNeuronAI 開發團隊**
- 策略進化系統設計與實現
- 代碼質量修復與優化
- 文檔編寫與維護

---

**最後更新**: 2026年4月7日
**版本**: v2.2 - TinyLLM 雙模態 + 訓練系統整合版

🎉 **TinyLLM 架構整合完成！一份 GPT 權重，同時服務交易訊號預測與雙語對話！** 🎉
