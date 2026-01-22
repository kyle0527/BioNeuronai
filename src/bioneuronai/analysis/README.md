# Analysis 分析模組

加密貨幣新聞分析和市場關鍵字識別。

## 📋 模組概述

Analysis 模組提供新聞情緒分析、市場關鍵字識別、市場體制檢測和特徵工程功能，是系統的核心分析服務。

## 🎯 主要組件

### 1. CryptoNewsAnalyzer (新聞分析器)

基於多層次情緒分析的新聞分析系統，支持英文和中文。

**主要功能：**
- 實時新聞抓取（多個來源）
- 多維度情緒分析（情緒、緊急度、影響力）
- 市場關鍵字識別
- 新聞去重和排序
- 分幣種情緒統計

**使用示例：**
```python
from bioneuronai.analysis import CryptoNewsAnalyzer

# 初始化分析器
analyzer = CryptoNewsAnalyzer()

# 獲取最新新聞
news_list = await analyzer.get_latest_news(hours=24, limit=50)

# 分析新聞情緒
for news in news_list:
    result = analyzer.analyze_sentiment(news)
    print(f"情緒分數: {result.sentiment_score}")
    print(f"影響力: {result.impact_level}")

# 獲取特定幣種的情緒
btc_sentiment = await analyzer.get_symbol_sentiment("BTC")
```

**新聞來源：**
- CoinDesk
- CoinTelegraph
- Decrypt
- The Block
- Bitcoin.com

### 2. MarketKeywords (市場關鍵字)
市場熱門關鍵字識別系統。

**主要類**:
- `MarketKeywords` - 關鍵字管理器

**核心功能**:
- 關鍵字提取
- 重要性評分
- 趨勢追蹤
- SQLite 存儲

**使用示例**:
```python
from bioneuronai.analysis import MarketKeywords

# 初始化關鍵字系統
keywords = MarketKeywords()

# 提取關鍵字
important_keywords = keywords.extract_keywords(news_text)

# 獲取熱門關鍵字
trending = keywords.get_trending_keywords(days=7)
```

### 3. MarketRegime (市場體制檢測)
識別當前市場所處的體制狀態。

**主要類**:
- `MarketRegime` - 體制檢測器

**體制類型**:
- 趨勢市場 (Trending)
- 震盪市場 (Ranging)
- 突破市場 (Breakout)
- 高波動市場 (High Volatility)

**使用示例**:
```python
from bioneuronai.analysis import MarketRegime

# 初始化體制檢測器
regime = MarketRegime()

# 檢測市場體制
current_regime = regime.detect_regime('BTCUSDT', window=100)
print(f"當前體制: {current_regime['type']}")
print(f"置信度: {current_regime['confidence']}")
```

### 4. FeatureEngineering (特徵工程)
為機器學習模型生成技術指標特徵。

**主要類**:
- `FeatureEngineering` - 特徵工程器

**特徵類型**:
- 技術指標 (RSI, MACD, Bollinger Bands)
- 價格特徵 (收益率, 波動率)
- 成交量特徵
- 時間特徵

**使用示例**:
```python
from bioneuronai.analysis import FeatureEngineering

# 初始化特徵工程器
fe = FeatureEngineering()

# 生成特徵
features = fe.create_features(market_data)

# 選擇重要特徵
top_features = fe.select_features(features, target, top_k=20)
```

### 5. BacktestEngine (回測引擎)

識別和分類市場相關的關鍵字和事件。

**主要功能：**
- 關鍵字分類（監管、技術、市場、機構）
- 關鍵字權重評分
- 上下文匹配
- 多語言支持

**使用示例：**
```python
from bioneuronai.analysis import MarketKeywords

# 初始化關鍵字系統
keywords = MarketKeywords()

# 檢測新聞中的關鍵字
text = "SEC approves Bitcoin ETF application"
matches = keywords.find_keywords(text)

for match in matches:
    print(f"關鍵字: {match.keyword}")
    print(f"類別: {match.category}")
    print(f"權重: {match.weight}")
```

**關鍵字分類：**
- 🏛️ `REGULATORY` - 監管相關
- 💻 `TECHNICAL` - 技術相關
- 📈 `MARKET` - 市場相關
- 🏢 `INSTITUTIONAL` - 機構相關

### 3. get_news_analyzer() 單例函數

獲取共享的新聞分析器實例（單例模式）。

```python
from bioneuronai.analysis import get_news_analyzer

# 獲取分析器實例（整個應用共享）
analyzer = await get_news_analyzer()
```

## 📦 導出 API

```python
from bioneuronai.analysis import (
    CryptoNewsAnalyzer,    # 新聞分析器
    NewsArticle,           # 新聞文章數據類
    NewsAnalysisResult,    # 分析結果數據類
    get_news_analyzer,     # 單例獲取函數
    MarketKeywords,        # 關鍵字識別
    KeywordMatch,          # 關鍵字匹配結果
)
```

