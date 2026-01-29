# 📊 宏觀市場數據來源完整指南

**版本**: 1.0  
**最後更新**: 2026年1月22日  
**用途**: 步驟2 - 宏觀市場掃描數據抓取方案  
**狀態**: ✅ API 已驗證

---

## 📋 目錄

1. [數據需求清單](#數據需求清單按檢查頻率分類)
2. [詳細數據源配置](#詳細數據源配置)
3. [API 實現範例](#api-實現範例)
4. [錯誤處理](#錯誤處理)
5. [性能優化建議](#性能優化建議)
6. [監控與告警](#監控與告警)

---

## 🎯 數據需求清單（按檢查頻率分類）

根據**步驟2：宏觀市場掃描**，我們需要以下數據：

### 📅 每日必查指標（變化快，影響大）

| # | 指標名稱 | 數據來源 | 免費API | 檢查頻率 | 狀態 |
|---|---------|---------|---------|---------|------|
| 1 | 恐慌與貪婪指數 | Alternative.me | ✅ | 每天 | 🟢 可用 |
| 2 | 24小時交易量變化 | CoinGecko | ✅ | 每天 | 🟢 可用 |
| 3 | 全球市值變化率 | CoinGecko | ✅ | 每天 | 🟢 可用 |

### 📊 每週選查指標（變化慢，趨勢性）

| # | 指標名稱 | 數據來源 | 免費API | 檢查頻率 | 狀態 |
|---|---------|---------|---------|---------|------|
| 4 | BTC 市場占比 | CoinGecko | ✅ | 每週一次 | 🟢 可用 |
| 5 | DeFi TVL | DefiLlama | ✅ | 每週一次 | 🟢 可用 |
| 6 | 穩定幣供應總量 | CoinGecko | ✅ | 每週一次 | 🟢 可用 |

### 🚨 突發事件監控（新聞系統負責）

以下情況**不需要主動監控**，因為會在新聞中出現：
- ✅ BTC主導率劇烈變化（±5%）→ 新聞會報導
- ✅ 穩定幣大量流入/流出（>10億）→ 新聞會報導
- ✅ DeFi 重大協議遭駭 → 新聞會報導
- ✅ 監管重大變化 → 新聞會報導

> 💡 **策略優化**: 依賴現有的 RAG 新聞系統捕捉突發事件，避免過度查詢 API

---

## 📡 詳細數據源配置

### 1️⃣ 全球市值趨勢 + BTC 主導率

#### 主要來源：CoinGecko API（免費 ✅）

**API 端點**:
```
https://api.coingecko.com/api/v3/global
```

**請求限制**: 
- 免費：50 calls/分鐘
- 無需 API Key

**回傳數據**:
```json
{
  "data": {
    "total_market_cap": {
      "usd": 2500000000000
    },
    "total_volume": {
      "usd": 150000000000
    },
    "market_cap_percentage": {
      "btc": 48.5,
      "eth": 18.2
    },
    "market_cap_change_percentage_24h_usd": 2.3
  }
}
```

**實現代碼**:
```python
import aiohttp
import asyncio

async def fetch_global_market_data():
    """獲取全球市場數據（CoinGecko）"""
    url = "https://api.coingecko.com/api/v3/global"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "total_market_cap_usd": data["data"]["total_market_cap"]["usd"],
                        "total_volume_24h_usd": data["data"]["total_volume"]["usd"],
                        "btc_dominance": data["data"]["market_cap_percentage"]["btc"],
                        "eth_dominance": data["data"]["market_cap_percentage"].get("eth", 0),
                        "market_cap_change_24h": data["data"]["market_cap_change_percentage_24h_usd"],
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise Exception(f"CoinGecko API Error: {response.status}")
    except Exception as e:
        print(f"❌ 獲取全球市場數據失敗: {e}")
        return None
```

#### 備用來源：Binance API（免費 ✅）

**API 端點**:
```
https://api.binance.com/api/v3/ticker/24hr
```

**優點**: 
- 無請求限制
- 數據實時性強

**缺點**: 
- 只有 Binance 上的幣種
- 需要自己計算市值

---

### 2️⃣ 恐慌與貪婪指數

#### 主要來源：Alternative.me（免費 ✅）

**API 端點**:
```
https://api.alternative.me/fng/?limit=7&format=json
```

**請求限制**: 
- 免費，無需 API Key
- 無明確限制

**回傳數據**:
```json
{
  "name": "Fear and Greed Index",
  "data": [
    {
      "value": "65",
      "value_classification": "Greed",
      "timestamp": "1705622400",
      "time_until_update": "43200"
    }
  ]
}
```

**指數分級**:
- 0-24: Extreme Fear（極度恐慌）
- 25-49: Fear（恐慌）
- 50-74: Greed（貪婪）
- 75-100: Extreme Greed（極度貪婪）

**實現代碼**:
```python
async def fetch_fear_greed_index():
    """獲取恐慌與貪婪指數"""
    url = "https://api.alternative.me/fng/?limit=7&format=json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    latest = data["data"][0]
                    
                    return {
                        "index_value": int(latest["value"]),
                        "classification": latest["value_classification"],
                        "timestamp": latest["timestamp"],
                        "interpretation": _interpret_fng(int(latest["value"])),
                        "history_7d": [int(d["value"]) for d in data["data"]]
                    }
                else:
                    raise Exception(f"Alternative.me API Error: {response.status}")
    except Exception as e:
        print(f"❌ 獲取恐慌指數失敗: {e}")
        return None

def _interpret_fng(value: int) -> str:
    """解釋恐慌貪婪指數"""
    if value < 25:
        return "極度恐慌，可能是買入機會"
    elif value < 50:
        return "恐慌，市場悲觀"
    elif value < 75:
        return "貪婪，市場樂觀"
    else:
        return "極度貪婪，注意風險"
```

#### 備用方案：自建恐慌指數（完全免費 ✅）

如果 Alternative.me 無法訪問，可以基於以下數據自己計算：

**計算公式**:
```python
def calculate_custom_fear_greed(
    btc_volatility: float,      # 30日波動率
    btc_volume_change: float,   # 24h交易量變化
    btc_price_momentum: float,  # 7日價格動量
    market_dominance: float,    # BTC 市場占比
    social_sentiment: float     # 社交媒體情緒（從新聞）
) -> int:
    """
    自建恐慌貪婪指數（0-100）
    
    權重分配：
    - 波動率：25%（低波動率 = 貪婪）
    - 交易量：20%（高交易量 = 貪婪）
    - 價格動量：30%（上漲 = 貪婪）
    - BTC 主導率：15%（高主導率 = 恐慌）
    - 社交情緒：10%（正面 = 貪婪）
    """
    
    # 標準化各指標到 0-100
    vol_score = max(0, min(100, (1 - btc_volatility / 0.1) * 100))
    volume_score = max(0, min(100, 50 + btc_volume_change * 50))
    momentum_score = max(0, min(100, 50 + btc_price_momentum * 50))
    dominance_score = max(0, min(100, (1 - (market_dominance - 40) / 20) * 100))
    sentiment_score = max(0, min(100, (social_sentiment + 1) * 50))
    
    # 加權平均
    fng_index = (
        vol_score * 0.25 +
        volume_score * 0.20 +
        momentum_score * 0.30 +
        dominance_score * 0.15 +
        sentiment_score * 0.10
    )
    
    return int(fng_index)
```

---

### 3️⃣ 24小時交易量變化

#### 主要來源：CoinGecko API（已包含在全球數據中）

直接從步驟1的 `/global` 端點獲取。

#### 備用來源：Binance API

```python
async def fetch_24h_volume_change():
    """從 Binance 獲取 24h 交易量變化"""
    url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            
            return {
                "symbol": "BTCUSDT",
                "volume": float(data["volume"]),
                "quote_volume": float(data["quoteVolume"]),
                "volume_change": float(data["priceChangePercent"]),  # 近似
                "count": int(data["count"])
            }
```

---

### 4️⃣ 穩定幣流入/流出 🟡

#### 問題：主要數據源都是付費的

**付費來源**:
- ❌ Glassnode: $39-799/月
- ❌ CryptoQuant: $49-499/月
- ❌ Nansen: $150-3000/月

#### 免費替代方案 ✅

##### 方案A：監控交易所儲備金（間接指標）

```python
async def fetch_exchange_stablecoin_reserves():
    """
    監控主要交易所的穩定幣儲備
    可以通過已知的交易所地址查詢區塊鏈
    """
    # Binance USDT 熱錢包地址（示例）
    binance_usdt_addresses = [
        "0x28C6c06298d514Db089934071355E5743bf21d60",  # Binance 14
        # ... 更多地址
    ]
    
    # 可以使用免費的區塊鏈瀏覽器 API
    # 例如：Etherscan (免費配額：5 calls/秒)
    url = f"https://api.etherscan.io/api?module=account&action=tokenbalance&contractaddress=0xdac17f958d2ee523a2206206994597c13d831ec7&address={binance_usdt_addresses[0]}&tag=latest&apikey=YourApiKeyToken"
    
    # 實現細節...
```

##### 方案B：計算穩定幣市值變化（簡化版）

```python
async def fetch_stablecoin_supply_change():
    """
    通過 CoinGecko 獲取主要穩定幣的市值變化
    間接反映資金流入/流出
    """
    stablecoins = ["tether", "usd-coin", "binance-usd", "dai"]
    
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(stablecoins),
        "order": "market_cap_desc"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            
            total_supply = sum(coin["market_cap"] for coin in data)
            supply_change_24h = sum(
                coin["market_cap"] * coin["market_cap_change_percentage_24h"] / 100
                for coin in data
            )
            
            return {
                "total_stablecoin_supply": total_supply,
                "supply_change_24h": supply_change_24h,
                "flow_direction": "INFLOW" if supply_change_24h > 0 else "OUTFLOW",
                "stablecoins": [{
                    "name": coin["name"],
                    "market_cap": coin["market_cap"],
                    "change_24h": coin["market_cap_change_percentage_24h"]
                } for coin in data]
            }
```

##### 方案C：暫時跳過此指標 ⚠️

如果以上方案都太複雜，可以：
1. 先不實現穩定幣流動數據
2. 用其他5個指標完成宏觀掃描
3. 未來有預算再整合付費 API

---

### 5️⃣ DeFi 總鎖倉量 (TVL)

#### 主要來源：DefiLlama API（免費 ✅）

**API 端點**:
```
https://api.llama.fi/v2/protocols
```

**請求限制**: 
- 完全免費
- 無需 API Key
- 較寬鬆的請求限制

**實現代碼**:
```python
async def fetch_defi_tvl():
    """獲取 DeFi 總鎖倉量"""
    url = "https://api.llama.fi/v2/protocols"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 計算總 TVL
                    total_tvl = sum(p.get("tvl", 0) for p in data)
                    
                    # 獲取 Top 10 協議
                    top_protocols = sorted(
                        data, 
                        key=lambda x: x.get("tvl", 0), 
                        reverse=True
                    )[:10]
                    
                    return {
                        "total_tvl": total_tvl,
                        "total_protocols": len(data),
                        "top_10_protocols": [
                            {
                                "name": p["name"],
                                "tvl": p["tvl"],
                                "chain": p.get("chain", "multi"),
                                "change_24h": p.get("change_1d", 0)
                            }
                            for p in top_protocols
                        ],
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise Exception(f"DefiLlama API Error: {response.status}")
    except Exception as e:
        print(f"❌ 獲取 DeFi TVL 失敗: {e}")
        return None
```

**備用端點**（更簡單）:
```
https://api.llama.fi/charts
```

回傳全市場 TVL 歷史數據。

---

## 🔧 完整實現模組

### 創建統一的市場掃描器

**文件位置**: `src/bioneuronai/trading_plan/market_scanner.py`

```python
"""
宏觀市場掃描器 - 步驟2實現
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MacroMarketScanner:
    """
    宏觀市場數據掃描器
    
    整合多個免費 API，獲取市場全貌
    """
    
    def __init__(self):
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        self.fear_greed_url = "https://api.alternative.me/fng"
        self.defillama_url = "https://api.llama.fi"
        
    async def scan_all(self, check_frequency: str = "daily") -> Dict:
        """
        執行宏觀市場掃描（根據頻率調整檢查項目）
        
        Args:
            check_frequency: "daily" 每日檢查 / "weekly" 每週完整檢查
        
        Returns:
            Dict: 包含相應數據的結果
        """
        logger.info(f"🌍 開始宏觀市場掃描（模式: {check_frequency}）...")
        
        # 每日必查：恐慌指數 + 市場概況
        daily_tasks = [
            self.fetch_fear_greed_index(),
            self.fetch_global_market_data(),
        ]
        
        # 每週選查：DeFi TVL + 穩定幣
        weekly_tasks = [
            self.fetch_defi_tvl(),
            self.fetch_stablecoin_supply(),
        ] if check_frequency == "weekly" else []
        
        # 並行獲取數據
        results = await asyncio.gather(
            *daily_tasks,
            *weekly_tasks,
            return_exceptions=True
        )
        
        if check_frequency == "weekly":
            fng_data, global_data, tvl_data, stable_data = results
        else:
            fng_data, global_data = results
            tvl_data, stable_data = None, None
        
        # 整合結果
        scan_result = {
            "timestamp": datetime.now().isoformat(),
            "status": "SUCCESS",
            "data": {
                # 1. 全球市值與BTC主導率
                "market_overview": global_data if not isinstance(global_data, Exception) else None,
                
                # 2. 恐慌貪婪指數
                "fear_greed": fng_data if not isinstance(fng_data, Exception) else None,
                
                # 3. DeFi TVL
                "defi_tvl": tvl_data if not isinstance(tvl_data, Exception) else None,
                
                # 4. 穩定幣供應
                "stablecoin": stable_data if not isinstance(stable_data, Exception) else None,
            },
            "errors": []
        }
        
        # 記錄錯誤
        for i, (name, result) in enumerate([
            ("市場概況", global_data),
            ("恐慌指數", fng_data),
            ("DeFi TVL", tvl_data),
            ("穩定幣", stable_data)
        ]):
            if isinstance(result, Exception):
                scan_result["errors"].append(f"{name}: {str(result)}")
                logger.error(f"❌ {name} 獲取失敗: {result}")
        
        # 生成市場評估
        scan_result["assessment"] = self._assess_market_condition(scan_result["data"])
        
        logger.info("✅ 宏觀市場掃描完成")
        return scan_result
    
    async def fetch_global_market_data(self) -> Dict:
        """獲取全球市場數據（CoinGecko）"""
        url = f"{self.coingecko_url}/global"
        # [實現代碼如前所述]
    
    async def fetch_fear_greed_index(self) -> Dict:
        """獲取恐慌貪婪指數（Alternative.me）"""
        url = f"{self.fear_greed_url}/?limit=7&format=json"
        # [實現代碼如前所述]
    
    async def fetch_defi_tvl(self) -> Dict:
        """獲取 DeFi TVL（DefiLlama）"""
        url = f"{self.defillama_url}/v2/protocols"
        # [實現代碼如前所述]
    
    async def fetch_stablecoin_supply(self) -> Dict:
        """獲取穩定幣供應變化（CoinGecko）"""
        # [實現代碼如前所述]
    
    def _assess_market_condition(self, data: Dict) -> Dict:
        """
        綜合評估市場狀況
        
        Returns:
            Dict: 包含市場趨勢、風險等級、建議等
        """
        assessment = {
            "overall_trend": "UNKNOWN",
            "risk_level": "MEDIUM",
            "confidence": 0.0,
            "recommendations": []
        }
        
        # 根據數據進行評估...
        # (具體邏輯可以後續細化)
        
        return assessment
```

---

## ⚠️ 無法抓取數據時的處理策略

### 策略1: 優雅降級（Graceful Degradation）

```python
async def fetch_with_fallback(primary_func, fallback_func, default_value):
    """
    嘗試主要來源，失敗則使用備用，都失敗則返回預設值
    """
    try:
        result = await primary_func()
        if result:
            return result
    except Exception as e:
        logger.warning(f"主要數據源失敗: {e}")
    
    try:
        result = await fallback_func()
        if result:
            logger.info("使用備用數據源")
            return result
    except Exception as e:
        logger.error(f"備用數據源也失敗: {e}")
    
    logger.warning("使用預設值")
    return default_value
```

### 策略2: 本地緩存（Cache）

```python
import pickle
from pathlib import Path

class DataCache:
    """數據緩存系統"""
    
    def __init__(self, cache_dir="data_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def save(self, key: str, data: any, ttl_hours: int = 24):
        """保存數據到緩存"""
        cache_file = self.cache_dir / f"{key}.pkl"
        cache_data = {
            "data": data,
            "timestamp": datetime.now(),
            "ttl_hours": ttl_hours
        }
        with open(cache_file, "wb") as f:
            pickle.dump(cache_data, f)
    
    def load(self, key: str) -> Optional[any]:
        """從緩存載入數據"""
        cache_file = self.cache_dir / f"{key}.pkl"
        
        if not cache_file.exists():
            return None
        
        with open(cache_file, "rb") as f:
            cache_data = pickle.load(f)
        
        # 檢查是否過期
        age_hours = (datetime.now() - cache_data["timestamp"]).total_seconds() / 3600
        if age_hours > cache_data["ttl_hours"]:
            return None
        
        return cache_data["data"]

# 使用範例
cache = DataCache()

async def fetch_with_cache(key: str, fetch_func):
    """先嘗試緩存，失敗則抓取並緩存"""
    cached = cache.load(key)
    if cached:
        logger.info(f"使用緩存數據: {key}")
        return cached
    
    data = await fetch_func()
    if data:
        cache.save(key, data, ttl_hours=6)
    
    return data
```

### 策略3: 跳過非必要指標

```python
async def scan_essential_only(self) -> Dict:
    """
    只掃描必要指標（最小可行版本）
    
    必要指標：
    - ✅ 全球市值 + BTC 主導率（CoinGecko）
    - ✅ 恐慌貪婪指數（Alternative.me）
    
    可選指標：
    - ⚪ DeFi TVL（DefiLlama）
    - ⚪ 穩定幣流動（付費 API）
    """
    essential_data = await asyncio.gather(
        self.fetch_global_market_data(),
        self.fetch_fear_greed_index(),
        return_exceptions=True
    )
    
    return {
        "market_overview": essential_data[0],
        "fear_greed": essential_data[1],
        "mode": "ESSENTIAL_ONLY"
    }
```

### 策略4: 人工輸入（最後手段）

```python
def manual_market_assessment():
    """
    當所有自動化手段都失敗時，允許人工輸入市場評估
    """
    print("\n" + "="*70)
    print("⚠️  自動市場掃描失敗，請手動輸入市場狀況")
    print("="*70)
    
    btc_dominance = float(input("BTC 市場占比 (%): ") or "48")
    fear_greed = int(input("恐慌貪婪指數 (0-100): ") or "50")
    market_trend = input("市場趨勢 (BULLISH/BEARISH/SIDEWAYS): ") or "SIDEWAYS"
    
    return {
        "btc_dominance": btc_dominance,
        "fear_greed_index": fear_greed,
        "market_trend": market_trend,
        "source": "MANUAL_INPUT"
    }
```

---

## 📊 數據源總結

### 完全免費且可靠 ✅
1. **CoinGecko** - 市場概況、幣種數據
2. **Alternative.me** - 恐慌貪婪指數
3. **DefiLlama** - DeFi TVL
4. **Binance API** - 實時交易數據

### 免費但有限制 🟡
5. **Etherscan** - 區塊鏈數據（5 calls/秒）
6. **CoinMarketCap** - 市場數據（免費版有限制）

### 付費但值得考慮 ❌
7. **Glassnode** - 鏈上數據分析（$39+/月）
8. **CryptoQuant** - 交易所數據（$49+/月）

---

## 🚀 建議實施順序

### 第1階段：每日核心功能（立即實施）✅
- [x] Alternative.me 恐慌指數（每日）
- [x] CoinGecko 市場概況（每日）
- [x] 24h交易量變化（每日，已包含在市場概況）

### 第2階段：每週補充功能（低優先級）
- [ ] DefiLlama TVL 數據（每週一次）
- [ ] 穩定幣供應監控（每週一次，簡化版）
- [ ] BTC 主導率趨勢（每週一次，已包含在市場概況）

### 第3階段：優化與增強
- [ ] 數據緩存系統（避免重複查詢）
- [ ] 智能頻率調整（發現異常時自動增加檢查頻率）
- [ ] 與新聞系統聯動（新聞提到時觸發檢查）

### ❌ 不建議實施（性價比低）
- ~~整合付費 API~~（新聞系統已覆蓋突發事件）
- ~~每日監控穩定幣流動~~（變化慢，新聞會報導）
- ~~每日檢查 BTC 主導率~~（變化慢，趨勢性指標）

---

## 📝 相關文檔

- [10步驟交易計劃](./TRADING_PLAN_10_STEPS.md)
- [交易 SOP](./CRYPTO_TRADING_SOP.md)
- [API 錯誤處理指南](./API_ERROR_HANDLING.md) ← 待創建
