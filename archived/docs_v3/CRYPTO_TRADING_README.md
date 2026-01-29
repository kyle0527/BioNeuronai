> ⚠️ **歸檔文檔** - 此為 v3.0 舊版 README，已於 2026年1月26日歸檔  
> 📖 **最新文檔**: 請參閱 [BIONEURONAI_MASTER_MANUAL.md](../../docs/BIONEURONAI_MASTER_MANUAL.md) (v4.0)

---

# 🚀 BioNeuronai 虛擬貨幣期貨交易系統

基於 AI 的智能加密貨幣期貨交易系統，整合 Binance Futures API 實現實時市場監控和自動交易決策。

**版本**: v3.0 (AI 整合版)  
**最後更新**: 2026年1月21日  
**狀態**: ⚠️ 已歸檔（僅供參考）

---

> 📘 **完整操作指南**: 請參閱 [用戶操作手冊](USER_MANUAL.md)

---

## 📋 目錄

1. [核心特性](#核心特性)
2. [快速開始](#快速開始)
3. [使用指南](#使用指南)
4. [系統架構](#系統架構)
5. [風險管理](#風險管理)
6. [故障排除](#故障排除)

---

## ✨ 核心特性

### 🧠 AI 神經網路驅動
- **111.2M 參數模型**: 完整 MLP 架構，~22ms 推論延遲
- **1024 維特徵工程**: 價格、成交量、訂單簿等 10 類特徵
- **AI 信號融合**: AI 預測 (40%) + 策略信號 (60%)

### 🔥 實時市場數據
- **WebSocket 連接**：毫秒級實時價格更新
- **多交易對支持**：同時監控 BTC, ETH, BNB 等多個幣種
- **市場深度數據**：獲取訂單簿、成交量、資金費率等完整信息

### 🤖 AI 驅動決策
- **智能信號生成**：基於技術分析自動生成交易信號
- **置信度評分**：每個信號都有 AI 計算的置信度（0-100%）
- **多策略支持**：移動平均線、RSI、MACD 等技術指標
- **自我進化**：可整合 BioNeuronai 的自我學習系統持續優化

### 🛡️ 風險管理
- **自動止損/止盈**：每筆交易自動設置風險控制
- **倉位管理**：智能控制每次交易的倉位大小
- **最大回撤保護**：超過設定回撤自動停止交易
- **日交易次數限制**：防止過度交易

### 🎯 用戶友好
- **測試網模式**：使用虛擬資金零風險練習
- **交互式界面**：簡單易用的命令行界面
- **詳細日誌**：記錄所有交易決策和執行過程
- **信號歷史**：保存所有 AI 生成的信號供分析

## 📦 快速開始

### 1. 安裝依賴

```bash
# 基本依賴
pip install -r requirements-crypto.txt

# 或手動安裝
pip install websocket-client requests
```

### 2. 配置 API 密鑰

編輯 `config/trading_config.py`：

```python
# 從 Binance 獲取你的 API Key
BINANCE_API_KEY = "your_api_key_here"
BINANCE_API_SECRET = "your_api_secret_here"

# 建議先使用測試網
USE_TESTNET = True  # 測試網地址: https://testnet.binancefuture.com
```

### 3. 運行系統

```bash
# 啟動交互式交易系統
python use_crypto_trader.py

# 或直接使用核心模塊
python src/bioneuronai/crypto_futures_trader.py
```

## 📖 使用指南

### 獲取 Binance API 密鑰

#### 測試網（推薦新手）🧪
1. 訪問 [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. 使用 GitHub/Google 賬號登入
3. 點擊右上角獲取 API Key
4. **零風險**：使用虛擬資金練習

#### 正式網 💰
1. 登入 [Binance](https://www.binance.com/)
2. 進入 **API Management**
3. 創建新 API Key 並啟用 **Futures** 權限
4. ⚠️ **重要**：不要啟用提現權限

### 基本使用示例

```python
from src.bioneuronai.crypto_futures_trader import CryptoFuturesTrader

# 創建交易器（測試網模式）
trader = CryptoFuturesTrader(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)

# 1. 獲取實時價格
price = trader.get_real_time_price("BTCUSDT")
print(f"BTC: ${price.price:,.2f}")

# 2. 查看賬戶
account = trader.get_account_summary()
print(f"餘額: ${account['balance']:.2f}")

# 3. 開始監控（WebSocket 實時數據）
trader.start_monitoring("BTCUSDT")
```

### 自動交易模式

```python
# ⚠️ 謹慎使用！建議在測試網充分測試後再啟用
trader.auto_trade = True

# 系統會根據 AI 信號自動執行交易
# 只有置信度 > 70% 的信號會被執行
```

## 🎯 系統架構

```
BioNeuronai/
├── src/bioneuronai/
│   ├── crypto_futures_trader.py    # 核心交易系統
│   └── self_improvement.py         # AI 自我進化系統
│
├── config/
│   └── trading_config.py           # 配置文件
│
├── docs/
│   └── CRYPTO_TRADING_GUIDE.md     # 詳細使用指南
│
├── use_crypto_trader.py            # 啟動腳本
└── requirements-crypto.txt         # 依賴列表
```

### 核心組件

#### 1. BinanceFuturesConnector
- 處理所有與 Binance API 的通信
- 支持 REST API 和 WebSocket
- 自動簽名認證

#### 2. AITradingStrategy
- AI 驅動的交易策略引擎
- 技術指標計算（MA, RSI, MACD）
- 生成帶置信度的交易信號

#### 3. CryptoFuturesTrader
- 整合連接器和策略
- 實時市場監控
- 自動/手動交易執行
- 風險管理和倉位控制

## 📊 監控和分析

### 實時監控

系統運行時會顯示：

```
💰 BTCUSDT: $43,250.50 | 信號: BUY (置信度: 85%)
   原因: 短期均線 (43200.00) 上穿長期均線 (43000.00)
   
🚀 自動買入信號！
✅ 交易成功: OrderId=12345678
```

### 信號歷史

所有 AI 生成的信號會保存到 `signals_history.json`：

```json
[
  {
    "action": "BUY",
    "symbol": "BTCUSDT",
    "confidence": 0.85,
    "reason": "短期均線上穿長期均線",
    "target_price": 44000.0,
    "stop_loss": 42500.0,
    "take_profit": 45000.0
  }
]
```

## ⚙️ 配置選項

### 交易配置

```python
# 監控的交易對
TRADING_PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

# 自動交易（謹慎開啟）
AUTO_TRADE_ENABLED = False

# 最大交易金額
MAX_TRADE_AMOUNT = 100.0  # USDT

# 槓桿倍數（1-125）
LEVERAGE = 1
```

### 風險管理

```python
# 止損比例
STOP_LOSS_PERCENTAGE = 0.02  # 2%

# 止盈比例
TAKE_PROFIT_PERCENTAGE = 0.03  # 3%

# 最大回撤
MAX_DRAWDOWN_PERCENTAGE = 0.10  # 10%

# 單日最大交易次數
MAX_TRADES_PER_DAY = 10
```

### AI 策略

```python
# 最低信號置信度
MIN_SIGNAL_CONFIDENCE = 0.7  # 70%

# 移動平均線週期
SHORT_MA_PERIOD = 5
LONG_MA_PERIOD = 20

# 價格歷史窗口
PRICE_HISTORY_SIZE = 100
```

## 🔒 安全建議

### 重要原則

1. **從測試網開始** 🧪
   - 至少練習 1 週
   - 理解系統運作
   - 測試各種策略

2. **控制風險** ⚠️
   - 只投入可承受損失的金額
   - 使用低槓桿（1-3 倍）
   - 設置嚴格止損

3. **API 安全** 🔐
   - 不要啟用提現權限
   - 設置 IP 白名單
   - 定期更換 API Key
   - 不要分享你的 Secret Key

4. **監控系統** 👀
   - 定期檢查日誌
   - 監控賬戶餘額
   - 及時處理異常

## 🚨 風險警告

⚠️ **重要免責聲明**：

- 加密貨幣交易具有極高風險
- 可能導致全部資金損失
- 過去表現不代表未來結果
- 本系統僅供學習和研究使用
- 使用者需自行承擔所有交易風險
- 作者不對任何損失負責

**建議**：
- 先在測試網充分練習
- 從小額開始
- 不要使用借貸資金
- 理解期貨交易機制
- 做好心理準備

## 📚 進階功能

### 整合自我進化系統

```python
from src.bioneuronai.self_improvement import SelfImprovementSystem

# 創建進化系統
evolution = SelfImprovementSystem("crypto_trading")

# 記錄交易結果
evolution.record_interaction(
    user_input=f"市場狀況: {market_data}",
    model_output=f"信號: {signal}",
    confidence_score=signal.confidence
)

# 添加反饋
evolution.add_feedback(
    interaction_id=interaction_id,
    feedback="excellent" if trade_profitable else "bad",
    correct_answer=f"應該 {correct_action}"
)

# 定期生成訓練數據
training_data = evolution.generate_training_data()
```

### 自定義策略

修改 `AITradingStrategy` 類實現你的策略：

```python
class MyCustomStrategy(AITradingStrategy):
    def analyze_market(self, market_data: MarketData) -> TradingSignal:
        # 計算 RSI
        rsi = self.calculate_rsi(market_data)
        
        # 計算 MACD
        macd, signal_line = self.calculate_macd(market_data)
        
        # 自定義邏輯
        if rsi < 30 and macd > signal_line:
            return TradingSignal(
                action="BUY",
                symbol=market_data.symbol,
                confidence=0.9,
                reason="RSI 超賣 + MACD 金叉"
            )
        # ...
```

## 🛠️ 疑難排解

### 常見問題

**Q: WebSocket 連接失敗？**
- 檢查網絡連接
- 確認 API Key 正確
- 檢查防火牆設置

**Q: 無法下單？**
- 確認 API 權限已啟用 Futures
- 檢查賬戶餘額
- 確認訂單參數正確

**Q: 測試網資金用完了？**
- 重新登入測試網網站
- 點擊 "Get Test Funds"
- 每日可領取測試資金

詳見 [完整使用指南](docs/CRYPTO_TRADING_GUIDE.md)

## 📞 技術支持

- 📧 Email: support@bioneuronai.com
- 💬 Telegram: @BioNeuronaiSupport
- 📖 文檔: [完整文檔](docs/CRYPTO_TRADING_GUIDE.md)
- 🐛 問題報告: [GitHub Issues](https://github.com/yourusername/BioNeuronai/issues)

## 📜 許可證

MIT License - 詳見 [LICENSE](LICENSE) 文件

## 🤝 貢獻

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何參與。

---

**記住**：加密貨幣交易存在高風險，請謹慎投資，理性決策！🚨
