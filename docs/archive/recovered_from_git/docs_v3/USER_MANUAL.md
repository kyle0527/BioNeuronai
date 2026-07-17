> ⚠️ **歸檔文檔** - 此為 v3.1 舊版文檔，已於 2026年1月26日歸檔  
> 📖 **最新文檔**: 請參閱 [BIONEURONAI_MASTER_MANUAL.md](../../docs/BIONEURONAI_MASTER_MANUAL.md) (v4.0)

---

# 📘 BioNeuronAI 用戶操作手冊

**版本**: v3.1  
**最後更新**: 2026年1月22日  
**適用對象**: 加密貨幣期貨交易系統使用者  
**狀態**: ⚠️ 已歸檔（僅供參考）

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [環境安裝](#環境安裝)
3. [API 配置](#api-配置)
4. [快速啟動](#快速啟動)
5. [功能詳解](#功能詳解)
6. [SOP 自動化系統](#sop-自動化系統)
7. [AI 模型使用](#ai-模型使用)
8. [策略選擇指南](#策略選擇指南)
9. [數據庫管理](#數據庫管理)
10. [風險管理](#風險管理)
11. [故障排除](#故障排除)
12. [常見問題 FAQ](#常見問題-faq)

---

## 🎯 系統概述

### 什麼是 BioNeuronAI？

BioNeuronAI 是一個整合 AI 神經網路的加密貨幣期貨交易系統，具備以下特點：

- **AI 驅動決策**: 111.2M 參數的 MLP 模型提供智能預測
- **多策略融合**: 趨勢追隨、突破交易、均值回歸、波段交易等策略自動融合
- **SOP 自動化**: 10步驟標準作業流程自動執行
- **交易前檢查**: 自動風險評估與市場檢查
- **實時市場監控**: WebSocket 毫秒級行情推送
- **SQLite 數據庫**: 完整的數據持久化與查詢功能
- **完整風險管理**: 動態止損、倉位控制、回撤保護

### 系統架構

```
┌──────────────────────────────────────────────────────────┐
│                    用戶界面層                             │
│  ┌─────────────────┐  ┌─────────────────────────────┐   │
│  │ use_crypto_     │  │ use_trading_engine_v2.py    │   │
│  │ trader.py       │  │ (推薦: 含 AI 整合)           │   │
│  └────────┬────────┘  └─────────────┬───────────────┘   │
└───────────┼─────────────────────────┼───────────────────┘
            │                         │
┌───────────▼─────────────────────────▼───────────────────┐
│                    交易引擎層                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │              TradingEngine                       │    │
│  │  • 市場監控  • 信號處理  • 訂單執行  • AI 融合    │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    AI 推論層                             │
│  ┌─────────────────────────────────────────────────┐    │
│  │           InferenceEngine (神經連結)             │    │
│  │  ModelLoader → FeaturePipeline → Predictor      │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    策略分析層                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ RSI 背離策略  │ │ 布林帶突破   │ │ MACD 趨勢    │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │           StrategyFusion (策略融合器)            │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    數據連接層                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │        BinanceFuturesConnector                   │    │
│  │  REST API + WebSocket + 深度數據 + 清算流         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 環境安裝

### 系統要求

| 項目 | 最低要求 | 建議配置 |
|------|----------|----------|
| Python | 3.8+ | 3.10+ |
| 記憶體 | 4GB | 8GB+ |
| 硬碟空間 | 1GB | 2GB+ |
| 網路 | 穩定連線 | 低延遲 |

### 步驟 1: 安裝 Python

確認 Python 版本：
```bash
python --version
# 應該顯示 Python 3.8 或更高版本
```

### 步驟 2: 安裝依賴套件

```bash
# 進入項目目錄
cd C:\D\E\BioNeuronai

# 安裝交易系統依賴
pip install -r requirements-crypto.txt
```

**主要依賴**:
- `torch` - PyTorch 深度學習框架
- `numpy` - 數值計算
- `pandas` - 數據分析
- `websocket-client` - WebSocket 連接
- `requests` - HTTP 請求

### 步驟 3: 驗證安裝

```bash
# 運行整合測試
python test_integration.py
```

預期輸出：
```
✅ 測試 1: 模組導入測試 - 通過
✅ 測試 2: 推論引擎測試 - 通過
✅ 測試 3: 交易引擎測試 - 通過
✅ 測試 4: 效能測試 - 通過
```

---

## 🔑 API 配置

### 獲取 Binance API 金鑰

#### 方法 A: 測試網 (推薦新手)

1. 訪問 [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. 使用 GitHub 或 Google 帳號登入
3. 點擊右上角 **API Keys**
4. 複製 API Key 和 Secret Key

**優點**: 使用虛擬資金，零風險練習

#### 方法 B: 正式網 (真實交易)

1. 登入 [Binance](https://www.binance.com/)
2. 進入 **API Management**
3. 創建新 API Key
4. 啟用 **Futures** 權限
5. **不要**啟用提現權限

### 配置 API 金鑰

編輯 `config/trading_config.py`:

```python
# ======================================
# Binance API 配置
# ======================================

# 您的 API 金鑰 (必填)
BINANCE_API_KEY = "your_api_key_here"
BINANCE_API_SECRET = "your_api_secret_here"

# 測試網 vs 正式網
USE_TESTNET = True  # True: 測試網 (虛擬資金)
                    # False: 正式網 (真實資金)
```

### 驗證 API 連接

```bash
python -c "
from src.bioneuronai.connectors.binance_futures import BinanceFuturesConnector
from config.trading_config import BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET

connector = BinanceFuturesConnector(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)
print('連接測試:', '成功' if connector else '失敗')
"
```

---

## 🚀 快速啟動

### 啟動方式 1: 互動式交易系統

```bash
python use_crypto_trader.py
```

**功能選單**:
```
╔════════════════════════════════════════════╗
║       BioNeuronAI 交易系統                  ║
╠════════════════════════════════════════════╣
║  1. 獲取實時價格                            ║
║  2. 查看賬戶信息                            ║
║  3. 開始監控市場                            ║
║  4. 查看策略權重                            ║
║  5. 查看風險統計                            ║
║  6. 切換自動交易                            ║
║  7. 停止監控                                ║
║  8. 保存並退出                              ║
╚════════════════════════════════════════════╝
```

### 啟動方式 2: AI 整合交易引擎 (推薦)

```bash
python use_trading_engine_v2.py
```

此版本包含完整的 AI 模型整合，提供更智能的交易決策。

### 啟動方式 3: 程式化調用

```python
from src.bioneuronai.core.trading_engine import TradingEngine

# 創建交易引擎
engine = TradingEngine(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True,
    enable_ai_model=True  # 啟用 AI 模型
)

# 啟動監控
engine.start_monitoring("BTCUSDT")
```

---

## 📊 功能詳解

### 1. 實時價格查看

```python
# 獲取當前價格
price = engine.get_current_price("BTCUSDT")
print(f"BTC 當前價格: ${price:,.2f}")
```

### 2. 帳戶信息

```python
# 查看帳戶
account = engine.get_account_summary()
print(f"可用餘額: ${account['available_balance']:.2f}")
print(f"總資產: ${account['total_balance']:.2f}")
print(f"未實現盈虧: ${account['unrealized_pnl']:.2f}")
```

### 3. 市場監控

```python
# 開始監控 (WebSocket 實時數據)
engine.start_monitoring("BTCUSDT")

# 監控多個交易對
engine.start_monitoring(["BTCUSDT", "ETHUSDT", "BNBUSDT"])
```

### 4. 策略權重查看

```python
# 查看當前策略權重
weights = engine.get_strategy_weights()
for name, weight in weights.items():
    print(f"{name}: {weight:.2%}")
```

輸出範例：
```
RSI_Divergence: 35.2%
Bollinger_Breakout: 32.1%
MACD_Trend: 32.7%
```

### 5. 風險統計

```python
# 查看風險統計
stats = engine.get_risk_statistics()
print(f"今日交易次數: {stats['trades_today']}")
print(f"當前回撤: {stats['current_drawdown']:.2%}")
print(f"最大回撤: {stats['max_drawdown']:.2%}")
```

### 6. 手動下單

```python
# 市價買入
result = engine.place_order(
    symbol="BTCUSDT",
    side="BUY",
    quantity=0.001,
    stop_loss=95000,   # 止損價
    take_profit=105000  # 止盈價
)
```

### 7. 自動交易

```python
# 啟用自動交易
engine.enable_auto_trading()

# 停用自動交易
engine.disable_auto_trading()
```

⚠️ **警告**: 自動交易模式下，系統會根據 AI 信號自動執行交易。請確保風險參數設置正確。

---

## � SOP 自動化系統

### 什麼是 SOP 自動化？

SOP (Standard Operating Procedure) 自動化是系統核心功能，自動執行 10 步驟交易流程：

```
1. 新聞分析 (AI)         → 分析市場情緒
2. 市場狀態評估         → 識別趨勢/震盪/突破
3. 策略選擇             → 自動選擇最佳策略
4. 交易對篩選             → 多維度評分排序
5. 信號生成             → 策略融合生成信號
6. 風險檢查             → 倉位、風險散口
7. 倉位計算             → Kelly 公式計算
8. 交易前檢查           → 流動性、系統、賬戶
9. 訂單執行             → 市價/限價下單
10. 後續監控            → 止損止盈監控
```

### 使用 SOP 自動化

```python
from src.bioneuronai.trading import SOPAutomation
from src.bioneuronai.data import BinanceFuturesConnector

# 初始化
connector = BinanceFuturesConnector(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)
sop = SOPAutomation(connector)

# 執行完整 SOP 流程
results = sop.run_full_sop(
    symbols=['BTCUSDT', 'ETHUSDT'],
    initial_capital=10000
)

# 檢查結果
print(f"選擇策略: {results['selected_strategy']}")
print(f"交易信號: {results['signals']}")
print(f"風險評估: {results['risk_check']}")
```

### 數據存儲

所有 SOP 檢查結果雙重存儲：
- **JSON 文件**: `sop_automation_data/sop_check_*.json`
- **SQLite 數據庫**: `news_analysis` 表

### 交易前檢查

系統自動執行多項檢查：

```python
from src.bioneuronai.trading import PretradeAutomation

pretrade = PretradeAutomation(connector)

check_result = pretrade.run_pretrade_checks(
    symbol='BTCUSDT',
    side='BUY',
    quantity=0.1,
    price=45000
)

if check_result['passed']:
    print("✅ 所有檢查通過，可以交易")
else:
    print(f"❌ 檢查失敗: {check_result['errors']}")
```

**檢查項目**:
- ✅ 市場開放時間
- ✅ 交易對可用性
- ✅ 流動性充足性
- ✅ 帳戶餘額足夠
- ✅ 倉位限制
- ✅ 風險散口
- ✅ API 連接狀態

### 錯誤處理原則

⚠️ **重要**: 系統遵循嚴格的 Fail Fast 原則：

- ❌ **不使用模擬數據**
- ❌ **不使用緩存降級**
- ❌ **不跳過檢查步驟**
- ✅ **遇錯即停**
- ✅ **完整錯誤日誌**

---

## �🧠 AI 模型使用

### AI 模型概述

| 屬性 | 值 |
|------|-----|
| 模型架構 | MLP (多層感知機) |
| 參數量 | 111.2M |
| 輸入維度 | 1024 |
| 輸出維度 | 512 |
| 推論延遲 | ~22ms |
| 權重文件 | model/my_100m_model.pth |

### 啟用/停用 AI 模型

```python
# 啟用 AI 模型
engine = TradingEngine(
    api_key="...",
    api_secret="...",
    enable_ai_model=True,      # 啟用 AI
    ai_min_confidence=0.6      # 最低置信度閾值
)

# 運行時切換
engine.toggle_ai_model(enabled=False)  # 停用
engine.toggle_ai_model(enabled=True)   # 啟用
```

### AI 預測輸出

```python
# 獲取 AI 預測
prediction = engine.get_ai_prediction(market_data)

print(f"預測動作: {prediction['action']}")       # BUY/SELL/HOLD
print(f"置信度: {prediction['confidence']:.2%}") # 0-100%
print(f"風險等級: {prediction['risk_level']}")   # LOW/MEDIUM/HIGH
print(f"建議倉位: {prediction['position_size']:.2%}")
```

### AI 信號融合邏輯

系統自動融合 AI 預測和策略信號：

```
最終決策 = AI 信號 × 40% + 策略信號 × 60%
```

只有當融合後的置信度 > 60% 時，才會執行交易。

---

## 📈 策略選擇指南

### 三大策略比較

| 策略 | RSI 背離 | 布林帶突破 | MACD 趨勢 |
|------|----------|------------|-----------|
| **類型** | 反轉 | 突破 | 趨勢跟隨 |
| **適用市場** | 震盪盤整 | 趨勢啟動 | 明確趨勢 |
| **信號頻率** | 中 | 低 | 中 |
| **風險** | 中 | 高 | 低 |
| **持倉時間** | 短 | 中 | 長 |

### 市場環境對應

| 市場狀態 | 推薦策略 | 權重建議 |
|----------|----------|----------|
| 強勢上漲 ↗↗ | MACD | 50% MACD, 30% BB, 20% RSI |
| 橫盤震盪 ↔ | RSI | 50% RSI, 30% BB, 20% MACD |
| 高波動 ⚡ | 布林帶 | 50% BB, 30% RSI, 20% MACD |
| 突破 💥 | 布林帶 | 60% BB, 25% MACD, 15% RSI |

### 手動調整策略權重

```python
# 調整策略權重
engine.set_strategy_weights({
    "RSI_Divergence": 0.4,
    "Bollinger_Breakout": 0.35,
    "MACD_Trend": 0.25
})
```

---

## �️ 數據庫管理

### SQLite 數據庫

系統使用 SQLite 數據庫存儲所有交易數據：

**數據庫文件**: `trading_data/trading.db`

**表結構**:
```sql
trades              -- 交易記錄
signals             -- 信號歷史
risk_stats          -- 風險統計
pretrade_checks     -- 交易前檢查
news_analysis       -- 新聞分析
performance_metrics -- 性能指標
```

### 使用數據庫管理器

```python
from src.bioneuronai.data import get_database_manager

# 獲取數據庫管理器
db = get_database_manager()

# 保存交易
trade_id = db.save_trade({
    'order_id': '12345',
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'quantity': 0.1,
    'price': 45000,
    'timestamp': '2026-01-22T10:00:00'
})

# 查詢交易
trades = db.get_trades(
    start_date='2026-01-01',
    symbol='BTCUSDT',
    limit=100
)

# 獲取統計
stats = db.get_latest_risk_stats()
print(f"總交易次數: {stats['total_trades']}")
print(f"勝率: {stats['win_rate']:.2%}")
```

### 數據導出

```python
# 導出為 JSON
db.export_to_json(
    table_name='trades',
    output_file='trades_backup.json',
    start_date='2026-01-01'
)

# 獲取數據庫統計
stats = db.get_database_stats()
for table, count in stats.items():
    print(f"{table}: {count} 條記錄")
```

### 數據清理

```python
# 清理 90 天前的舊數據
deleted = db.cleanup_old_data(days=90)
print(f"已清理 {deleted} 條記錄")
```

### 數據備份

系統採用雙重備份策略：

1. **主要存儲**: SQLite 數據庫
2. **備份存儲**: JSONL 文件 (在相應目錄)

建議定期備份 `trading_data/trading.db` 文件。

---

## �🛡️ 風險管理

### 風險參數配置

編輯 `config/trading_config.py`:

```python
# ======================================
# 風險管理配置
# ======================================

# 單筆交易風險
MAX_RISK_PER_TRADE = 0.02      # 單筆最大風險 2%
STOP_LOSS_PERCENTAGE = 2.0     # 止損百分比
TAKE_PROFIT_PERCENTAGE = 4.0   # 止盈百分比

# 帳戶保護
MAX_DRAWDOWN = 0.10            # 最大回撤 10%
MAX_TRADES_PER_DAY = 10        # 每日最大交易次數

# 槓桿控制
MAX_LEVERAGE = 10              # 最大槓桿倍數
DEFAULT_LEVERAGE = 5           # 預設槓桿

# AI 置信度門檻
MIN_SIGNAL_CONFIDENCE = 0.65   # 最低置信度 65%
```

### 風險管理功能

#### 1. 動態倉位計算

系統根據帳戶餘額和風險參數自動計算倉位：

```
倉位 = (帳戶餘額 × 風險比例) / (入場價 × 止損幅度)
```

#### 2. 回撤保護

當帳戶回撤超過設定值時，系統自動暫停交易：

```python
# 查看回撤狀態
if engine.is_drawdown_exceeded():
    print("⚠️ 回撤保護已觸發，交易暫停")
```

#### 3. 交易頻率控制

```python
# 查看今日交易次數
trades_today = engine.get_trades_count_today()
if trades_today >= MAX_TRADES_PER_DAY:
    print("⚠️ 已達每日交易上限")
```

### 風險檢查清單

每次交易前，請確認：

- [ ] 止損價格已設置
- [ ] 倉位大小合理 (< 帳戶 10%)
- [ ] 槓桿不過高 (建議 ≤ 10x)
- [ ] 回撤未超過限制
- [ ] 今日交易次數未超限

---

## 🔧 故障排除

### 問題 1: 模組導入失敗

**錯誤信息**:
```
ModuleNotFoundError: No module named 'torch'
```

**解決方案**:
```bash
pip install torch
# 或重新安裝所有依賴
pip install -r requirements-crypto.txt
```

### 問題 2: API 連接失敗

**錯誤信息**:
```
ConnectionError: Unable to connect to Binance API
```

**檢查項目**:
1. 確認 API Key 和 Secret 正確
2. 確認網路連接正常
3. 確認是否使用正確的網域 (測試網 vs 正式網)
4. 檢查 API 權限是否啟用 Futures

### 問題 3: AI 模型載入失敗

**錯誤信息**:
```
FileNotFoundError: model/my_100m_model.pth not found
```

**解決方案**:
1. 確認 `model/` 目錄存在
2. 確認 `my_100m_model.pth` 文件存在
3. 檢查文件大小 (應約 424MB)

### 問題 4: WebSocket 斷線

**症狀**: 行情停止更新

**解決方案**:
```python
# 重新連接
engine.reconnect_websocket()
```

系統內建自動重連機制，通常會在 30 秒內自動恢復。

### 問題 5: 交易被拒絕

**可能原因**:
1. 餘額不足
2. 倉位超過限制
3. 交易對不支持
4. API 權限不足

**檢查**:
```python
# 檢查帳戶狀態
account = engine.get_account_summary()
print(f"可用餘額: {account['available_balance']}")
print(f"保證金率: {account['margin_ratio']}")
```

---

## ❓ 常見問題 FAQ

### Q1: 測試網和正式網有什麼區別？

| 項目 | 測試網 | 正式網 |
|------|--------|--------|
| 資金 | 虛擬資金 | 真實資金 |
| 風險 | 零風險 | 真實風險 |
| 行情 | 模擬 (接近真實) | 真實 |
| 適用 | 學習、測試 | 實際交易 |

### Q2: 建議從多少資金開始？

- **新手**: 從測試網開始，0 資金風險
- **進階**: 100-500 USDT，低槓桿 (1-5x)
- **有經驗**: 根據個人風險承受能力決定

### Q3: AI 模型準確率如何？

AI 模型提供的是概率預測，非確定性結論。實際表現受市場環境影響，建議：
- 結合多種策略信號
- 設置嚴格的風險管理
- 持續監控和調整

### Q4: 可以 24 小時自動運行嗎？

技術上可以，但建議：
- 定期檢查系統狀態
- 設置回撤保護
- 使用穩定的網路和電源
- 考慮使用雲伺服器

### Q5: 如何提高交易勝率？

1. 選擇適合當前市場的策略
2. 嚴格遵守風險管理規則
3. 不要過度交易
4. 定期回測和優化參數
5. 保持耐心，等待高置信度信號

---

## 📞 支援

遇到問題？

1. 查看本手冊的故障排除章節
2. 檢查 [GitHub Issues](https://github.com/kyle0527/BioNeuronai/issues)
3. 提交新 Issue 詳細描述問題

---

## 📝 版本歷史

| 版本 | 日期 | 更新內容 |
|------|------|----------|
| v3.1 | 2026-01-22 | SQLite 數據庫整合、SOP 自動化、交易前檢查 |
| v3.0 | 2026-01-21 | AI 模型整合、推論引擎、特徵工程 |
| v2.0 | 2026-01-19 | 三大策略實現、風險管理完善 |
| v1.0 | 2026-01-15 | 基礎交易系統、Binance API 整合 |

---

**祝您交易順利！** 🎯

> ⚠️ **免責聲明**: 本系統僅供學習和研究使用。加密貨幣交易具有高風險，可能損失全部本金。請謹慎投資，風險自負。
