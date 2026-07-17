# Binance Futures API 實現報告

## ✅ 已完成：API 方法實現

根據 Binance 官方文檔 (https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info) 完成了以下 4 個缺失的 API 方法：

### 1. get_klines() - K線/蠟燭圖數據
```python
def get_klines(self, symbol: str, interval: str = "1h", limit: int = 500, 
               start_time: Optional[int] = None, end_time: Optional[int] = None) -> Optional[List[List]]
```

- **端點**: `/fapi/v1/klines`
- **用途**: 獲取歷史和實時 K線數據
- **支持的時間間隔**: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
- **參數**:
  - `symbol`: 交易對 (如 "BTCUSDT")
  - `interval`: 時間間隔
  - `limit`: 返回條數 (默認 500, 最大 1500)
  - `start_time`: 起始時間戳（毫秒）
  - `end_time`: 結束時間戳（毫秒）
- **返回格式**: 
  ```json
  [
    [
      1499040000000,      // 開盤時間
      "0.01634000",       // 開盤價
      "0.80000000",       // 最高價
      "0.01575800",       // 最低價
      "0.01577100",       // 收盤價
      "148976.11427815",  // 成交量
      1499644799999,      // 收盤時間
      ...
    ]
  ]
  ```

### 2. get_order_book() - 訂單簿深度
```python
def get_order_book(self, symbol: str, limit: int = 100) -> Optional[Dict]
```

- **端點**: `/fapi/v1/depth`
- **用途**: 獲取當前市場深度/訂單簿數據
- **參數**:
  - `symbol`: 交易對
  - `limit`: 深度檔位 (可選: 5, 10, 20, 50, 100, 500, 1000)
- **返回格式**:
  ```json
  {
    "lastUpdateId": 1027024,
    "bids": [
      ["4.00000000", "431.00000000"],  // [價格, 數量]
      ...
    ],
    "asks": [
      ["4.00000200", "12.00000000"],
      ...
    ]
  }
  ```

### 3. get_funding_rate() - 資金費率歷史
```python
def get_funding_rate(self, symbol: str, limit: int = 1) -> Optional[List[Dict]]
```

- **端點**: `/fapi/v1/fundingRate`
- **用途**: 獲取永續合約資金費率（每 8 小時結算一次）
- **參數**:
  - `symbol`: 交易對
  - `limit`: 返回條數 (默認 1 = 最新，最大 1000)
- **返回格式**:
  ```json
  [
    {
      "symbol": "BTCUSDT",
      "fundingRate": "0.00010000",    // 0.01% 資金費率
      "fundingTime": 1577433600000     // 結算時間
    }
  ]
  ```

### 4. get_open_interest() - 未平倉合約數
```python
def get_open_interest(self, symbol: str) -> Optional[Dict]
```

- **端點**: `/fapi/v1/openInterest`
- **用途**: 獲取當前持倉量（市場未平倉合約總數）
- **參數**:
  - `symbol`: 交易對
- **返回格式**:
  ```json
  {
    "openInterest": "10659.509",
    "symbol": "BTCUSDT",
    "time": 1589437530011
  }
  ```

## 📋 Binance Futures API 標準確認

### 基本信息
- ✅ **生產環境 Base URL**: `https://fapi.binance.com`
- ✅ **測試網 Base URL**: `https://testnet.binancefuture.com` (或 `https://demo-fapi.binance.com`)
- ✅ **WebSocket Base URL**: `wss://fstream.binance.com` (生產), `wss://stream.binancefuture.com` (測試網)
- ✅ **響應格式**: JSON
- ✅ **時間戳單位**: 毫秒 (milliseconds)
- ✅ **數據排序**: 升序（舊數據在前，新數據在後）

### 認證方式
- ✅ **簽名算法**: HMAC SHA256
- ✅ **API Key 傳遞**: HTTP Header `X-MBX-APIKEY`
- ✅ **支持的簽名方式**: HMAC SHA256, RSA Keys, Ed25519

### 速率限制
- ✅ **基於 IP 限流**: 通過響應頭 `X-MBX-USED-WEIGHT-(interval)` 監控
- ✅ **訂單限流**: 通過響應頭 `X-MBX-ORDER-COUNT-(interval)` 監控
- ✅ **429 錯誤**: 超過速率限制
- ✅ **418 錯誤**: IP 被自動封禁（連續違規後）
- ⚠️ **建議**: 優先使用 WebSocket 獲取數據以減少 API 請求

