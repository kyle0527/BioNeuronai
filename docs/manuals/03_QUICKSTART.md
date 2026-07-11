# BioNeuronai v2.1 快速開始指南

> **套件版本**：v2.1（`pyproject.toml`）  
> **更新日期**：2026-07-11  
> **方向權威**：[`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)  
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)  
> **建議環境**：本機全域 Python 3.13。Docker 留到本機預設流程穩定後再重建。  
> **驗收**：真實 CLI／Paper／歷史回測；**不要**用 pytest 當完成標準。

---

## 目錄

1. [安裝與依賴](#1-安裝與依賴)
2. [設定環境變數](#2-設定環境變數)
3. [現行方向與雙執行主線（必讀）](#3-現行方向與雙執行主線必讀)
   - [3.1 你現在該先做什麼](#31-你現在該先做什麼)
   - [3.2 雙入口](#32-雙入口共用模型與-paper-執行)
4. [驗證系統狀態](#4-驗證系統狀態)
5. [核心功能驗證（建議順序）](#5-核心功能驗證建議順序)
   - [步驟 A News](#步驟-a觀察市場news)
   - [步驟 B Plan](#步驟-b啟動高階計劃plan)
   - [步驟 C Pretrade](#步驟-c盤前檢查pretrade)
   - [步驟 D 自主單輪](#步驟-d自主單輪主線-b先確認規劃鏈)
   - [步驟 E 自主 paper（核心）](#步驟-e預設-ai-自主-paper本階段核心主線-b)
   - [步驟 F trade paper-live](#步驟-f即時-tick-paper主線-at0t2-觀測)
   - [步驟 G 歷史回測](#步驟-g長期選用歷史資料回測)
   - [步驟 H Chat](#步驟-h選用ai-對話chat)
6. [產出物快速檢查](#6-產出物快速檢查)
7. [下一步閱讀](#7-下一步閱讀)

---

## 1. 安裝與依賴

在 repo 根目錄執行：

```bash
git clone https://github.com/kyle0527/BioNeuronai.git
cd BioNeuronai
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0+cpu torchvision==0.23.0+cpu torchaudio==2.8.0+cpu
python -m pip install -e .
```

PyTorch 2.8.0+cpu 是目前 Windows 本機已確認可 import 的 CPU 組合。`pyproject.toml` **沒有** `[rl]` optional extra；RL 訓練（`training/rl_trainer.py`）使用主依賴內的 PyTorch，無需 `pip install -e ".[rl]"`。

---

## 2. 設定環境變數

日常不接交易所時只保留 `.env.example` 即可。只有要使用 Binance、新聞 API、testnet 或 live 時，才建立 `.env`：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

請編輯 `.env` 填入需要的金鑰；安全試用請確保 `BINANCE_TESTNET=true`。完整變數說明見 [17_ENVIRONMENT_VARIABLES.md](17_ENVIRONMENT_VARIABLES.md)。

---

## 3. 現行方向與雙執行主線（必讀）

### 3.1 你現在該先做什麼

依 [`CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)：

1. **先讓預設流程在虛擬帳戶／Paper 上自己跑通**（工程自主 + 記帳正確）。  
2. 再穩定長跑。  
3. **之後**再基線訓練與開滿在線改善。  
4. 終局是 **自主時直接改善**（交易即訓練），不是永遠只跑不學。  
5. **多帳戶／認證等商用周邊後續再加。**  
6. **驗收不用 test 檔**；日常用真實 Paper，長期先下載歷史再回測。

### 3.2 雙入口（共用模型與 paper 執行）

| 維度 | 主線 A：`trade` | 主線 B：`autonomous`（**預設 AI 自主**） |
|------|-----------------|----------------------------------------|
| 驅動 | WebSocket 即時 tick | 定時規劃（`--cycles N`，N>1 為持續） |
| 典型用途 | tick 監控、T0–T2 觀測 | **自主長跑**、規劃→pretrade→執行 |
| 模型 | shared `unified_v2_100m` | **同一** shared |
| Paper 執行 | 引擎內 | 委派 TradingEngine |
| ActionRecord / LoRA | ✅ paper 平倉 | ✅ 經 shared 平倉回調進入引擎鏈 |
| Decision Ledger | ❌ | ✅ JSONL |
| AdaptiveLearningHub | ✅ | ✅ |

**主線 B 執行層**：

- `--mode paper_auto` + `--execute-paper` 才會送 paper 單（`advisor` 不下單）。  
- quantity：**優先** pretrade；無效 fallback `--paper-notional-fraction`。  
- 已有持倉：`skipped=existing_position`。  
- 卡單：`--max-position-hold-cycles`；反思：`--reflect-every`（需 cycles>1）。  
- 獨立反思：`python main.py reflect --sample-size 50`（需記憶中有樣本）。

完整參數：[04_CLI_OPERATION.md](04_CLI_OPERATION.md)。

---

## 4. 驗證系統狀態

