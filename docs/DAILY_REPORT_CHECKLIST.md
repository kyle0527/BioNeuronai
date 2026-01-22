# 📋 daily_market_report.py 功能確認清單

> 最後更新: 2026-01-22  
> 檔案位置: `src/bioneuronai/analysis/daily_market_report.py`

---

## ✅ 已實現功能

### 1. 新聞情緒分析 ✅
- [x] 共享 CryptoNewsAnalyzer 實例
- [x] 讀取新聞分析結果
- [x] 情緒評分與關鍵事件
- [x] 與市場決策整合

**程式碼位置**: Line 362-393  
**狀態**: **完整實現，可直接使用**

---

### 2. 基礎策略選擇 ✅
- [x] 選擇 StrategyFusion
- [x] 返回策略參數

**程式碼位置**: Line 398-405  
**狀態**: **基本實現，可使用**

---

### 3. 風險參數計算 ✅
- [x] 1% 風險規則
- [x] 倉位大小計算
- [x] 每日交易限制

**程式碼位置**: Line 641-655  
**狀態**: **基本實現，可使用**

---

## ⚠️ 待實現功能

### 🔴 高優先級 - 需要外部 API 整合

#### 1. 全球市場數據 ⚠️
**功能**: 獲取美股期貨、亞洲市場、歐洲市場數據  
**當前狀態**: 返回 "NEUTRAL" 假數據  
**程式碼位置**: Line 322-339  
**優先級**: 🔴 高

**需要做什麼**:
```python
# 選項 1: TradingView API
- 需要註冊 TradingView API Key
- 整合 WebSocket 實時數據

# 選項 2: Yahoo Finance API
- 使用 yfinance 套件
- 獲取 S&P500, Nikkei, DAX 指數

# 選項 3: 簡化方案
- 只獲取 Bitcoin 恐慌貪婪指數
- API: https://api.alternative.me/fng/
```

**建議**: 先實現選項 3（最簡單），獲取恐慌貪婪指數即可

---

#### 2. 經濟日曆 ⚠️
**功能**: 檢查當日重要經濟數據發布  
**當前狀態**: 返回空列表  
**程式碼位置**: Line 344-358  
**優先級**: 🔴 高

**需要做什麼**:
```python
# 選項 1: Investing.com API
- 需要爬蟲或第三方 API
- 複雜度較高

# 選項 2: TradingEconomics API
- 需要付費訂閱
- 數據最完整

# 選項 3: 簡化方案
- 使用 FED Calendar RSS Feed
- 或手動配置重要日期
```

**建議**: 選項 3，手動配置重要日期（CPI、NFP、FOMC）到 JSON 檔案

---

#### 3. 回測系統整合 ⚠️
**功能**: 驗證交易計劃的歷史表現  
**當前狀態**: 返回 "NOT_IMPLEMENTED"  
**程式碼位置**: Line 622-639  
**優先級**: 🟡 中

**需要做什麼**:
```python
# 整合 data_downloads/run_backtest.py
1. 載入歷史數據
2. 執行策略回測
3. 計算性能指標:
   - 年化回報率
   - 最大回撤
   - 夏普比率
   - 勝率
```

**建議**: 先使用 `data_downloads/run_backtest.py` 獨立運行，暫時跳過此步驟

---

### 🟡 中優先級 - 使用模擬數據

#### 4. 市場狀況分析 🟡
**功能**: 分析當前市場趨勢、波動率  
**當前狀態**: 返回固定值 "NORMAL", "MEDIUM"  
**程式碼位置**: Line 410-420  
**優先級**: 🟡 中

**需要做什麼**:
```python
# 實際實現方案:
1. 從 Binance 獲取 K 線數據
2. 計算 ATR (Average True Range) 波動率
3. 使用 ADX 判斷趨勢強度
4. 返回實際市場狀況
```

**影響**: 影響策略選擇準確性

---

#### 5. 策略表現評估 🟡
**功能**: 評估各策略歷史表現  
**當前狀態**: 返回固定值 勝率 65.5%  
**程式碼位置**: Line 422-432  
**優先級**: 🟡 中

**需要做什麼**:
```python
# 實際實現方案:
1. 從 SQLite 數據庫讀取歷史交易記錄
2. 計算各策略的:
   - 勝率
   - 盈虧比
   - 最大回撤
3. 返回最佳策略
```

**影響**: 影響策略選擇決策

---

#### 6. 交易對流動性分析 🟡
**功能**: 計算流動性與波動性匹配  
**當前狀態**: 返回固定交易對 ["BTCUSDT", "ETHUSDT"]  
**程式碼位置**: Line 545-590  
**優先級**: 🟡 中

