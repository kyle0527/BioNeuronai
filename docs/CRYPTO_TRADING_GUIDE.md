# 虛擬貨幣期貨交易系統使用指南

## 📚 目錄
1. [快速開始](#快速開始)
2. [幣安 API 設置](#幣安-api-設置)
3. [基本使用](#基本使用)
4. [進階功能](#進階功能)
5. [風險管理](#風險管理)
6. [常見問題](#常見問題)

---

## 🚀 快速開始

### 1. 安裝依賴

```bash
# 安裝所需套件
pip install websocket-client requests

# 或者使用 requirements.txt
pip install -r requirements.txt
```

### 2. 配置 API 密鑰

在 `config/trading_config.py` 中填入你的 API 密鑰：

```python
BINANCE_API_KEY = "your_api_key_here"
BINANCE_API_SECRET = "your_api_secret_here"
USE_TESTNET = True  # 建議先使用測試網
```

### 3. 運行系統

```bash
# 基本運行
python src/bioneuronai/crypto_futures_trader.py

# 或使用我們的主程序
python use_crypto_trader.py
```

---

## 🔑 幣安 API 設置

### 獲取 API 密鑰

#### 正式網（真實交易）
1. 登入 [Binance](https://www.binance.com/)
2. 進入 **API Management**
3. 創建新的 API Key
4. **重要：** 啟用 "Futures" 權限
5. 複製 API Key 和 Secret Key

#### 測試網（推薦新手）
1. 訪問 [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. 使用 GitHub 或 Google 賬號登入
3. 在右上角獲取測試網 API Key
4. **優點：** 使用虛擬資金，零風險練習

### API 權限設置
- ✅ 啟用讀取權限（Read）
- ✅ 啟用期貨交易（Enable Futures）
- ❌ 不要啟用提現權限（Withdraw）- 安全考量

### IP 白名單（可選）
為了安全，建議設置 IP 白名單：
```
# 在 Binance API 設置頁面添加：
- 你的服務器 IP
- 或選擇 "Unrestricted" 但風險較高
```

---

## 💡 基本使用

### 1. 獲取實時價格

```python
from src.bioneuronai.crypto_futures_trader import CryptoFuturesTrader

# 創建交易器
trader = CryptoFuturesTrader(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)

# 獲取當前價格
price = trader.get_real_time_price("BTCUSDT")
print(f"BTC 價格: ${price.price:,.2f}")
```

### 2. 監控市場

```python
# 開始實時監控（WebSocket）
trader.start_monitoring("BTCUSDT")

# 程序會持續運行，實時顯示：
# - 最新價格
# - AI 生成的交易信號
# - 置信度評分
```

### 3. 查看賬戶信息

```python
# 獲取賬戶摘要
account = trader.get_account_summary()
print(f"餘額: ${account['balance']:.2f}")
print(f"持倉數量: {len(account['positions'])}")
```

### 4. 手動執行交易

```python
from src.bioneuronai.crypto_futures_trader import TradingSignal

# 創建交易信號
signal = TradingSignal(
    action="BUY",
    symbol="BTCUSDT",
    confidence=0.85,
    reason="測試買入",
    target_price=45000,
    stop_loss=43000
)

# 執行交易
trader.execute_trade(signal)
```

---

## 🎯 進階功能

### 1. 多交易對監控

```python
# 同時監控多個幣種
symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

for symbol in symbols:
    trader.start_monitoring(symbol)
```

### 2. 自定義策略

修改 `AITradingStrategy.analyze_market()` 方法來實現你的策略：

```python
def analyze_market(self, market_data: MarketData) -> TradingSignal:
    # 你的自定義邏輯
    rsi = self.calculate_rsi(market_data)
    macd = self.calculate_macd(market_data)
    
    if rsi < 30 and macd > 0:
        return TradingSignal(
            action="BUY",
            symbol=market_data.symbol,
            confidence=0.9,
            reason="RSI 超賣 + MACD 金叉"
        )
    # ...
```

### 3. 回測歷史數據

```python
# 載入歷史價格數據
historical_prices = load_historical_data("BTCUSDT", days=30)

# 模擬交易
for price in historical_prices:
    signal = strategy.analyze_market(price)
    # 記錄結果...
```

### 4. 風險管理規則

```python
# 在 CryptoFuturesTrader 中添加：
def check_risk_limits(self, signal: TradingSignal) -> bool:
    """檢查風險限制"""
    
    # 1. 檢查最大持倉數
    if len(self.positions) >= MAX_POSITIONS:
        return False
    
    # 2. 檢查日交易次數
    if self.trades_today >= MAX_TRADES_PER_DAY:
        return False
    
    # 3. 檢查賬戶餘額
    account = self.get_account_summary()
    if account['balance'] < MIN_BALANCE:
        return False
    
    return True
```

---

## ⚠️ 風險管理

### 重要原則

1. **從小額開始**
   - 測試網練習至少 1 週
   - 正式交易先用最小金額
   - 逐步增加投入

2. **設置止損**
   ```python
   # 自動止損（建議 1-3%）
   STOP_LOSS_PERCENTAGE = 0.02
   ```

3. **控制槓桿**
   ```python
   # 新手建議 1-3 倍
   LEVERAGE = 1
   ```

4. **分散投資**
   - 不要把所有資金投入單一幣種
   - 建議 3-5 個不同的交易對

5. **監控系統**
   ```python
   # 啟用通知
   ENABLE_NOTIFICATIONS = True
   ```

### 風險檢查清單

- [ ] 已在測試網測試 7 天以上
- [ ] 設置了止損和止盈
- [ ] API 密鑰已限制權限（無提現）
- [ ] 投入金額在可承受損失範圍內
- [ ] 理解期貨交易風險
- [ ] 已設置 IP 白名單
- [ ] 定期檢查系統狀態

---

## ❓ 常見問題

### Q1: 為什麼連接失敗？

**A:** 檢查以下幾點：
1. API Key 是否正確
2. 是否使用了正確的網絡（測試網/正式網）
3. IP 是否在白名單中
4. 網絡連接是否正常

```python
# 測試連接
price = trader.get_real_time_price("BTCUSDT")
if price:
    print("✅ 連接成功")
else:
    print("❌ 連接失敗")
```

### Q2: WebSocket 斷線怎麼辦？

**A:** 系統會自動重連。如果持續斷線：
```python
# 檢查防火牆設置
# 或使用更穩定的網絡
```

### Q3: 如何計算盈虧？

**A:** 系統會自動計算：
```python
position = trader.positions[0]
pnl = (position.current_price - position.entry_price) * position.quantity
print(f"盈虧: ${pnl:.2f}")
```

### Q4: 可以 24/7 運行嗎？

**A:** 可以，但建議：
- 使用 VPS 或雲服務器
- 設置異常監控
- 定期檢查日誌
- 設置自動重啟機制

```bash
# 使用 nohup 在後台運行
nohup python use_crypto_trader.py > output.log 2>&1 &
```

### Q5: AI 策略準確率如何提高？

**A:** 優化建議：
1. 增加訓練數據
2. 調整參數（均線週期等）
3. 結合多個指標（RSI, MACD, 布林帶）
4. 持續回測和優化

### Q6: 測試網資金用完了怎麼辦？

**A:** 
```
1. 重新登入測試網網站
2. 點擊 "Get Test Funds"
3. 每日可領取一定額度的測試資金
```

---

## 📞 技術支持

遇到問題？
- 📧 Email: support@bioneuronai.com
- 💬 Telegram: @BioNeuronaiSupport
- 📖 文檔: https://docs.bioneuronai.com

⚠️ **免責聲明**：虛擬貨幣交易存在高風險，可能導致全部資金損失。本系統僅供學習和研究使用，使用者需自行承擔交易風險。