```bash
python main.py status
```

預期出現各模組回報 `[OK]` 以及 `系統狀態: 正常`。若 API 已啟動，`GET /api/v1/status` 應回傳 `ready=true`、`blocking=[]`；缺少 PyTorch、現役交易模型、聊天模型或必要設定檔時應直接顯示阻擋項目。

---

## 5. 核心功能驗證（建議順序）

### 步驟 A：觀察市場（News）

```bash
python main.py news --symbol BTCUSDT
```

即時抓取新聞並計算情緒分數；結果會寫入 RAG，供策略融合與 TradingEngine 參考。

### 步驟 B：啟動高階計劃（Plan）

```bash
python main.py plan --symbol BTCUSDT --output output/daily_plan.json
```

整合宏觀指標與 K 線體制，輸出當日規劃建議。

### 步驟 C：盤前檢查（Pretrade）

```bash
python main.py pretrade --symbol BTCUSDT --action long
```

綜合技術面、新聞/RAG、內部 `RiskCalculation` 與 `AIConfidenceCalibrator`，輸出 `PROCEED` / `CAUTION` / `REJECT` 及 `order_parameters`。**此路徑不直接呼叫 `RiskManager.calculate_position_size()`**（見 [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md)）。

### 步驟 D：自主單輪（主線 B，先確認規劃鏈）

```bash
python main.py autonomous --mode advisor --symbol BTCUSDT --output output/autonomous_advisor.json
```

這一輪會：plan → 候選 pretrade → adaptation → 寫 decision ledger。終端印出 `final_action`、`reasons` 與 Pretrade 摘要。

若 `final_action` 為 `advise_only` 或 pretrade 為 WAIT／REJECT，先觀察，不必急著執行 paper。

### 步驟 E：預設 AI 自主 paper（本階段核心，主線 B）

這是 **工程自主** 主路徑（真實虛擬帳戶時序；**不是** pytest）：

```bash
python main.py autonomous --mode paper_auto --execute-paper --cycles 5 --symbol BTCUSDT --paper-balance 10000
```

預期行為：

- 多輪 `run_forever`（`--cycles` > 1）
- adaptation 允許時經 **共用 TradingEngine** 送 paper 單
- 已有持倉時可能 `skipped=existing_position`（屬預期）
- ledger 追加多輪；可抽查決策與 execution／跳過原因
- 平倉時 shared callback 回寫引擎學習鏈 + ledger
- 若 `active_model.json` 為 `trained: false`：**流程可通 ≠ AI 已會交易**

可選：`--max-position-hold-cycles N` 測卡單。詳見 [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md)。

### 步驟 F：即時 tick paper（主線 A，T0–T2 觀測）

```bash
python main.py trade --symbol BTCUSDT --paper-live --paper-balance 10000
```

預期：

- WebSocket 行情；虛擬成交進 `VirtualAccount`
- 平倉觸發 ActionRecord → EpisodicMemory → LoRA／Hub（視寫入策略）
- `Ctrl+C` 可停

測試網（需 testnet 金鑰）：

```bash
python main.py trade --symbol BTCUSDT --testnet
```

**不建議**同時對同 symbol 無協調地跑 `trade --paper-live` 與 `autonomous --execute-paper`。

### 步驟 G（長期，選用）：歷史資料回測

日常用 Paper；**大區間**請先下載歷史再回測（見 [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md)、[08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)）。
### 步驟 H（選用）：AI 對話（Chat）

```bash
python main.py chat --symbol BTCUSDT
python main.py chat --allow-rule-based-fallback   # 僅開發測試
```

對話與交易共用 `unified_v2_100m`。未訓練可執行，回應應標 `UNTRAINED`，不代表模型品質。

---

## 6. 產出物快速檢查

操作後可用以下路徑驗收（**非 pytest**）：

| 路徑 | 產生時機 |
|------|----------|
| `data/bioneuronai/planning/autonomous/decision_ledger.jsonl` | `autonomous` 每輪 |
| `data/bioneuronai/trading/paper_live/` | `trade --paper-live` 或 `autonomous --execute-paper` |
| `data/bioneuronai/learning/adaptive_hub.json` | 平倉後 hub 更新 |
| `data/bioneuronai/memory/` | paper 平倉後（A 直接；B 經 shared callback） |
| `output/*.json` | `--output` 指定的單輪 JSON |

詳見 [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)。

---

## 7. 下一步閱讀

| 順序 | 手冊 | 用途 |
|------|------|------|
| 0 | [`CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md) | 優先級與驗收哲學 |
| 1 | [04_CLI_OPERATION.md](04_CLI_OPERATION.md) | 完整 CLI 與 SOP |
| 2 | [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) | 自主 paper／testnet／live |
| 3 | [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md) | 對帳產物 |
| 4 | [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md) | Level 2.5 等驗收矩陣 |
| 5 | [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) | 長期歷史驗證 |
| 6 | [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md) | 開機、關機、API |
