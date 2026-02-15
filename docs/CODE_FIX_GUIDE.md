# BioNeuronai 代碼修復與開發指南

> **基於 AIVA Common 專業化標準，適配加密貨幣交易系統**  
> **最後更新**: 2026年2月15日

---

## 📑 目錄

1. [核心原則](#核心原則)
   - [單一數據來源](#單一數據來源-single-source-of-truth)
   - [四層優先級原則](#四層優先級原則)
   - [程式可運行原則](#程式可運行原則)
   - [直接運作驗證原則](#直接運作驗證原則)
2. [修復前檢查清單](#修復前檢查清單)
   - [執行前必做事項](#執行前必做事項)
3. [批量修復規範](#批量修復規範)
   - [批量處理前置原則](#批量處理前置原則)
   - [批量處理禁忌](#批量處理禁忌)
4. [代碼定義規範](#代碼定義規範)
   - [禁止重複定義](#禁止重複定義)
   - [模組專屬定義判斷](#模組專屬定義判斷)
5. [Import 路徑規範](#import-路徑規範)
   - [標準導入結構](#標準導入結構)
   - [常見導入錯誤修復](#常見導入錯誤修復)
   - [路徑查找方法](#路徑查找方法)
6. [Schema 設計原則](#schema-設計原則)
   - [Pydantic v2 標準格式](#pydantic-v2-標準格式)
   - [Schema 修改檢查清單](#schema-修改檢查清單)
7. [錯誤處理最佳實踐](#錯誤處理最佳實踐)
   - [標準異常處理](#標準異常處理)
   - [重試機制](#重試機制)
8. [測試與驗證](#測試與驗證)
   - [單元測試範例](#單元測試範例)
   - [驗證命令](#驗證命令)
   - [實際執行驗證原則](#實際執行驗證原則)
9. [認知複雜度降低](#認知複雜度降低)
   - [認知複雜度增量規則](#認知複雜度增量規則)
   - [降低認知複雜度的最佳實踐](#降低認知複雜度的最佳實踐)
   - [本專案常見複雜函數修復策略](#本專案常見複雜函數修復策略)
   - [使用 Pylance 自動重構工具](#使用-pylance-自動重構工具)
   - [修復驗證清單](#修復驗證清單)
   - [延伸閱讀](#延伸閱讀)
10. [常見問題修復](#常見問題修復)
    - [問題 1: Import 路徑錯誤](#問題-1-import-路徑錯誤)
    - [問題 2: Schema 驗證失敗](#問題-2-schema-驗證失敗)
    - [問題 3: 類型標註不一致](#問題-3-類型標註不一致)
    - [問題 4: 配置檔案路徑](#問題-4-配置檔案路徑)
    - [問題 5: 資料庫路徑錯誤](#問題-5-資料庫路徑錯誤)
11. [保留未使用函數原則](#保留未使用函數原則)
12. [修復工作流程總結](#修復工作流程總結)
13. [快速參考](#快速參考)
    - [關鍵文檔位置](#關鍵文檔位置)
    - [常用命令](#常用命令)
    - [需要協助時](#需要協助時)
14. [附錄：標準資源連結](#附錄標準資源連結)
    - [金融交易標準](#金融交易標準)
    - [Python 標準](#python-標準)
    - [技術分析](#技術分析)
    - [開發工具](#開發工具)

---

## 核心原則

### 🎯 單一數據來源 (Single Source of Truth)

**基本理念**: `src/schemas/` 是所有數據結構的唯一定義來源

```python
# ✅ 正確做法 - 從 schemas 導入
from schemas.market import MarketData, OrderData
from schemas.trading import Signal, TradeResult
from schemas.rag import RAGNewsItem, NewsSentiment

# ❌ 錯誤做法 - 在其他模組重複定義
class MarketData(BaseModel):  # 禁止！schemas 已定義
    price: float
    volume: float
```

### 📊 四層優先級原則

```
┌─────────────────────────────────────────────────────────────┐
│  優先級 1: 金融交易標準 (最高優先級)                         │
│     • ISO 20022 (金融訊息標準)                              │
│     • FIX Protocol (金融資訊交換協議)                       │
│     • Binance API 標準 (交易所官方規範)                     │
│     • CCXT 統一接口 (加密貨幣交易標準)                      │
│     ✅ 必須嚴格遵循，不可自創                               │
│                                                              │
│  優先級 2: Python 語言標準                                   │
│     • PEP 8 (代碼風格)                                      │
│     • PEP 484 (類型標註)                                    │
│     • Pydantic v2 (數據驗證)                                │
│     ✅ 所有代碼必須符合                                     │
│                                                              │
│  優先級 3: BioNeuronai schemas 統一定義                     │
│     • MarketData, OrderData, Signal...                      │
│     • RAGNewsItem, NewsCategory, NewsSentiment...           │
│     • TradingState, Position, Balance...                    │
│     ✅ 系統內所有模組必須使用                               │
│                                                              │
│  優先級 4: 模組專屬定義 (最低優先級)                         │
│     • 僅當功能完全限於該模組內部時才允許                    │
│     ⚠️ 需經過審查確認不會與通用定義重複                     │
└─────────────────────────────────────────────────────────────┘
```

### 🚀 程式可運行原則

**基本理念**: 完整的程式應該本身就可以直接運行

```python
# ✅ 正確做法 - 程式自帶執行入口
if __name__ == "__main__":
    # 初始化必要元件
    config = load_config()
    
    # 執行主功能
    result = main(config)
    
    # 輸出結果
    print(f"執行結果: {result}")

# ❌ 錯誤做法 - 只有類和函數定義，無法直接運行
class MyStrategy:
    pass  # 沒有任何執行示例
```

**檢查要點**:
- 每個主要模組應有 `if __name__ == "__main__":` 區塊
- 執行入口應包含基本使用範例
- 應能獨立運行而不依賴外部測試檔

### 🔬 直接運作驗證原則

**基本理念**: 除非必要，優先讓程式直接運作進行驗證，而非依賴測試檔

```python
# ✅ 優先做法 - 直接在程式中驗證
if __name__ == "__main__":
    # 載入真實數據
    data = load_real_market_data("ETHUSDT", "1h")
    
    # 初始化策略
    strategy = TrendFollowingStrategy()
    
    # 實際運作驗證
    signal = strategy.generate_signal(data)
    print(f"✅ 策略運作正常: {signal}")

# ⚠️ 次要做法 - 只在必要時使用測試檔
# tests/test_trend_following.py
def test_trend_signal():
    # 使用 mock 數據測試（僅用於 CI/CD）
    ...
```

**適用場景**:
| 驗證方式 | 適用時機 |
|---------|---------|
| 直接運作 | 功能開發、整合測試、效能驗證 |
| 測試檔案 | CI/CD 自動化、邊界條件、錯誤處理 |

**優點**:
- 更快發現實際運作問題
- 減少 mock 與真實環境差異
- 直接觀察系統行為

---

## 修復前檢查清單

### ✅ 執行前必做事項

#### 1. 檢查現有定義

```bash
# 檢查是否已有相似的 Schema
grep -r "class YourClassName" src/schemas/

# 檢查功能是否已實現
grep -r "def your_function" src/bioneuronai/

# 搜尋相關配置
grep -r "your_config_key" config/
```

#### 2. 利用開發工具

```python
# Pylance MCP 工具（強烈推薦）:
# - mcp_pylance_mcp_s_pylanceFileSyntaxErrors: 檢查語法錯誤
# - mcp_pylance_mcp_s_pylanceImports: 分析導入關係
# - mcp_pylance_mcp_s_pylanceInvokeRefactoring: 自動重構

# Python 環境工具:
# - configure_python_environment: 配置環境
# - get_python_environment_details: 檢查已安裝套件
# - install_python_packages: 安裝依賴
```

#### 3. 查閱官方文檔

```python
# 交易所 API
fetch_webpage("https://binance-docs.github.io/apidocs/futures/en/")
fetch_webpage("https://ccxt.readthedocs.io/")

# Python 套件
fetch_webpage("https://docs.pydantic.dev/latest/")
fetch_webpage("https://pandas.pydata.org/docs/")

# 技術分析
fetch_webpage("https://ta-lib.org/")
```

#### 4. 選擇最佳方案

**判斷標準**:
```python
✅ 優先使用金融交易標準（Binance API, CCXT, FIX）
✅ 優先參考官方文檔和規範
✅ 類別命名使用 PascalCase
✅ 函數命名使用 snake_case
✅ Schema 必須繼承 BaseModel 並使用 Field()
⚠️ 避免自創標準，優先對接現有標準
⚠️ 新標準不確定時，先查詢官方規範
```

---

## 批量修復規範

### ⚠️ 批量處理前置原則

> **重要守則**: 在進行任何批量處理前，必須嚴格遵循以下原則以避免擴大問題範圍

#### 📋 批量處理流程

**階段一：全面分析並分類**
```python
# 1. 獲取完整錯誤清單
from tools import get_errors
errors = get_errors()

# 2. 對錯誤進行分類
syntax_errors = [e for e in errors if "SyntaxError" in e.type]
import_errors = [e for e in errors if "ImportError" in e.type]
type_errors = [e for e in errors if "TypeError" in e.type]

# 3. 識別依賴關係
# - 哪些錯誤會影響其他模組？
# - 修復順序是什麼？
```

**階段二：個別修復複雜錯誤**
```python
# ❌ 不適合批量處理：
# - 前向引用問題（需理解類定義順序）
# - 循環導入問題（需重構架構）
# - 方法簽名不一致（需理解業務邏輯）
# - 複雜的類型推導（需上下文分析）

# ✅ 適合批量處理：
# - 統一的語法替換（如 Dict → dict）
# - 導入語句修正（已知路徑模式）
# - 未使用變數清理
# - 統一的類型註解
```

**階段三：批量處理前二次確認**
```bash
# 確認所有待處理錯誤都屬於同一類型
# 驗證批量處理的模式和範圍
# 無法確定時，只以單一檔案為單位處理
```

**階段四：安全執行原則**
```python
# 每次只處理一種類型的錯誤
# 每次只處理一個檔案
# 處理後立即驗證結果
# 建立回退機制
```

### 🚨 批量處理禁忌

```bash
# ❌ 絕對禁止：
# 1. 跨多種錯誤類型的混合批量處理
# 2. 跨多個檔案的無差別批量替換
# 3. 未經二次確認的大範圍自動修復
# 4. 忽略錯誤依賴關係的盲目處理

# ✅ 正確流程：
# 1. 全面分析 → 2. 分類整理 → 3. 個別修復複雜問題
# → 4. 二次確認 → 5. 單一類型批量處理 → 6. 立即驗證
```

---

## 代碼定義規範

### 📝 禁止重複定義

```python
# ❌ 嚴格禁止 - 重複定義已存在的 Schema
# src/bioneuronai/trading/models.py
class MarketData(BaseModel):  # 錯誤！schemas.market 已定義
    price: float
    volume: float

# ❌ 嚴格禁止 - 重複定義已存在的配置類
class TradingConfig:  # 錯誤！config/trading_config.py 已定義
    leverage: int
    margin_type: str

# ✅ 正確做法 - 直接使用 schemas
from src.bioneuronai.schemas.market import MarketData
from config.trading_config import TradingConfig
```

### 🎯 模組專屬定義判斷

只有滿足**所有**以下條件時，才能在模組內定義專屬類別：

```python
✅ 允許自定義的情況:
1. 該類別僅用於模組內部，不會跨模組傳遞
2. 該類別與業務邏輯強綁定，無法抽象為通用概念
3. 該類別在 schemas 中不存在類似定義
4. 該類別未來不太可能被其他模組使用

# 範例：模組專屬類別（合理）
class BacktestState(BaseModel):
    """回測模組專屬的狀態 - 僅用於回測引擎內部"""
    current_bar: int
    positions_snapshot: Dict[str, Position]
    # 這些概念高度專屬於回測模組

class NewsParserCache:
    """新聞分析器專屬的快取 - 僅用於內部優化"""
    _cache: Dict[str, RAGNewsItem]
    _ttl: int
    # 內部實現細節，不需要標準化
```

```python
❌ 禁止自定義的情況（必須使用 schemas）:
1. 任何與市場數據相關 → 使用 schemas.market
2. 任何與訂單相關 → 使用 schemas.trading
3. 任何與新聞相關 → 使用 schemas.rag
4. 任何與技術指標相關 → 使用 schemas.indicators
5. 任何與風險管理相關 → 使用 schemas.risk

# 範例：必須使用 schemas（錯誤示範）
class MyPrice(BaseModel):  # ❌ 錯誤！
    value: float
    # 即使名稱不同，概念相同就必須使用 MarketData

class CustomSignal(BaseModel):  # ❌ 錯誤！
    action: str  # "buy" or "sell"
    # 必須使用 schemas.trading.Signal
```

---

## Import 路徑規範

### 📂 標準導入結構

```python
# ✅ 正確的導入順序和分組

# 1. 標準庫
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

# 2. 第三方套件
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

# 3. 本地 schemas（最高優先級）
from schemas.market import MarketData, OrderData
from schemas.trading import Signal, Position
from schemas.rag import RAGNewsItem

# 4. 本地配置
from config.trading_config import TradingConfig
from config.trading_costs import TradingCosts

# 5. 關鍵字管理（新聞分析）
from bioneuronai.analysis.market_keywords import KeywordManager
from bioneuronai.analysis.keyword_learner import KeywordLearner

# 5. 本地模組
from src.bioneuronai.data.binance_futures import BinanceFuturesConnector
from src.bioneuronai.strategies.base import BaseStrategy
```

### 🔍 常見導入錯誤修復

```python
# ❌ 錯誤 1: 錯誤的相對導入
from ..trading.data_fetcher import get_price  # 路徑不存在

# ✅ 正確: 使用正確的模組路徑
from src.bioneuronai.data.binance_futures import BinanceFuturesConnector

# ❌ 錯誤 2: 循環導入
# module_a.py
from src.bioneuronai.module_b import ClassB

# module_b.py
from src.bioneuronai.module_a import ClassA  # 循環！

# ✅ 正確: 使用 TYPE_CHECKING 避免循環
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.bioneuronai.module_a import ClassA

# ❌ 錯誤 3: 導入未使用的模組
from src.bioneuronai.data.binance_futures import BinanceFuturesConnector  # 未使用

# ✅ 正確: 只導入需要的
from src.bioneuronai.data.binance_futures import BinanceFuturesConnector
# 然後確實在代碼中使用它
connector = BinanceFuturesConnector()
```

### 📍 路徑查找方法

```bash
# 使用 grep 查找正確的模組位置
grep -r "class BinanceFuturesConnector" src/

# 使用 file_search 找到檔案
# 搜尋模式: **/binance*.py

# 使用 semantic_search 語義搜尋
# 查詢: "binance futures connector implementation"
```

---

## Schema 設計原則

### 🏗️ Pydantic v2 標準格式

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class TradingSignal(BaseModel):
    """交易信號 - 標準格式範例
    
    Attributes:
        symbol: 交易對符號 (如 BTCUSDT)
        action: 操作類型 (long/short/close)
        price: 觸發價格
        quantity: 交易數量
        timestamp: 信號產生時間
        confidence: 信號可信度 (0-1)
        strategy_name: 產生信號的策略名稱
        metadata: 額外資訊
    """
    
    # 必填欄位 - 使用 Field 添加描述
    symbol: str = Field(..., description="交易對符號", examples=["BTCUSDT"])
    action: str = Field(..., description="操作類型: long/short/close")
    price: float = Field(..., description="觸發價格", gt=0)
    quantity: float = Field(..., description="交易數量", gt=0)
    timestamp: datetime = Field(default_factory=datetime.now, description="信號產生時間")
    
    # 可選欄位 - 使用 Optional
    confidence: Optional[float] = Field(default=0.5, ge=0, le=1, description="信號可信度")
    strategy_name: Optional[str] = Field(default=None, description="策略名稱")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="額外資訊")
    
    # 驗證器 - 自訂驗證邏輯
    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        """驗證操作類型"""
        allowed = ['long', 'short', 'close']
        if v.lower() not in allowed:
            raise ValueError(f"action 必須是 {allowed} 之一")
        return v.lower()
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """驗證交易對格式"""
        if not v.endswith('USDT'):
            raise ValueError("目前只支援 USDT 交易對")
        return v.upper()
    
    # 配置
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "action": "long",
                    "price": 45000.0,
                    "quantity": 0.1,
                    "confidence": 0.85,
                    "strategy_name": "RSI_MACD_Strategy"
                }
            ]
        }
    }
```

### 📋 Schema 修改檢查清單

在提交修改前，確認以下項目：

- [ ] **基本結構**
  - [ ] 繼承自 `BaseModel`
  - [ ] 所有欄位都有類型標註
  - [ ] 必填欄位使用 `Field(...)`
  - [ ] 可選欄位使用 `Optional[T]`

- [ ] **文檔完整性**
  - [ ] 類別有完整的 docstring
  - [ ] 所有欄位都有 `description`
  - [ ] 有使用範例（`examples`）
  - [ ] 複雜邏輯有註解說明

- [ ] **驗證規則**
  - [ ] 數值範圍有限制（`gt`, `ge`, `lt`, `le`）
  - [ ] 字串格式有驗證（如正規表示式）
  - [ ] 列舉值有檢查（`@field_validator`）
  - [ ] 日期時間有預設值

- [ ] **向後兼容性**
  - [ ] 新增欄位使用可選或有預設值
  - [ ] 沒有移除現有必填欄位
  - [ ] 沒有改變現有欄位類型
  - [ ] 已測試舊代碼仍可運行

---

## 錯誤處理最佳實踐

### 🛡️ 標準異常處理

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TradingError(Exception):
    """交易系統基礎異常"""
    pass

class InsufficientBalanceError(TradingError):
    """餘額不足"""
    pass

class InvalidOrderError(TradingError):
    """無效訂單"""
    pass

class APIConnectionError(TradingError):
    """API 連接失敗"""
    pass

# ✅ 正確的異常處理範例
def execute_order(order: OrderData) -> Optional[TradeResult]:
    """執行訂單
    
    Args:
        order: 訂單數據
        
    Returns:
        交易結果，失敗時返回 None
        
    Raises:
        InsufficientBalanceError: 餘額不足
        InvalidOrderError: 訂單參數無效
        APIConnectionError: API 連接失敗
    """
    try:
        # 1. 參數驗證
        if order.quantity <= 0:
            raise InvalidOrderError(f"訂單數量必須大於 0: {order.quantity}")
        
        # 2. 餘額檢查
        balance = get_balance(order.symbol)
        required = order.quantity * order.price
        if balance < required:
            raise InsufficientBalanceError(
                f"餘額不足: 需要 {required}, 可用 {balance}"
            )
        
        # 3. 執行交易
        result = api_client.place_order(order)
        logger.info(f"訂單執行成功: {result.order_id}")
        return result
        
    except InvalidOrderError:
        # 業務邏輯錯誤 - 直接拋出
        raise
        
    except InsufficientBalanceError:
        # 業務邏輯錯誤 - 直接拋出
        raise
        
    except ConnectionError as e:
        # 網路錯誤 - 包裝後拋出
        logger.error(f"API 連接失敗: {e}")
        raise APIConnectionError(f"無法連接到交易所: {e}") from e
        
    except Exception as e:
        # 未預期的錯誤 - 記錄並返回 None
        logger.exception(f"執行訂單時發生未預期錯誤: {e}")
        return None
```

### 🔄 重試機制

```python
import time
from functools import wraps

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重試裝飾器
    
    Args:
        max_attempts: 最大嘗試次數
        delay: 初始延遲時間（秒）
        backoff: 延遲倍增因子
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} 失敗，已達最大重試次數")
                        raise
                    
                    logger.warning(
                        f"{func.__name__} 失敗 (嘗試 {attempt}/{max_attempts}), "
                        f"{current_delay:.1f}秒後重試: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
            raise last_exception
        return wrapper
    return decorator

# 使用範例
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def fetch_market_data(symbol: str) -> MarketData:
    """獲取市場數據（帶重試）"""
    return api_client.get_ticker(symbol)
```

---

## 測試與驗證

### 🧪 單元測試範例

```python
import pytest
from datetime import datetime
from src.bioneuronai.schemas.trading import Signal
from src.bioneuronai.strategies.rsi_strategy import RSIStrategy

class TestRSIStrategy:
    """RSI 策略測試"""
    
    def setup_method(self):
        """每個測試前執行"""
        self.strategy = RSIStrategy(
            symbol="BTCUSDT",
            rsi_period=14,
            oversold=30,
            overbought=70
        )
    
    def test_generate_buy_signal_when_oversold(self):
        """測試超賣時產生買入信號"""
        # 準備測試數據 - RSI = 25 (超賣)
        market_data = self._create_oversold_data()
        
        # 執行
        signal = self.strategy.generate_signal(market_data)
        
        # 驗證
        assert signal is not None
        assert signal.action == "long"
        assert signal.symbol == "BTCUSDT"
        assert signal.confidence > 0.6
    
    def test_generate_sell_signal_when_overbought(self):
        """測試超買時產生賣出信號"""
        # 準備測試數據 - RSI = 75 (超買)
        market_data = self._create_overbought_data()
        
        # 執行
        signal = self.strategy.generate_signal(market_data)
        
        # 驗證
        assert signal is not None
        assert signal.action == "short"
        assert signal.confidence > 0.6
    
    def test_no_signal_when_neutral(self):
        """測試中性區間不產生信號"""
        # 準備測試數據 - RSI = 50 (中性)
        market_data = self._create_neutral_data()
        
        # 執行
        signal = self.strategy.generate_signal(market_data)
        
        # 驗證
        assert signal is None
    
    def test_invalid_symbol_raises_error(self):
        """測試無效交易對拋出錯誤"""
        with pytest.raises(ValueError):
            RSIStrategy(symbol="INVALID")
    
    def _create_oversold_data(self):
        """創建超賣測試數據"""
        # 實現省略...
        pass
```

### ✅ 驗證命令

```bash
# 1. 類型檢查（使用 Pylance）
python -c "
from src.bioneuronai.trading.engine import TradingEngine
engine = TradingEngine()
"

# 2. 語法檢查
python -m py_compile src/bioneuronai/trading/engine.py

# 3. 執行測試
pytest tests/ -v

# 4. 測試覆蓋率
pytest tests/ --cov=src/bioneuronai --cov-report=html

# 5. 代碼風格檢查（如果有配置）
ruff check src/bioneuronai/

# 6. 實際執行驗證（最重要！）
python use_trading_engine_v2.py
```

### 💡 實際執行驗證原則

> **最佳實踐**: 實際執行程式本身就是最好的驗證，比寫測試腳本更準確、更直接。

```bash
# ✅ 最佳：直接執行實際功能驗證
python use_trading_engine_v2.py
python use_crypto_trader.py
python -m src.bioneuronai.analysis.news_analyzer

# ✅ 次選：必要時執行測試套件
pytest tests/ -v

# ❌ 錯誤：創建大量測試腳本卻不實際運行程式
```

---

## 認知複雜度降低

**認知複雜度 (Cognitive Complexity)** 是由 SonarSource 提出的代碼可讀性指標，用於衡量函數理解難度。

**核心概念**:
- **循環複雜度 (Cyclomatic Complexity)**: 計算控制流路徑數量
- **認知複雜度**: 衡量人類理解代碼的困難程度

**SonarQube 標準**: 單一函數認知複雜度不應超過 **15**

### 🎯 認知複雜度增量規則

```python
# +1: 每個流程控制語句
if condition:        # +1
    pass

for item in items:   # +1
    pass

while condition:     # +1
    pass

try:                 # +1
    pass
except:             # +1
    pass

# +1: 每個邏輯運算符（嵌套時額外計分）
if a and b:          # +1
if a or b or c:      # +1

# +嵌套層級: 嵌套結構會累加複雜度
if condition:        # +1
    if other:        # +2 (嵌套層級 1)
        if third:    # +3 (嵌套層級 2)
            pass

# +1: 遞歸調用
def recursive(n):
    if n > 0:
        return recursive(n-1)  # +1
```

---

### 🔧 降低認知複雜度的最佳實踐

#### ✅ 方法 1: 提取輔助函數（最推薦）

**原則**: 將複雜邏輯拆分為多個小函數，每個函數負責單一職責

```python
# ❌ 認知複雜度 = 23 (過高)
def execute_trade(self, signal: TradingSignal):
    if signal is None:
        return
    
    if signal.action == "long":
        if self.positions:
            if self.positions[0].side == "short":
                self._close_position()
        
        if self.risk_manager.check_risk(signal):
            if self.account_balance > signal.cost:
                if not self._check_market_hours():
                    logger.warning("非交易時段")
                    return
                
                if self._check_news_risk(signal.symbol):
                    logger.warning("新聞風險")
                    return
                
                order = self._create_order(signal)
                if order:
                    self._submit_order(order)
            else:
                logger.error("餘額不足")
        else:
            logger.error("風險檢查失敗")
    elif signal.action == "short":
        # 類似邏輯...
        pass

# ✅ 認知複雜度 < 10 (優化後)
def execute_trade(self, signal: TradingSignal):
    """執行交易 - 主流程"""
    if not self._validate_signal(signal):  # 提取驗證邏輯
        return
    
    if not self._handle_position_conflict(signal):  # 提取倉位處理
        return
    
    if not self._check_preconditions(signal):  # 提取前置檢查
        return
    
    self._execute_order(signal)  # 提取訂單執行

def _validate_signal(self, signal: TradingSignal) -> bool:
    """驗證信號有效性"""
    if signal is None:
        return False
    return signal.action in ["long", "short"]

def _handle_position_conflict(self, signal: TradingSignal) -> bool:
    """處理倉位衝突"""
    if not self.positions:
        return True
    
    current_side = self.positions[0].side
    if current_side != signal.action:
        self._close_position()
    return True

def _check_preconditions(self, signal: TradingSignal) -> bool:
    """檢查交易前置條件"""
    if not self.risk_manager.check_risk(signal):
        logger.error("風險檢查失敗")
        return False
    
    if self.account_balance <= signal.cost:
        logger.error("餘額不足")
        return False
    
    if not self._check_market_hours():
        logger.warning("非交易時段")
        return False
    
    if self._check_news_risk(signal.symbol):
        logger.warning("新聞風險")
        return False
    
    return True

def _execute_order(self, signal: TradingSignal):
    """執行訂單"""
    order = self._create_order(signal)
    if order:
        self._submit_order(order)
```

**優勢**:
- ✅ 每個函數職責單一，易於理解
- ✅ 易於測試和維護
- ✅ 可複用性高
- ✅ 認知複雜度大幅降低

---

#### ✅ 方法 2: 使用提前返回 (Early Return)

**原則**: 使用 Guard Clauses 提前處理異常情況，減少嵌套

```python
# ❌ 認知複雜度 = 17 (嵌套過深)
def analyze_market(self, data: MarketData):
    if data is not None:
        if data.volume > 1000:
            if data.price > self.threshold:
                if self._check_trend(data):
                    return self._generate_signal(data)
                else:
                    return None
            else:
                return None
        else:
            return None
    else:
        return None

# ✅ 認知複雜度 = 5 (使用提前返回)
def analyze_market(self, data: MarketData):
    """分析市場數據"""
    # Guard Clauses - 提前處理異常情況
    if data is None:
        return None
    
    if data.volume <= 1000:
        return None
    
    if data.price <= self.threshold:
        return None
    
    if not self._check_trend(data):
        return None
    
    # 主邏輯在最外層，無嵌套
    return self._generate_signal(data)
```

**優勢**:
- ✅ 減少嵌套層級
- ✅ 主邏輯更清晰
- ✅ 異常處理集中在開頭

---

#### ✅ 方法 3: 使用查詢表 (Lookup Table) / 策略模式

**原則**: 用數據結構替代複雜的 if-elif-else 鏈

```python
# ❌ 認知複雜度 = 19 (長 if-elif 鏈)
def get_market_status(self, sentiment: float, volatility: float):
    if sentiment > 0.7 and volatility < 0.3:
        return "BULLISH_STABLE"
    elif sentiment > 0.7 and volatility >= 0.3:
        return "BULLISH_VOLATILE"
    elif sentiment > 0.3 and sentiment <= 0.7 and volatility < 0.3:
        return "NEUTRAL_STABLE"
    elif sentiment > 0.3 and sentiment <= 0.7 and volatility >= 0.3:
        return "NEUTRAL_VOLATILE"
    elif sentiment <= 0.3 and volatility < 0.3:
        return "BEARISH_STABLE"
    elif sentiment <= 0.3 and volatility >= 0.3:
        return "BEARISH_VOLATILE"
    else:
        return "UNKNOWN"

# ✅ 認知複雜度 = 3 (使用查詢表)
def get_market_status(self, sentiment: float, volatility: float):
    """獲取市場狀態 - 使用分類邏輯"""
    sentiment_level = self._classify_sentiment(sentiment)
    volatility_level = self._classify_volatility(volatility)
    
    # 查詢表
    status_map = {
        ('high', 'low'): 'BULLISH_STABLE',
        ('high', 'high'): 'BULLISH_VOLATILE',
        ('medium', 'low'): 'NEUTRAL_STABLE',
        ('medium', 'high'): 'NEUTRAL_VOLATILE',
        ('low', 'low'): 'BEARISH_STABLE',
        ('low', 'high'): 'BEARISH_VOLATILE',
    }
    
    return status_map.get(
        (sentiment_level, volatility_level),
        'UNKNOWN'
    )

def _classify_sentiment(self, value: float) -> str:
    """分類情緒水平"""
    if value > 0.7:
        return 'high'
    elif value > 0.3:
        return 'medium'
    else:
        return 'low'

def _classify_volatility(self, value: float) -> str:
    """分類波動水平"""
    return 'high' if value >= 0.3 else 'low'
```

**優勢**:
- ✅ 邏輯清晰易懂
- ✅ 易於擴展新狀態
- ✅ 分類規則可獨立測試

---

#### ✅ 方法 4: 合併相似條件

**原則**: 將重複的條件判斷合併為單一條件

```python
# ❌ 認知複雜度 = 12 (重複判斷)
def check_risk(self, signal: TradingSignal):
    risk_score = 0
    
    if signal.confidence < 0.5:
        risk_score += 2
    
    if signal.volatility > 0.8:
        risk_score += 2
    
    if signal.volume_ratio < 0.5:
        risk_score += 1
    
    if signal.news_sentiment < -0.5:
        risk_score += 3
    
    if signal.market_trend == "bearish":
        risk_score += 2
    
    if risk_score > 5:
        return "HIGH_RISK"
    elif risk_score > 3:
        return "MEDIUM_RISK"
    else:
        return "LOW_RISK"

# ✅ 認知複雜度 = 6 (使用數據驅動)
def check_risk(self, signal: TradingSignal):
    """檢查風險等級 - 數據驅動方法"""
    # 定義風險因子及其權重
    risk_factors = [
        (signal.confidence < 0.5, 2),
        (signal.volatility > 0.8, 2),
        (signal.volume_ratio < 0.5, 1),
        (signal.news_sentiment < -0.5, 3),
        (signal.market_trend == "bearish", 2),
    ]
    
    # 計算總風險分數
    risk_score = sum(weight for condition, weight in risk_factors if condition)
    
    # 返回風險等級
    return self._classify_risk_level(risk_score)

def _classify_risk_level(self, score: int) -> str:
    """分類風險等級"""
    if score > 5:
        return "HIGH_RISK"
    elif score > 3:
        return "MEDIUM_RISK"
    else:
        return "LOW_RISK"
```

---

#### ✅ 方法 5: 使用狀態機 (State Machine)

**原則**: 對於複雜的狀態轉換邏輯，使用狀態機模式

```python
# ❌ 認知複雜度 = 30+ (複雜狀態轉換)
def process_order(self, order: Order):
    if order.status == "pending":
        if self._validate_order(order):
            if self._check_balance(order):
                order.status = "validated"
                if self._submit_to_exchange(order):
                    order.status = "submitted"
                    if self._wait_for_fill(order):
                        order.status = "filled"
                    else:
                        order.status = "partial"
                else:
                    order.status = "failed"
            else:
                order.status = "rejected"
        else:
            order.status = "invalid"
    elif order.status == "submitted":
        # 更多嵌套邏輯...
        pass

# ✅ 認知複雜度 < 8 (狀態機模式)
class OrderStateMachine:
    """訂單狀態機"""
    
    def __init__(self):
        self.transitions = {
            'pending': self._handle_pending,
            'validated': self._handle_validated,
            'submitted': self._handle_submitted,
            'partial': self._handle_partial,
        }
    
    def process(self, order: Order) -> Order:
        """處理訂單狀態轉換"""
        handler = self.transitions.get(order.status)
        if handler:
            return handler(order)
        return order
    
    def _handle_pending(self, order: Order) -> Order:
        """處理待處理訂單"""
        if not self._validate_order(order):
            order.status = 'invalid'
            return order
        
        if not self._check_balance(order):
            order.status = 'rejected'
            return order
        
        order.status = 'validated'
        return order
    
    def _handle_validated(self, order: Order) -> Order:
        """處理已驗證訂單"""
        if self._submit_to_exchange(order):
            order.status = 'submitted'
        else:
            order.status = 'failed'
        return order
    
    def _handle_submitted(self, order: Order) -> Order:
        """處理已提交訂單"""
        if self._check_fill_status(order):
            order.status = 'filled'
        elif self._is_partially_filled(order):
            order.status = 'partial'
        return order
    
    def _handle_partial(self, order: Order) -> Order:
        """處理部分成交訂單"""
        if self._check_complete(order):
            order.status = 'filled'
        return order
```

---

### 🎯 本專案常見複雜函數修復策略

根據 SonarQube 分析，以下是需要優先處理的高複雜度函數：

#### 📍 trading_engine.py

```python
# 問題函數:
# - __init__ (複雜度 17) → 提取初始化輔助函數
# - _fuse_signals (複雜度 23) → 提取信號融合邏輯
# - execute_trade (複雜度 27) → 使用方法 1 (提取輔助函數)

# 修復策略: 提取輔助函數 + 提前返回
```

#### 📍 swing_trading.py

```python
# 問題函數:
# - analyze_market (複雜度 32) → 拆分為多個分析函數
# - evaluate_entry_conditions (複雜度 38) → 使用查詢表 + 輔助函數
# - evaluate_exit_conditions (複雜度 51) → 拆分為 entry/exit/risk 三個函數
# - manage_position (複雜度 30) → 使用狀態機模式

# 修復策略: 大規模重構，使用方法 1 + 方法 5
```

#### 📍 pretrade_automation.py

```python
# 問題函數:
# - _calculate_risk (複雜度 21) → 使用方法 4 (合併相似條件)

# 修復策略: 數據驅動 + 提取輔助函數
```

---

### 🛠️ 使用 Pylance 自動重構工具

**推薦**: 使用 VS Code 內建的重構功能

```python
# 1. 選中需要提取的代碼塊
# 2. 右鍵 → Refactor → Extract Method
# 3. 或使用快捷鍵: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)

# Pylance 會自動:
# ✅ 識別需要傳遞的參數
# ✅ 識別返回值類型
# ✅ 生成函數簽名
# ✅ 更新調用點
```

**手動重構插件**:
```bash
# 安裝 Python Refactor 插件（如需要）
# Extension ID: ms-python.vscode-pylance (已內建)
```

---

### ✅ 修復驗證清單

完成重構後，請確認：

- [ ] 認知複雜度降至 15 以下
- [ ] 每個函數職責單一
- [ ] 函數名稱清晰描述功能
- [ ] 添加類型標註
- [ ] 添加 Docstring
- [ ] 原有測試仍然通過
- [ ] 執行 SonarQube 重新掃描確認

```bash
# 重新執行 SonarQube 分析
sonar-scanner \
  -Dsonar.projectKey=BioNeuronai \
  -Dsonar.sources=src \
  -Dsonar.python.version=3.11

# 或使用 get_errors 檢查
python -c "
from tools import get_errors
errors = get_errors()
print(f'剩餘錯誤數: {len(errors)}')
"
```

---

### 📚 延伸閱讀

- **SonarSource 認知複雜度白皮書**: https://www.sonarsource.com/resources/cognitive-complexity/
- **Clean Code (Robert C. Martin)**: 函數應該短小精悍
- **Refactoring (Martin Fowler)**: 重構技巧大全
- **Python 設計模式**: 使用設計模式降低複雜度

---

## 常見問題修復

### 問題 1: Import 路徑錯誤

```python
# ❌ 錯誤
from ..trading.data_fetcher import get_price
# ModuleNotFoundError: No module named 'trading.data_fetcher'

# ✅ 修復步驟
# 1. 搜尋正確位置
grep -r "def get_price" src/

# 2. 發現正確路徑
# src/bioneuronai/data/binance_futures.py: def get_ticker_price(...)

# 3. 使用正確導入
from src.bioneuronai.data.binance_futures import BinanceFuturesConnector
connector = BinanceFuturesConnector()
price_data = connector.get_ticker_price(symbol)
```

### 問題 2: Schema 驗證失敗

```python
# ❌ 錯誤
signal = Signal(
    symbol="BTC",  # 錯誤：應該是 BTCUSDT
    action="buy",  # 錯誤：應該是 long
    price=-100     # 錯誤：價格不能為負
)
# ValidationError: ...

# ✅ 修復
signal = Signal(
    symbol="BTCUSDT",  # 正確格式
    action="long",     # 使用標準術語
    price=45000.0,     # 正數價格
    quantity=0.1,
    timestamp=datetime.now()
)
```

### 問題 3: 類型標註不一致

```python
# ❌ 錯誤
def process_data(data):  # 缺少類型標註
    return data

# ❌ 錯誤
def fetch_price(symbol: str):  # 缺少返回類型
    return get_price(symbol)

# ✅ 正確
from typing import Optional
from src.bioneuronai.schemas.market import MarketData

def process_data(data: MarketData) -> MarketData:
    """處理市場數據"""
    return data

def fetch_price(symbol: str) -> Optional[float]:
    """獲取價格，失敗時返回 None"""
    try:
        market_data = get_price(symbol)
        return market_data.price
    except Exception as e:
        logger.error(f"獲取價格失敗: {e}")
        return None
```

### 問題 4: 配置檔案路徑

```python
# ❌ 錯誤
with open("trading_config.json") as f:  # 相對路徑不可靠
    config = json.load(f)

# ✅ 正確
from pathlib import Path

# 方法 1: 使用項目根目錄
PROJECT_ROOT = Path(__file__).parent.parent.parent
config_file = PROJECT_ROOT / "config" / "trading_config.json"

# 方法 2: 使用配置模組
from config.trading_config import TradingConfig
config = TradingConfig()
```

### 問題 5: 資料庫路徑錯誤

```python
# ❌ 錯誤
with open("news_records.json") as f:  # 路徑不明確
    records = json.load(f)

# ✅ 正確
from pathlib import Path

# 使用標準資料目錄
DATA_DIR = Path(__file__).parent.parent.parent / "sop_automation_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

news_records_file = DATA_DIR / "news_records.json"

# 讀取時檢查檔案是否存在
if news_records_file.exists():
    with open(news_records_file, 'r', encoding='utf-8') as f:
        records = json.load(f)
else:
    records = []
```

---

## 保留未使用函數原則

> **重要原則**: 在程式碼修復過程中，若發現有定義但尚未使用的函數或方法，只要不影響程式正常運作，建議予以保留。

**原因**:
1. 這些函數可能為未來功能預留
2. 可能作為 API 的擴展接口
3. 刪除可能影響系統的擴展性
4. 保持向前兼容性

**範例**:
```python
class NewsAnalyzer:
    def analyze_news(self, symbol: str):
        """當前使用的方法"""
        pass
    
    def analyze_batch(self, symbols: List[str]):
        """未使用但保留 - 可能用於批次分析"""
        pass
    
    def export_to_csv(self, filename: str):
        """未使用但保留 - 可能用於數據導出"""
        pass
```

---

## 修復工作流程總結

```
1. 問題識別
   ↓
2. 搜尋現有解決方案
   ├─ 檢查 schemas
   ├─ 查閱文檔
   └─ 搜尋相似代碼
   ↓
3. 選擇修復方案
   ├─ 使用現有 Schema？ → 直接導入
   ├─ 需要新 Schema？ → 在 schemas/ 中定義
   └─ 模組專屬？ → 確認符合原則
   ↓
4. 實施修復
   ├─ 單一檔案修復
   ├─ 立即驗證
   └─ 檢查影響範圍
   ↓
5. 測試驗證
   ├─ 語法檢查
   ├─ 類型檢查
   ├─ 單元測試
   └─ 實際執行 ✨
   ↓
6. 文檔更新
   └─ 更新相關說明
```

---

## 快速參考

### 📚 關鍵文檔位置

```
src/schemas/                # 所有 Schema 定義（單一數據來源）
├── market.py               # 市場數據
├── trading.py              # 交易相關
├── rag.py                  # 新聞分析
├── risk.py                 # 風險管理
├── orders.py               # 訂單結構
├── positions.py            # 持倉結構
├── portfolio.py            # 投資組合
├── strategy.py             # 策略相關
├── database.py             # 資料庫結構
├── api.py                  # API 回應結構
├── commands.py             # 指令結構
└── enums.py                # 列舉定義

config/                     # 配置檔案
├── trading_config.py       # 交易配置
├── trading_costs.py        # 交易成本
├── market_keywords.json    # 新聞關鍵字（舊版單一檔案）
├── market_keywords.db      # 關鍵字 SQLite 快取
└── keywords/               # 關鍵字分類目錄（v3.0 新架構）
    ├── _index.json         # 索引檔
    ├── person.json         # 人物（crypto_leader, fed_official, politician）
    ├── institution.json    # 機構（central_bank, regulator, exchange）
    ├── macro.json          # 宏觀經濟（monetary_policy, economic_data）
    ├── legislation.json    # 法規政策（us_law, global_law, tax_policy）
    ├── event.json          # 事件（market, security, adoption）
    ├── coin.json           # 幣種（major, altcoin, stablecoin）
    └── tech.json           # 技術（ai, blockchain）

docs/                       # 文檔
├── NEWS_ANALYZER_GUIDE.md  # 新聞分析使用手冊
├── USER_MANUAL.md          # 使用者手冊
└── CODE_FIX_GUIDE.md       # 本文件
```

### 🔧 常用命令

```bash
# 搜尋類別定義
grep -r "class ClassName" src/

# 搜尋函數定義
grep -r "def function_name" src/

# 查看檔案結構
tree src/bioneuronai/ -L 2

# 執行主程式
python use_trading_engine_v2.py

# 執行新聞分析
python -c "
from bioneuronai.analysis import CryptoNewsAnalyzer
analyzer = CryptoNewsAnalyzer()
result = analyzer.analyze_news('BTCUSDT')
result.print_news_with_links(max_items=5)
"
```

### 📞 需要協助時

1. 查閱本指南的相關章節
2. 查看 `docs/` 中的其他文檔
3. 使用 `grep` 或 `semantic_search` 搜尋相似代碼
4. 查閱官方文檔（Binance, CCXT, Pydantic）
5. 檢查 schemas 中是否有現成定義

---

**最後更新**: 2026年1月25日  
**維護者**: BioNeuronai 開發團隊  
**基於**: AIVA Common 專業化標準 v6.3

---

## 附錄：標準資源連結

### 金融交易標準
- Binance API: https://binance-docs.github.io/apidocs/futures/en/
- CCXT: https://ccxt.readthedocs.io/
- ISO 20022: https://www.iso20022.org/

### Python 標準
- PEP 8: https://peps.python.org/pep-0008/
- PEP 484: https://peps.python.org/pep-0484/
- Pydantic v2: https://docs.pydantic.dev/latest/

### 技術分析
- TA-Lib: https://ta-lib.org/
- Pandas: https://pandas.pydata.org/docs/

### 開發工具
- Pylance: VS Code 內建
- Python MCP Tools: VS Code Extension
