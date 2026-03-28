# 📂 BioNeuronAI 項目結構

## 📑 目錄

1. 🎯 項目概覽
2. 🧠 核心模組 (src/bioneuronai/)
3. 📚 文檔結構 (docs/)
4. 💾 數據存儲 (trading_data/)
5. 🛠️ 開發工具 (tools/)
6. 🚀 快速開始
7. 📝 開發指南
8. 🔗 相關鏈接

---

## 🎯 項目概覽

### 統計數據
- **總文件數**: 451
- **Python 代碼**: 40,509 行 (102 個文件)
- **文檔**: 20,389 行 (56 個 Markdown 文件)
- **核心模型**: 111.2M 參數 AI 模型 (424MB)

### 技術棧
- **語言**: Python 3.11+
- **AI 框架**: PyTorch
- **數據庫**: SQLite (交易數據) + SQLite (關鍵字)
- **API**: Binance Futures REST + WebSocket
- **數據驗證**: Pydantic v2

---

## 🧠 核心模組 (src/bioneuronai/)

### 1. **core/** - 核心引擎 🎯

**核心功能**:
- ✅ 111.2M 參數 AI 模型推論 (~22ms 延遲)
- ✅ 1024 維特徵工程 (10 類特徵)
- ✅ Binance Futures WebSocket 實時數據
- ✅ AI + 策略信號融合
- ✅ 自動數據庫持久化

**主要文件**:
- `inference_engine.py` - AI 推論引擎 (1296 行)
- `trading_engine.py` - 交易引擎 (1045 行)
- `self_improvement.py` - 自我進化系統

---

### 2. **data/** - 數據層 💾

**數據架構**:
- ✅ SQLite 數據庫 (trading.db)
- ✅ 6 個核心表 (trades, signals, risk_stats, etc.)
- ✅ 自動備份機制 (JSON + JSONL)
- ✅ 高效索引查詢

**主要文件**:
- `database_manager.py` - 數據庫管理器 (662 行)
- `binance_futures.py` - Binance API 連接器
- `exchange_rate_service.py` - 匯率服務

---

### 3. **schemas/** - 數據結構 📋

**設計原則**:
- ✅ Pydantic v2 驗證
- ✅ 完整類型標註
- ✅ 統一數據源 (Single Source of Truth)
- ✅ 符合金融標準 (ISO 20022, FIX Protocol)

**核心 Schema**:
- `market.py` - 市場數據結構
- `trading.py` - 交易信號結構
- `risk.py` - 風險管理結構
- `orders.py` - 訂單結構
- `rag.py` - 新聞分析結構

---

### 4. **analysis/** - 分析模組 📊

**核心功能**:
- ✅ 實時新聞分析 (3 個 RSS 源)
- ✅ 181 個關鍵字智能過濾
- ✅ 市場狀態自動識別 (10 種)
- ✅ 關鍵字權重自我優化

**主要文件**:
- `news_analyzer.py` - 新聞分析器
- `market_keywords.py` - 關鍵字系統
- `feature_engineering.py` - 特徵工程
- `market_regime.py` - 市場狀態檢測

---

### 5. **trading/** - 交易模組 💼

**交易流程**:
1. 市場分析 → 策略選擇 → 交易對篩選
2. 信號生成 → 風險評估 → 交易前檢查
3. 訂單執行 → 記錄保存 → 統計更新

**主要文件**:
- `risk_manager.py` - 風險管理器 (1307 行)
- `market_analyzer.py` - 市場分析器
- `strategy_selector.py` - 策略選擇器
- `pretrade_automation.py` - 交易前檢查 (864 行)
- `sop_automation.py` - SOP 自動化 (934 行)

---

### 6. **strategies/** - 交易策略 📈

**策略系統**:
- ✅ RSI 背離策略
- ✅ 布林帶突破策略
- ✅ MACD 趨勢跟隨策略
- ✅ 動態權重調整
- ✅ 加權投票機制

