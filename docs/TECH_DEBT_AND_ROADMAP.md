# BioNeuronai 技術債與開發路線圖

> 更新日期：2026-04-17
> 本文件彙整多輪分析 session 中發現的所有問題、已完成的修復、以及後續行動計畫。

## 📑 目錄

1. 已完成的修復
2. 已確認的技術債
3. 建議執行順序
4. 新聞模組驗證框架設計
5. 策略系統測試的補充說明

---

## 一、已完成的修復（本 session）

### P0 架構修復
| 項目 | 說明 |
|------|------|
| 移除硬編碼憑證 | `config/trading_config.py` 改用 `os.getenv()` |
| 統一憑證注入架構 | 入口層（CLI/API）讀取環境變數後注入模組，模組不再自行讀取 |
| `.env.example` 精簡 | 從 19 個變數削減至 4 個實際使用的變數 |
| API 健康檢查清理 | 移除 `app.py` 中已不存在的 `BacktestEngine`、`PlanController` 參照 |
| 新聞情緒接通 | `calculate_comprehensive_sentiment()` 的第 4 項從硬編碼 0.0 改為實際呼叫 `CryptoNewsAnalyzer` |
| 新增 `evolve` CLI 命令 | `StrategyArena.run()` 對應單一 CLI 入口，不再需要手動 3 步驟 |
| `.env` 自動載入 | `main.py` 已加入 `load_dotenv()`，並補上 `python-dotenv` 依賴 |
| `BINANCE_TESTNET` 一致化 | `config/trading_config.py` 統一解析，各模組不再各自判讀 |
| 對話 fallback 顯式化 | `chat` 未載入模型時，需明確加 `--allow-rule-based-fallback` 才會進入規則模式 |
| 交易 / 對話模型路徑分離 | `InferenceEngine` 使用 `my_100m_model.pth`；`ChatEngine` 使用 `tiny_llm_100m.pth` |
| RAG 基礎修補 | 交易規則檢索不再回空；embedding fallback 改為 deterministic hashed embedding |
| 新聞時效欄位 | `NewsAnalysisResult` 已加入 `signal_valid_hours`、`signal_expires_at`、`signal_urgency` |
| 交易成本與強平邊界 | 交易引擎、策略基底與 `pretrade` 已補成本效益 / 強平安全檢查 |
| **T1 外部 API 移至 data/ 層** | `analysis/` 模組不再直接呼叫 `requests.get()`；新增 `NewsDataFetcher` 與 `SyncExternalDataFetcher`；`BinanceFuturesConnector` 補充 `get_all_exchange_info()` 與 `get_all_tickers_24hr()` |

### 文件修正
| 文件 | 修正內容 |
|------|---------|
| `docs/OPERATION_MANUAL.md` | 憑證設定改為 `.env` 格式；移除硬編碼範例 |
| `docs/BIONEURONAI_MASTER_MANUAL.md` | 移除硬編碼憑證範例；`USE_TESTNET` → `BINANCE_TESTNET` |
| `docs/API_INTEGRATION_BASELINE.md` | 標記所有已完成批次 A/B/C/D |
| `docs/BRANCH_ANALYSIS_COMPARISON.md` | 改寫為現役狀態摘要，不再保留已刪除報告對照 |
| `docs/QUICKSTART_V2.1.md` | 補上目錄，並修正 chat fallback 與 PowerShell 操作說明 |

---

## 二、已確認的技術債（待處理）

### 2026-04-17 部署前盤點摘要

本次新增正式紀錄：[DEPLOYMENT_READINESS_RECORD_20260417.md](DEPLOYMENT_READINESS_RECORD_20260417.md)。

**目前部署判斷：**
- `frontend/devops-d/` 作為第一階段前端主線，已完成 npm install / build 驗證。
- `frontend/admin-da/` 與 `frontend/trading/` 暫緩，不列入第一階段部署驗收。
- 分析模組、策略模組、AI/模型主鏈已有主體，但尚未完成 backend runtime 與模型載入 smoke test。
- 本機目前沒有可用 Python runtime，Docker daemon 也未啟動，因此不能宣稱 backend 已完成部署驗收。

