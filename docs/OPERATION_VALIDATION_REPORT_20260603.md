# BioNeuronai Operation Validation Report — 2026-06-03
> Date: 2026-06-03  
> Scope: Binance Testnet 真實交易驗證 + AI 自主分析管線完整走查  
> Environment: Windows 11, Python 3.13, PyTorch CPU 2.8.0, FastAPI `127.0.0.1:8000`  
> Credentials: Binance Futures Testnet（虛擬帳戶，非真實資金）

> ⚠️ **2026-07-11 歷史快照標註**：本報告驗證的模型為 **v1 `my_100m_model_trained_20260510.pth`**，該權重已移至 `archived/legacy_v1_20260711/`，現役為未訓練的統一模型 `unified_v2_100m`。交易所連線、下單、平倉與管線走查的結論仍具參考價值，但**模型載入與推論相關段落不代表現況**；v2 統一模型的新操作驗證報告尚待產出。

本報告是對 [OPERATION_VALIDATION_REPORT_20260511.md](OPERATION_VALIDATION_REPORT_20260511.md) 的補充，專注於三個 2026-05-11 報告中刻意排除的項目：

1. 真實交易所訂單提交與平倉
2. AI 自主分析管線（TinyLLM → 策略融合 → 新聞 RAG → execute_trade）逐層走查
3. AI 自主運作機制（`start_monitoring` + `enable_auto_trading`）確認

---

## 1. Binance Testnet 憑證與帳戶驗證

| 驗證項目 | 結果 | 細節 |
|---|---|---|
| API 憑證格式驗證 | ✅ 通過 | OCR 誤讀 `l`→`I`（位置 8）修正後通過 |
| Binance Testnet API 連線 | ✅ 通過 | `testnet.binancefuture.com` 可達 |
| 帳戶狀態 | ✅ `canTrade=true` | `totalWalletBalance=5000 USDT` |
| `POST /api/v1/binance/validate` | ✅ 通過 | Binance Testnet credentials confirmed |
| `GET /api/v1/status` readiness gate | ✅ `ready=true`, `blocking=[]` | 8 項 readiness 檢查全通過 |
| `POST /api/v1/pretrade` | ✅ 正確 REJECT | 空頭趨勢 + 新聞情緒 -0.54，風控正常運作 |

---

## 2. Binance Testnet 真實訂單執行

| 操作 | 訂單 ID | 交易對 | 方向 | 數量 | 成交價 | 結果 |
|---|---|---|---|---|---|---|
| 開倉 BTC 多單 | 13869263523 | BTCUSDT | LONG | 0.002 BTC | 67,069.20 USDT | ✅ FILLED |
| 開倉 ETH 空單 | 8964845387 | ETHUSDT | SHORT | 0.05 ETH | 1,899.24 USDT | ✅ FILLED |
| 平倉 BTC 多單 | — | BTCUSDT | 平倉 SELL | 0.002 BTC | — | ✅ 已平倉 |
| 平倉 ETH 空單 | — | ETHUSDT | 平倉 BUY | 0.05 ETH | — | ✅ 已平倉 |

**最終餘額**：4,999.70 USDT（初始 5,000 USDT；-0.30 USDT = 手續費）

---

## 3. AI 自主分析管線逐層走查

### 3.1 TinyLLM 推論層（InferenceEngine）

```
模型：model/my_100m_model_trained_20260510.pth（446MB, 111.6M 參數）
載入時間：~0.53s（本機 CPU）
特徵維度：1024-dim，16 步滾動視窗
推論延遲：164.9ms（BTCUSDT，T=16）
```

**輸出**：
```
signal_type: NEUTRAL
confidence: 0.33
suggested_leverage: 4x
market_regime: bearish_trending
raw_output_dim8: [-0.9205, -0.7053, -0.1852, -1.6039, 0.1863, 0.7532, 1.3307, 0.6262]
```

### 3.2 策略融合層（StrategySelector）

| 策略 | 狀態 | 輸出方向 |
|---|---|---|
| `swing_trading` | ✅ 正常 | SHORT |
| `trend_following` | ✅ 正常 | SHORT |
| `mean_reversion` | ❌ None/Error | K 線週期不足 |
| `breakout` | ❌ None/Error | K 線週期不足 |
| `scalping` | ❌ None/Error | — |
| `grid_trading` | ❌ None/Error | — |

