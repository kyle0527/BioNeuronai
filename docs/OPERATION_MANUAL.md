# BioNeuronai 操作手冊
**版本**：v4.3.1
**更新日期**：2026-03-16
**適用對象**：初次使用者 / 日常操作參考

---

## 📑 目錄

1. 系統概述
2. 安裝與環境設定
3. Binance API 金鑰設定
4. CLI 命令完整參考
5. 設定檔說明
6. 標準操作流程
7. 歷史數據下載
8. 工具腳本
9. 常見問題排查
10. 風險警示
11. 附錄：快速指令速查

---

## 系統概述

BioNeuronai 是一套加密貨幣期貨量化交易系統，整合 AI 推論引擎、多策略融合、新聞情緒分析與完整的風險管理框架。

### 核心能力

| 功能 | 說明 | 需要 torch | 需要 API 金鑰 |
|------|------|:----------:|:------------:|
| 系統健康檢查 | 診斷所有模組狀態 | ✗ | ✗ |
| 新聞情緒分析 | 217 關鍵字、8 種事件類型 | ✗ | ✗ |
| 每日交易計劃 | 10 步驟 SOP | ✗ | 部分步驟 |
| 進場前 5 步驟驗核 | 技術 / 基本面 / 風險三重確認 | ✗ | ✅ |
| 歷史回測 | AI 回測（需本地數據） | ⚠️ 可選 | ✗ |
| 紙交易模擬 | 逐根 K 線推進 | ⚠️ 可選 | ✗ |
| 實盤 / 測試網交易 | WebSocket 即時自動交易 | ✅ | ✅ |

---

## 安裝與環境設定

### 前置需求

- Python **3.9** 以上（推薦 3.10 / 3.11）
- pip 23+
- 網路連線（部分功能需連接外部 API）

### 步驟一：進入專案目錄

```bash
cd /home/user/BioNeuronai
```

### 步驟二：建立虛擬環境（建議）

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# 或
venv\Scripts\activate           # Windows
```

### 步驟三：安裝依賴

**基礎安裝**（不含 torch，可執行 `status` / `news` / `plan` / `pretrade`）：

```bash
pip install pydantic>=2.0.0 numpy>=1.24.0 pandas>=2.0.0 \
            websocket-client>=1.7.0 requests>=2.31.0 aiohttp>=3.9.0
```

**完整安裝**（含 torch，可執行全部功能）：

```bash
pip install -r requirements-crypto.txt
```

**開發者安裝**：

```bash
pip install -e .
pip install -r requirements-dev.txt
```

### 步驟四：驗證安裝

```bash
python main.py status
```

正常輸出示例：

```
[OK] TradingEngine
[OK] BinanceFutures
[OK] NewsAnalyzer
[OK] SOPSystem
[OK] PlanController
[OK] PreTradeCheck
[OK] BacktestEngine
版本: bioneuronai v4.3.1
系統狀態: 正常
```

若 torch 未安裝，`TradingEngine` 會顯示 `[WARN]`，其餘模組仍正常。

---

## Binance API 金鑰設定

> ⚠️ 部分內容過時：
> 本章節中的「直接修改 `config/trading_config.py`」仍可視為舊版本地操作方式，但不應再作為後續架構與 UI 整合的主要基準。
> 依最新規劃，Binance 屬於使用者級憑證來源，後續應優先對照 [API_INTEGRATION_BASELINE.md](C:/D/E/BioNeuronai/docs/API_INTEGRATION_BASELINE.md) 中的憑證流原則。
> 可繼續參考本章節的內容：
> - 哪些命令需要 Binance 憑證
> - Testnet / Live 的差別
> 需謹慎使用的內容：
> - `方式 A：編輯設定檔`
> - 把 `config/trading_config.py` 視為長期標準做法

### 哪些命令需要 API 金鑰

| 命令 | 是否需要 |
|------|:-------:|
| `status` / `news` / `backtest` / `simulate` | ✗ 不需要 |
| `pretrade` | ✅ 需要（查詢帳戶與即時行情） |
| `plan` | ⚠️ 部分步驟需要 |
| `trade --testnet` | ✅ 需要測試網金鑰 |
| `trade --live` | ✅ 需要正式網金鑰 |

### 取得 API 金鑰

- **測試網（Testnet）**：前往 [Binance Testnet](https://testnet.binancefuture.com) 免費申請，完全無風險。
- **正式網（Live）**：登入 Binance 帳戶 → 帳戶管理 → API 管理，建立期貨交易金鑰。

### 設定方式

**方式 A：.env 檔案**（推薦）

```bash
cp .env.example .env
# 編輯 .env，填入以下值：
# BINANCE_API_KEY=你的 API Key
# BINANCE_API_SECRET=你的 API Secret
# BINANCE_TESTNET=true     # false = 正式網
# CRYPTOPANIC_API_TOKEN=free  # 選填，新聞 API
```

**方式 B：環境變數**（適合生產環境 / Docker）

```bash
export BINANCE_API_KEY="你的 API Key"
export BINANCE_API_SECRET="你的 API Secret"
export BINANCE_TESTNET="true"
```

> **安全提醒**：`.env` 請確認已加入 `.gitignore`，勿提交至版本控制。金鑰不應直接寫入任何 `.py` 原始碼。

---

## CLI 命令完整參考

### 入口方式

```bash
# 方式 1（推薦，從根目錄執行）
python main.py <命令> [選項]