**新增 P0/P1 阻塞：**
| 項目 | 說明 | 優先 |
|------|------|------|
| Backend runtime 未實跑 | `python` / `py` 不可用，Docker daemon 無法連線 | P0 |
| `EventContext` 型別落差 | `strategy_fusion.py` 期待 `EventContext` 物件，部分上游仍組 dict | P0 |
| 最小測試缺口 | `pyproject.toml` 指向 `tests/`，但目前未找到正式測試目錄 | P0 |
| 模型 artifact 驗收 | `my_100m_model.pth` 仍走 legacy 相容載入；chat model 權重交付需確認 | P1 |
| API 安全 | `api/app.py` CORS 仍為 `allow_origins=["*"]`，正式部署前需收斂 | P1 |
| Docker compose bind mount | `${LOGS_DIR:-./logs}` 需先確保本機 `logs/` 存在 | P1 |

### ✅ T1：外部 API 呼叫散落在 analysis/ 模組（已完成 — 2026-04-13）

**原問題：** `analysis/` 模組直接使用 `requests.get()`，違反「外部 API 呼叫集中在 `data/` 層」的架構原則。

**已完成：**
- 新增 `data/news_data_fetcher.py`（`NewsDataFetcher`）：封裝 CryptoPanic API + RSS 的同步 HTTP 呼叫。
- 新增 `data/sync_external_fetcher.py`（`SyncExternalDataFetcher`）：封裝 Fear & Greed / Yahoo Finance / Binance Spot 的同步 HTTP 呼叫。
- `BinanceFuturesConnector` 新增 `get_all_exchange_info()`、`get_all_tickers_24hr()`、`_make_list_request()` 方法。
- `analysis/daily_report/market_data.py`：`MarketDataCollector.__init__` 改為接收 `connector` 與 `external_fetcher` 注入參數；移除所有直接 `requests.get()` 呼叫。
- `analysis/daily_report/strategy_planner.py`：`StrategyPlanner.analyze_current_market_condition()` 改透過 `connector.get_klines()` 取得 K 線；移除 `requests` 直接呼叫。
- `analysis/daily_report/risk_manager.py`：`scan_available_trading_pairs()` 和 `analyze_liquidity_metrics()` 改透過 `connector.get_all_exchange_info()` 與 `connector.get_all_tickers_24hr()` 取得；移除 `requests` 直接呼叫。
- `analysis/news/analyzer.py`：`CryptoNewsAnalyzer.__init__` 改為接收 `news_fetcher` 注入參數（未提供時自動建立預設 `NewsDataFetcher`）；`_fetch_from_cryptopanic()`、`_fetch_from_rss()`、`_process_single_rss_feed()` 全部委託 `news_fetcher` 進行 HTTP 呼叫。

---

### ✅ T2：兩個同名 StrategySelector（已完成 — 2026-04-03）

**原問題：** 專案中存在兩個功能重疊的 `StrategySelector` 類別。

| 位置 | 狀態 |
|------|------|
| `strategies/selector/core.py` | ✅ 唯一實作，保留 |
| `trading/strategy_selector.py` | ✅ 已於 commit `80d4da3` 刪除 |

**已完成：**
- `trading/strategy_selector.py` 已刪除，唯一實作為 `strategies/selector/core.py`。
- `trading/README.md` 確認「已統一使用 src/bioneuronai/strategies/selector/」。
- T2 可視為已解決。

---

### T3：RAG 模組知識庫已接通新聞分析（部分完成）

**已完成（2026-04-02）：**
- `CryptoNewsAnalyzer.analyze_news()` → `_ingest_analysis_to_rag()` → `InternalKnowledgeBase.add_news_analysis()`
- 知識庫現有 123 篇新聞 + 5 條預設交易規則，且每次 `news` 命令自動更新
- `rag/services/news_adapter.ingest_news_analysis_with_status()` 為唯一寫入入口
- `schemas/rag.py` 為所有跨模組 RAG 類型的 Single Source of Truth
- `UnifiedRetriever._retrieve_trading_rules()` 已不再直接回空陣列
- `rag/core/embeddings.py` 在缺少 `sentence-transformers` 時，已改為 deterministic hashed embedding 並輸出警告