**需要做什麼**:
```python
# 實際實現方案:
1. 從 Binance 獲取所有交易對
2. 計算 24h 交易量
3. 計算波動率 (過去 7 天)
4. 篩選符合條件的交易對
```

**影響**: 影響交易對選擇準確性

---

## 🎯 優先處理順序

### 第一階段：核心功能可用 (1-2 天)
1. ✅ **恐慌貪婪指數** - 替代全球市場數據
2. ✅ **手動經濟日曆** - JSON 配置檔案
3. ✅ **基本市場分析** - 從 Binance 計算實際波動率

### 第二階段：精準度提升 (3-5 天)
4. ✅ **策略表現評估** - 從數據庫讀取歷史數據
5. ✅ **交易對流動性** - 實時計算 Binance 數據

### 第三階段：完整功能 (1-2 週)
6. ✅ **回測系統整合** - 整合 run_backtest.py
7. ✅ **外部市場 API** - TradingView 或 Yahoo Finance

---

## 🔧 快速修復方案

### 方案 1: 恐慌貪婪指數（最簡單）

```python
async def _get_global_market_data(self) -> Optional[Dict]:
    """獲取恐慌貪婪指數（簡化版全球市場情緒）"""
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        fng_value = int(data['data'][0]['value'])
        fng_class = data['data'][0]['value_classification']
        
        # 映射到市場狀態
        if fng_value >= 75:
            sentiment = "BULLISH"
        elif fng_value <= 25:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        return {
            "us_futures": sentiment,
            "asian_markets": sentiment,
            "european_markets": sentiment,
            "crypto_sentiment": fng_value / 100,  # 0-1 範圍
            "data_source": "Fear & Greed Index",
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"獲取恐慌貪婪指數失敗: {e}")
        return None
```

---

### 方案 2: 手動經濟日曆（JSON 配置）

創建 `config/economic_calendar.json`:
```json
{
  "2026-01": [
    {"date": "2026-01-15", "event": "CPI 數據發布", "importance": "high"},
    {"date": "2026-01-29", "event": "FOMC 會議", "importance": "critical"}
  ],
  "2026-02": [
    {"date": "2026-02-07", "event": "非農就業數據", "importance": "high"}
  ]
}
```

```python
async def _check_economic_calendar(self) -> List[str]:
    """從 JSON 配置讀取經濟日曆"""
    try:
        calendar_path = Path("config/economic_calendar.json")
        if not calendar_path.exists():
            return []
        
        with open(calendar_path, 'r', encoding='utf-8') as f:
            calendar = json.load(f)
        
        today = datetime.now()
        month_key = today.strftime("%Y-%m")
        today_str = today.strftime("%Y-%m-%d")
        
        events = calendar.get(month_key, [])
        today_events = [
            f"{e['event']} ({e['importance']})"
            for e in events if e['date'] == today_str
        ]
        
        return today_events
    except Exception as e:
        logger.error(f"讀取經濟日曆失敗: {e}")
        return []
```

---

## 📌 使用建議

### 當前可用功能
```python
# 1. 執行每日報告（使用新聞分析 + 基礎策略）
system = SOPAutomationSystem()
results = await system.execute_daily_premarket_check()

# 2. 查看新聞情緒分析
news_analysis = results['market_environment'].news_analysis
print(f"情緒評分: {news_analysis['sentiment_score']}")

# 3. 查看策略建議
strategy = results['trading_plan'].selected_strategy
print(f"推薦策略: {strategy}")
```

### 需要手動操作
```python
# 1. 全球市場 → 查看 CNN Fear & Greed Index
# 2. 經濟日曆 → 查看 Investing.com
# 3. 回測驗證 → 運行 data_downloads/run_backtest.py
```

---

## ✅ 下一步行動

### 立即可做
1. [ ] 實現恐慌貪婪指數 API（5 分鐘）
2. [ ] 創建經濟日曆 JSON 配置（10 分鐘）
3. [ ] 測試當前新聞分析功能

### 本週可做
4. [ ] 從 Binance 計算實際波動率
5. [ ] 實現策略表現數據庫讀取
6. [ ] 測試完整每日報告流程

### 長期目標
7. [ ] 整合 run_backtest.py
8. [ ] 實現外部市場 API
9. [ ] 完善所有 20 個步驟

---

**總結**: 
- ✅ **新聞分析已完成** - 可直接使用
- ⚠️ **3 個核心功能需要 API** - 可用簡化方案替代
- 🟡 **3 個分析功能使用模擬數據** - 不影響基本使用

**建議**: 先實現恐慌貪婪指數和經濟日曆 JSON，系統即可正常使用！
