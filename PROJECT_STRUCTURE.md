# 📂 BioNeuronAI 項目結構

**最後更新**: 2026年1月19日  
**項目專注**: 加密貨幣期貨交易系統

---

## 🎯 當前活躍文件 (Trading System)

### 根目錄
```
BioNeuronai/
├── README.md                              # 主項目說明 (已更新為交易系統)
├── CRYPTO_TRADING_README.md               # 交易系統完整指南 (600+ 行)
├── STRATEGIES_IMPLEMENTATION_SUMMARY.md   # 策略實施總結
├── PROJECT_STRUCTURE.md                   # 本文件 - 項目結構說明
│
├── use_crypto_trader.py                   # ⭐ 交易系統啟動器 (200+ 行)
├── test_trading_strategies.py             # ⭐ 策略測試工具 (300+ 行)
│
├── requirements-crypto.txt                # 交易系統依賴
├── requirements-dev.txt                   # 開發依賴
├── pyproject.toml                         # Python 項目配置
└── BioNeuronai.code-workspace             # VS Code 工作區
```

### 核心交易代碼 (src/bioneuronai/)
```
src/
├── __init__.py
└── bioneuronai/
    ├── __init__.py
    ├── crypto_futures_trader.py           # ⭐ 主交易系統 (570+ 行)
    │   ├── BinanceFuturesConnector        # Binance API 連接器
    │   ├── AITradingStrategy               # AI 交易策略基類
    │   └── CryptoFuturesTrader             # 交易系統協調器
    │
    ├── trading_strategies.py              # ⭐ 三大策略 + AI 融合 (800+ 行)
    │   ├── Strategy1_RSI_Divergence        # RSI 背離策略
    │   ├── Strategy2_Bollinger_Bands_Breakout  # 布林帶突破策略
    │   ├── Strategy3_MACD_Trend_Following  # MACD 趨勢跟隨策略
    │   └── StrategyFusion                  # AI 策略融合系統
    │
    └── self_improvement.py                # ⭐ AI 自我進化系統 (200+ 行)
        └── SelfImprovingAgent              # 自主學習代理
```

### 配置文件 (config/)
```
config/
└── trading_config.py                      # ⭐ 完整交易配置 (150+ 行)
    ├── Binance API 設置
    ├── 策略選擇
    ├── 風險管理參數
    ├── RSI 策略參數
    ├── 布林帶策略參數
    └── MACD 策略參數
```

### 交易文檔 (docs/)
```
docs/
├── CRYPTO_TRADING_GUIDE.md                # 📘 完整交易指南 (400+ 行)
├── TRADING_STRATEGIES_GUIDE.md            # 📗 策略詳解 (2000+ 行)
└── STRATEGIES_QUICK_REFERENCE.md          # 📙 快速參考 (500+ 行)
```

---

## 📦 歸檔文件 (Archived LLM Development)

### 歸檔結構
```
archived/
├── ARCHIVE_INDEX.md                       # 📋 歸檔文件索引和說明
│
├── llm_development/                       # LLM 開發相關
│   ├── bilingual_tokenizer.py             # 雙語分詞器
│   ├── bpe_tokenizer.py                   # BPE 分詞器
│   ├── generation_utils.py                # 文本生成工具
│   ├── hallucination_detection.py         # 幻覺檢測
│   ├── honest_generation.py               # 誠實生成
│   ├── inference_utils.py                 # 推理工具
│   ├── lora.py                            # LoRA 微調
│   ├── model_export.py                    # 模型導出
│   ├── quantization.py                    # 模型量化
│   ├── rag_system.py                      # RAG 檢索增強
│   ├── tiny_llm.py                        # 小型語言模型
│   ├── uncertainty_quantification.py      # 不確定性量化
│   ├── models/                            # 預訓練模型
│   ├── weights/                           # 模型權重
│   ├── training/                          # 訓練數據和腳本
│   └── tools/                             # 開發工具
│
├── old_docs/                              # LLM 文檔
│   ├── CAPABILITIES.md                    # 功能說明
│   ├── CHANGELOG.md                       # 變更記錄
│   ├── EVOLUTION.md                       # 演化歷程
│   ├── FINAL_REPORT.md                    # 最終報告
│   ├── HONESTY.md                         # 誠實機制
│   ├── HONESTY_REPORT.md                  # 誠實報告
│   ├── IMPROVEMENTS.md                    # 改進記錄
│   ├── QUICK_START.md                     # 快速開始
│   ├── RAG.md                             # RAG 文檔
│   ├── STATUS_FINAL.md                    # 最終狀態
│   ├── SUMMARY.md                         # 總結
│   ├── docs_README.md                     # 文檔 README
│   ├── QUICKSTART.md                      # 快速開始
│   ├── 大語言模型權重腳本分類.md           # 中文分類文檔
│   ├── 大語言模型權重腳本分類.docx         # Word 版本
│   └── 知識蒸餾訓練指南.md                 # 訓練指南
│
├── old_scripts/                           # LLM 使用腳本
│   ├── use_model.py                       # 模型使用工具
│   ├── use_model_evolving.py              # 演化模型腳本
│   └── use_rag.py                         # RAG 使用腳本
│
├── old_src/                               # 保留給未來使用
│
├── core.py                                # 舊神經元模組
├── hundred_million_net.py                 # 舊通用網絡
├── pytorch_100m_model.py                  # 舊 MLP 模型
└── README.md                              # 舊項目說明
```