**剩餘未完成：**
- `UnifiedRetriever.retrieve_for_trading()` 仍未在交易前檢查中呼叫
- `strategy_fusion.py` 的 `EventContext` 仍未從 RAG 知識庫填充
- `report_generator.py` 尚未將每日報告存入 `knowledge_base`（`MARKET_ANALYSIS` 類型）

**後續接通方案（最小可行）：**
```
pretrade._final_confirmation_check()
       ↓
InternalKnowledgeBase.search(symbol + regime + event_type)
       ↓
返回相關交易規則/歷史新聞 → 填入 EventContext
       ↓
strategy_fusion._adjust_weights_by_event(event_context)
```

---

### T4：news/analyzer.py 過大（中優先）

**問題：** `analysis/news/analyzer.py` 達 1146 行，混合了：
- HTTP 抓取邏輯（CryptoPanic API、RSS Feed）
- 文章篩選與去重
- 情緒分析（規則式）
- 關鍵字整合
- 結果聚合

**拆分建議：**
```
news/
  analyzer.py        → 保留：統整入口、結果聚合（< 200 行）
  fetcher.py         → 新增：HTTP 抓取（移至 data/ 層或此處）
  sentiment.py       → 新增：情緒評分邏輯
  aggregator.py      → 新增：多來源結果合併
  models.py          → 已存在，維持
  evaluator.py       → 已存在，維持
```

---

### T5：新聞抓取時間邏輯（中優先）

**問題：** 所有新聞抓取都硬編碼 `hours=24`，沒有「從上次分析到現在」的累積邏輯。

**影響：**
- 若 1 小時內執行兩次分析，第二次仍拿整整 24 小時的新聞（重複）
- 若超過 24 小時沒執行，中間的新聞可能遺漏

**修復方向：**
```python
# 在 InternalKnowledgeBase 或獨立的 AnalysisStateStore 記錄
last_analysis_time: datetime

# 抓取時
hours_since_last = (datetime.now() - last_analysis_time).total_seconds() / 3600
news = analyzer.analyze_news(symbol, hours=max(1, min(48, hours_since_last)))
```

---

### T6：CryptoNewsAnalyzer 有兩層 Wrapper（低優先）

**問題：** 同一個 `CryptoNewsAnalyzer` 被兩個 wrapper 包裝：
- `analysis/daily_report/news_sentiment.py` → 給 daily_report 用
- `rag/services/news_adapter.py` → 給 RAG retriever 用

**現況影響：低**（兩者輸出格式確實不同，功能有各自用途）

**建議：** 在兩個檔案頂部加上明確注釋說明「本檔為 CryptoNewsAnalyzer 之 X 用途適配器，勿新增第三個 wrapper」。

---

### T7：其他遺留項目

| 項目 | 位置 | 優先 |
|------|------|------|
| `api/app.py` 全域狀態未封裝 | `_trade_task`/`_trade_engine` → 應封裝為 `TradeManager` | 低 |
| `analysis/daily_report/__init__.py` | Backtest 驗證步驟未完成 | 低 |
| `phase_router.py` 認知複雜度過高 | 單一函式邏輯過多 | 低 |
| `nlp/rag_system.py` | legacy 腳本仍留存，非正式主線 | 低 |

---

## 三、建議執行順序

```
優先執行（地基）
  T1 → ✅ 已完成（2026-04-13）
  T2 → ✅ 已完成（2026-04-03）

中期執行（功能完整）
  T5 → 新聞時間邏輯修復                （具體功能缺口）
  T4 → news/analyzer.py 拆分          （可維護性）
  T3 → RAG 接通 strategy_fusion/pretrade（知識庫已有資料，剩接通消費端）

延後執行（精進）
  T6 → Wrapper 加注釋               （低風險，1 小時內完成）
  T7 → 其餘遺留項目
```

---

## 四、新聞模組驗證框架設計（新提案）

### 4.1 核心概念：事件合約（News Event Contract）

**問題：** 目前新聞情緒分析產出一個 `-1 ~ +1` 的分數，但這個分數「能影響市場多久」是固定寫死的（`decay_hours`），沒有基於實際市場反應的動態學習。

