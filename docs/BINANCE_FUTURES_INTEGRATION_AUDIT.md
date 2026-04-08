# Binance 期貨合約交易 — 整合審計報告

> 建立日期：2026-04-08  
> 分析人員：AI 代碼審計  
> 範圍：交易規則認知、費用計算整合、新聞信號時效性、整體可測試性

---

## 一、Binance 期貨交易規則認知現況

### 1.1 費用結構（`config/trading_costs.py`）

**現狀：已定義，但未整合進交易決策流程。**

`config/trading_costs.py` 已完整定義以下內容，覆蓋幣安期貨的主要成本結構：

| 成本項目 | 實作狀態 | 說明 |
|---------|---------|------|
| Maker 手續費 | ✅ 已定義 | VIP 0 = 0.02%；VIP 1–9 依級遞減 |
| Taker 手續費 | ✅ 已定義 | VIP 0 = 0.05% |
| BNB 折扣 | ✅ 已定義 | 10% 折扣 |
| 資金費率（Funding Rate） | ✅ 已定義 | 每 8 小時結算；BTCUSDT 均值 0.01% |
| 買賣價差（Spread） | ✅ 已定義 | BTCUSDT 典型值 1 bps |
| 滑點（Slippage） | ✅ 已定義 | BTCUSDT 0.01%，市場波動乘數 |
| 槓桿強制平倉距離 | ✅ 已定義 | 公式：`(1/leverage) - 維持保證金率` |
| 最低獲利目標（Breakeven）| ✅ 已定義 | `get_minimum_profit_target()` |
| ROI（保證金基準/名義基準） | ✅ 已定義 | 兩種視角均支援 |

**`TradingCostCalculator` 可計算完整的開倉/平倉總成本，包含：**

```python
{
  "entry_fee": 0.50,       # 開倉手續費 (USDT)
  "exit_fee": 0.50,        # 平倉手續費 (USDT)
  "funding_cost": 0.30,    # 資金費率（持倉 24h = 3 次結算）
  "spread_cost": 0.20,     # 買賣價差
  "slippage_cost": 0.20,   # 滑點
  "total_cost": 1.70,      # 總成本
  "cost_percentage": 0.17, # 佔名義價值比例
  "cost_percentage_on_margin": ..., # 佔保證金比例 (槓桿放大後)
  "liquidation_price": ..., # 強制平倉價
  "breakeven_price": ...,   # 損益平衡價
  "roi_on_margin": ...      # 實際 ROI (保證金基準)
}
```

---

### 1.2 ❌ 核心問題：費用計算器從未被交易決策流程呼叫

**嚴重程度：中高（影響每一筆交易的盈虧判斷）**

搜尋全專案 Python 檔案，`TradingCostCalculator` 只在以下位置出現：
- `config/__init__.py` — 僅作為套件匯出
- `config/trading_costs.py` — 定義本身

**以下關鍵模組完全未引用費用計算器：**

| 模組 | 路徑 | 應整合的位置 |
|------|------|------------|
| 交易引擎 | `src/bioneuronai/core/trading_engine.py` | `execute_trade()` 下單前最小獲利驗證 |
| 風險管理器 | `src/bioneuronai/risk_management/position_manager.py` | `calculate_position_size()` 中的收益預期計算 |
| 策略基礎類 | `src/bioneuronai/strategies/base_strategy.py` | `execute_entry()` 信號強度與成本比較 |
| 事前自動化 | `src/bioneuronai/planning/pretrade_automation.py` | 進場前成本效益驗核 |

**實際影響：**

目前系統在決定是否下單時，只考慮：
- 信號置信度 (`MIN_SIGNAL_CONFIDENCE = 0.7`)
- 新聞風險（高風險禁止交易）
- 帳戶餘額是否足夠

**完全沒有考慮**：這筆交易的手續費 + 資金費率 + 滑點是否會把預期獲利吃掉。

**範例說明（目前系統的盲點）：**

```
場景：BTCUSDT，名義倉位 $1000，10x 槓桿，信號預期漲 0.1%
當前系統判斷：置信度 0.75 > 0.70 → 下單 ✅

正確判斷：
  - 開倉 Taker 手續費：$0.50
  - 平倉 Taker 手續費：$0.50
  - 資金費率（24h）：$0.30
  - 價差 + 滑點：$0.40
  - 總成本：$1.70
  - 預期獲利（0.1%）：$1.00
  - 結論：淨虧損 $0.70 → 不應下單 ❌
```

---

### 1.3 資金費率整合現況

`BinanceFuturesConnector.get_funding_rate()` 已實作，可獲取即時資金費率，但：
- 在交易引擎的資料收集流程中僅用於顯示，未用於持倉成本估算
- 未整合進「持倉是否值得繼續持有」的判斷

**建議加入**：每次決策時比較當前資金費率 vs 預期報酬，若資金費率過高（如 > 0.1%/8h）則降低槓桿或縮短持倉時間目標。

---

### 1.4 槓桿規則認知