**詳細說明**: 查看 [archived/ARCHIVE_INDEX.md](archived/ARCHIVE_INDEX.md)

---

## 🔍 文件分類

### ✅ 交易系統 (Active)
- **啟動器**: `use_crypto_trader.py`
- **測試器**: `test_trading_strategies.py`
- **核心交易**: `src/bioneuronai/crypto_futures_trader.py`
- **策略實現**: `src/bioneuronai/trading_strategies.py`
- **AI 進化**: `src/bioneuronai/self_improvement.py`
- **配置**: `config/trading_config.py`
- **文檔**: `docs/CRYPTO_TRADING_GUIDE.md` 等
- **依賴**: `requirements-crypto.txt`

### 📦 已歸檔 (Archived)
- **LLM 源碼**: `archived/llm_development/` (12 個模組)
- **LLM 文檔**: `archived/old_docs/` (16 個文檔)
- **LLM 腳本**: `archived/old_scripts/` (3 個腳本)
- **舊模組**: `archived/*.py` (3 個舊文件)

### ⚙️ 配置與元數據
- `pyproject.toml` - Python 項目元數據
- `requirements-dev.txt` - 開發依賴
- `BioNeuronai.code-workspace` - VS Code 工作區
- `PROJECT_STRUCTURE.md` - 本文件

---

## 📊 統計數據

### 代碼統計 (Trading System Only)
```
文件類型          文件數    代碼行數
─────────────────────────────────
Python 核心        3        1,570+
Python 配置        1          150+
Python 腳本        2          500+
Markdown 文檔      6        4,000+
─────────────────────────────────
總計              12        6,220+
```

### 歸檔統計 (LLM Development)
```
類型              數量
───────────────────────
Python 源碼       12 個模組
訓練腳本           4 個
使用腳本           3 個
文檔              16 個
目錄               4 個 (models, weights, training, tools)
```

---

## 🎯 使用指南

### 交易系統快速開始
```bash
# 1. 安裝依賴
pip install -r requirements-crypto.txt

# 2. 配置 API
# 編輯 config/trading_config.py

# 3. 測試策略
python test_trading_strategies.py

# 4. 啟動交易
python use_crypto_trader.py
```

### 查看歸檔文件
```bash
# 查看歸檔索引
cat archived/ARCHIVE_INDEX.md

# 列出 LLM 源碼
ls archived/llm_development/

# 查看舊文檔
ls archived/old_docs/
```

---

## 🔄 項目轉型歷史

### Phase 1: LLM 開發 (已完成)
- ✅ 124M 參數雙語語言模型
- ✅ 17 個核心能力
- ✅ 知識蒸餾訓練系統
- ✅ RAG 檢索增強生成
- 📦 **已歸檔至 archived/**

### Phase 2: 加密貨幣交易 (當前)
- ✅ Binance API 集成
- ✅ 三大交易策略
- ✅ AI 策略融合
- ✅ 風險管理系統
- ✅ 完整文檔
- 🚀 **正在使用中**

---

## 📝 維護注意事項

### 添加新功能
1. 所有交易相關代碼放在 `src/bioneuronai/`
2. 配置文件放在 `config/`
3. 文檔放在 `docs/`
4. 測試腳本放在根目錄

### 不要修改
- ❌ `archived/` - 歸檔文件，僅供參考
- ⚠️ 移動已歸檔文件需更新 `ARCHIVE_INDEX.md`

### 更新文檔
- 修改功能後更新相應的 `.md` 文檔
- 保持 `README.md` 與實際功能同步
- 記錄重大變更

---

## 🔗 相關文檔

- [主 README](README.md) - 項目主頁
- [交易指南](CRYPTO_TRADING_README.md) - 交易系統說明
- [策略詳解](docs/TRADING_STRATEGIES_GUIDE.md) - 策略深度文檔
- [歸檔索引](archived/ARCHIVE_INDEX.md) - LLM 開發歸檔

---

**項目狀態**: ✅ 活躍開發中  
**專注方向**: 加密貨幣期貨交易  
**技術棧**: Python 3.8+, Binance API, WebSocket, TA-Lib  
**上次整理**: 2026年1月19日
