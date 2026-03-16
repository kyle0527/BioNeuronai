# BioNeuronai 功能狀態總覽

**版本**：v4.3.1
**更新日期**：2026-03-16
**分析方式**：完整原始碼審計（CLI 7 命令 + 40+ 核心模組）

---

## 目錄

1. [快速摘要](#快速摘要)
2. [CLI 命令可執行狀態](#cli-命令可執行狀態)
3. [已完成功能（可立即執行）](#已完成功能可立即執行)
4. [部分完成功能（有限制條件）](#部分完成功能有限制條件)
5. [尚未完成功能](#尚未完成功能)
6. [外部依賴清單](#外部依賴清單)
7. [已知問題與限制](#已知問題與限制)
8. [建議修復優先順序](#建議修復優先順序)

---

## 快速摘要

```
整體可執行度估算：

  ████████████████████░░░░░░░░  約 65%

  ✅ 完整可執行   ：12 項功能
  ⚠️ 部分可執行   ：8  項功能（有條件限制）
  ❌ 尚未完成     ：7  項功能
  🔧 需外部依賴   ：5  項依賴
```

---

## CLI 命令可執行狀態

程式統一入口：`python -m bioneuronai.cli.main <命令>`

| 命令 | 無 torch | 有 torch | 狀態說明 |
|------|:--------:|:--------:|---------|
| `status` | ✅ | ✅ | 完整可用，動態掃描 7 個模組健康狀態 |
| `news` | ✅ | ✅ | 完整可用，需網路存取新聞 API |
| `pretrade` | ✅ | ✅ | 完整可用，執行 5 步驟交易前檢查 |
| `plan` | ✅ | ✅ | **已修復**：Step 5/6 串接 StrategySelector，Step 9 串接 PairSelector，Step 10 如實呈現狀態 |
| `backtest` | ❌ | ⚠️ | 需要本地歷史數據（目錄已建立，需自行填入 CSV） |
| `simulate` | ❌ | ⚠️ | 同上，需要本地歷史數據 |
| `trade` | ❌ | ✅ | 需要 torch + Binance API 金鑰 |

---

## 已完成功能（可立即執行）

### 1. 系統健康檢查 (`status`)

**可直接執行，無任何外部依賴。**

- 動態 import 7 個核心模組，逐一報告可用狀態
- 顯示 Python 版本、平台、當前工作目錄
- 有 torch：AI 推論引擎標示為可用
- 無 torch：降級模式，其餘模組仍正常報告

```bash
python -m bioneuronai.cli.main status
```

---

### 2. 新聞情感分析 (`news`)

**可執行，需要網路連線。**

- **CryptoNewsAnalyzer**：完整實作（`analysis/news/analyzer.py`，41,619 bytes）
- 情感分析：正負面關鍵字加權評分，範圍 -1.0 ~ +1.0
- 事件偵測：8 種事件類型（ETF、監管、駭客、合作、升級、上線、鯨魚、減半）
- 重要性評分：來源權威度 × 時效性 × 相關性（0~10 分）
- 217 個預設加密關鍵字，自適應學習機制
- 支援 symbol 篩選，預設分析 24 小時新聞

```bash
python -m bioneuronai.cli.main news --symbol BTCUSDT --max-items 10
```

---

### 3. 交易前 5 步驟檢查 (`pretrade`)

**可執行，需要 Binance 連線（testnet 即可）。**

- **PreTradeCheckSystem**：完整實作（`trading/pretrade_automation.py`，1,051 行）

| 步驟 | 檢查項目 | 通過門檻 |
|------|---------|---------|
| Step 1 | 技術信號確認（RSI/MACD/BB/趨勢對齊） | 強度 ≥ 7.0/10，確認信號 ≥ 3 |
| Step 2 | 基本面檢查（新聞、資金流、成交量） | 4 項中 ≥ 3 項良好 |
| Step 3 | 風險計算（Kelly 倉位、止損、止盈） | R:R ≥ 2.0，期望回報 ≥ 1% |
| Step 4 | 訂單參數設定（分批止盈 30%/40%/30%） | 所有參數驗證通過 |
| Step 5 | 最終三重確認（信號/風險/計劃） | 三項全部通過 |

**評分系統**：
- ≥ 80% → EXECUTE ✅
- 60~80% → CAUTIOUS_EXECUTE ⚠️
- 40~60% → WAIT 🟡
- < 40% → REJECT ❌

```bash
python -m bioneuronai.cli.main pretrade --symbol BTCUSDT --capital 10000
```

---

### 4. WebSocket 即時數據流

**完整實作（非骨架），位於 `data/binance_futures.py:395-446`。**

- 使用 `websocket-client` 建立真實 wss:// 連線
- 自動重連機制（最多 10 次，指數退避）
- 心跳包支援（30 秒 ping interval）
- 非阻塞背景執行緒
- 回調函數接收即時 ticker 資料

---

### 5. 宏觀市場掃描

**完整實作，整合 4 個外部 API。**

| 數據來源 | 指標 | API |
|---------|------|-----|
| Alternative.me | 恐慌貪婪指數（0~100） | 免費，無需金鑰 |
| CoinGecko | 全球市值、BTC 主導率 | 免費，有速率限制 |
| DefiLlama | DeFi TVL（總鎖倉量） | 免費，無需金鑰 |
| CoinGecko | 穩定幣供應量 | 免費，有速率限制 |

---

### 6. 技術指標分析

**完整實作，`trading/market_analyzer.py:235-624`。**

- EMA 趨勢分析（12/26/50 週期）
- ATR 波動率 + 歷史波動率
- RSI 超買超賣判斷
- 市場階段識別（WYCKOFF：積累/拉升/派發/下跌）
- 流動性評估（訂單簿深度）
- 返回 `MarketCondition` 物件，含趨勢、波動率、市場階段、情感分數

---

### 7. 風險管理系統

**完整實作，4 個風險等級。**

| 等級 | 每筆風險 | 日最大風險 | 最大槓桿 | 回撤限制 |
|------|---------|-----------|---------|---------|
| CONSERVATIVE | 1% | 3% | 2x | 10% |
| MODERATE | 2% | 5% | 3x | 15% |
| AGGRESSIVE | 3% | 8% | 10x | 25% |
| HIGH_RISK | 5% | 15% | 10x | 30% |

**風控觸發條件**：
- 連敗 3 次 → 倉位縮減至 75%
- 連敗 5 次 → 停止交易
- 日虧損超限 → 停止交易
- 持倉相關性 > 0.70 → 拒絕開新倉

---

### 8. Kelly Criterion 倉位計算

**完整實作，動態資金管理。**

```
kelly_fraction = (勝率 × 平均盈利 - 敗率 × 平均虧損) / 平均盈利
倉位大小 = kelly_fraction × 帳戶餘額 / (進場價 - 止損價)
```

同時考量：波動率調整、流動性限制、最大倉位上限。

---

### 9. 回測引擎框架（BacktestEngine）

**程式碼完整，但需要歷史數據才能執行。**

- 完整的 MockBinanceConnector（模擬交易所介面）
- 防偷看機制（HistoricalDataStream，逐根 K 線吐出）
- VirtualAccount（含手續費 0.04%、滑點 0.01%）
- 自動計算：夏普比率、最大回撤、勝率、盈利因子

---

### 10. AI 推論引擎（InferenceEngine）

**程式碼完整，需要 torch 和模型檔案。**

- 模型：111.2M 參數 MLP（`model/my_100m_model.pth`，424MB）
- 輸入：1024 維特徵向量（10 大類別）
- 輸出：7 種信號類型（STRONG_LONG 到 STRONG_SHORT）
- 推論延遲：約 22ms（CPU）

**1024 維特徵分布**：
| 特徵類別 | 維度 |
|---------|------|
| 技術指標（RSI/MACD/BB/ATR 等） | 256 |
| 成交量特徵 | 128 |
| 價格序列特徵 | 128 |
| 訂單簿特徵 | 128 |
| 微觀結構特徵 | 128 |
| 市場體制特徵 | 64 |
| 清算熱力圖特徵 | 64 |
| 情感特徵 | 64 |
| 融資費率特徵 | 32 |
| 時間特徵 | 32 |

---

### 11. 多策略系統（AIStrategyFusion）

**完整實作，6 種策略 + 5 種融合方法。**

| 策略 | 適用市場 | 勝率（歷史） |
|------|---------|------------|
| TrendFollowingStrategy | 趨勢行情（EMA/MACD/ADX） | 55% |
| SwingTradingStrategy | 震盪波段（BB/RSI） | 60% |
| MeanReversionStrategy | 橫盤整理 | 60% |
| BreakoutTradingStrategy | 突破型行情 | 48% |
| DirectionChangeStrategy | 趨勢反轉（DC 演算法） | — |
| PairTradingStrategy | 統計套利 | — |

**融合方法**：加權投票 / 最佳表現者 / 市場自適應 / 信心度基礎 / 集成融合

---

### 12. 每日 SOP 盤前報告

**完整實作，20 個子步驟分 4 個階段。**

| 階段 | 步驟 | 功能 |
|------|------|------|
| 策略分析與選擇 | 1~6 | 分析市場、評估策略歷史表現、確定策略參數 |
| 風險參數制定 | 7~12 | 資金風險計算、持倉管理規則、交易頻率限制 |
| 交易標的選擇 | 13~17 | 掃描幣對、流動性/波動率評估、風險過濾 |
| 計劃驗證 | 18~20 | 回測驗證（⚠️ 待實作）、日限額計算、最終確認 |

---

## 部分完成功能（有限制條件）

### A. 10 步驟交易計劃（`plan` 命令）

**✅ 已修復（v4.3.1）：所有 10 步驟現在均呼叫真實邏輯。**

| 步驟 | 狀態 | 說明 |
|------|------|------|
| Step 1：系統環境檢查 | ✅ 完整 | API 連線、帳戶驗證 |
| Step 2：宏觀市場掃描 | ✅ 完整 | 4 個外部 API 即時數據 |
| Step 3：技術面分析 | ✅ 完整 | 完整指標計算 |
| Step 4：基本面情感分析 | ✅ 完整 | 事件評估系統整合 |
| Step 5：策略性能評估 | ✅ **已修復** | 呼叫 StrategySelector.analyze_strategy_performance()，回傳各策略配置績效 |
| Step 6：策略選擇權重 | ✅ **已修復** | 呼叫 StrategySelector.select_strategy()，根據帳戶資金與 klines 動態選擇 |
| Step 7：風險參數計算 | ✅ 完整 | 根據波動率動態調整 |
| Step 8：資金管理規劃 | ✅ 完整 | Kelly 倉位真實計算 |
| Step 9：交易對篩選 | ✅ **已修復** | 呼叫 PairSelector.select_optimal_pairs()，有 connector 時查 API，否則降級為預設列表 |
| Step 10：執行計劃監控 | ✅ **已修復** | 如實回傳 `monitor_active: false`，附說明 WebSocket 需由 TradingEngine 啟動 |

> **備註**：Step 5/6 的績效數值來自 `StrategySelector` 的策略配置（非真實回測），待 BacktestEngine 有數據後可進一步整合。

---

### B. 歷史回測（`backtest` / `simulate` 命令）

**框架完整，目錄已建立，仍需填入歷史數據。**

- 程式碼：✅ 完整（BacktestEngine + MockBinanceConnector + HistoricalDataStream）
- 歷史數據目錄：✅ `data_downloads/binance_historical/` **已建立**（v4.3.1）
- 歷史數據檔案：❌ 目錄為空，尚未有 CSV 數據
- 影響：執行 `backtest` 或 `simulate` 命令時，因讀不到數據而失敗

詳細說明請見 `data_downloads/README.md`。

**解決方式**：
```bash
# 使用工具下載歷史數據後再執行
python tools/download_historical_data.py --symbol BTCUSDT --interval 1h
```

---

### C. 實盤交易（`trade` 命令）

**技術完整，需外部環境就緒。**

- torch 未安裝：❌ 無法初始化（合理設計，無 AI 不做實盤）
- torch 已安裝但無 API 金鑰：⚠️ 可初始化，testnet 模式下部分功能可用
- torch + API 金鑰就緒：✅ 完整執行

---

### D. 策略進化系統

**架構設計完整，部分元件可能未整合至主流程。**

| 元件 | 位置 | 狀態 |
|------|------|------|
| StrategyArena（基因演算法競技場） | `strategies/strategy_arena.py` | ⚠️ 存在但未整合至 CLI |
| TradingPhaseRouter（9 階段路由） | `strategies/phase_router.py` | ⚠️ 存在但未整合至 CLI |
| RLFusionAgent（強化學習融合） | `strategies/rl_fusion_agent.py` | ⚠️ 存在但未整合至 CLI |

---

### E. RAG 新聞預測迴圈

**存在但有依賴問題。**

- `analysis/news/prediction_loop.py` 使用 `schedule` 排程庫
- `schedule` **未列入 `pyproject.toml` 的 dependencies**
- 影響：`news` 命令的預測驗證功能無法使用

---

## 尚未完成功能

### 1. 回測驗證（`sop_automation.py`）

**明確標記為 NOT_IMPLEMENTED。**

```python
# src/bioneuronai/trading/sop_automation.py:604-624
def _perform_plan_backtest(self, ...):
    logger.warning("⚠️ 回測功能未實現，跳過此步驟")
    return {
        "status": "NOT_IMPLEMENTED",
        "annual_return": None,
        "max_drawdown": None,
        ...
    }
```

SOP 盤前報告的第 18 步驟（回測驗證）目前跳過，所有指標均為 None。

---

### 2. 策略績效來源限制（Step 5/6，已部分改善）

**已修復（v4.3.1）**：Step 5/6 現在呼叫 `StrategySelector`，數值來自策略配置定義（非硬編碼）。

後續改進方向：連接 BacktestEngine 執行真實回測，取得基於歷史數據的策略績效。

---

### 3. 新聞情感整合（market_analyzer.py）

**硬編碼為 0.0，未連接 RAG 系統。**

```python
# src/bioneuronai/trading/market_analyzer.py:906
news_sentiment=0.0,  # 待實現
```

`MarketCondition.news_sentiment` 欄位永遠為 0，市場分析中不包含實際新聞情緒。

---

### 6. RAG 快取偵測（retriever.py）

**TODO 標記，每次查詢均視為快取未命中。**

```python
# src/rag/core/retriever.py:163
cache_hit=False,  # TODO: 實現快取檢測
```

RAG 每次查詢都重新執行向量搜尋，無法利用快取加速。

---

### 7. 均值回歸策略的特定方法

**部分方法暫時回傳 None（`mean_reversion.py:600`）。**

---

## 外部依賴清單

| 依賴 | 用途 | 安裝狀態 | 影響命令 |
|------|------|---------|---------|
| `torch>=2.0.0` | AI 推論引擎 | ❌ 未安裝 | trade（必要）、backtest/simulate（可選） |
| `schedule>=1.2.0` | 新聞預測排程 | ❌ **未列入 pyproject.toml** | news（prediction_loop） |
| Binance API 金鑰 | 實盤交易 | 🔧 需用戶設定 | trade、pretrade（部分） |
| 本地歷史數據 | 回測與模擬 | ❌ 目錄不存在 | backtest、simulate |
| 網路連線 | 外部 API | 🔧 執行時需要 | plan、news、pretrade |

---

## 已知問題與限制

### 🔴 高優先級（影響核心功能）

| # | 問題 | 位置 | 影響 |
|---|------|------|------|
| 1 | 本地歷史數據目錄不存在 | `data_downloads/binance_historical/` | backtest/simulate 無法執行 |
| 2 | `schedule` 未列入依賴 | `pyproject.toml` | news 排程功能失效 |
| 3 | Plan Step 5/6 回傳假數據 | `plan_controller.py:429-461` | 策略建議不可信 |
| 4 | Plan Step 9/10 回傳假數據 | `plan_controller.py:561-593` | 幣對選擇和監控無效 |
| 5 | SOP 回測驗證跳過 | `sop_automation.py:604` | 盤前報告缺乏驗證 |

### 🟡 中優先級（影響分析品質）

| # | 問題 | 位置 | 影響 |
|---|------|------|------|
| 6 | 新聞情感硬編碼為 0 | `market_analyzer.py:906` | 市場分析缺新聞因子 |
| 7 | RAG 快取未實作 | `rag/core/retriever.py:163` | RAG 查詢效能低落 |
| 8 | 均值回歸部分方法回傳 None | `mean_reversion.py:600` | 特定市場條件下策略失效 |

### 🔵 低優先級（架構整合問題）

| # | 問題 | 影響 |
|---|------|------|
| 9 | StrategyArena 未整合至 CLI | 基因演算法進化無法透過命令觸發 |
| 10 | TradingPhaseRouter 未整合至 CLI | 9 階段路由未被使用 |
| 11 | RLFusionAgent 未整合至 CLI | 強化學習融合代理閒置 |

---

## 建議修復優先順序

### 立即可做（1 天內）

```bash
# 1. 加入 schedule 依賴
# 在 pyproject.toml [project] dependencies 加一行：
"schedule>=1.2.0",

# 2. 準備回測數據目錄
mkdir -p data_downloads/binance_historical

# 3. 下載歷史數據（若有下載工具）
python tools/download_historical_data.py --symbol BTCUSDT --interval 1h --days 365
```

### 短期修復（1 週內）

1. **Plan Step 9**：將靜態幣對列表改為呼叫 `PairSelector.select_optimal_pairs()`（已實作，只需串接）
2. **market_analyzer.py:906**：將 `news_sentiment=0.0` 改為呼叫 `CryptoNewsAnalyzer.analyze_news()`
3. **Plan Step 5/6**：整合 BacktestEngine 計算真實策略績效

### 中期規劃（1 個月內）

1. **Plan Step 10**：實作真正的 WebSocket 監控，整合現有的 `subscribe_ticker_stream()`
2. **SOP 回測驗證**：啟用 `_perform_plan_backtest()`，連接 BacktestEngine
3. **RAG 快取**：實作 `retriever.py` 的快取偵測邏輯
4. **策略進化整合**：將 StrategyArena、TradingPhaseRouter、RLFusionAgent 加入 CLI

---

## 附錄：核心檔案行數一覽

| 模組 | 檔案 | 行數 | 完成度 |
|------|------|------|--------|
| CLI 入口 | `cli/main.py` | 671 | ✅ 100% |
| 交易引擎 | `core/trading_engine.py` | 1,194 | ✅ 95% |
| AI 推論引擎 | `core/inference_engine.py` | 1,293 | ✅ 95% |
| 策略融合 | `strategies/strategy_fusion.py` | 1,160 | ✅ 90% |
| 趨勢策略 | `strategies/trend_following.py` | 1,192 | ✅ 90% |
| 波段策略 | `strategies/swing_trading.py` | 1,338 | ✅ 90% |
| 均值回歸 | `strategies/mean_reversion.py` | 1,295 | ⚠️ 85% |
| 突破策略 | `strategies/breakout_trading.py` | 1,194 | ⚠️ 85% |
| 交易計劃控制器 | `trading/plan_controller.py` | 608 | ⚠️ 70% |
| SOP 自動化 | `trading/sop_automation.py` | 824 | ⚠️ 75% |
| 交易前檢查 | `trading/pretrade_automation.py` | 1,051 | ✅ 95% |
| 市場分析器 | `trading/market_analyzer.py` | 1,068+ | ⚠️ 80% |
| 新聞分析器 | `analysis/news/analyzer.py` | 1,200+ | ✅ 90% |
| 回測引擎 | `backtest/backtest_engine.py` | 250+ | ✅ 95%（缺數據）|
| Binance 連接器 | `data/binance_futures.py` | 466 | ✅ 95% |

---

> 📖 上層目錄：[docs/README.md](README.md)
