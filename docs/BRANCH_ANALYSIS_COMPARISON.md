# 分支對照分析報告

> 更新日期：2026-04-10  
> 目的：將先前多輪分支比對與修復結果，收斂成目前可作為現役參考的狀態文件。  
> 原則：只記錄已由現役程式與現役文件確認的內容；不再保留已刪除報告的逐條摘錄與對照表。

---

## 目錄

1. 文件定位
2. 目前已完成的非資料類修復
3. 目前仍存在的結構性技術債
4. 刻意延後的資料類項目
5. 文件維護結論
6. 一句話結論

---

## 1. 文件定位

本文件不再作為「歷史分支報告比對表」，而是改為記錄目前主線已確認的落地狀態。

目前用途如下：

- 給接手開發者快速確認哪些非資料類問題已經落地修復。
- 明確區分「仍存在的結構性技術債」與「刻意延後的訓練 / 歷史資料工作」。
- 避免後續 session 重複引用已過時或已移除的報告內容。

---

## 2. 目前已完成的非資料類修復

### 2.1 交易主線與交易成本整合

以下項目已接入現役交易主線：

- `TradingEngine` 已整合交易成本過濾與市場微結構資料轉接，不再只依賴靜態成本假設。  
  位置：`src/bioneuronai/core/trading_engine.py`
- `TradingCostCalculator` 已支援動態 `funding_rate`、`spread_bps` 與強平邊界估算。  
  位置：`config/trading_costs.py`
- 策略進場前已補上成本效益與強平安全檢查。  
  位置：`src/bioneuronai/strategies/base_strategy.py`
- `pretrade` 流程也已補上同樣的成本與強平檢查。  
  位置：`src/bioneuronai/planning/pretrade_automation.py`
- Binance 匯率整合已真正接到使用點，不再只停留在 service 層。  
  位置：`src/bioneuronai/data/exchange_rate_service.py`、`src/bioneuronai/data/database.py`

### 2.2 模型與對話主線收斂

以下項目已由現役程式確認：

- `InferenceEngine` 已能處理正式交易 checkpoint 載入，並維持舊版交易模型相容路徑。  
  位置：`src/bioneuronai/core/inference_engine.py`
- `ChatEngine` 預設改用 `model/tiny_llm_100m.pth`，不再混用交易 checkpoint。  
  位置：`src/nlp/chat_engine.py`
- CLI `chat` 不再默默退回規則模式；若要使用開發 fallback，必須明確加上 `--allow-rule-based-fallback`。  
  位置：`src/bioneuronai/cli/main.py`
- `train_with_ai_teacher.py` 的示範資料已明確標示為 demo，用於開發驗證時必須顯式加上 `--allow-demo-data`。  
  位置：`src/nlp/training/train_with_ai_teacher.py`

### 2.3 訓練與冷啟動防呆

以下項目已改為 fail-fast 或顯式模式：

- `auto_evolve.py` 在非互動環境不再卡在 `input()`。  
  位置：`src/nlp/training/auto_evolve.py`
- `unified_trainer.py` 預設不再靜默生成隨機 signal 資料，沒有真實 JSONL 會直接報錯。  
  位置：`src/nlp/training/unified_trainer.py`
- `backtest/service.py` 不再在推論引擎不可用時寫入全零 signal 標籤。  
  位置：`backtest/service.py`

### 2.4 新聞與 RAG 修補

以下項目已從空殼或缺欄位狀態修補為可用版本：

- `NewsAnalysisResult` 已補上 `signal_valid_hours`、`signal_expires_at`、`signal_urgency` 等欄位。  
  位置：`src/bioneuronai/analysis/news/models.py`
- 新聞分析器已在輸出階段填入信號有效期與時效資訊。  
  位置：`src/bioneuronai/analysis/news/analyzer.py`
- `UnifiedRetriever` 的交易規則檢索不再直接回空陣列。  
  位置：`src/rag/core/retriever.py`
