# BioNeuronai src/ 目錄結構分析報告

**用途**: 呈現 `src/` 目錄下各模組的職責劃分與互相依賴關係，包含資料結構、資料層、分析層、規劃層、交易層等分層架構。
**版本**: v2.1
**更新日期**: 2026-04-06
**分析範圍**: `C:\D\E\BioNeuronai\src`

---

## 📑 目錄

1. 模組依賴關係圖
2. 分層模組詳細說明
3. schemas/ 數據結構層
4. RAG 與 NLP 子系統
5. 文件總結

---

## 1. 模組依賴關係圖

### 核心依賴層級

```
第 0 層 (資料契約)
  ↓
schemas/          ← 所有模組的 Single Source of Truth
  ├── types.py         (基礎類型)
  ├── enums.py         (全局枚舉)
  └── ...

第 1 層 (基礎設施層)
  ↓
bioneuronai.data/  ← 數據獲取與存儲、外部 API
  ├── binance_futures.py
  ├── database.py     
  └── web_data_fetcher.py

第 2 層 (帳本層與風控基礎)
  ↓
bioneuronai.trading/  ← 訂單、虛擬帳戶與持倉事實
bioneuronai.risk_management/ ← Sizing 與風險計算公式

第 3 層 (策略與分析層)
  ↓
bioneuronai.analysis/  ← 新聞解析、特徵工程、市場狀態
bioneuronai.strategies/ ← 具體策略、Selector、Fusion

第 4 層 (規劃與決策層)
  ↓
bioneuronai.planning/ ← 生成整體交易計畫、交易前檢查、Pair 選擇
bioneuronai.core/  ← 整合並調用 Engine 進行主要推理與對外執行 (TradingEngine, InferenceEngine)

第 5 層 (接口與測試層)
  ↓
bioneuronai.api/ 和 bioneuronai.cli/  ← 最終對外端口
backtest/          ← 抽換掉真實 Data 層用作回顧測試
```

---

## 2. 分層模組詳細說明

### 2.1 對外入口 (`bioneuronai/cli/` & `bioneuronai/api/`)
負責接收使用者的指令或 HTTP 請求。會直接呼叫 `planning/` 產出計畫或呼叫 `core/trading_engine.py` 執行交易。

### 2.2 核心大腦 (`bioneuronai/core/`)
- `trading_engine.py`: 主驅動迴圈，負責協調資料、模型、風控與執行。
- `inference_engine.py`: AI 推理，提煉出 1024 維特徵交由 model 推算方向。
- `self_improvement.py`: 負責針對過往的回測與實盤資料，對策略參數進行更新或汰換。

### 2.3 規劃層 (`bioneuronai/planning/`)
- 整合大盤的趨勢與情緒。
- `pretrade_automation.py` 負責 6 點硬性檢查。
- 產出給 `trading_engine.py` 遵循的高階指示。

### 2.4 策略層 (`bioneuronai/strategies/`)
所有傳統指標或技術分析策略（如 trend_following、mean_reversion）及它們的管理者。
- `selector/`: 負責決定何時啟用何策略。
- `strategy_fusion.py`: 將 AI 出的訊號與傳統技術指標結合計算權重。
- `strategy_arena.py`: 策略互相競技的「養蠱」機制。

### 2.5 帳本與風控 (`bioneuronai/trading/` & `bioneuronai/risk_management/`)
- `trading/virtual_account.py`: 無論真假資金，記錄一切資金轉移、留倉量的事實來源，供回測器及虛擬盤使用。
- `risk_management/`: 以純粹的數學機制計算每個 Signal 可以分配的保證金數額、最大回撤(Drawdown)監控。

---

## 3. schemas/ 數據結構層

**作用**: 定義整個系統的所有核心模型，確保嚴格的 Pydantic 模型驗證與類型安全，徹底避免辭典 (dict) 的無序操作。

- **`types.py` / `enums.py`**: 枚舉如 `OrderSide`, `PositionType`, `RiskLevel`。
- **`market.py` / `external_data.py`**: 描述 K線、委託簿、恐慌指數等大盤指標。
- **`trading.py` / `orders.py`**: 訂單明細與交易狀態流轉紀錄。
- **`strategy.py`**: 定義回測及交易時所需的統一 Config Schema。

**設計原則**: 完全 0 依賴其他子系統，所有上層模組皆反向依賴於此。

---

## 4. RAG 與 NLP 子系統

### 4.1 `src/rag/` (內部檢索增強)
提供針對新聞與盤後日報的內置知識搜查。
- 透過 `core/retriever.py` 與 `internal/knowledge_base.py`，把即時新聞存成 FAISS 向量庫，供 `planning/` 判斷盤前風險。

### 4.2 `src/nlp/` (自研微型模型與訓練鏈)
提供 100M 以下自研模型的對話與編譯。
- 包含 Training (AI teacher)、矩陣乘法優化 (LoRA)、量化腳本等模組工具，確保 `my_100m_model.pth` 可持續更新。

---

## 5. 文件總結

`src/` 目錄現已高度模組化，明確捨棄了過去混雜的巨大交易腳本 (如原本的 `trading_strategies.py` 或是舊的 `trading/risk_manager.py`)，將**策略決策**、**風險運算**與**帳本追蹤**嚴格拆解。接手開發者只需遵循「從 `schemas` 定義資料，在 `planning` 做決策，交由 `core` 執行調度」的思路即可順利接軌 `v2.1`。