## 🔗 依賴關係

**被依賴於：**
- `core.TradingEngine` - 用於交易決策
- `automation.SOPAutomation` - SOP 流程分析
- `automation.PreTradeAutomation` - 交易前檢查

**外部依賴：**
- `requests` - HTTP 請求
- `beautifulsoup4` - HTML 解析
- `textblob` - 情緒分析（備用）
- `feedparser` - RSS 解析

## 🎨 架構設計

```
analysis/
├── news_analyzer.py        # 新聞分析核心
├── market_keywords.py      # 關鍵字系統
└── __init__.py            # 模組導出
```

## 📊 數據模型

### NewsArticle (新聞文章)

```python
@dataclass
class NewsArticle:
    title: str              # 標題
    url: str                # 網址
    source: str             # 來源
    published_time: datetime  # 發布時間
    content: str            # 內容
    summary: str            # 摘要
```

### NewsAnalysisResult (分析結果)

```python
@dataclass
class NewsAnalysisResult:
    sentiment_score: float        # 情緒分數 (-1 到 1)
    impact_level: str            # 影響級別 (HIGH/MEDIUM/LOW)
    urgency: str                 # 緊急度
    related_symbols: List[str]   # 相關幣種
    keywords: List[str]          # 關鍵字
    category: str                # 分類
```

## 🔧 配置說明

```python
# 新聞來源配置
NEWS_SOURCES = {
    'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
    'cointelegraph': 'https://cointelegraph.com/rss',
    'decrypt': 'https://decrypt.co/feed',
}

# 情緒分析配置
SENTIMENT_CONFIG = {
    'positive_threshold': 0.3,    # 正面閾值
    'negative_threshold': -0.3,   # 負面閾值
    'impact_keywords_weight': 2.0, # 關鍵字權重
}
```

## 📝 使用場景

### 場景 1：監控市場情緒

```python
async def monitor_market_sentiment():
    analyzer = await get_news_analyzer()
    
    while True:
        # 每小時檢查一次
        news = await analyzer.get_latest_news(hours=1)
        
        # 計算整體情緒
        overall_sentiment = sum(
            analyzer.analyze_sentiment(n).sentiment_score 
            for n in news
        ) / len(news)
        
        print(f"市場情緒: {overall_sentiment:.2f}")
        await asyncio.sleep(3600)
```

### 場景 2：重大事件警報

```python
async def alert_major_events():
    analyzer = await get_news_analyzer()
    
    news = await analyzer.get_latest_news(hours=1)
    
    for article in news:
        result = analyzer.analyze_sentiment(article)
        
        if result.impact_level == "HIGH":
            print(f"⚠️ 重大事件: {article.title}")
            print(f"情緒: {result.sentiment_score}")
            print(f"關鍵字: {', '.join(result.keywords)}")
```

### 場景 3：幣種特定分析

```python
async def analyze_specific_coin(symbol: str):
    analyzer = await get_news_analyzer()
    
    # 獲取該幣種的情緒
    sentiment_data = await analyzer.get_symbol_sentiment(symbol)
    
    print(f"{symbol} 情緒分析:")
    print(f"平均情緒: {sentiment_data['average_sentiment']:.2f}")
    print(f"新聞數量: {sentiment_data['news_count']}")
    print(f"正面新聞: {sentiment_data['positive_count']}")
    print(f"負面新聞: {sentiment_data['negative_count']}")
```

## ⚠️ 注意事項

1. **API 限制**：某些新聞源可能有請求頻率限制
2. **語言支持**：主要針對英文，中文支持有限
3. **情緒準確性**：情緒分析基於規則和關鍵字，不是 100% 準確
4. **網絡依賴**：需要穩定的網絡連接

## 🚀 快速開始

```python
import asyncio
from bioneuronai.analysis import get_news_analyzer

async def main():
    # 獲取分析器
    analyzer = await get_news_analyzer()
    
    # 獲取最新新聞
    news = await analyzer.get_latest_news(hours=24, limit=10)
    
    # 分析每條新聞
    for article in news:
        result = analyzer.analyze_sentiment(article)
        print(f"\n📰 {article.title}")
        print(f"情緒: {result.sentiment_score:.2f}")
        print(f"影響: {result.impact_level}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📈 性能指標

- 新聞抓取時間：2-5 秒（多個來源）
- 單條新聞分析：< 10ms
- 關鍵字匹配：< 5ms
- 支持並發分析：是

## 🔄 版本歷史

- v2.1.0 - 模組化重構，改進 API
- v2.0.0 - 新增多語言支持
- v1.5.0 - 優化情緒分析算法
- v1.0.0 - 初始版本
