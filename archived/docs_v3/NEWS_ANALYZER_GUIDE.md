> ⚠️ **歸檔文檔** - 此為舊版新聞系統文檔，已於 2026年1月26日歸檔  
> 📖 **最新文檔**: 請參閱 [BIONEURONAI_MASTER_MANUAL.md](../../docs/BIONEURONAI_MASTER_MANUAL.md) 第 7.3 章（RLHF 新聞預測驗證系統）

---

# 新聞分析系統使用手冊

## 📋 目錄

1. [系統概述](#系統概述)
2. [核心功能](#核心功能)
3. [快速開始](#快速開始)
4. [基本使用](#基本使用)
5. [進階功能](#進階功能)
6. [自動評估系統](#自動評估系統)
7. [關鍵字系統](#關鍵字系統)
8. [API 參考](#api-參考)
9. [配置說明](#配置說明)
10. [常見問題](#常見問題)

---

## 系統概述

**新聞分析系統** 是一個自動化的加密貨幣新聞監控和分析工具，能夠：

- 🔍 **自動抓取新聞** - 從多個可信來源獲取最新新聞
- 🎯 **智能關鍵字過濾** - 使用 181 個加權關鍵字篩選重要新聞
- 📊 **情感分析** - 自動判斷新聞情緒（正面/負面/中性）
- 💰 **價格追蹤** - 記錄新聞發布時的價格
- 🤖 **自動學習** - 根據實際市場反應調整關鍵字權重
- 📈 **影響評估** - 評估新聞對價格的實際影響

---

## 核心功能

### 1. 多源新聞聚合
從以下來源獲取新聞：
- **Cointelegraph** - 頂級加密貨幣新聞網站
- **CoinDesk** - 權威區塊鏈媒體
- **Decrypt** - 深度分析報導
- **CryptoPanic API** - 重要新聞聚合

### 2. 智能過濾系統
基於 181 個加權關鍵字：
- **人物** (29個) - Elon Musk, Vitalik, Powell...
- **機構** (25個) - SEC, Fed, BlackRock...
- **事件** (110個) - ETF approval, hack, regulation...
- **幣種** (17個) - Bitcoin, Ethereum, BNB...

### 3. 自動評分機制
綜合多個因素計算新聞重要性：
- **關鍵字權重** - base_weight × dynamic_weight
- **時間衰減** - 新聞越新分數越高
- **來源可信度** - Bloomberg (2.0) > CoinDesk (1.7) > 小網站 (0.8)
- **情感強度** - 情緒分數絕對值

### 4. 自動學習系統
新聞發布後 24 小時：
- 自動檢查價格變化
- 漲跌 >3%：提高關鍵字權重 × 1.15
- 漲跌 1-3%：適度提高 × 1.08
- 變化 <1%：降低權重 × 0.95

---

## 快速開始

### 安裝依賴

```bash
pip install requests feedparser
```

### 最簡單的使用

```python
from bioneuronai.analysis import CryptoNewsAnalyzer

# 創建分析器
analyzer = CryptoNewsAnalyzer()

# 分析 BTC 新聞
result = analyzer.analyze_news('BTCUSDT', hours=24)

# 顯示結果（含連結）
result.print_news_with_links(max_items=5)
```

### 輸出示例

```
📰 BTCUSDT 新聞摘要 (47 則)
情緒: neutral (分數: -0.19)
建議: 市場情緒偏中性，建議觀望
----------------------------------------------------------------------
1. 🟢 SEC Approves Bitcoin Spot ETF
   📅 2026-01-22 10:30 | 🌐 coindesk.com
   🔑 關鍵字: etf, sec, approval, bitcoin, spot
   🔗 https://coindesk.com/...

2. 🔴 Major Exchange Reports Security Breach
   📅 2026-01-22 09:15 | 🌐 cointelegraph.com
   🔑 關鍵字: hack, security, breach, exchange
   🔗 https://cointelegraph.com/...
```

---

## 基本使用

### 1. 基本新聞分析

```python
from bioneuronai.analysis import CryptoNewsAnalyzer

analyzer = CryptoNewsAnalyzer()

# 分析特定幣種，指定時間範圍
result = analyzer.analyze_news(
    symbol='ETHUSDT',  # 交易對
    hours=48           # 過去 48 小時
)

# 查看統計信息
print(f"總新聞數: {result.total_articles}")
print(f"正面: {result.positive_count}")
print(f"負面: {result.negative_count}")
print(f"情緒分數: {result.sentiment_score}")
print(f"建議: {result.recommendation}")
```

### 2. 獲取結構化數據

```python
# 取得標題和連結列表
headlines = result.get_headlines_with_urls()

for item in headlines[:5]:
    print(f"標題: {item['title']}")
    print(f"連結: {item['url']}")
    print(f"來源: {item['source']}")
    print(f"情緒: {item['sentiment']}")
    print(f"關鍵字: {item['keywords']}")
    print()
```

### 3. 過濾特定情緒

```python
# 只看正面新聞
positive_news = [a for a in result.articles if a.sentiment == 'positive']

# 只看負面新聞
negative_news = [a for a in result.articles if a.sentiment == 'negative']

# 按重要性排序
sorted_news = sorted(result.articles, 
                    key=lambda x: x.importance_score, 
                    reverse=True)
```

### 4. 檢查關鍵事件

```python
# 查看檢測到的重要事件
print(f"關鍵事件: {result.key_events}")

# 查看高頻關鍵字
print(f"熱門關鍵字: {result.top_keywords}")
```

---

## 進階功能

### 1. 快速摘要

```python
# 獲取快速摘要文字
summary = analyzer.get_quick_summary('BTCUSDT')
print(summary)
```

輸出示例：
```
📰 BTCUSDT 新聞摘要 (過去 24 小時)
----------------------------------------
✅ 分析了 47 篇新聞
📊 市場情緒: neutral (分數: -0.19)
📈 正面新聞: 15 篇
📉 負面新聞: 18 篇
⚪ 中性新聞: 14 篇

🎯 建議: 市場情緒偏中性，建議觀望
```

### 2. 交易決策輔助

```python
# 判斷是否適合交易
can_trade, reason = analyzer.should_trade('BTCUSDT')

if can_trade:
    print(f"✅ 可以交易: {reason}")
else:
    print(f"⚠️ 建議暫緩: {reason}")
```

### 3. 訪問單篇新聞詳情

```python
for article in result.articles[:3]:
    print(f"\n標題: {article.title}")
    print(f"來源: {article.source}")
    print(f"發布時間: {article.published_at}")
    print(f"情緒: {article.sentiment} ({article.sentiment_score:.2f})")
    print(f"重要性: {article.importance_score}/10")
    print(f"分類: {article.category}")
    print(f"關鍵字: {', '.join(article.keywords[:5])}")
    print(f"幣種: {article.target_coin}")
    print(f"發布時價格: ${article.price_at_news:,.2f}")
    print(f"連結: {article.url}")
```

### 4. 多幣種批次分析

```python
symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

for symbol in symbols:
    result = analyzer.analyze_news(symbol, hours=24)
    print(f"\n{symbol}:")
    print(f"  新聞數: {result.total_articles}")
    print(f"  情緒: {result.overall_sentiment}")
    print(f"  分數: {result.sentiment_score:.2f}")
```

---

## 自動評估系統

### 工作原理

1. **新聞發布時**
   - 自動記錄新聞內容、關鍵字、發布時價格
   - 保存到 `sop_automation_data/news_records.json`

2. **24 小時後**
   - 獲取當前價格
   - 計算漲跌幅
   - 判斷新聞影響力
   - 自動調整關鍵字權重

3. **權重更新規則**
   ```
   漲跌 > 3%  → 強影響 → 權重 × 1.15
   漲跌 1-3% → 中影響 → 權重 × 1.08
   漲跌 < 1% → 弱影響 → 權重 × 0.95
   ```

### 手動執行評估

```python
from bioneuronai.analysis import CryptoNewsAnalyzer

analyzer = CryptoNewsAnalyzer()

# 評估所有待處理的新聞
stats = analyzer.evaluate_pending_news()

print(f"已評估: {stats['evaluated']} 則")
print(f"看漲新聞: {stats['bullish']} 則")
print(f"看跌新聞: {stats['bearish']} 則")
print(f"中性新聞: {stats['neutral']} 則")
```

### 自動化評估（定時任務）

```python
import schedule
import time

def daily_evaluation():
    """每天執行一次評估"""
    analyzer = CryptoNewsAnalyzer()
    stats = analyzer.evaluate_pending_news()
    print(f"[{datetime.now()}] 評估完成: {stats}")

# 每天凌晨 2 點執行
schedule.every().day.at("02:00").do(daily_evaluation)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 查看新聞記錄

```python
import json

# 讀取所有記錄
with open('sop_automation_data/news_records.json', 'r', encoding='utf-8') as f:
    records = json.load(f)

print(f"總記錄數: {len(records)}")

# 查看待評估的新聞
pending = [r for r in records if not r.get('evaluated', False)]
print(f"待評估: {len(pending)} 則")

# 查看最近一則
if records:
    latest = records[-1]
    print(f"\n最新記錄:")
    print(f"  標題: {latest['title']}")
    print(f"  幣種: {latest['target_coin']}")
    print(f"  價格: ${latest['price_at_news']:,.2f}")
    print(f"  關鍵字: {latest['keywords']}")
    print(f"  已評估: {latest['evaluated']}")
```

---

## 關鍵字系統

### 關鍵字結構

每個關鍵字包含：
- **keyword** - 關鍵字文字
- **category** - 分類 (person/institution/event/coin)
- **base_weight** - 基礎權重 (1.0-2.5)
- **dynamic_weight** - 動態權重 (0.3-2.0)
- **sentiment_bias** - 情感傾向 (positive/negative/neutral/uncertain)
- **hit_count** - 命中次數
- **prediction_count** - 預測次數
- **correct_count** - 正確次數

### 有效權重計算

```
effective_weight = base_weight × dynamic_weight
```

### 高權重關鍵字示例

```python
"elon musk":        2.5 × 1.0 = 2.5
"sec":              2.5 × 1.0 = 2.5
"federal reserve":  2.5 × 1.0 = 2.5
"etf approval":     2.5 × 1.0 = 2.5
"hack":             2.5 × 1.0 = 2.5
```

### 查看關鍵字統計

```python
from bioneuronai.analysis import MarketKeywords

# 查看所有關鍵字
keywords = MarketKeywords.get_all_keywords()
print(f"關鍵字總數: {len(keywords)}")

# 按權重排序
sorted_kw = sorted(keywords, 
                   key=lambda x: x['base_weight'] * x['dynamic_weight'], 
                   reverse=True)

print("\n前 10 個高權重關鍵字:")
for kw in sorted_kw[:10]:
    weight = kw['base_weight'] * kw['dynamic_weight']
    print(f"  {kw['keyword']:20s} - {weight:.2f} ({kw['category']})")
```

### 手動更新權重

```python
from bioneuronai.analysis import MarketKeywords

# 提高權重
MarketKeywords.update_weight('etf', factor=1.15)

# 降低權重
MarketKeywords.update_weight('某個失效的關鍵字', factor=0.85)

# 記錄預測
MarketKeywords.record_prediction('bitcoin')

# 記錄正確預測
MarketKeywords.record_correct_prediction('ethereum')
```

---

## API 參考

### CryptoNewsAnalyzer 類

#### `__init__()`
創建新聞分析器實例。

```python
analyzer = CryptoNewsAnalyzer()
```

#### `analyze_news(symbol, hours=24)`
分析指定幣種的新聞。

**參數：**
- `symbol` (str) - 交易對符號，如 'BTCUSDT'
- `hours` (int) - 時間範圍（小時），預設 24

**返回：** `NewsAnalysisResult` 對象

```python
result = analyzer.analyze_news('BTCUSDT', hours=48)
```

#### `get_quick_summary(symbol='BTCUSDT')`
獲取快速摘要文字。

**返回：** str - 格式化的摘要文字

```python
summary = analyzer.get_quick_summary('ETHUSDT')
print(summary)
```

#### `should_trade(symbol='BTCUSDT')`
判斷是否適合交易。

**返回：** (bool, str) - (是否可交易, 原因)

```python
can_trade, reason = analyzer.should_trade('BTCUSDT')
```

#### `evaluate_pending_news()`
評估待處理的新聞並更新關鍵字權重。

**返回：** dict - 評估統計信息

```python
stats = analyzer.evaluate_pending_news()
```

### NewsAnalysisResult 類

#### 屬性

```python
result.symbol              # str - 交易對
result.total_articles      # int - 總新聞數
result.positive_count      # int - 正面新聞數
result.negative_count      # int - 負面新聞數
result.neutral_count       # int - 中性新聞數
result.overall_sentiment   # str - 整體情緒
result.sentiment_score     # float - 情緒分數 (-1.0 到 1.0)
result.key_events          # List[str] - 關鍵事件
result.top_keywords        # List[Tuple[str, int]] - 熱門關鍵字
result.recommendation      # str - 交易建議
result.analysis_time       # datetime - 分析時間
result.articles            # List[NewsArticle] - 文章列表
```

#### 方法

**`print_news_with_links(max_items=10)`**
印出新聞標題和連結。

```python
result.print_news_with_links(max_items=5)
```

**`get_headlines_with_urls()`**
取得結構化的標題和連結列表。

```python
headlines = result.get_headlines_with_urls()
for item in headlines:
    print(item['title'], item['url'])
```

### NewsArticle 類

#### 屬性

```python
article.title              # str - 標題
article.source             # str - 來源
article.url                # str - 連結
article.published_at       # datetime - 發布時間
article.summary            # str - 摘要
article.sentiment          # str - 情緒 (positive/negative/neutral)
article.sentiment_score    # float - 情緒分數
article.importance_score   # float - 重要性分數 (0-10)
article.keywords           # List[str] - 關鍵字列表
article.keyword_score      # float - 關鍵字總分
article.category           # str - 分類
article.target_coin        # str - 目標幣種
article.price_at_news      # float - 發布時價格
```

---

## 配置說明

### 新聞來源配置

位置：`src/bioneuronai/analysis/news/` (子模組)

```python
# RSS Feeds 列表
rss_feeds = [
    'https://cointelegraph.com/rss',
    'https://decrypt.co/feed',
    'https://www.coindesk.com/arc/outboundfeeds/rss/',
]
```

**添加新來源：**
```python
rss_feeds.append('https://新網站.com/rss')
```

### 來源可信度配置

```python
SOURCE_AUTHORITY = {
    'coindesk.com': 2.0,        # 最高
    'cointelegraph.com': 2.0,
    'bloomberg.com': 2.0,
    'reuters.com': 2.0,
    'decrypt.co': 1.8,
    'theblock.co': 1.8,
    'default': 0.8,             # 預設
}
```

### 事件重要性配置

```python
EVENT_IMPORTANCE = {
    'security': 3.0,      # 安全事件 - 最高
    'regulation': 2.8,    # 監管政策
    'etf': 2.5,           # ETF 相關
    'halving': 2.5,       # 減半事件
    'listing': 2.0,       # 上市/下市
    'partnership': 1.8,   # 合作夥伴
    'upgrade': 1.5,       # 升級更新
    'market': 1.0,        # 市場動態
    'general': 0.5,       # 一般新聞
}
```

### 關鍵字配置

關鍵字文件：`config/market_keywords.json`

```json
{
  "version": "2.0",
  "total_keywords": 181,
  "keywords": [
    {
      "keyword": "elon musk",
      "category": "person",
      "base_weight": 2.5,
      "dynamic_weight": 1.0,
      "sentiment_bias": "uncertain",
      "description": "特斯拉CEO，推文常引發市場波動"
    }
  ]
}
```

### 緩存配置

```python
# 緩存生存時間（秒）
self._cache_ttl = 300  # 5 分鐘

# 新聞記錄保留時間
records_retention_days = 30  # 30 天
```

---

## 常見問題

### Q1: 新聞數量太少怎麼辦？

**A:** 可能原因和解決方法：

1. **時間範圍太短**
   ```python
   # 擴大時間範圍
   result = analyzer.analyze_news('BTCUSDT', hours=48)
   ```

2. **關鍵字過濾太嚴格**
   - 檢查 `config/market_keywords.json`
   - 確保包含常見關鍵字

3. **RSS 來源問題**
   ```python
   # 檢查是否能訪問 RSS
   import requests
   response = requests.get('https://cointelegraph.com/rss')
   print(response.status_code)  # 應該是 200
   ```

### Q2: 如何提高特定關鍵字的權重？

**A:** 手動編輯 `config/market_keywords.json`：

```json
{
  "keyword": "my_important_keyword",
  "base_weight": 2.5,  // 提高到 2.5 (最高)
  "dynamic_weight": 1.5  // 動態權重也可以調整
}
```

或使用 API：
```python
from bioneuronai.analysis import MarketKeywords
MarketKeywords.update_weight('my_keyword', factor=1.2)
```

### Q3: 評估系統什麼時候會執行？

**A:** 不會自動執行，需要手動調用：

```python
# 方式1：手動執行
analyzer.evaluate_pending_news()

# 方式2：設定定時任務（推薦）
import schedule
schedule.every().day.at("02:00").do(analyzer.evaluate_pending_news)
```

### Q4: 如何查看哪些新聞被過濾掉了？

**A:** 啟用 DEBUG 日誌：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

analyzer = CryptoNewsAnalyzer()
result = analyzer.analyze_news('BTCUSDT')
# 會顯示被過濾的新聞
```

### Q5: 可以添加自定義關鍵字嗎？

**A:** 可以！編輯 `config/market_keywords.json`：

```json
{
  "keyword": "your_keyword",
  "category": "event",
  "base_weight": 2.0,
  "dynamic_weight": 1.0,
  "sentiment_bias": "positive",
  "description": "自定義關鍵字",
  "added_date": "2026-01-22",
  "last_updated": "2026-01-22",
  "hit_count": 0,
  "prediction_count": 0,
  "correct_count": 0
}
```

### Q6: 情緒分析的準確度如何？

**A:** 基於關鍵字匹配，準確度約 70-80%。判斷規則：

- **正面關鍵字**: approval, bullish, partnership, adoption...
- **負面關鍵字**: hack, crash, ban, lawsuit...
- **權重計算**: 正面關鍵字分數 - 負面關鍵字分數

### Q7: 如何只看重要新聞？

**A:** 按重要性分數過濾：

```python
result = analyzer.analyze_news('BTCUSDT')

# 只看分數 > 7 的重要新聞
important = [a for a in result.articles if a.importance_score > 7]

for article in important:
    print(f"{article.title} (分數: {article.importance_score})")
```

### Q8: 記憶體占用會不會太大？

**A:** 已優化：
- 緩存只保留 5 分鐘
- 新聞記錄只保留 30 天
- 單次分析約占用 5-10 MB

清理舊記錄：
```python
import json
from datetime import datetime, timedelta

with open('sop_automation_data/news_records.json', 'r') as f:
    records = json.load(f)

# 只保留最近 7 天
cutoff = (datetime.now() - timedelta(days=7)).isoformat()
records = [r for r in records if r['timestamp'] > cutoff]

with open('sop_automation_data/news_records.json', 'w') as f:
    json.dump(records, f)
```

### Q9: 可以用在實盤交易嗎？

**A:** 可以，但建議：
1. 結合技術指標使用
2. 不要單獨依賴新聞分析
3. 設置風險控制
4. 先在測試環境驗證

```python
# 交易決策示例
result = analyzer.analyze_news('BTCUSDT')
can_trade, reason = analyzer.should_trade('BTCUSDT')

if can_trade and result.sentiment_score > 0.3:
    print("✅ 情緒積極，可考慮做多")
elif can_trade and result.sentiment_score < -0.3:
    print("⚠️ 情緒消極，可考慮做空或觀望")
else:
    print("⏸️ 情緒中性，建議觀望")
```

### Q10: 如何備份和還原關鍵字數據？

**A:** 

**備份：**
```bash
cp config/market_keywords.json config/market_keywords.backup.json
```

**還原：**
```bash
cp config/market_keywords.backup.json config/market_keywords.json
```

**Python 備份：**
```python
import shutil
from datetime import datetime

backup_name = f"market_keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
shutil.copy('config/market_keywords.json', f'config/backups/{backup_name}')
```

---

## 最佳實踐

### 1. 定期評估

```python
# 每天運行一次
import schedule

def daily_routine():
    analyzer = CryptoNewsAnalyzer()
    
    # 分析主要幣種
    for symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
        result = analyzer.analyze_news(symbol, hours=24)
        print(f"\n{symbol}: {result.overall_sentiment}")
    
    # 評估待處理新聞
    stats = analyzer.evaluate_pending_news()
    print(f"\n評估完成: {stats}")

schedule.every().day.at("08:00").do(daily_routine)
```

### 2. 結合技術分析

```python
from bioneuronai.analysis import CryptoNewsAnalyzer

analyzer = CryptoNewsAnalyzer()
result = analyzer.analyze_news('BTCUSDT')

# 新聞情緒
news_sentiment = result.sentiment_score

# 結合技術指標（假設已有）
rsi = 55  # 從技術分析模組獲取
macd = 0.5

# 綜合判斷
if news_sentiment > 0.2 and rsi < 70 and macd > 0:
    print("✅ 多重信號看漲，可考慮進場")
```

### 3. 風險監控

```python
# 檢查高風險事件
high_risk_keywords = ['hack', 'breach', 'lawsuit', 'ban', 'crash']

for article in result.articles:
    if any(kw in article.keywords for kw in high_risk_keywords):
        print(f"⚠️ 風險警報: {article.title}")
        print(f"   關鍵字: {article.keywords}")
```

### 4. 日誌記錄

```python
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(
    filename=f'logs/news_analyzer_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 記錄分析結果
result = analyzer.analyze_news('BTCUSDT')
logging.info(f"分析完成: {result.total_articles} 則新聞, 情緒: {result.overall_sentiment}")
```

---

## 技術支援

遇到問題？

1. 查看日誌文件
2. 檢查 `sop_automation_data/news_records.json`
3. 驗證 RSS 來源是否可訪問
4. 確認關鍵字配置文件格式正確

需要協助請提供：
- 錯誤訊息
- 使用的代碼
- Python 版本
- 依賴版本

---

## 更新日誌

**v2.0 (2026-01-22)**
- ✨ 新增自動評估系統
- ✨ 新增關鍵字權重自動調整
- ✨ 新增價格追蹤功能
- 🐛 修復 RSS 解析問題
- 📚 完善文檔

**v1.0 (2026-01-19)**
- 🎉 初始版本發布
- 基本新聞抓取功能
- 情感分析功能
- 關鍵字過濾系統

---

## 授權

本系統為 BioNeuronai 項目的一部分，遵循項目主授權協議。

---

*最後更新: 2026年1月22日*