**主要文件**:
- `strategy_fusion.py` - 策略融合
- `trend_following.py` - 趨勢跟隨策略
- `breakout_trading.py` - 突破交易策略
- `mean_reversion.py` - 均值回歸策略

---

## 📚 文檔結構 (docs/)

### 交易指南 🎯
- `CRYPTO_TRADING_GUIDE.md` - 加密貨幣交易完整指南
- `CRYPTO_TRADING_README.md` - 交易系統說明
- `BINANCE_TESTNET_STEP_BY_STEP.md` - 測試網詳細教學
- `TRADING_PLAN_10_STEPS.md` - 10 步交易計劃
- `TRADING_STRATEGIES_GUIDE.md` - 策略指南

### 風險管理 🛡️
- `RISK_MANAGEMENT_MANUAL.md` - 風險管理手冊
- `TRADING_COSTS_GUIDE.md` - 交易成本指南

### 數據與分析 📊
- `DATABASE_UPGRADE_GUIDE.md` - 數據庫升級指南
- `DATA_STORAGE_INTEGRATION.md` - 數據存儲整合
- `DATAFLOW_ANALYSIS.md` - 數據流分析
- `DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md` - 存儲策略

### 開發指南 🔧
- `CODE_FIX_GUIDE.md` - 代碼修復指南
- `USER_MANUAL.md` - 用戶操作手冊
- `NEWS_ANALYZER_GUIDE.md` - 新聞分析器指南

---

## 💾 數據存儲 (trading_data/)

### SQLite 主數據庫
```
trading.db
├── trades                       # 交易記錄表
├── signals                      # 信號歷史表
├── risk_stats                   # 風險統計表
├── pretrade_checks              # 交易前檢查表
├── news_analysis                # 新聞分析表
└── performance_metrics          # 性能指標表
```

### 數據分層
- **熱數據** (內存): 當前信號、持倉、緩存
- **溫數據** (SQLite): 近期交易 (90 天)
- **冷數據** (歸檔): 歷史備份

---

## 🛠️ 開發工具 (tools/)

- `generate_project_report.ps1` - 項目報告生成器
- `generate_tree_ultimate_chinese.ps1` - 目錄樹生成器
- `PROJECT_REPORT_*.txt` - 項目分析報告

---

## 🚀 快速開始

### 1. 環境配置
```bash
git clone https://github.com/kyle0527/BioNeuronai.git
cd BioNeuronai
pip install -r requirements-crypto.txt
```

### 2. 配置 API

> ⚠️ 本節部分過時：
> 這裡把 `config/trading_config.py` 視為主要 API 憑證配置方式，僅能作為舊版本地操作參考；
> 後續若涉及 UI、REST API、Binance 憑證流或 schema 設計，應以最新基準文件為優先。

編輯 `config/trading_config.py` 填入 Binance API 憑證

### 3. 運行系統
```bash
# 互動式交易系統
python use_crypto_trader.py

# AI 整合交易引擎
python use_trading_engine_v2.py
```

### 4. 數據遷移（首次使用）
```bash
python migrate_to_database.py
```

---

## 📝 開發指南

### 模組依賴順序
```
schemas (最底層)
  ↓
data (數據層)
  ↓
analysis (分析層)
  ↓
strategies (策略層)
  ↓
trading (交易層)
  ↓
core (核心引擎)
```

### 代碼規範
- 遵循 PEP 8
- 使用 Type Hints
- Pydantic v2 數據驗證
- 完整文檔註釋

---

## 🔗 相關鏈接

- **主文檔**: [README.md](README.md)
- **用戶手冊**: [docs/USER_MANUAL.md](docs/USER_MANUAL.md)
- **測試網教學**: [docs/BINANCE_TESTNET_STEP_BY_STEP.md](docs/BINANCE_TESTNET_STEP_BY_STEP.md)
- **風險管理**: [docs/RISK_MANAGEMENT_MANUAL.md](docs/RISK_MANAGEMENT_MANUAL.md)
- **數據庫升級**: [docs/DATABASE_UPGRADE_GUIDE.md](docs/DATABASE_UPGRADE_GUIDE.md)