`config/trading_config.py` 已設定 `LEVERAGE = 1`（保守，可調整），`trading_costs.py` 中已正確計算：
- 保證金需求 = 名義價值 / 槓桿
- 強制平倉距離 = 1/槓桿 - 維持保證金率（BTCUSDT 0.4%，其他 1%）

但強制平倉價格只在費用計算器內部計算，**未傳遞給止損設定邏輯**，可能造成止損設定比強制平倉更遠，失去保護意義。

---

## 二、新聞分析模組時效性現況

### 2.1 問題描述

**使用者需求：** 每次新聞分析完成後，應附帶「此分析預計可用的時間段」，讓交易決策系統知道這個情報的有效期限，並以此作為入場評估依據。

**現狀：`NewsAnalysisResult` 沒有信號有效期欄位。**

目前 `recommendation` 欄位只輸出靜態文字，例如：
```
🟢 強烈看漲信號，可考慮做多
🔴 強烈看跌信號，建議觀望或做空
⚪ 中性市場，維持現有策略
```

完全沒有「這個建議在幾小時後會失效」的資訊。

---

### 2.2 現有的時效性機制（事後評估，非前瞻）

`analyzer.py` 內部確實存在一個 `evaluation_window_hours = 24` 的概念，但它是用於**事後評估**（新聞發出後 24 小時後，回頭比較預測是否準確），不是給交易決策系統使用的「預計有效時間窗」。

```python
# analyzer.py:1008 — 這是事後評估用的，不是信號有效期
record = {
    'evaluation_window_hours': 24   # 24 小時後回頭評估準確率
}
```

---

### 2.3 各新聞類型應有的時效性分類

不同類型的新聞對價格的影響時間長短差異極大，應依類別給出對應的有效時間窗：

| 新聞類別 | 現有 `category` 標籤 | 建議有效時間窗 | 說明 |
|---------|-------------------|--------------|------|
| 監管事件（SEC、禁令） | `regulation` | 24–72 小時 | 影響持續，需密切追蹤 |
| 機構採購/大型投資 | `institutional` | 4–24 小時 | 利多效應但衰減快 |
| 技術/協議升級 | `technical` | 2–12 小時 | 短期博弈，升級後即衰退 |
| 黑天鵝/安全事件 | `security` | 6–48 小時 | 恐慌持續，需人工介入 |
| 市場情緒/一般新聞 | `sentiment` | 1–4 小時 | 最快衰退 |
| 宏觀經濟（Fed、CPI） | `macro` | 8–24 小時 | 影響面廣但速度慢 |
| 幣種特定新聞 | `coin_specific` | 2–8 小時 | 依新聞重要性調整 |

---

### 2.4 建議新增至 `NewsAnalysisResult` 的欄位

```python
@dataclass
class NewsAnalysisResult:
    # ... 現有欄位 ...
    
    # 新增：信號時效性
    signal_valid_hours: float          # 此分析預計有效的小時數
    signal_expires_at: datetime        # 信號到期時間（analysis_time + signal_valid_hours）
    signal_urgency: str                # "immediate"(0-1h) / "short"(1-4h) / "medium"(4-24h) / "long"(24h+)
    applicable_timeframes: List[str]   # 建議配合使用的時間框架，如 ["5m","15m","1h"]
```

**`_generate_recommendation()` 也應對應更新**，不只回傳文字，也計算有效時間：

```python
def _generate_recommendation(self, ..., category: str) -> Tuple[str, float]:
    """
    返回: (recommendation文字, signal_valid_hours)
    """
    validity_by_category = {
        'regulation': 48.0,
        'security':   24.0,
        'institutional': 12.0,
        'technical':   6.0,
        'macro':      16.0,
        'sentiment':   2.0,
        'coin_specific': 4.0,
    }
    valid_hours = validity_by_category.get(category, 4.0)
    # ... 依情緒強度再調整 ...
    return recommendation_text, valid_hours
```

---

### 2.5 交易決策如何使用信號有效期

整合後，`trading_engine.py` 可以在執行交易前先驗證新聞信號是否已過期：

```python
def _check_news_risk(self, symbol: str) -> bool:
    result = self.news_analyzer.analyze_news(symbol)
    
    # 新增：檢查信號是否仍在有效期內
    if datetime.now() > result.signal_expires_at:
        logger.warning(f"新聞信號已過期（有效至 {result.signal_expires_at}），跳過新聞過濾")
        return True   # 信號過期視為無新聞影響，不阻擋交易
    
    # 原有邏輯...
    return not result.is_high_risk()
```

---

## 三、整合度評估總覽

