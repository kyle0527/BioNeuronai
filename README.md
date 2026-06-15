# BioNeuronAI

[![Python](https://img.shields.io/badge/python-3.13-blue)](pyproject.toml)
[![License](https://img.shields.io/github/license/kyle0527/BioNeuronai)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/kyle0527/BioNeuronai)](https://github.com/kyle0527/BioNeuronai/commits/main)

> 以 Binance 虛擬 API 為訓練場的自我成長 AI 交易系統。交易即訓練，每筆決策都記錄並用於更新模型。
>
> **套件版本**：v2.1（`pyproject.toml`）｜**最後更新**：2026-06-15

---

## 目錄

1. [系統定位](#系統定位)
2. [快速啟動](#快速啟動)
3. [雙執行主線](#雙執行主線)
4. [主線 A：TradingEngine 流程](#主線-atradingengine-流程)
5. [模組現況](#模組現況)
6. [待完成缺口](#待完成缺口)
7. [開發進度時間線](#開發進度時間線)
8. [技術規格](#技術規格)
9. [目錄結構](#目錄結構)
10. [設定](#設定)
11. [授權](#授權)

---

## 系統定位

BioNeuronAI 不是傳統的「預測模型」——它是一個在虛擬交易中不斷自我學習的活體系統。

| 傳統交易 AI | BioNeuronAI |
|---|---|
| 離線訓練一次，靜態部署 | 交易即訓練，每筆都學習 |
| 忘記歷史極端事件 | 極端行情/爆倉永久記憶 |
| 黑盒子輸出 | 每次決策完整快照可審計 |
| 只看數字 | 數值 + 新聞 + K 線圖三模態輸入（建設中） |

---

## 快速啟動

```bash
# 安裝
pip install -e .

# 啟動 API
uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000

# 盤前檢查
python main.py pretrade --symbol BTCUSDT --action long

# 主線 A：Paper trading（WebSocket 即時，完整學習閉環）
python main.py trade --paper-live --paper-balance 10000

# 主線 A：只看信號（不下單）
python main.py trade --symbol BTCUSDT

# 主線 B：自主規劃（單輪建議）
python main.py autonomous --mode advisor --symbol BTCUSDT
```

---

## 雙執行主線

系統有兩條**平行**的執行路徑，文件與驗收時請先確認用的是哪一條：

| | **主線 A：TradingEngine** | **主線 B：AutonomousOperator** |
|---|---|---|
| CLI | `main.py trade [--paper-live]` | `main.py autonomous [--execute-paper]` |
| 驅動 | WebSocket 即時 tick | 定時規劃迴圈（`run_forever`） |
| 信號 | StrategySelector + InferenceEngine | Plan + Pretrade + Adaptation |
| 學習閉環 | ActionRecord → EpisodicMemory → LoRA | Decision Ledger → AdaptiveHub |
| LoRA 更新 | ✅（平倉觸發） | ❌（未接通） |

詳細對照見 [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) 第一節 1.4。

---

## 主線 A：TradingEngine 流程

```
市場 tick (WebSocket)
         │
         ▼
  _process_market_data()
         │
         ├─ VirtualAccount.update_price()        ← Paper trading：每 tick 更新，觸發 SL/TP 檢查
         ├─ NewsAdapter.get_event_context()       ← 最近新聞事件分數
         │
         ▼
  generate_trading_signal()
         │
         ├─ T0: ActionRecord 建立（features + logits 快照）
         │
         ├─ _generate_strategy_signal()
         │       └─ StrategySelector.get_actionable_signal()
         │               └─ 5 個子策略 + Meta-Learner 融合
         │               └─ generate_fusion_signal()：新聞 direction_bias 方向框架（minimal）
         │               └─ event_score 非對稱過濾（極端值攔截逆勢）
         │
         ├─ InferenceEngine.predict()            ← 若 AI 模型已載入
         │       └─ TinyLLM v1 (1024 → 512 維)
         │
         └─ _fuse_signals()                      ← 策略 70% + AI 25% + 新聞 event_score 5%
                  │
                  ▼
         _handle_trading_signal()
                  │
                  ├─ auto_trade=False → 只記錄，不執行（預設）
                  └─ auto_trade=True  → execute_trade()
                           │
                           └─ T1: ActionRecord 進場快照

出場（SL/TP/強平 自動觸發）
         │
         └─ VirtualAccount._on_position_closed callback
                  │
                  └─ notify_trade_closed()
                           └─ T2: ActionRecord 出場快照 → EpisodicMemory → LoRA 更新
```

---

## 模組現況

### 核心交易主線（已可運行）

| 模組 | 檔案 | 狀態 |
|---|---|---|
| 交易引擎 | `core/trading_engine.py` | ✅ 可運行，WebSocket 驅動 |
| 策略選擇器 | `strategies/selector/` | ✅ 正式主線 |
| 策略融合 | `strategies/strategy_fusion.py` | ✅ 5 種策略 + Meta-Learner |
| AI 推論 | `core/inference_engine.py` | ✅ TinyLLM v1，需手動載入模型 |
| 風控 | `risk_management/position_manager.py` | ✅ Kelly 倉位 + 回撤限制 |
| 虛擬帳戶 | `trading/virtual_account.py` | ✅ Paper trading 完整支援 |
| 資料庫 | `data/database_manager.py` | ✅ SQLite，9 張表 |

### 新聞與事件

| 模組 | 實際角色 | 狀態 |
|---|---|---|
| CryptoNewsAnalyzer | 新聞抓取 + 情緒分析 | ✅ 已整合 |
| NewsAdapter | event_score + direction_bias | ✅ 已整合 |
| EventContract | 新聞事件衰減與驗證 | ✅ 已整合 |
| PreTradeCheckSystem | RAG 風控攔截（下單前） | ✅ 已整合 |
| **新聞方向框架** | `generate_fusion_signal()` 攔截逆勢共識 | ✅ minimal 版（2026-06-12） |
| **新聞時序聚合** | 多事件加權方向偏好 | 🧩 P1 待擴充 |

> 新聞同時扮演三種角色：**極端 event_score 過濾器**、**StrategyFusion 方向框架**（minimal）、**Pretrade RAG 攔截**。`TradingEngine._fuse_signals()` 仍用 event_score 加權，尚未改用 direction_bias。

### 自我學習層（主線 A 已接通）

| 模組 | 檔案 | 狀態 |
|---|---|---|
| TinyLLM v2 | `src/nlp/tiny_llm_v2.py` | 🧩 架構完成，未接通推論引擎 |
| Action Record | `core/action_record.py` | ✅ T0/T1/T2 全部接通 |
| EpisodicMemory | `memory/episodic_memory.py` | ✅ 熱緩衝 + 冷金庫完成 |
| OnlineLearner | `core/online_learner.py` | ✅ LoRA 微更新器完成 |
| VirtualAccount 平倉回調 | `trading/virtual_account.py` | ✅ SL/TP/強平 自動觸發 T2 |
| 多目標 Reward | `core/reward.py` | ✅ 盈虧 + 時間效率 + 信心校準 + 風控紀律 |

### 自適應閉環（學習 → 決策回饋）

| 模組 | 檔案 | 狀態 |
|---|---|---|
| 自適應中樞 | `core/adaptive_hub.py` | ✅ 策略×幣對 EWMA 績效 → 動態策略權重，JSON 持久化 |
| 平倉 → 權重回饋 | `core/trading_engine.py` | ✅ notify_trade_closed 自動更新中樞並重注入 selector |
| 自主持續迴圈 | `planning/autonomous_operator.py` | ✅ run_forever：結算 → 規劃 → 執行 → ledger 回寫 |
| 自我修正規則 | `planning/adaptation_controller.py` | ✅ 連敗/回撤/學習狀態 → 降風險或暫停 |
| 卡單自動平倉 | `autonomous_operator._check_stale_positions` | ✅ 超限反向 reduce-only 強制出場（2026-06-12） |

### 回測與驗證

| 模組 | 狀態 |
|---|---|
| Backtest 子系統 | ✅ `backtest/` 可獨立運行 |
| Walk-forward 驗證 | ✅ 架構建立 |
| 歷史資料 RL 訓練管線 | ✅ `training/rl_trainer.py`（2026-06-12） |

---

## 待完成缺口

> 標記原則：✅ 完成｜🧩 擴充點｜❌ 未開始。完整清單見 [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) 第四、五節。

### P1 🧩 新聞時序聚合

`get_direction_bias()` minimal 版已接入 `generate_fusion_signal()`。剩餘：多事件時序加權，完成後將 `implemented_level` 改為 `"full"`。

### P3 🧩 TinyLLM v2 接上交易引擎

`InferenceEngine.enable_v2_mode()` 為誠實 stub，predict() 仍走 v1。剩餘：16×64 patch 特徵管線、SignalInterpreterV2、v2 訓練權重。

### P4 🧩 目標層級自動回饋

GoalTracker 每輪寫入 ledger；`recommended_risk_scale` 尚未自動回饋到風險參數。

### 自主迴圈已知限制

- 2026-06-15 已對齊：優先採 pretrade `quantity`、持倉檢查、calibrator 回填；`reflect` CLI + `--reflect-every`
- `reflection_loop` 樣本仍來自 EpisodicMemory（需主線 A 累積）
- 長時間連續 paper run 的權重漂移尚未驗證

商用化缺口（API 認證、監控告警、訂單重試、DB 索引等）見 PROJECT_STATUS 第五節。

---

## 開發進度時間線

| 日期 | 完成事項 |
|---|---|
| 2026-05-10 | TinyLLM 100M 模型訓練完成（Run2: 50 epoch, loss=3.85） |
| 2026-05-19 | Paper-live 虛擬執行層驗證完成 |
| 2026-06-05 | TinyLLM v2 架構設計（三模態 + MoE + 65 維全監督輸出） |
| 2026-06-05 | EpisodicMemory（熱緩衝 + 極端事件冷金庫）實作完成 |
| 2026-06-05 | ActionRecord T0/T1 接通交易引擎 |
| 2026-06-05 | OnlineLearner LoRA 微更新器實作完成 |
| 2026-06-07 | VirtualAccount 平倉回調接通，LoRA 在線學習迴路完整運作 |
| 2026-06-07 | SL/TP 每 tick 觸發修復 |
| 2026-06-11 | AdaptiveLearningHub、run_forever、多目標 reward |
| 2026-06-12 | 歷史 RL 訓練管線、卡單自動平倉、新聞 direction_bias 方向框架 |

---

## 技術規格

| 項目 | v1（現役） | v2（建設中） |
|---|---|---|
| 模型架構 | GPT-2, 12 層, embed=768 | 同骨幹 + MoE + 三模態 |
| 輸入 | 1024 維扁平向量 | 16 × 64 patch token + 文字 + 圖像 |
| 輸出 | 512 維（23 維有效，479 維空置） | 65 維全監督 |
| 可訓練參數 | 全部（無 LoRA） | 0.25%（LoRA，骨幹凍結） |
| 在線學習 | LoRA 微更新，每 100 筆觸發 | 同左（需主線 A） |
| 極端事件記憶 | EpisodicMemory 冷庫（JSONL） | 同左 |

---

## 目錄結構

```
src/
  bioneuronai/
    core/           # 交易引擎、推論、ActionRecord、OnlineLearner
    memory/         # EpisodicMemory（熱緩衝 + 冷金庫）
    strategies/     # 策略選擇器、策略融合、Meta-Learner
    analysis/       # 新聞分析、市場狀態、特徵工程
    data/           # Binance 連接器、資料庫、Paper trading
    risk_management/
    planning/
    training/       # 歷史 RL 訓練管線
    api/            # FastAPI routes
    cli/
  nlp/              # TinyLLM v1 + v2、LoRA、RAG
  rag/              # FAISS 向量索引、知識庫
  schemas/

docs/
  ARCHITECTURE_OVERVIEW.md    # 架構說明
  PROJECT_STATUS.md           # 當前進度（權威來源）
  manuals/                    # 操作手冊
  adr/                        # 架構決策紀錄

model/                        # 模型權重（Git LFS）
config/                       # 交易設定、API 金鑰環境變數
```

---

## 設定

```bash
# 必要環境變數（不寫在程式碼裡）
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"
export BINANCE_TESTNET="true"   # true = 測試網 / false = 主網

# 可選：GCP Secret Manager
export GCP_SECRET_MANAGER_ENABLED="1"
export GCP_PROJECT_ID="your_project"
```

詳細設定請見 [docs/manuals/17_ENVIRONMENT_VARIABLES.md](docs/manuals/17_ENVIRONMENT_VARIABLES.md)

---

## 授權

MIT License