**使用者提出的驗證思路：**
把每次新聞分析視為一份「有效期合約」——預測這則新聞會在接下來的 N 小時內持續影響價格。然後在每個時間節點（1h、2h、4h、8h、24h）驗證市場是否如預期反應，最終確定這則新聞實際有效的持續時間。

---

### 4.2 現有基礎

系統已有部分機制可以擴充：

```python
# keywords/learner.py
log_prediction(keywords, predicted_direction, symbol, price_at_prediction, check_after_hours=4)
validate_and_learn(get_current_price)  # 驗證後更新關鍵字權重

# news/evaluator.py
EventRule.decay_hours  # 目前硬編碼（48h, 72h, 168h...）
cleanup_expired_events()  # 按 decay_hours 移除

# analysis/keywords/manager.py
record_prediction()  # 記錄預測
verify_prediction()  # 驗證結果（±8% 調整 dynamic_weight）
```

**缺口：** 這些機制只做「對/錯」二元驗證，沒有「這個事件持續了多久」的時間維度學習。

---

### 4.3 事件合約資料結構

```python
@dataclass
class NewsEventContract:
    """新聞事件時效合約"""
    contract_id: str                    # 唯一識別
    created_at: datetime                # 分析時間
    symbol: str                         # 交易對
    headline: str                       # 觸發新聞標題
    event_type: str                     # WAR / HACK / ETF_APPROVAL 等

    # 預測
    predicted_direction: str            # "bullish" / "bearish"
    predicted_magnitude: float          # 預期價格變動 % (e.g., 2.5)
    predicted_duration_hours: int       # 預測有效持續時間
    price_at_analysis: float            # 分析時的價格

    # 時間節點驗證結果
    checkpoints: List[ContractCheckpoint]  # [1h, 2h, 4h, 8h, 24h]

    # 最終結論（由最後一個 checkpoint 填入）
    actual_duration_hours: Optional[int] = None    # 實際有效持續時間
    final_grade: Optional[str] = None              # EXACT / OVER / UNDER / WRONG

@dataclass
class ContractCheckpoint:
    """單一時間節點的驗證"""
    hours_after: int                    # 幾小時後
    scheduled_at: datetime              # 預計驗證時間
    verified_at: Optional[datetime]     # 實際驗證時間
    price_at_check: Optional[float]     # 當時價格
    price_change_pct: Optional[float]   # 相對於分析時的價格變動 %
    still_effective: Optional[bool]     # 事件是否仍在影響市場
    confidence: Optional[float]         # 0~1，基於量能和趨勢一致性
```

---

### 4.4 「仍在影響市場」的判定邏輯

這是最關鍵的判定——不能只看價格漲跌，因為可能有其他因素干擾：

```python
def is_still_effective(
    predicted_direction: str,
    price_at_analysis: float,
    price_now: float,
    volume_ratio: float,          # 當前量 / 20日平均量
    adx: float,                   # 趨勢強度
    hours_elapsed: int
) -> Tuple[bool, float]:
    """
    判定新聞是否仍在影響市場

    Returns:
        (still_effective, confidence)
    """
    price_change_pct = (price_now - price_at_analysis) / price_at_analysis * 100

    # 方向一致性（最重要）
    direction_match = (
        (predicted_direction == "bullish" and price_change_pct > 0.3) or
        (predicted_direction == "bearish" and price_change_pct < -0.3)
    )

    if not direction_match:
        return False, 0.0

    # 量能支撐（量縮 = 事件效應衰退）
    volume_support = volume_ratio > 1.2   # 量要大於均量 20%

    # 趨勢仍強（ADX > 20）
    trend_strength = adx > 20

    # 時間折扣（越久越難維持）
    time_decay = max(0.3, 1.0 - hours_elapsed * 0.05)

    # 綜合信心度
    confidence = time_decay * (
        0.5 * (1 if direction_match else 0) +
        0.3 * (1 if volume_support else 0) +
        0.2 * (1 if trend_strength else 0)
    )

    still_effective = confidence > 0.4
    return still_effective, confidence
```

---

### 4.5 學習回饋機制

合約完成後，驗證結果反哺到兩個系統：

**A. 更新 EventRule.decay_hours（動態學習事件類型的實際持續時間）：**

