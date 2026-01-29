# 🧠 BioNeuronAI - AI 驅動的加密貨幣期貨交易系統

**AI 神經網路 + 智能交易融合 | 111.2M 參數量化推論引擎**

**最後更新**: 2026年1月22日  
**版本**: v2.1.0 (風險管理整合版)

---

## 📋 目錄

1. [系統亮點](#系統亮點)
2. [快速開始](#快速開始)
3. [項目結構](#項目結構)
4. [核心功能](#核心功能)
5. [使用文檔](#使用文檔)
6. [開發指南](#開發指南)
7. [常見問題](#常見問題)
8. [授權信息](#授權信息)

---

## ✨ 系統亮點

| 特性 | 描述 |
|------|------|
| 🧠 **AI 神經網路** | 111.2M 參數 MLP 模型，~22ms 推論延遲 |
| 🔗 **推論引擎整合** | 完整 InferenceEngine 連接 AI 大腦與交易系統 |
| 📊 **1024 維特徵工程** | 價格、成交量、訂單簿、技術指標等 10 大類特徵 |
| 🎯 **三大策略融合** | RSI 背離、布林帶突破、MACD 趨勢跟隨 |
| 🛡️ **企業級風險管理** | 4 等級風險控制、Kelly Criterion、動態回撤監控 |
| 📰 **智能新聞分析** | 181 關鍵字過濾、自動情感分析、價格預測驗證 |
| 📈 **10 種市場狀態** | 自動識別趨勢、震盪、高波動等市場環境 |
| 🔌 **Binance Futures API** | 完整 REST + WebSocket 支持，含歷史數據整合 |

---

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements-crypto.txt
```

### 2. 配置 API 金鑰
編輯 `config/trading_config.py`:
```python
BINANCE_API_KEY = "your_api_key"
BINANCE_API_SECRET = "your_secret_key"
USE_TESTNET = True  # 建議先使用測試網
```

### 3. 運行交易系統
```bash
# 互動式交易系統
python use_crypto_trader.py

# 交易引擎 V2 (含 AI 整合)
python use_trading_engine_v2.py
```

---

## 📁 項目結構

```
BioNeuronai/
├── 📄 use_crypto_trader.py       # 互動式交易系統入口
├── 📄 use_trading_engine_v2.py   # AI 整合交易引擎
├── 📄 test_integration.py        # 系統整合測試
│
├── 📁 model/                     # AI 模型權重
│   └── my_100m_model.pth         # 111.2M MLP 模型 (424MB)
│
├── 📁 config/                    # 配置文件
│   ├── trading_config.py         # 交易參數配置
│   ├── trading_costs.py          # 交易成本配置
│   └── market_keywords.json      # 市場關鍵詞
│
├── 📁 src/bioneuronai/           # 核心交易代碼
│   ├── 📁 core/                  # 核心模組
│   │   ├── inference_engine.py   # 🧠 AI 推論引擎 (神經連結)
│   │   └── trading_engine.py     # 交易引擎
│   │
│   ├── 📁 analysis/              # 分析模組
│   │   ├── 📁 daily_report/      # 每日報告子模組
│   │   │   ├── __init__.py       # 模組初始化
│   │   │   ├── market_data.py    # 市場數據分析
│   │   │   ├── models.py         # 數據模型定義
│   │   │   ├── news_sentiment.py # 新聞情緒分析
│   │   │   ├── report_generator.py # 報告生成器
│   │   │   ├── risk_manager.py   # 風險評估
│   │   │   └── strategy_planner.py # 策略規劃
│   │   ├── 📁 keywords/          # 關鍵字系統子模組
│   │   │   ├── __init__.py       # 模組初始化
│   │   │   ├── loader.py         # 關鍵字載入器
│   │   │   ├── manager.py        # 關鍵字管理器
│   │   │   ├── models.py         # 關鍵字數據模型
│   │   │   └── static_utils.py   # 靜態工具函數
│   │   ├── 📁 news/              # 新聞分析子模組
│   │   │   ├── __init__.py       # 模組初始化
│   │   │   ├── analyzer.py       # 核心新聞分析器
│   │   │   ├── evaluator.py      # 規則評估器
│   │   │   └── models.py         # 新聞數據模型
│   │   ├── __init__.py           # 模組導出
│   │   ├── feature_engineering.py # 特徵工程 (1024維)
│   │   ├── keyword_learner.py    # 關鍵字學習器
│   │   ├── market_regime.py      # 市場狀態檢測
│   │   ├── news_prediction_loop.py # 新聞預測循環
│   │   └── README.md             # 分析模組說明
│   │   └── news_prediction_loop.py # 新聞預測循環
│   │
│   ├── 📁 strategies/            # 策略模組
│   │   ├── trend_following.py    # 趨勢跟隨策略
│   │   ├── swing_trading.py      # 波段交易策略
│   │   ├── mean_reversion.py     # 均值回歸策略
│   │   ├── breakout_trading.py   # 突破交易策略
│   │   └── strategy_fusion.py    # AI 策略融合
│   │
│   ├── 📁 trading/               # 交易管理模組
│   │   ├── risk_manager.py       # ✅ 風險管理器 (新增 4 方法)
│   │   ├── plan_controller.py    # 交易計劃控制器
│   │   └── pair_selector.py      # 交易對選擇器
│   │
│   ├── 📁 data/                  # 數據連接器
│   │   └── binance_futures.py    # ✅ Binance Futures API (新增 4 方法)
│   │
│   └── 📁 schemas/               # 數據結構定義
│       ├── trading.py            # 交易信號結構
│       ├── market.py             # 市場數據結構
│       └── risk.py               # 風險管理結構
│
├── 📁 docs/                      # 📚 完整文檔
│   ├── USER_MANUAL.md            # 用戶操作手冊
│   ├── CRYPTO_TRADING_GUIDE.md   # 交易指南
│   ├── TRADING_STRATEGIES_GUIDE.md # 策略詳解
│   └── NEWS_ANALYZER_GUIDE.md    # 新聞分析器使用手冊
│
├── 📄 RISK_MANAGEMENT_MANUAL.md  # 🛡️ 風險管理完整手冊
├── 📄 DATA_STORAGE_INTEGRATION.md # 💾 數據存儲整合方案
├── 📄 BINANCE_API_IMPLEMENTATION.md # 🔌 API 實現文檔
├── 📄 PROJECT_STATUS_ANALYSIS.md # 📊 項目狀態分析
│
└── 📁 trading_data/              # 交易數據
    ├── signals_history.json      # 信號歷史
    ├── strategy_weights.json     # 策略權重
    ├── risk_statistics.json      # ✅ 風險統計 (自動保存)
    └── trades_history.jsonl      # 交易記錄
```

---

## 🧠 AI 推論系統架構

### 核心組件

```
┌─────────────────────────────────────────────────────────────────┐
│                      InferenceEngine (神經連結)                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────┐ │
│  │ ModelLoader │→ │FeaturePipe │→ │  Predictor  │→ │ Signal │ │
│  │ (載入權重)   │  │(1024維特徵) │  │ (AI推論)    │  │Interpret│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     TradingEngine (交易引擎)                     │
├─────────────────────────────────────────────────────────────────┤
│  AI Signal Fusion = AI 預測 (40%) + 策略信號 (60%)               │
│  → 最終交易決策                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 特徵工程 (1024 維)

| 類別 | 維度 | 描述 |
|------|------|------|
| 價格特徵 | 128 | OHLCV、回報率、波動率 |
| 成交量特徵 | 96 | 成交量剖面、買賣量比 |
| 訂單簿特徵 | 128 | 深度、價差、不平衡度 |
| 技術指標 | 192 | RSI、MACD、布林帶等 |
| 微結構特徵 | 96 | 成交頻率、訂單流 |
| 市場狀態 | 64 | 趨勢強度、波動regime |
| 時間特徵 | 64 | 小時、星期、月份 |
| 情緒特徵 | 96 | 恐懼指數、多空比 |
| 清算特徵 | 96 | 清算熱力圖 |
| 資金費率 | 64 | 費率趨勢 |

### 市場狀態檢測 (10 種)

```
STRONG_UPTREND     ↗↗  強勢上漲
UPTREND            ↗   上漲趨勢
WEAK_UPTREND       →↗  弱勢上漲
RANGING            ↔   橫盤震盪
WEAK_DOWNTREND     →↘  弱勢下跌
DOWNTREND          ↘   下跌趨勢
STRONG_DOWNTREND   ↘↘  強勢下跌
HIGH_VOLATILITY    ⚡   高波動
BREAKOUT           💥   突破
CONSOLIDATION      📦   整理
```

---

## 💡 核心功能

### 🎯 三大交易策略

| 策略 | 類型 | 適用場景 | 信號 |
|------|------|----------|------|
| **RSI 背離** | 反轉 | 震盪市場 | 超買超賣 + 價格背離 |
| **布林帶突破** | 突破 | 趨勢啟動 | 帶寬收縮 + 量能突破 |
| **MACD 趨勢** | 趨勢 | 明確趨勢 | 金叉死叉 + 動量 |

### 🛡️ 風險管理系統 (v2.1 重大升級)

#### 四大核心功能
| 功能 | 描述 | 狀態 |
|------|------|------|
| **交易檢查** | 6 點驗證：信心度、回撤、交易次數、餘額、警報、槓桿 | ✅ 完成 |
| **交易記錄** | 自動記錄交易、更新每日計數器、追蹤回撤 | ✅ 完成 |
| **統計分析** | 12 項指標：勝率、獲利因子、夏普比率等 | ✅ 完成 |
| **餘額管理** | 峰值追蹤、回撤計算、自動警報 | ✅ 完成 |

#### 四級風險等級
```python
CONSERVATIVE: 每筆 1%風險，最大回撤 5%，夏普比率 > 0.8
MODERATE:     每筆 2%風險，最大回撤 10%，夏普比率 > 0.6  ⭐ 推薦
AGGRESSIVE:   每筆 3%風險，最大回撤 15%，夏普比率 > 0.5
HIGH_RISK:    每筆 5%風險，最大回撤 20%，夏普比率 > 0.3
```

#### 統計指標示例
- 📈 **勝率**: 62.68% (84勝/50敗)
- 💰 **獲利因子**: 2.08 (盈利/虧損比)
- 📊 **夏普比率**: 1.87 (風險調整後報酬)
- 📉 **最大回撤**: -8.45% (峰值下跌)

**詳細文檔**: [RISK_MANAGEMENT_MANUAL.md](RISK_MANAGEMENT_MANUAL.md)

### 📡 Binance Futures API 完整整合

| API 類型 | 功能 | 狀態 |
|----------|------|------|
| **WebSocket** | 實時行情、深度、清算數據 (毫秒級) | ✅ 完成 |
| **REST - 基礎** | 訂單執行、倉位查詢、槓桿設置 | ✅ 完成 |
| **REST - 高級** | 訂單簿、資金費率、未平倉合約、K線數據 | ✅ 完成 |
| **測試網支持** | Testnet 完整支持 | ✅ 完成 |

**詳細文檔**: [BINANCE_API_IMPLEMENTATION.md](BINANCE_API_IMPLEMENTATION.md)

---

## ⚙️ 配置說明

### 基本配置 (trading_config.py)

```python
# API 配置
BINANCE_API_KEY = "your_api_key"
BINANCE_API_SECRET = "your_secret_key"
USE_TESTNET = True  # True: 測試網, False: 實盤

# 交易配置
SYMBOL = "BTCUSDT"           # 交易對
LEVERAGE = 10                 # 槓桿倍數 (1-125)
POSITION_SIZE_USDT = 100     # 單次交易金額

# 風險管理
STOP_LOSS_PERCENTAGE = 2.0   # 止損百分比
TAKE_PROFIT_PERCENTAGE = 4.0 # 止盈百分比
MAX_TRADES_PER_DAY = 10      # 每日最大交易次數
MAX_DRAWDOWN = 0.10          # 最大回撤 10%

# AI 配置
ENABLE_AI_MODEL = True       # 啟用 AI 模型
AI_MIN_CONFIDENCE = 0.6      # AI 最低置信度
AI_SIGNAL_WEIGHT = 0.4       # AI 信號權重
```

---

## 📖 完整文檔

| 文檔 | 描述 |
|------|------|
| 📘 [用戶操作手冊](docs/USER_MANUAL.md) | **完整操作指南，必讀！** |
| 📗 [幣安測試網教學](BINANCE_TESTNET_STEP_BY_STEP.md) | 詳細測試網設置 |
| 📙 [交易指南](docs/CRYPTO_TRADING_GUIDE.md) | API 設置和基礎用法 |
| 📕 [策略詳解](docs/TRADING_STRATEGIES_GUIDE.md) | 策略原理深入解析 |
| 📓 [交易成本指南](docs/TRADING_COSTS_GUIDE.md) | 手續費和滑點說明 |

---

## 🧪 測試

```bash
# 運行整合測試
python test_integration.py

# 測試 125x 槓桿
python test_125x_leverage.py
```

### 測試結果預期

```
✅ 模組導入測試: 通過
✅ 推論引擎測試: 通過 (~22ms 延遲)
✅ 交易引擎測試: 通過
✅ 效能測試: 通過
```

---

## ⚠️ 風險警告

> **⚠️ 重要提示**
> 
> - 加密貨幣期貨交易具有**極高風險**，可能損失全部本金
> - 請務必先在 **Testnet 測試網**充分測試
> - 建議從**小額資金**開始，設置合理止損
> - AI 預測僅供參考，**不保證盈利**
> - 本系統不構成投資建議

---
完成度 | 說明 |
|------|------|--------|------|
| **AI 模型權重** | ✅ 正常 | 100% | 111.2M 參數已載入 |
| **推論引擎** | ✅ 正常 | 100% | ~22ms 平均延遲 |
| **風險管理器** | ✅ 正常 | 100% | ⭐ v2.1 新增 4 方法 |
| **新聞分析器** | ✅ 正常 | 100% | 181 關鍵字、47 文章源 |
| **市場關鍵字** | ✅ 正常 | 100% | SQLite 持久化 |
| **數據結構** | ✅ 正常 | 100% | 5 模組完整定義 |
| **Binance API** | ✅ 正常 | 100% | REST + WebSocket 完整 |
| **交易引擎** | ⚠️ 開發中 | 90% | 23 個錯誤待修正 |
| **特徵工程** | ✅ 正常 | 100% | 1024 維特徵提取 |
| **策略融合** | ✅ 正常 | 100% | AI + 傳統策略整合 |

---

## 🆕 v2.1 更新內容 (2026-01-22)

### 風險管理系統完整實現
1. ✅ **check_can_trade()** - 6 點交易驗證檢查
2. ✅ **record_trade()** - 自動交易記錄與追蹤
3. ✅ **get_risk_statistics()** - 12 項風險統計指標
4. ✅ **update_balance()** - 餘額與回撤管理

### 多幣種支持
- 移除所有硬編碼的 "BTCUSDT"
- 交易引擎支持任意交易對
- 策略模組動態配置交易對

### 完整文檔
- 📘 [風險管理完整手冊](RISK_MANAGEMENT_MANUAL.md) - 7 大章節
- 💾 [數據存儲整合方案](DATA_STORAGE_INTEGRATION.md) - 完整架構
- 🔌 [Binance API 實現文檔](BINANCE_API_IMPLEMENTATION.md) - 所有 API 方法延遲 |
| 交易引擎 | ✅ 正常 | AI 整合完成 |
| 特徵工程 | ✅ 正常 | 1024 維特徵提取 |
| 風險管理 | ✅ 正常 | 動態調整啟用 |

---

## 🗂️ 歸檔說明

本項目歷史版本和開發文件已移至 `archived/` 目錄：

- **archived/llm_development/** - 原始 LLM 開發代碼
- **archived/old_docs/** - 舊版文檔（含過時分析報告）
- **archived/pytorch_100m_model.py** - 模型定義（供參考）

詳見 [archived/ARCHIVE_INDEX.md](archived/ARCHIVE_INDEX.md)

---

## 📝 授權

MIT License

---

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

---

**🎯 開始你的 AI 交易之旅！**

```bash
python use_trading_engine_v2.py
```