# 方式 2（模組方式）
python -m bioneuronai.cli.main <命令> [選項]
```

---

### `status` — 系統健康檢查

**用途**：快速診斷所有模組是否可用，排查安裝問題。

```bash
python main.py status
```

**無任何參數**，輸出各模組狀態與版本號。

---

### `news` — 新聞情緒分析

**用途**：擷取並分析加密貨幣相關新聞，評估市場情緒。

```bash
python main.py news [選項]
```

| 選項 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--symbol` | 字串 | `BTCUSDT` | 篩選與特定幣種相關的新聞 |
| `--max-items` | 整數 | `10` | 顯示新聞數量上限 |

**範例**：

```bash
python main.py news                                    # BTC 最新 10 則
python main.py news --symbol ETHUSDT --max-items 20   # ETH 最新 20 則
python main.py news --symbol SOLUSDT --max-items 5
```

**輸出內容**：新聞標題、情緒評分（-1.0 到 +1.0）、關鍵字命中、新聞來源。

---

### `pretrade` — 進場前驗核

**用途**：執行 5 步驟三重確認，判斷是否適合進場。評分 ≥ 80% 建議執行，< 40% 建議放棄。

```bash
python main.py pretrade [選項]
```

| 選項 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--symbol` | 字串 | `BTCUSDT` | 交易對 |
| `--action` | 選擇 | `long` | 交易方向：`long` 或 `short` |
| `--capital` | 浮點數 | `10000` | 可用資金（USDT） |
| `--output` | 路徑 | 無 | 輸出結果至 JSON 檔案 |

**範例**：

```bash
python main.py pretrade --symbol BTCUSDT --action long
python main.py pretrade --symbol ETHUSDT --action short --output pretrade.json
python main.py pretrade --symbol BTCUSDT --action long --capital 50000
```

**輸出判決**：

| 評分 | 結果 | 建議 |
|------|------|------|
| ≥ 80% | `EXECUTE` ✅ | 可進場 |
| 60–79% | `CAUTIOUS_EXECUTE` ⚠️ | 謹慎進場，縮小倉位 |
| 40–59% | `WAIT` 🟡 | 等待更好時機 |
| < 40% | `REJECT` ❌ | 不建議進場 |

---

### `plan` — 每日交易計劃（10 步驟 SOP）

**用途**：生成完整的每日盤前分析報告，涵蓋宏觀掃描、技術分析、策略選擇、風險計算與資金管理。

```bash
python main.py plan [選項]
```

| 選項 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--output` | 路徑 | 無 | 輸出完整報告至 JSON 檔案 |

**範例**：

```bash
python main.py plan                                  # 顯示於終端
python main.py plan --output daily_plan.json        # 同時儲存
python main.py plan --output reports/$(date +%F).json
```