| 層面 | 現況 | 建議動作 | 優先級 |
|------|------|---------|-------|
| **費用計算器定義** | ✅ 完整定義於 `config/trading_costs.py` | 已就緒，待整合 | — |
| **費用計算 → 交易決策** | ❌ 完全未整合 | 在 `execute_trade()` 加入最小獲利驗證 | **P1** |
| **費用計算 → 策略信號過濾** | ❌ 未整合 | 在 `base_strategy.execute_entry()` 加成本檢查 | **P1** |
| **資金費率 → 槓桿建議** | ❌ 未整合 | 高資金費率時自動降槓桿 | P2 |
| **強制平倉價 → 止損設定** | ❌ 未整合 | 確保止損必須在強制平倉價之前 | **P1** |
| **`.env` 自動載入** | ❌ 無 `load_dotenv()` 呼叫 | 在 `main.py` 加入 `python-dotenv` | **P0** |
| **新聞信號有效期** | ❌ 無此欄位 | 新增 `signal_valid_hours` 到 `NewsAnalysisResult` | **P1** |
| **新聞類別 → 有效時間映射** | ❌ 未實作 | 實作 `validity_by_category` 映射表 | P2 |
| **過期信號跳過邏輯** | ❌ 未實作 | 交易決策前驗證信號有效期 | P2 |
| **回測歷史資料** | ✅ BTCUSDT / ETHUSDT 1m~1h | 可直接執行回測 | — |
| **模型檔案** | ✅ `model/my_100m_model.pth` | 可直接載入 | — |
| **Testnet 即時交易** | ⚠️ 需手動設定環境變數 | 修復 `.env` 載入後可直接測試 | P0 |

---

## 四、最小改動清單（達到可實際測試的最低要求）

### P0：30 分鐘內完成（阻擋所有測試）

1. **`main.py`** — 加入 `python-dotenv` 載入：
   ```python
   # 在 from bioneuronai.cli.main import cli_main 之前加
   try:
       from dotenv import load_dotenv
       load_dotenv()
   except ImportError:
       pass
   ```
   `pyproject.toml` 的 `dependencies` 加入 `"python-dotenv>=1.0.0"`

### P1：高優先（直接影響交易品質）

2. **`trading_engine.py` — `execute_trade()` 加入成本過濾**：
   ```python
   from config.trading_costs import TradingCostCalculator
   
   def _is_cost_effective(self, signal, current_price, position_size_usd) -> bool:
       calc = TradingCostCalculator(default_leverage=self.leverage)
       min_move_pct = calc.get_minimum_profit_target(
           position_size_usd, signal.symbol, 0.005, self.leverage
       )
       expected_move_pct = abs(signal.take_profit - current_price) / current_price * 100
       return expected_move_pct >= min_move_pct
   ```

3. **`analysis/news/models.py` — `NewsAnalysisResult` 加入時效欄位**：
   ```python
   signal_valid_hours: float = 4.0
   signal_expires_at: Optional[datetime] = None
   signal_urgency: str = "short"
   applicable_timeframes: List[str] = field(default_factory=lambda: ["15m", "1h"])
   ```

4. **`analysis/news/analyzer.py` — `_generate_recommendation()` 計算有效期**：
   按新聞 `category` 映射到對應的有效小時數，並在 `NewsAnalysisResult` 建構時帶入。

### P2：中優先（提升交易品質）

5. 資金費率高時自動降槓桿建議（在 `pretrade_automation.py`）
6. 確保止損設在強制平倉價之前的驗證邏輯
7. 新聞信號過期後的「交易決策旁路」邏輯

---

## 五、可直接執行的指令（修完 P0 後）

```bash
# 1. 設定環境變數（或填入 .env）
cp .env.example .env
# 填入 BINANCE_API_KEY 和 BINANCE_API_SECRET

# 2. 回測（不需要 API key）
python main.py backtest --symbol BTCUSDT --interval 1h

# 3. 紙交易模擬（不需要 API key）
python main.py simulate --symbol BTCUSDT --interval 15m --balance 50000

# 4. Testnet 即時交易測試（需要 API key）
python main.py trade --testnet

# 5. 事前技術面驗核
python main.py pretrade --symbol BTCUSDT --action long

# 6. 新聞情緒分析
python main.py news --symbol BTCUSDT --max-items 5
```

---

## 六、費用認知對交易判斷的影響量化

以下範例說明**整合費用計算前後的差異**：

### 範例：BTCUSDT 10x 槓桿，$1000 名義倉位

| 情境 | 預期漲幅 | 開倉費 | 平倉費 | 資金費率(24h) | 總成本 | 淨損益 | 現系統判斷 | 正確判斷 |
|------|---------|-------|-------|------------|-------|-------|----------|---------|
| A    | +0.1%   | $0.50 | $0.50 | $0.30      | $1.70 | **-$0.70** | ✅ 下單 | ❌ 不應下單 |
| B    | +0.3%   | $0.50 | $0.50 | $0.30      | $1.70 | **+$1.30** | ✅ 下單 | ✅ 下單 |
| C    | +0.15%  | $0.50 | $0.50 | $0.90      | $2.30 | **-$0.80** | ✅ 下單 | ❌ 不應下單（資金費率高） |

**結論：** 不整合費用計算，系統在 10x 槓桿下的有效最小獲利門檻為 **0.17%** 才能保本，但目前系統無法辨識這個門檻，會持續下單虧損的交易。

---

*本文件建立於 2026-04-08，供下一階段代碼修復使用。*
