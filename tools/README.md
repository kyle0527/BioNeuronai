# tools/ — 開發與運維工具

> **更新日期**: 2026-02-15

---

## 目錄

- [工具總覽](#工具總覽)
- [交易模擬工具](#交易模擬工具)
- [策略進化示範](#策略進化示範)
- [關鍵字工具](#關鍵字工具)
- [數據下載與回測](#數據下載與回測)
- [專案報告腳本](#專案報告腳本)
- [產出檔案](#產出檔案)

---

## 工具總覽

```
tools/
├── ai_trade_nexttick.py                 # AI 模擬交易（next_tick 推進）
├── demo_strategy_evolution.py           # 策略進化系統完整示範
├── quick_start_optimized.py             # 優化配置快速啟動測試
├── simulate_trading_environment.py      # 完整交易環境模擬驗證
├── split_keywords.py                    # 關鍵字 JSON 拆分
├── upgrade_keywords.py                  # 關鍵字分類架構升級
├── generate_project_report.ps1          # 專案報告生成（PowerShell）
├── generate_tree_ultimate_chinese.ps1   # 程式碼樹狀圖生成
├── data_download/                       # 數據下載與回測子目錄
│   ├── data_feeder.py                   # 歷史 K 線數據串流餵送器
│   ├── download-kline.py               # Binance K 線歷史數據下載
│   ├── run_backtest.py                  # 策略回測驗證
│   ├── mock_api.py                      # 模擬 API 連接器
│   ├── download-aggTrade.py             # 聚合交易數據下載
│   ├── download-trade.py               # 交易數據下載
│   ├── download-futures-*.py            # 期貨指數/標記價格下載
│   ├── enums.py                         # 下載器列舉定義
│   └── utility.py                       # 工具函數
├── PROJECT_REPORT*.txt                  # 歷次專案報告
└── tree*.mmd                            # 歷次 Mermaid 樹狀圖
```

---

## 交易模擬工具

### ai_trade_nexttick.py (~166 行)

使用 `MockBinanceConnector` + `next_tick()` 逐步推進的 AI 模擬交易腳本。

```bash
python tools/ai_trade_nexttick.py
```

- 交易對：ETHUSDT 15m
- 使用推論引擎產生交易信號
- 模擬訂單執行與帳戶狀態

### simulate_trading_environment.py (~184 行)

模擬完整交易環境（含 mock 連接器、asyncio、隨機數據），用於系統驗證。

```bash
python tools/simulate_trading_environment.py
```

### quick_start_optimized.py (~107 行)

Jules Session 優化配置後的快速啟動測試腳本。

```bash
python tools/quick_start_optimized.py
```

---

## 策略進化示範

### demo_strategy_evolution.py (~330 行)

展示三層策略進化優化系統的完整流程：

1. **策略競技場** — 並行回測、適者生存
2. **階段路由器** — 市場狀態識別 → 策略選擇
3. **組合優化器** — 權重分配最佳化

```bash
python tools/demo_strategy_evolution.py
```

---

## 關鍵字工具

### split_keywords.py (~86 行)

將單一 `config/market_keywords.json` 按類別拆分為多個 JSON 檔案至 `config/keywords/`。

```bash
python tools/split_keywords.py
```

### upgrade_keywords.py (~374 行)

升級關鍵字分類架構，重新分類並新增 `macro`、`legislation` 等類別。

```bash
python tools/upgrade_keywords.py
```

---

## 數據下載與回測

> 📁 位於 `tools/data_download/` 子目錄

### data_feeder.py (~451 行)

按時間順序、可調速度地餵送歷史 K 線數據，模擬實時數據流供回測使用。

### download-kline.py (~117 行)

從 Binance 官方下載 K 線歷史數據。

```bash
python tools/data_download/download-kline.py
```

### run_backtest.py (~159 行)

連接 AI 推論引擎，使用歷史數據進行策略回測驗證。

### mock_api.py (~187 行)

模擬真實 API 連接，按順序餵送 K 線數據給 AI 系統。

---

## 專案報告腳本

### generate_project_report.ps1 (~431 行)

PowerShell 腳本，生成專案完整報告（樹狀結構 + 統計數據 + 程式碼分析）。

```powershell
.\tools\generate_project_report.ps1
```

產出：`tools/PROJECT_REPORT_<日期>.txt`

### generate_tree_ultimate_chinese.ps1 (~786 行)

生成程式碼樹狀架構圖，支援版本比對並以顏色標記新增/刪除/不變。

```powershell
.\tools\generate_tree_ultimate_chinese.ps1
```

產出：`tools/tree_<日期>.mmd`（Mermaid 格式）

---

## 產出檔案

| 類型 | 檔案模式 | 說明 |
|------|----------|------|
| 專案報告 | `PROJECT_REPORT_*.txt` | 歷次專案結構與統計報告 |
| 樹狀圖 | `tree_*.mmd` | Mermaid 格式程式碼架構圖 |

---

> 📖 上層目錄：[根目錄 README](../README.md)