- embedding fallback 已改為 deterministic hashed embedding，並會明確輸出警告，不再用隨機向量污染檢索結果。  
  位置：`src/rag/core/embeddings.py`

### 2.5 環境與一致性修復

以下一致性問題已收斂：

- `main.py` 已加入 `.env` 自動載入。  
  位置：`main.py`
- `python-dotenv` 依賴已補上。  
  位置：`pyproject.toml`
- `BINANCE_TESTNET` 已統一由單一 helper 解析，不再由各模組各自判讀。  
  位置：`config/trading_config.py` 與各呼叫點
- 版本敘述已統一為 `v2.1`，不再有現役文件聲稱 `v2.2`。  
  位置：現役 `docs/`、`README.md`、`CHANGELOG.md`

---

## 3. 目前仍存在的結構性技術債

以下項目不是訓練資料問題，但目前仍屬結構性技術債：

### 3.1 交易模型仍保留 legacy 相容路徑

- `InferenceEngine` 目前仍保留舊版 `HundredMillionModel` 相容載入。
- 這讓正式交易主線可用，但代表交易模型架構尚未完全收斂成單一路徑。
- 目前建議把這視為「受控相容層」，不是新的待辦錯誤。

位置：`src/bioneuronai/core/inference_engine.py`

### 3.2 analysis 層仍有外部 HTTP 呼叫散落

- `analysis/news/analyzer.py`
- `analysis/daily_report/market_data.py`
- `analysis/daily_report/risk_manager.py`
- `analysis/daily_report/strategy_planner.py`

這代表「外部 API 集中在 `data/` 層」的架構原則還沒完全落地。

### 3.3 REST API 交易狀態仍使用全域變數

- `api/app.py` 仍使用 `_trade_task`、`_trade_engine` 等全域狀態。
- 這在單機可用，但還沒有收斂成管理類別。

位置：`src/bioneuronai/api/app.py`

### 3.4 RAG 的消費端尚未完全接通

目前已完成的是：

- 新聞入庫
- 交易規則檢索
- embedding fallback 修補

目前尚未完成的是：

- `UnifiedRetriever.retrieve_for_trading()` 尚未成為 `pretrade` / `strategy_fusion` 的正式消費入口。
- `EventContext` 仍未由 RAG 檢索結果自動填充。

---

## 4. 刻意延後的資料類項目

以下項目已知存在，但本階段刻意不處理：

| 項目 | 目前狀態 | 原因 |
|------|---------|------|
| 訓練語料不足 | `ALL_TRADING_DATA` 規模仍小 | 需等待更完整交易域資料 |
| `train_with_ai_teacher.py` demo 資料 | 已改為顯式 opt-in | 示範資料不應當正式語料 |
| signal bootstrap 資料來源 | 不再寫入全零標籤，但仍缺第一輪真實標籤 | 需依賴真實交易 / 回放資料 |
| tokenizer / vocab 擴充 | 現有 `vocab.json` 可用但覆蓋率有限 | 屬語料工程，不是主線 bug |
| 歷史資料與歷史數據整備 | 仍需後續補完 | 已明確排除於本輪工作之外 |

---

## 5. 文件維護結論

本文件已完成以下整理：

- 移除舊的逐條摘錄、A/B/C/D 判定表與已刪除文件引用。
- 改為只保留目前主線已確認的完成項與仍存在的技術債。
- 將「訓練資料 / 歷史資料」與「非資料類主線修復」明確拆開，避免後續 session 重複把已延期事項重新列為當前 bug。

後續若有新修復，請直接更新本文件第 2、3、4 節，不再新增新的平行報告。

---

## 6. 一句話結論

截至 2026-04-10，非資料類主線修復已大致落地；目前仍需持續追蹤的，主要是外部 API 分層、RAG 消費端接通，以及交易模型的 legacy 相容層收斂。
