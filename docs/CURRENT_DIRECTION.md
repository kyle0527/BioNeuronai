# BioNeuronAI 已確定方向（權威摘要）

> **文件狀態**：現行方向單一事實來源之一  
> **生效日期**：2026-07-11  
> **套件版本**：v2.1（`pyproject.toml`）  
> **與現況關係**：模組完成度細節仍以 [`PROJECT_STATUS.md`](PROJECT_STATUS.md) 為準；**優先級、驗證哲學、預設流程定義以本文為準**。  
> **若其他文件與此文衝突**：以本文與 `PROJECT_STATUS.md` 較新段落為準，並應回修舊文。

---

## 目錄

1. [一句話目標](#1-一句話目標)
2. [工作優先順序（已確認）](#2-工作優先順序已確認)
   - [2.1 為什麼是這個順序](#21-為什麼是這個順序)
   - [2.2 兩種「自主成功」必須分開說](#22-兩種自主成功必須分開說)
3. [預設流程定義（什麼叫「跑通」）](#3-預設流程定義什麼叫跑通)
   - [3.1 建議預設入口](#31-建議預設入口)
   - [3.2 階段 1「跑通」驗收清單](#32-階段-1跑通驗收清單正式非-pytest)
   - [3.3 「正確證據」是什麼](#33-正確證據是什麼白話)
4. [雙入口、單一模型與執行層](#4-雙入口單一模型與執行層)
   - [4.1 對照表](#41-對照表現行)
   - [4.2 模型現況](#42-模型現況不得寫錯)
5. [驗證哲學（正式驗收）](#5-驗證哲學正式驗收)
   - [5.1 核心原則](#51-核心原則)
   - [5.2 為什麼不用 test 檔](#52-為什麼不用-test-檔做時機驗收)
   - [5.3 建議驗證路徑](#53-建議驗證路徑對齊階段)
6. [學習與訓練在流程中的位置](#6-學習與訓練在流程中的位置)
   - [6.1 終局](#61-終局正確)
   - [6.2 過渡](#62-過渡工程自主階段建議)
   - [6.3 離線訓練與歷史 RL](#63-離線訓練與歷史-rl)
7. [商用周邊：明確延後](#7-商用周邊明確延後)
8. [與舊文件的常見衝突（修正對照）](#8-與舊文件的常見衝突修正對照)
9. [建議閱讀與操作順序](#9-建議閱讀與操作順序)
10. [修訂紀錄](#修訂紀錄)

---

## 1. 一句話目標

先讓系統在 **幣安虛擬帳戶／Paper 真實時序** 下，依 **預設自主流程** 能長時間自己跑完  
（決策 → 下單 → 持倉 → 平倉 → **正確記帳**），  
再在此底座上 **邊自主邊改善**（在線學習／後續基線訓練）。  

**不是**先做多帳戶、API 認證、單元測試覆蓋；**也不是**把「模型尚未訓練」當成流程失敗。

---

## 2. 工作優先順序（已確認）

以下順序為產品與工程共識，**請勿顛倒**：

| 階段 | 名稱 | 要證明什麼 | 不要求什麼 |
|:----:|------|------------|------------|
| **0** | 單輪接通 | `status`、單輪 `autonomous` / 短 `trade` 能初始化並產出可觀察結果 | 勝率、商用多租戶 |
| **1** | **工程自主（目前主戰場）** | 預設路徑能持續跑：真實行情時序、虛擬帳戶真下真平、帳本對得上、可重啟 | 模型已訓練、績效優秀 |
| **2** | **穩定確認** | 多輪／多小時不崩、卡單與重複進場行為可預期、產物可審計 | 對外 SaaS 能力 |
| **3** | **訓練改善** | 歷史資料＋真實軌跡訓練基線；再開滿在線學習，改善決策 | 在階段 1 未通前強訓 |
| **終局** | **自主＝改善** | 交易即訓練：平倉結果回寫 → Hub／LoRA（等）影響後續 | 永遠「只跑不學」 |

### 2.1 為什麼是這個順序

1. **沒有穩定執行與記帳，訓練與在線學習沒有可信教材。**  
2. **終局仍是「自主運行時直接改善」**，不是永久拆成「只自主」與「另開訓練專案」。  
3. 在功能未穩或模型仍為 **deterministic untrained** 時，學習 **寫入** 可以先降級（只記錄），避免 bug／噪音污染 Hub／LoRA 狀態；**這是過渡安全閥，不是否定交易即訓練。**

### 2.2 兩種「自主成功」必須分開說

| 層級 | 含義 | 目前是否為驗收目標 |
|------|------|-------------------|
| **工程自主** | 無人值守能跑：不崩、會下單／平倉、ledger／ActionRecord 正確、風控生效 | ✅ **是（階段 1–2）** |
| **智能自主** | 決策品質可信任、可談績效與商用智能 | ❌ 屬階段 3 之後；**未訓練模型不得用 PnL 證明 AI 能力** |

---

## 3. 預設流程定義（什麼叫「跑通」）

### 3.1 建議預設入口

| 角色 | CLI | 說明 |
|------|-----|------|
| **AI 自主主路徑（預設）** | `python main.py autonomous ...` | 定時規劃迴圈；`--cycles N`（N>1）進入 `run_forever`；真下單需 `--mode paper_auto` + `--execute-paper` |
| **即時 tick／完整 T0–T2 觀測** | `python main.py trade --paper-live ...` | WebSocket 驅動；適合補樣本與觀測策略＋AI 融合 |
| **長期／大區間驗證** | 先下載歷史 → `backtest`／`strategy-backtest`／`readiness-gate` | 不取代日常虛擬帳戶真實操作 |

兩條 CLI **控制方式不同**，但現役設計目標為：

- **同一** `unified_v2_100m` InferenceEngine 實例（`get_shared_inference_engine()`）  
- **主線 B paper 執行**委派 `TradingEngine.execute_prepared_order()`  
- **平倉**經 shared callback：同時走 TradingEngine 學習鏈與 autonomous ledger  

手冊不得再寫成「B 線永遠有獨立 paper 連接器、永遠沒有 LoRA」。

### 3.2 階段 1「跑通」驗收清單（正式，非 pytest）

全部在 **repo 根目錄**、用 **真實 CLI／產物檔** 驗證：

1. **啟動**：一條指令進入持續或可重複的自主／paper 流程。  
2. **行情**：使用真實市場資料流或真實歷史 K（依模式），非假 mock 單元測試。  
3. **虛擬帳戶**：有進場、有持倉狀態、有出場（SL/TP／規則平倉／卡單等至少一種可觀察路徑）。  
4. **記帳對帳**（「正確證據」）：  
   - 決策當下有紀錄（ledger 與／或 ActionRecord T0）  
   - 進場有紀錄（T1 或 paper_execution）  
   - 出場結果掛回**同一業務脈絡**（T2／ledger outcome／餘額變化可對）  
5. **重啟合理性**：重啟後不應無故幽靈倉、不應在「已有持倉」時無提示重複開倉（B 線 `existing_position` 跳過為預期行為）。  
6. **學習開關可預期**：操作者能說明當前是「只記錄」還是「Hub／LoRA 有寫入」（見第 6 節）。  
7. **模型誠實**：`config/active_model.json` 為 `trained: false` 時，log／說明須標示未訓練；**流程可通，智能未成立**。

### 3.3 「正確證據」是什麼（白話）

**不是**現在就要訓練，**是**自主跑時把日記寫對：

- 當時看到什麼（特徵／計畫／pretrade）  
- 決定做什麼（方向、數量、是否跳過）  
- 後來結果怎樣（pnl、平倉原因）  

以後（或當下開啟在線學習時）改善吃的就是這本帳。帳錯了，現在學也是錯的。

---

## 4. 雙入口、單一模型與執行層

### 4.1 對照表（現行）

| 維度 | 主線 A：`trade` | 主線 B：`autonomous` |
|------|-----------------|----------------------|
| 驅動 | WebSocket 即時 tick | `run_forever` 定時規劃 |
| 決策 | StrategySelector + shared InferenceEngine | Plan → shared InferenceEngine → Pretrade → Adaptation |
| Paper 執行 | TradingEngine 內 | **委派** `TradingEngine.execute_prepared_order()` |
| 模型 | `unified_v2_100m` shared | **同一** shared instance |
| ActionRecord T0/T1/T2 | ✅ 引擎主路徑完整 | 平倉經 shared callback 進入引擎學習鏈；B 自身以 ledger 為主審計 |
| EpisodicMemory / LoRA | ✅ paper 平倉觸發 | ✅ **經** `TradingEngine._on_paper_close`（shared callback） |
| Decision Ledger | ❌ | ✅ append-only JSONL |
| AdaptiveLearningHub | ✅ | ✅ |
| 典型用途 | 即時監控、tick 級融合與 T0–T2 觀測 | **預設 AI 自主長跑**、規劃閉環 |

### 4.2 模型現況（不得寫錯）

- 現役唯一：`unified_v2_100m`（TinyLLM v2），約 98.4M 參數。  
- `config/active_model.json`：`initialization: deterministic_untrained`，`trained: false`，`model_path: null` 直至產出 `model/unified_v2_100m.pth`。  
- v1 權重與舊腳本在 `archived/legacy_v1_20260711/`（或同等封存路徑），**不得**再當現役 loader 目標。  
- **禁止**再寫「`enable_v2_mode()` 仍是 stub、predict 仍走 v1」——與現行程式不符。

---

## 5. 驗證哲學（正式驗收）

### 5.1 核心原則

| 原則 | 說明 |
|------|------|
| **日常驗證** | 在 **幣安虛擬帳戶／Paper** 上真實操作；有真實行情時序與虛擬撮合規則 |
| **長期／大區間** | **先下載歷史資料**，再跑 backtest／replay／readiness-gate |
| **禁止以單元測試當功能完成標準** | `tests/`、pytest、臨時 mock 腳本 **不得**作為「流程已跑通」或「功能完成」的正式依據 |
| **正式入口** | CLI（`main.py`）、必要時 API／Dashboard／Docker；驗收看終端輸出與 runtime／ledger／memory 等**真實產物** |

### 5.2 為什麼不用 test 檔做時機驗收

單元測試無法忠實反映：

- 交易所／行情 WebSocket 時序  
- 虛擬帳戶成交、SL/TP 觸發節奏  
- 新聞與 pretrade 與真實盤面交錯  

因此專案驗收堅持 **End-to-End 真實入口**。  
（開發者可在本機使用 pytest 做防呆，但那是開發輔助，**不是**手冊驗收與進度證據。）

### 5.3 建議驗證路徑（對齊階段）

| 階段 | 建議真實入口 | 成功長相 |
|------|--------------|----------|
| 健康 | `python main.py status` | 核心模組可初始化 |
| 盤前 | `python main.py pretrade --symbol BTCUSDT --action long` | PROCEED／CAUTION／REJECT 可解釋 |
| 自主單輪 | `python main.py autonomous --mode advisor --symbol BTCUSDT` | ledger 追加；有 final_action |
| **自主 paper（預設流程核心）** | `autonomous --mode paper_auto --execute-paper --cycles N ...` | 虛擬帳戶有狀態；ledger 有 execution／outcome |
| 即時 paper | `trade --paper-live --paper-balance ...` | tick 驅動；可觀察信號與（若開啟）成交 |
| 長期 | 下載歷史 → `backtest`／`readiness-gate` | runtime 報告、門檻 PASS／FAIL 可讀 |

細節命令與產物路徑見：

- [`manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md`](manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md)  
- [`TESTING_AND_VALIDATION_GUIDE.md`](TESTING_AND_VALIDATION_GUIDE.md)  
- [`manuals/04_CLI_OPERATION.md`](manuals/04_CLI_OPERATION.md)  
- [`manuals/16_RUNTIME_ARTIFACTS.md`](manuals/16_RUNTIME_ARTIFACTS.md)

---

## 6. 學習與訓練在流程中的位置

### 6.1 終局（正確）

```text
自主運行
  → 真實虛擬帳戶成交與平倉
  → 正確記帳（證據）
  → AdaptiveLearningHub / LoRA 等更新
  → 影響後續決策
```

即：**功能完成且記帳正確後，自主時就應能訓練／改善**，無需另起一個與交易無關的「只訓練」人生。

### 6.2 過渡（工程自主階段建議）

| 模式 | 用途 |
|------|------|
| **只記錄** | 驗證流程與對帳；不寫入 LoRA／可限制 Hub |
| **記錄 + Hub** | 觀察策略權重是否隨結果變化 |
| **記錄 + Hub + LoRA** | 終局；建議在記帳穩定後再開滿 |

未訓練基線長跑時，若全力在線更新，可能把噪音寫進持久狀態；應用重置／備份狀態檔的方式可還原（路徑見 runtime 手冊）。

### 6.3 離線訓練與歷史 RL

- **基線訓練**（完整 v2 checkpoint）：階段 3；需要真實配對資料，舊 512 維 v1 輸出 **不可**當 v2 ground truth。  
- **歷史 RL**（`training/rl_trainer.py`）：離線強化 Meta-Learner 等，屬補強，不取代日常 paper 閉環。  
- **長期驗證**：歷史下載 → 回測，與日常虛擬帳戶操作 **互補**，不是二選一。

---

## 7. 商用周邊：明確延後

以下 **不是** 當前「預設流程跑通」的阻塞項，**後續再加**即可（難度相對可控，但現在不做）：

- 多帳戶／多租戶  
- API 認證、rate limiting  
- 監控告警產品化、訂單 dead-letter 平台級方案  
- 多實例負載均衡  

長期產品仍以可商用為價值方向，但 **當前唯一主線是預設自主流程跑通**。  
文件中若將上述列為 P0，視為 **過時優先級**，應改為「延後／非本階段」。

---

## 8. 與舊文件的常見衝突（修正對照）

| 舊說法 | 現行正確說法 |
|--------|----------------|
| 主線 B 無 LoRA／無學習閉環 | B 經 shared 平倉回調進入引擎學習鏈；另有 ledger |
| B 永遠獨立 paper 連接器 | Paper 應取自 TradingEngine；執行走 `execute_prepared_order` |
| `enable_v2_mode` 為 stub、現役 v1 | 現役 unified v2；可 untrained 但仍是 v2 路徑 |
| 正式驗收靠 pytest／`tests/` | **否**；真實 CLI／虛擬帳戶／歷史回測產物 |
| 先訓練再談自主 | **先工程自主與記帳，再訓練改善**；終局邊跑邊學 |
| 多帳戶／認證是當前重點 | **否**；延後 |
| 未訓練＝系統不能跑 | 未訓練＝**智能未成立**；工程流程仍應可驗證 |
| README「P3 仍 stub」 | P3 基線接通；缺的是 **已訓練權重** |

---

## 9. 建議閱讀與操作順序

1. 本文 [`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md)  
2. [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — 模組完成度  
3. [`ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) — 架構  
4. [`TESTING_AND_VALIDATION_GUIDE.md`](TESTING_AND_VALIDATION_GUIDE.md) — 驗證細節  
5. [`manuals/03_QUICKSTART.md`](manuals/03_QUICKSTART.md) → [`manuals/04_CLI_OPERATION.md`](manuals/04_CLI_OPERATION.md) → [`manuals/14_TESTNET_AND_LIVE_TRADING.md`](manuals/14_TESTNET_AND_LIVE_TRADING.md)  
6. [`manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md`](manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md) — 手冊式驗收矩陣  

---

## 修訂紀錄

| 日期 | 說明 |
|------|------|
| 2026-07-11 | 初版：固定優先級、預設流程、驗證哲學、學習終局、商用延後、舊文衝突表 |