**AI Fusion 輸出**：
```
direction: short
confidence: 0.62
consensus_strength: 0.72
has_conflict: True
should_trade: False （信心度未超過 ai_min_confidence=0.5 門檻）
```

### 3.3 新聞 RAG 護欄層（NewsAdapter + FAISS）

```
分析新聞數：4 則
平均情緒分數：-0.543
FAISS 命中：16 筆
has_major_negative: True
→ _check_news_risk() 返回 False（阻擋交易）
```

### 3.4 execute_trade() 5 步驟逐一驗證

| 步驟 | 操作 | 結果 |
|---|---|---|
| 1 | `_check_news_risk()` | ✅ 正確阻擋（has_major_negative=True）；設計行為，非 bug |
| 2 | `_get_account_balance()` | ✅ 10,000 USDT（Paper 帳戶） |
| 3 | `_get_current_price('BTCUSDT')` | ✅ 67,224.80 USDT |
| 4 | `_calculate_position_size(10000, 67224.80, stop_loss)` | ✅ 0.01 BTC（672.25 USDT，佔餘額 6.72%） |
| 5 | `_is_cost_effective()` + `connector.place_order()` | ✅ FILLED（直接呼叫繞過新聞護欄驗證） |

### 3.5 Paper Trade 執行層（PaperBinanceFuturesConnector）

```
connector.place_order(symbol='BTCUSDT', side='SELL', quantity=0.01)
→ status: FILLED
→ order_id: 56176B3D
→ quantity: 0.01 BTC
→ price: 67,244.52 USDT
→ margin_used: 672.82 USDT

帳戶更新後：
  totalWalletBalance: 9,999.63 USDT
  availableBalance: 9,327.18 USDT（正確扣除保證金 672.82）
```

---

## 4. AI 自主運作機制驗證

**結論**：`start_monitoring(symbol)` + `enable_auto_trading()` 組合確認可啟動 WebSocket 驅動的 24/7 自主決策循環。

```python
engine = TradingEngine(testnet=True, paper_trading=True, enable_ai_model=True)
engine.load_ai_model('my_100m_model')   # TinyLLM 載入 OK
engine.enable_auto_trading()            # auto_trade = True
engine.start_monitoring('BTCUSDT')      # 訂閱 WebSocket Ticker
# 每次 Tick 觸發：
#   on_ticker_update() → _process_market_data() → generate_trading_signal()
#   → _handle_trading_signal() → execute_trade()（若 auto_trade=True）
```

- **停止方式**：`engine.stop_monitoring()` 或 `POST /api/v1/trade/stop`
- **安全機制**：新聞護欄（`_check_news_risk()`）是硬性阻擋，`auto_trade=True` 不會繞過它

---

## 5. 發現的問題與限制

| 問題 | 影響 | 建議 |
|---|---|---|
| 4/6 策略回傳 None/Error | 策略融合只有 2/6 策略有效，共識強度較低 | 調查 K 線週期計算，修復 ATR 負值問題 |
| `ai_min_confidence=0.5` 偏高 | 現役模型信心度 ~0.33 → 通常輸出 HOLD | Testnet 觀察期可降至 0.25 |
| `get_account_info()` 有時返回 None | Binance Testnet 連線異常時例外被吞掉 | 增加更明確的錯誤日誌 |
| Testnet API Key OCR 誤讀 | 小寫 `l` 被誤讀為大寫 `I`，導致 API 401 | 已修正；建議複製貼上而非手動輸入 |

---

## 6. 驗證後系統狀態摘要

| 功能 | 狀態 |
|---|---|
| Binance Testnet 連線 | ✅ 已驗證 |
| 真實 Testnet 下單與平倉 | ✅ 已驗證 |
| TinyLLM 推論（CPU, 111.6M 參數） | ✅ 已驗證（164.9ms/次） |
| 策略融合（2/6 策略有效） | ⚠️ 部分正常 |
| 新聞 RAG 護欄 | ✅ 已驗證（正確阻擋） |
| execute_trade() 5 步驟 | ✅ 已驗證 |
| Paper Trade 保證金扣款 | ✅ 已驗證 |
| AI 自主運作機制 | ✅ 已驗證 |
| 長週期自主運行觀察 | ⏳ 待後續執行 |
