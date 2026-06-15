# BioNeuronai v2.1 快速開始指南

> **套件版本**：v2.1（`pyproject.toml`）
> **更新日期**：2026-06-15
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)
> **建議環境**：本機全域 Python 3.13。Docker 留到本機功能收斂後最後重建。

---

## 目錄

1. [安裝與依賴](#1-安裝與依賴)
2. [設定環境變數](#2-設定環境變數)
3. [雙執行主線（必讀）](#3-雙執行主線必讀)
4. [驗證系統狀態](#4-驗證系統狀態)
5. [核心功能驗證（建議順序）](#5-核心功能驗證建議順序)
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

## 3. 雙執行主線（必讀）

操作前請先選定主線。**兩者學習閉環不同，不可混用驗收標準。**

| 維度 | 主線 A：`trade` | 主線 B：`autonomous` |
|------|----------------|----------------------|
| 驅動 | WebSocket 即時 tick | 定時規劃迴圈（`--cycles N`） |
| 典型用途 | 即時監控、完整「交易即訓練」 | 盤前規劃、值班建議、定時 paper |
| ActionRecord / LoRA | ✅（`--paper-live` 平倉觸發） | ❌ |
| Decision Ledger | ❌ | ✅ JSONL |
| AdaptiveLearningHub | ✅ | ✅ |

**主線 B 執行層（2026-06-15）**：
- `--execute-paper` **優先**採 pretrade `order_parameters.quantity`（× `risk_multiplier`）；quantity 無效時 fallback `--paper-notional-fraction`
- 已有持倉時跳過進場（`paper_execution.skipped=true`）
- 卡單平倉：`--max-position-hold-cycles`；反思迴圈：`--reflect-every`（需 `--cycles >1`）
- 獨立反思：`python main.py reflect --sample-size 50`（樣本來自 EpisodicMemory，需主線 A 累積）

完整參數與 SOP 見 [04_CLI_OPERATION.md](04_CLI_OPERATION.md) §2、§5、§7。

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

### 步驟 D：自主值班單輪（主線 B，建議先做）

```bash
python main.py autonomous --mode advisor --symbol BTCUSDT --output output/autonomous_advisor.json
```

這一輪會：plan → 候選交易對 pretrade → adaptation 決策 → 寫入 decision ledger。終端機會印出 `final_action`、`reasons` 與 **Pretrade** 區塊（JSON 欄位為 `pretrade_summary`）。

若 `final_action` 為 `advise_only` 或 pretrade 顯示 `WAIT`/`REJECT`，代表本輪應先觀察，不必急著進主線 A。

### 步驟 E：主交易引擎（主線 A，建議先 paper-live）

確認分析與值班結果合理後，啟動長時間監控：

```bash
python main.py trade --symbol BTCUSDT --paper-live --paper-balance 10000
```

預期行為：

- `TradingEngine` 初始化成功
- AI 模型載入
- 行情來自 Binance mainnet public data，下單只進本地 `VirtualAccount`
- paper log 目錄位於 `data/bioneuronai/trading/paper_live/`
- 平倉後觸發 ActionRecord → EpisodicMemory → LoRA 學習閉環
- 可用 `Ctrl+C` 中止

測試網監控（需 `.env` testnet 金鑰）：

```bash
python main.py trade --symbol BTCUSDT --testnet
```

定時規劃 + 本機 paper 下單（主線 B，需明確旗標）：

```bash
python main.py autonomous --mode paper_auto --symbol BTCUSDT --execute-paper --paper-balance 10000
```

**不建議**同時對同 symbol 跑 `trade --paper-live` 與 `autonomous --execute-paper` 而不檢查持倉。

### 步驟 F（選用）：AI 對話（Chat）

```bash
python main.py chat --symbol BTCUSDT
python main.py chat --allow-rule-based-fallback   # 僅開發測試
```

正式對話需要 PyTorch 與 `model/tiny_llm_100m.pth`。模型未載入時預設報錯，不會默默降級。

---

## 6. 產出物快速檢查

操作後可用以下路徑驗收（**非 pytest**）：

| 路徑 | 產生時機 |
|------|----------|
| `data/bioneuronai/planning/autonomous/decision_ledger.jsonl` | `autonomous` 每輪 |
| `data/bioneuronai/trading/paper_live/` | `trade --paper-live` 或 `autonomous --execute-paper` |
| `data/bioneuronai/learning/adaptive_hub.json` | 平倉後 hub 更新 |
| `data/bioneuronai/memory/` | 主線 A 平倉（EpisodicMemory） |
| `output/*.json` | `--output` 指定的單輪 JSON |

詳見 [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)。

---

## 7. 下一步閱讀

| 順序 | 手冊 | 用途 |
|------|------|------|
| 1 | [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md) | 開機、關機、API |
| 2 | [04_CLI_OPERATION.md](04_CLI_OPERATION.md) | 完整 CLI 參考與 SOP |
| 3 | [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md) | news / plan / pretrade 細節 |
| 4 | [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md) | 風控雙層架構 |
| 5 | [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) | testnet / live 啟停 |