**10 步驟流程**：

| 步驟 | 名稱 | 數據來源 |
|------|------|---------|
| 1 | 系統環境檢查 | 本地 |
| 2 | 宏觀市場掃描 | Alternative.me、CoinGecko、DefiLlama |
| 3 | 技術面分析 | Binance API |
| 4 | 基本面情緒分析 | 事件評估系統 |
| 5 | 策略性能評估 | StrategySelector |
| 6 | 策略選擇權重 | StrategySelector |
| 7 | 風險參數計算 | RiskManager |
| 8 | 資金管理規劃 | Kelly Criterion |
| 9 | 交易對篩選 | PairSelector |
| 10 | 執行計劃監控設定 | 本地設定 |

---

### `backtest` — 歷史回測

**用途**：使用本地歷史 K 線數據對策略進行回測，評估歷史績效。

> ⚠️ **前置條件**：需先下載歷史數據至 `data_downloads/binance_historical/`，詳見[歷史數據下載](#歷史數據下載)。

```bash
python main.py backtest [選項]
```

| 選項 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--symbol` | 字串 | `ETHUSDT` | 交易對 |
| `--interval` | 字串 | `1h` | K 線週期（1m / 5m / 15m / 1h / 4h / 1d） |
| `--start-date` | 日期 | 最早可用 | 回測起始日（`YYYY-MM-DD`） |
| `--end-date` | 日期 | 最新可用 | 回測結束日（`YYYY-MM-DD`） |
| `--balance` | 浮點數 | `10000.0` | 初始資金（USDT） |

**範例**：

```bash
python main.py backtest --symbol BTCUSDT --interval 1h
python main.py backtest --symbol ETHUSDT --interval 4h --balance 50000
python main.py backtest --symbol BTCUSDT \
    --start-date 2025-01-01 \
    --end-date 2025-06-30 \
    --balance 100000
```

**輸出指標**：總報酬率、夏普比率、最大回撤、勝率、總交易次數。

**torch 狀態影響**：
- 有 torch：使用 AI 推論引擎生成信號
- 無 torch：以規則型策略執行，結果仍有參考價值

---

### `simulate` — 紙交易模擬

**用途**：逐根 K 線推進，完全模擬交易流程，不產生任何真實訂單。

> ⚠️ **前置條件**：同 `backtest`，需要本地歷史數據。

```bash
python main.py simulate [選項]
```

| 選項 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--symbol` | 字串 | `BTCUSDT` | 交易對 |
| `--interval` | 字串 | `15m` | K 線週期 |
| `--balance` | 浮點數 | `100000.0` | 初始模擬資金（USDT） |
| `--bars` | 整數 | `200` | 模擬 K 線數量上限 |
| `--start-date` | 日期 | 可選 | 起始日期 |
| `--end-date` | 日期 | 可選 | 結束日期 |

**範例**：

```bash
python main.py simulate --symbol BTCUSDT --bars 500
python main.py simulate --symbol ETHUSDT --interval 15m --balance 50000
python main.py simulate --symbol BTCUSDT \
    --interval 1h \
    --bars 1000 \
    --start-date 2025-03-01
```

每 20 根 K 線輸出一行進度狀態。

---

### `trade` — 實盤 / 測試網交易

**用途**：連接 Binance，啟動自動交易迴圈（WebSocket 即時數據驅動）。

> ⚠️ **前置條件**：需安裝 torch 且設定 Binance API 金鑰。

```bash
python main.py trade [選項]
```

| 選項 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `--symbol` | 字串 | `BTCUSDT` | 交易對 |
| `--testnet` | 旗標 | ✅（預設） | 使用 Binance 測試網（虛擬資金） |
| `--live` | 旗標 | ✗ | ⚠️ 使用正式網（真實資金） |

**範例**：

```bash
# 測試網（推薦，無資金風險）
python main.py trade --testnet
python main.py trade --testnet --symbol ETHUSDT

# 正式網（⚠️ 謹慎使用）
python main.py trade --live
# 系統會要求輸入 "YES" 確認，再次輸入後才會啟動
```

**停止交易**：按 `Ctrl+C`，系統會優雅關閉 WebSocket 連線。

---

## 設定檔說明

> ⚠️ 部分內容過時：
> 本章節中 `config/trading_config.py` 的靜態交易參數仍可參考，但 `BINANCE_API_KEY` / `BINANCE_API_SECRET` 不應再被理解為長期推薦的主要存放方式。
> 後續若涉及 API、UI、憑證輸入或整合設計，請先對照 [API_INTEGRATION_BASELINE.md](C:/D/E/BioNeuronai/docs/API_INTEGRATION_BASELINE.md)。

### `config/trading_config.py` — 主要交易設定

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `BINANCE_API_KEY` | — | API 金鑰（必填） |
| `BINANCE_API_SECRET` | — | API 密鑰（必填） |
| `USE_TESTNET` | `True` | `True`＝測試網；`False`＝正式網 |
| `LEVERAGE` | `1` | 槓桿倍數（1–125） |
| `MAX_TRADE_AMOUNT` | `100.0` | 單筆最大交易金額（USDT） |
| `MAX_POSITIONS` | `3` | 最大同時持倉數 |
| `RISK_LEVEL` | `MODERATE` | 風險等級（見下表） |
| `MAX_RISK_PER_TRADE` | `0.02` | 單筆最大風險（2%） |
| `MAX_DRAWDOWN_PERCENTAGE` | `0.10` | 最大回撤限制（10%） |
| `STOP_LOSS_PERCENTAGE` | `0.02` | 止損幅度（2%） |
| `TAKE_PROFIT_PERCENTAGE` | `0.04` | 止盈幅度（4%） |
| `MAX_TRADES_PER_DAY` | `10` | 每日交易上限 |
| `MIN_SIGNAL_CONFIDENCE` | `0.65` | 最低信號置信度（65%） |
| `ACTIVE_STRATEGY` | `AI_Fusion` | 使用策略（見下表） |

**風險等級對照**：

| `RISK_LEVEL` | 單筆風險 | 日最大風險 | 最大槓桿 |
|--------------|---------|-----------|---------|
| `CONSERVATIVE` | 1% | 3% | 2x |
| `MODERATE` | 2% | 5% | 3x |
| `AGGRESSIVE` | 3% | 8% | 10x |
| `HIGH_RISK` | 5% | 15% | 10x |

**可選策略（`ACTIVE_STRATEGY`）**：

| 值 | 說明 |
|----|------|
| `AI_Fusion` | AI 多策略融合（預設，推薦） |
| `RSI_Divergence` | RSI 背離策略 |
| `Bollinger_Bands` | 布林帶均值回歸 |
| `MACD_Trend` | MACD 趨勢跟隨 |

**技術指標參數**：

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `RSI_PERIOD` | `14` | RSI 計算週期 |
| `RSI_OVERBOUGHT` | `70` | RSI 超買線 |
| `RSI_OVERSOLD` | `30` | RSI 超賣線 |
| `BOLLINGER_PERIOD` | `20` | 布林帶週期 |
| `BOLLINGER_STD_DEV` | `2.0` | 布林帶標準差倍數 |
| `MACD_FAST_PERIOD` | `12` | MACD 快線週期 |
| `MACD_SLOW_PERIOD` | `26` | MACD 慢線週期 |
| `MACD_SIGNAL_PERIOD` | `9` | MACD 信號線週期 |

---

### `config/market_keywords.json` — 新聞情緒關鍵字

共 **217 個關鍵字**，分 7 大類別，由 `news` 命令使用。

| 類別 | 數量 | 範例 |
|------|------|------|
| coin | 102 | bitcoin, eth, solana... |
| event | 148 | halving, etf, liquidation... |
| institution | 56 | blackrock, grayscale... |
| legislation | 30 | sec, regulation, ban... |
| macro | 50 | inflation, fed rate, gdp... |
| person | 59 | elon musk, gary gensler... |
| tech | 60 | layer2, zk-proof, defi... |

每個關鍵字有動態權重機制（`dynamic_weight`），根據歷史預測準確率自動調整。如需新增關鍵字，直接編輯 JSON 檔案。

---

## 標準操作流程

### 每日盤前流程（建議順序）

```bash
# 1. 確認系統正常
python main.py status

# 2. 查看市場新聞情緒
python main.py news --symbol BTCUSDT --max-items 10

# 3. 生成完整盤前計劃
python main.py plan --output reports/$(date +%F)_plan.json

# 4. 對目標交易對執行進場前驗核
python main.py pretrade --symbol BTCUSDT --action long

# 5. 若評分 ≥ 80%，啟動測試網驗證
python main.py trade --testnet --symbol BTCUSDT
```

### 策略驗證流程（新策略上線前）

```bash
# 1. 下載足夠的歷史數據（見下一節）

# 2. 執行歷史回測
python main.py backtest \
    --symbol BTCUSDT \
    --interval 1h \
    --start-date 2024-01-01 \
    --end-date 2025-01-01 \
    --balance 10000

# 3. 紙交易模擬驗證
python main.py simulate \
    --symbol BTCUSDT \
    --interval 1h \
    --bars 1000 \
    --balance 10000

# 4. 測試網實盤驗證（至少 1–2 週）
python main.py trade --testnet

# 5. 確認無誤後才考慮正式網
```

---

## 歷史數據下載

`backtest` 和 `simulate` 命令需要本地歷史 K 線數據，存放於 `data_downloads/binance_historical/` 目錄。

### 使用內建下載工具

```bash
cd tools/data_download

# 複製設定檔
cp .env.example .env
```

編輯 `tools/data_download/.env`：

```ini
STORE_DIRECTORY=../../data_downloads/binance_historical
DEFAULT_MARKET_TYPE=um
DEFAULT_SYMBOLS=BTCUSDT ETHUSDT SOLUSDT
DEFAULT_INTERVALS=1h 4h
DEFAULT_START_DATE=2024-01-01
```

執行下載：

```bash
python download-kline.py
```

### 數據格式

下載完成後，檔案會存放於：

```
data_downloads/
└── binance_historical/
    ├── BTCUSDT_1h.csv
    ├── ETHUSDT_1h.csv
    ├── BTCUSDT_4h.csv
    └── ...
```

格式：`timestamp, open, high, low, close, volume`

> CSV 檔案已加入 `.gitignore`，不會被提交至版本控制。

---

## 工具腳本

位於 `tools/` 目錄，以下為常用腳本：

| 腳本 | 用途 | 執行方式 |
|------|------|---------|
| `quick_start_optimized.py` | 快速驗證系統設定是否正確 | `python tools/quick_start_optimized.py` |
| `simulate_trading_environment.py` | 交易環境完整模擬驗證 | `python tools/simulate_trading_environment.py` |
| `demo_strategy_evolution.py` | 策略遺傳演算法進化演示 | `python tools/demo_strategy_evolution.py` |
| `ai_trade_nexttick.py` | AI 逐 tick 模擬交易（舊版包裝） | `python tools/ai_trade_nexttick.py` |
| `split_keywords.py` | 將 `market_keywords.json` 拆分至子目錄 | `python tools/split_keywords.py` |
| `upgrade_keywords.py` | 升級關鍵字分類與結構 | `python tools/upgrade_keywords.py` |

**數據下載工具**（`tools/data_download/`）：

| 腳本 | 用途 |
|------|------|
| `download-kline.py` | Binance K 線歷史數據批量下載 |
| `data_feeder.py` | 將歷史數據按時序逐筆推送（供回測使用） |
| `run_backtest.py` | 策略快速回測驗證 |
| `mock_api.py` | 模擬 Binance API 連接器（離線測試用） |

---

## 常見問題排查

### Q：執行 `python main.py status` 出現 `ModuleNotFoundError`

確認是否在專案根目錄執行，且虛擬環境已啟動：

```bash
cd /home/user/BioNeuronai
source venv/bin/activate
python main.py status
```

若仍有問題，重新安裝依賴：

```bash
pip install -r requirements-crypto.txt
```

---

### Q：`TradingEngine` 顯示 `[WARN]` 或不可用

表示 `torch` 未安裝。執行 `trade` 命令需要 torch，其他命令不受影響：

```bash
pip install torch>=2.0.0
```

---

### Q：`backtest` 或 `simulate` 報錯「找不到數據文件」

歷史數據目錄為空，需先下載：

```bash
cd tools/data_download && python download-kline.py
```

---

### Q：`pretrade` 或 `trade` 報 API 驗證失敗

> ⚠️ 補註：
> 本節目前仍以 `config/trading_config.py` 為中心說明排查方式。
> 若後續已改為環境變數、secrets 或受控輸入流程，請把本節視為「舊路徑排查說明」，不要直接當作唯一標準。

1. 確認環境變數 `BINANCE_API_KEY` 和 `BINANCE_API_SECRET` 已設定（檢查 .env 或 export）
2. 確認 `BINANCE_TESTNET` 與金鑰類型一致（測試網金鑰需搭配 `BINANCE_TESTNET=true`）
3. 確認 Binance API 金鑰已開啟「期貨交易」權限
4. 可使用 `python main.py status` 或 `POST /api/v1/binance/validate` 快速驗證憑證

---

### Q：`trade --live` 啟動後要求確認

這是刻意設計的安全機制。系統會要求你輸入 `YES`（大寫），輸入其他內容或按 Enter 則取消，防止誤觸正式交易。

---

### Q：`plan` 的步驟 9 顯示 `default_fallback`

`PairSelector` 需要 Binance API 連線才能查詢即時成交量。若 API 未設定或連線失敗，會自動降級為預設幣對（BTCUSDT / ETHUSDT / BNBUSDT）。

---

### Q：WebSocket 連線中斷

`trade` 命令的 WebSocket 有自動重連機制（最多 10 次，指數退避）。若持續斷線，請檢查：
- 網路是否穩定
- Binance API 是否在你的地區可用（部分地區需 VPN）

---

## 風險警示

```
⚠️  使用本系統前請仔細閱讀以下事項：

1. 測試網與正式網的差異
   - --testnet  ：使用虛擬資金，不涉及任何真實金錢，強烈建議新手先用此模式。
   - --live     ：涉及真實資金，虧損不可撤回。

2. 在切換至 --live 前，請確認：
   - 已完成至少 30 天的 backtest 驗證
   - 已在 testnet 穩定運行至少 1-2 週
   - 充分理解所有風險參數設定
   - 投入的資金為可以承受全損的閒置資金

3. 系統風險
   - 市場行情劇烈變動時，止損可能因滑點而未能以預期價格成交
   - 網路中斷可能導致倉位無法及時平倉
   - AI 推論結果並不保證盈利，歷史回測績效不代表未來表現

4. 安全設定建議
   - RISK_LEVEL 建議從 CONSERVATIVE 開始
   - LEVERAGE 建議從 1x 開始
   - MAX_TRADE_AMOUNT 設定為可接受損失的金額
```

---

## 附錄：快速指令速查

```bash
# 系統診斷
python main.py status

# 新聞情緒（BTC，10 則）
python main.py news

# 進場前驗核（BTC 做多）
python main.py pretrade --symbol BTCUSDT --action long

# 每日計劃（儲存至檔案）
python main.py plan --output plan.json

# 歷史回測（ETHUSDT 1h，近一年）
python main.py backtest --symbol ETHUSDT --interval 1h \
    --start-date 2025-01-01 --balance 10000

# 紙交易模擬（500 根 K 線）
python main.py simulate --symbol BTCUSDT --bars 500

# 測試網交易（推薦）
python main.py trade --testnet

# 正式網交易（⚠️ 謹慎）
python main.py trade --live
```

---

> 📖 相關文件：
> - [功能狀態總覽](FEATURE_STATUS.md) — 已完成 / 部分完成 / 尚未完成的功能清單
> - [策略模組說明](../src/bioneuronai/strategies/README.md) — 策略架構與使用方式
> - [歷史數據說明](../data_downloads/README.md) — 回測數據取得方式
