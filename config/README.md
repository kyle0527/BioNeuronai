# config/ — 配置文件

> **更新日期**: 2026-03-10

---

## 目錄

- [配置總覽](#配置總覽)
- [交易配置](#交易配置)
- [交易成本](#交易成本)
- [市場關鍵字](#市場關鍵字)
- [策略與風險配置](#策略與風險配置)

---

## 配置總覽

```
config/
├── __init__.py                    # 模組匯出
├── trading_config.py              # 交易參數配置（API 金鑰、槓桿等）
├── trading_costs.py               # 交易成本計算器（手續費結構）
├── market_keywords.json           # 市場關鍵字定義
├── market_keywords.db             # 關鍵字 SQLite 資料庫
├── risk_config_optimized.json     # 優化後風險參數
├── strategy_weights_optimized.json # 優化後策略權重
└── keywords/                      # 按類別拆分的關鍵字
    ├── _index.json                # 類別索引
    ├── coin.json                  # 幣種相關
    ├── event.json                 # 事件相關
    ├── institution.json           # 機構相關
    ├── legislation.json           # 法規相關
    ├── macro.json                 # 宏觀經濟
    ├── person.json                # 人物相關
    └── tech.json                  # 技術相關
```

---

## 交易配置

**檔案**: `trading_config.py` (~152 行)

包含所有交易系統運行時配置：
- Binance API 金鑰（Testnet / 實盤）
- 交易對、槓桿、倉位大小
- 止損 / 止盈百分比
- AI 模型啟用開關與最低信心度
- 每日交易次數限制

---

## 交易成本

**檔案**: `trading_costs.py` (~557 行)

根據 Binance Futures 費率結構實現的交易成本計算器，匯出：
- `TradingCostCalculator` — 成本計算主類
- `STANDARD_FEES` / `VIP_FEES` — 費率等級定義
- `FUNDING_RATE` — 資金費率參考
- `SPREAD_COSTS` — 價差成本
- `BNB_DISCOUNT` — BNB 折扣

---

## 市場關鍵字

**檔案**: `market_keywords.json` + `keywords/` 子目錄

505 個市場關鍵字（v3.1，2026-03-10 更新），用於新聞分析與情緒判斷，分為 7 大類：
- **coin** — 幣種名稱與代號（102 個）
- **event** — 市場事件（減半、ETF、清算等）（148 個）
- **institution** — 機構動態（56 個）
- **legislation** — 法規政策（30 個）
- **macro** — 宏觀經濟指標（50 個）
- **person** — 關鍵人物（59 個）
- **tech** — 技術發展（60 個）

---

## 策略與風險配置

| 檔案 | 說明 |
|------|------|
| `risk_config_optimized.json` | 優化後的風險管理參數 |
| `strategy_weights_optimized.json` | 優化後的策略權重配置 |

---

> 📖 上層目錄：[根目錄 README](../README.md)