```python
class DecayHoursLearner:
    """根據歷史合約學習各事件類型的實際衰減時間"""

    def update_decay_hours(self, event_type: str, actual_duration: int):
        """
        EMA 更新（避免單一異常值影響太大）
        new_decay = 0.8 * old_decay + 0.2 * actual_duration
        """
        rule = self._get_rule(event_type)
        rule.decay_hours = int(0.8 * rule.decay_hours + 0.2 * actual_duration)
```

**B. 更新 KeywordWeight（哪些關鍵字的持續時間預測最準）：**

```python
# 在 keywords/learner.py 擴充
def validate_duration_accuracy(
    self,
    contract: NewsEventContract
):
    """
    不只驗證方向對錯，也驗證持續時間預測
    持續時間誤差 < 20% → 關鍵字權重 +5%
    持續時間誤差 > 50% → 關鍵字權重 -5%
    """
```

---

### 4.6 與現有排程的整合

系統已有 `schedule` 依賴。合約驗證可掛載到現有的排程循環：

```python
# 在 trading/pretrade_automation.py 或獨立的 contract_verifier.py
import schedule

def setup_contract_verification():
    # 每小時執行一次，找出到期的 checkpoint 並驗證
    schedule.every(1).hours.do(
        ContractVerifier().run_pending_checkpoints
    )
```

**資料儲存：** 合約存入現有的 `trading.db`（SQLite），新增 `news_event_contracts` 和 `contract_checkpoints` 兩張表，與現有的 `event_memory`、`prediction_history` 共用同一個資料庫。

---

### 4.7 事件合約的觸發時機

```
新聞分析完成
    ↓
news_score > 0.5 (or < -0.5)  ← 只有明確信號才建立合約
    ↓
建立 NewsEventContract
設定 checkpoints = [1h, 2h, 4h, 8h, 24h]
    ↓
背景排程每小時掃描到期的 checkpoint
    ↓
拿當時 K 線 + 量能判定 is_still_effective()
    ↓
記錄結果 → 最後一個 checkpoint 完成時
    ↓
計算 actual_duration_hours
    ├── 更新 EventRule.decay_hours
    └── 更新 keyword 權重（duration accuracy）
```

---

### 4.8 實作優先順序

| 步驟 | 工作量 | 說明 |
|------|--------|------|
| 1. 定義 schema | 小 | `NewsEventContract`、`ContractCheckpoint` dataclass |
| 2. 合約建立 | 小 | 在 `CryptoNewsAnalyzer` 完成分析後觸發 |
| 3. Checkpoint 驗證 | 中 | `is_still_effective()` 邏輯 + SQLite 寫入 |
| 4. 排程整合 | 小 | 掛載到現有 schedule loop |
| 5. decay_hours 學習 | 中 | `DecayHoursLearner` + EMA 更新 |
| 6. keyword duration 學習 | 中 | 擴充 `keywords/learner.py` |
| 7. 回測/回放模式 | 大 | 用歷史 K 線回放驗證（可選，用於初始訓練） |

**最小可行版本（步驟 1-4）**：只需約 300 行，即可讓系統開始收集實際有效時間的數據，為步驟 5-6 的學習提供基礎。

---

## 五、策略系統測試的補充說明

**使用者確認：** 策略系統（`strategy_fusion`、`market_regime` 等）可以完全用歷史 K 線資料進行回測，不依賴外部 API，測試框架相對單純。

**重點差異：新聞模組的挑戰**

| 比較項目 | 策略系統 | 新聞模組 |
|---------|---------|---------|
| 輸入來源 | 本地 K 線 CSV / Binance historical | 即時新聞 API（無法完全重播） |
| 驗證基準 | 價格結果明確 | 需定義「新聞有效」的判定標準 |
| 回測可行性 | 高 | 中（需要新聞存檔 + 對應 K 線） |
| 測試難點 | 無 | 怎麼定義新聞「持續了多久」 |

事件合約框架解決的正是最後一個難點：用市場實際反應（價格 + 量能 + 趨勢）來客觀定義一則新聞的「有效期」，而不是主觀判斷。

---

*文件結束 — 下次 session 從本文件的「建議執行順序」繼續*
