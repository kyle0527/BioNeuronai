# BioNeuronAI

[![Python](https://img.shields.io/badge/python-3.13-blue)](pyproject.toml)
[![License](https://img.shields.io/github/license/kyle0527/BioNeuronai)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/kyle0527/BioNeuronai)](https://github.com/kyle0527/BioNeuronai/commits/main)

> 以 Binance 虛擬 API 為訓練場的自我成長 AI 交易系統。交易即訓練，每筆決策都記錄並用於更新模型。

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

# Paper trading（虛擬交易）
python main.py trade --paper-live --paper-balance 10000

# 查看 AI 訊號（不下單）
python main.py trade --symbol BTCUSDT
```

---

## 實際架構（準確描述，非設計目標）

```
市場 tick (WebSocket)
         │
         ▼
  _process_market_data()
         │
         ├─ NewsAdapter.get_event_context()     ← 最近新聞事件分數
         │
         ▼
  generate_trading_signal()
         │
         ├─ T0: ActionRecord 建立（features + logits 快照）
         │
         ├─ _generate_strategy_signal()
         │       └─ StrategySelector.get_actionable_signal()   ← 主信號來源
         │               └─ 5 個子策略 + Meta-Learner 融合
         │               └─ event_score 作為非對稱過濾器
         │
         ├─ InferenceEngine.predict()            ← 若 AI 模型已載入
         │       └─ TinyLLM v1 (1024 → 512 維)
         │
         └─ _fuse_signals()                      ← 策略 70% + AI 25% + 新聞 5%
                  │
                  ▼
         _handle_trading_signal()
                  │
                  ├─ auto_trade=False → 只記錄，不執行（預設）
                  └─ auto_trade=True  → execute_trade()
                           │
                           └─ T1: ActionRecord 進場快照

出場（目前需人工觸發 notify_trade_closed）
         │
         └─ T2: ActionRecord 出場快照 → 推入 EpisodicMemory → LoRA 更新
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

### 新聞與事件（已建立，角色為過濾器）

| 模組 | 實際角色 | 狀態 |
|---|---|---|
| CryptoNewsAnalyzer | 新聞抓取 + 情緒分析 | ✅ 已整合 |
| NewsAdapter | 提供 event_score 給策略層 | ✅ 已整合 |
| EventContract | 新聞事件衰減與驗證 | ✅ 已整合 |
| PreTradeCheckSystem | RAG 風控攔截（下單前） | ✅ 已整合 |
| **新聞作為主信號** | **規劃中，尚未實作** | ⚠️ 缺口 |

> 目前新聞是「過濾器」（攔截逆勢信號），不是「主信號」（建議方向）。這是設計上待解決的缺口。

### 自我學習層（已建立，尚未完全接通）

| 模組 | 檔案 | 狀態 |
|---|---|---|
| TinyLLM v2 | `nlp/tiny_llm_v2.py` | ✅ 三模態 + MoE 架構完成 |
| Action Record | `core/action_record.py` | ✅ T0/T1 已接通 |
| EpisodicMemory | `memory/episodic_memory.py` | ✅ 熱緩衝 + 冷金庫完成 |
| OnlineLearner | `core/online_learner.py` | ✅ LoRA 微更新器完成 |
| **T2 出場觸發** | `notify_trade_closed()` | ❌ 未有呼叫方，需修正 |
| **TinyLLM v2 接上交易引擎** | — | ❌ 尚未完成 |

### 回測與驗證

| 模組 | 狀態 |
|---|---|
| Backtest 子系統 | ✅ `backtest/` 可獨立運行 |
| Walk-forward 驗證 | ✅ 架構建立 |
| **歷史資料 RL 訓練管線** | ❌ 規劃中，尚未實作 |

---

## 已知問題與待完成缺口

### P0 — 必須修正才能讓在線學習運作

1. **`notify_trade_closed()` 無呼叫方**：T2 從未被觸發，整個 LoRA 在線更新迴路目前是死程式碼。需要在 VirtualAccount 的持倉平倉事件中自動呼叫。

2. **新聞角色錯置**：新聞應作為主要信號建議方，目前只是過濾器。

### P1 — 架構層待連接

3. **TinyLLM v2 尚未接上交易引擎**：新模型建立了，但 `inference_engine.py` 仍用 v1 的 1024→512 路徑。

4. **歷史資料 RL 訓練管線缺失**：用歷史 K 線做強化學習驗證的路徑尚未建立。

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

---

## 技術規格

| 項目 | v1（現役） | v2（建設中） |
|---|---|---|
| 模型架構 | GPT-2, 12 層, embed=768 | 同骨幹 + MoE + 三模態 |
| 輸入 | 1024 維扁平向量 | 16 × 64 patch token + 文字 + 圖像 |
| 輸出 | 512 維（23 維有效，479 浪費） | 65 維全監督 |
| 可訓練參數 | 全部（無 LoRA） | 0.25%（LoRA，骨幹凍結） |
| 在線學習 | 無 | LoRA 微更新，每 100 筆觸發 |
| 極端事件記憶 | 無 | 永久冷庫（JSONL） |

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
    api/            # FastAPI routes
    cli/
  nlp/              # TinyLLM v1 + v2、LoRA、RAG
  rag/              # FAISS 向量索引、知識庫
  schemas/

docs/
  ARCHITECTURE_OVERVIEW.md    # 架構說明
  PROJECT_STATUS.md           # 當前進度（本文件的詳細版）
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

**最後更新**: 2026-06-06