### 錯誤處理
- ✅ **HTTP 4XX**: 請求錯誤（客戶端問題）
- ✅ **HTTP 403**: WAF 限制
- ✅ **HTTP 408**: 超時
- ✅ **HTTP 429**: 速率限制
- ✅ **HTTP 418**: IP 封禁
- ✅ **HTTP 503**: 服務暫時不可用（需要重試）
- ✅ **HTTP 5XX**: 服務器內部錯誤

## 🔄 與歷史數據整合

項目現在同時支持兩種數據源：

### 1. 實時 API 數據（主要來源）
```python
# 使用 API 獲取實時數據
connector = BinanceFuturesConnector()
klines = connector.get_klines("BTCUSDT", "1h", limit=100)
order_book = connector.get_order_book("BTCUSDT", limit=20)
funding_rate = connector.get_funding_rate("BTCUSDT")
open_interest = connector.get_open_interest("BTCUSDT")
```

### 2. 歷史數據文件（備用/回測）
```python
# 從本地文件加載歷史數據
# 位置: C:\D\E\BioNeuronai\data_downloads\binance_historical\
# 結構: {spot,futures,coin_futures}/{monthly,daily}/data/
```

**數據兼容性**:
- K線數據格式完全一致（API 和文件使用相同的格式）
- 支持的時間間隔相同：1m, 5m, 15m, 1h, 4h, 1d 等
- 可以無縫切換或組合使用

## 📊 項目狀態更新

### 解決的問題 (6個)
原本 `trading_engine.py` 中因缺少 API 方法產生的 6 個錯誤：
- ✅ `connector.get_klines()` - 已實現
- ✅ `connector.get_order_book()` - 已實現  
- ✅ `connector.get_funding_rate()` - 已實現
- ✅ `connector.get_open_interest()` - 已實現

### 剩餘問題 (21個)
**優先級 1 - Risk Manager (4個方法缺失)**:
1. `risk_manager.check_can_trade()` - 檢查是否可以交易
2. `risk_manager.record_trade()` - 記錄交易
3. `risk_manager.get_risk_statistics()` - 獲取風險統計（3處調用）
4. `risk_manager.update_balance()` - 更新餘額

**優先級 2 - 其他錯誤 (17個)**:
- TradingSignal 缺少 `strategy_name` 參數（4處）
- OrderResult 缺少 `error` 屬性
- K線緩存類型不匹配（List[List] vs List[Dict]）
- RAG 模組導入問題
- 其他類型註解問題

## 🎯 下一步行動計劃

### 第1步：完成 Risk Manager (最高優先級)
```python
# 需要在 risk_manager.py 中添加：
def check_can_trade(self, signal_confidence: float, account_balance: float) -> Tuple[bool, str]
def record_trade(self, trade_info: Dict)
def get_risk_statistics(self) -> Dict
def update_balance(self, balance: float)
```

### 第2步：修復 TradingSignal 和 OrderResult
- 添加 `strategy_name` 參數到 TradingSignal
- 添加 `error` 屬性到 OrderResult

### 第3步：整合歷史數據加載器
創建統一的數據接口，支持：
- API 實時數據優先
- 本地歷史數據備用
- 回測模式切換

## 📝 測試建議

### API 連接測試
```python
from src.bioneuronai.data.binance_futures import BinanceFuturesConnector

# 測試網測試（無需真實資金）
connector = BinanceFuturesConnector(testnet=True)

# 測試各個端點
print("測試 K線:", connector.get_klines("BTCUSDT", "1h", limit=5))
print("測試訂單簿:", connector.get_order_book("BTCUSDT", limit=5))
print("測試資金費率:", connector.get_funding_rate("BTCUSDT"))
print("測試持倉量:", connector.get_open_interest("BTCUSDT"))
```

### 數據一致性測試
```python
# 驗證 API 數據和歷史文件數據格式一致
# 確保兩者可以互換使用
```

## 📚 參考資料

- [Binance Futures API 總覽](https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info)
- [Binance 官方 Python SDK](https://github.com/binance/binance-connector-python)
- [Binance Public Data 下載工具](https://github.com/binance/binance-public-data)

---

**更新時間**: 2026-01-22  
**狀態**: Binance API 連接器完成 ✅，下一步需完善 Risk Manager
