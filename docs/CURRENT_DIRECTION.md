# BioNeuronAI 已確定方向（權威摘要）

> **文件狀態**：現行方向單一事實來源之一  
> **生效日期**：2026-07-12
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
    - [6.4 新聞—市場歷史回放訓練契約](#64-新聞市場歷史回放訓練契約)
7. [商用周邊：明確延後](#7-商用周邊明確延後)
8. [與舊文件的常見衝突（修正對照）](#8-與舊文件的常見衝突修正對照)
9. [建議閱讀與操作順序](#9-建議閱讀與操作順序)
10. [自主 runtime 與單一產品面板](#10-自主-runtime-與單一產品面板)
11. [修訂紀錄](#修訂紀錄)

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

### 6.4 新聞—市場歷史回放訓練契約

正式雙來源與事件重要性契約已實作；歷史回放收集器仍尚待程式實作，**不得**把回放訓練描述成目前已完成的功能。

#### 運行時三層責任與資料流

1. **新聞模組（戰略背景，一般程式）**：負責來源、HH:05 排程、語言／關鍵字篩選、去重、原始保存、事件合併、重要性衰減／延長、到期與經濟日曆；不得決定多空或下單。
2. **策略模組（戰術候選，一般程式）**：負責策略保存、載入、切換、市場計算與融合候選；不得抓新聞或執行訂單。
3. **AI（判斷與決策）**：只讀 16×64 市場數值、濃縮 `news_memory`、獨立 `strategy` 候選與部位狀態，輸出 LONG／SHORT／HOLD、信心、倉位／槓桿、SL／TP、持有時間與有效期限。
4. **執行層**：只執行 AI 的有效決策並回報成交／平倉結果，不替 AI 改方向。

自主程式啟動時抓取一次完整新聞，此後以 `Asia/Taipei` 每小時第 5 分鐘更新；其他戰術迴圈只讀事件類型、衰減後重要性、剩餘時間與日曆提醒，不重讀標題或正文。人的自然語言報告只在使用者要求時，從當時 AI 輸入與決策生成。

#### 即時新聞來源與失敗語意

正式目標只有兩個外部新聞入口，分工而非互為備援：

| 類別 | 唯一入口 | 用途 |
|------|----------|------|
| 幣圈新聞 | CoinDesk RSS／年度文章索引 | 幣種、交易所、ETF、監管、駭客、鏈上與產業事件 |
| 總經與地緣政治 | Google News RSS 的固定宏觀查詢 | 戰爭、制裁、能源、Fed/FOMC、通膨、衰退、美國與歐洲經濟、ECB 等 |

- 不再把 CryptoPanic、CoinTelegraph、Decrypt 或其他來源列為正式來源，也**不**建立第三、第四來源的降級鏈。
- 每次新聞輪次都必須同時取得兩類資料；任一來源 HTTP／解析失敗即回報明確錯誤。該輪不得把「無法取得」當成中性新聞、不得以部分新聞生成新的事件狀態，也不得據此產生新的自主下單決策。
- 「沒有符合關鍵字的文章」與「來源抓取失敗」是不同狀態：前者是有效的零篇結果，後者是錯誤。

#### 真實歷史回放資料

對每個決策時間點 `T`，訓練資料只能使用 `published_at <= T` 的新聞、在 `T` 前已可得的 Binance 市場數值，以及尚未衰減完的既有事件。接著才以 `T+1h`、`T+4h`、`T+24h` 的**真實**價格結果標記方向與結果。不可隨機打散相鄰且未來窗口重疊的資料，也不可讓修訂後或在 `T` 後發布的新聞倒灌進 `T`。

新聞保存的最小事實集為：來源類別、實際發布者、標題、RSS 摘要、URL、`published_at`（UTC）、抓取時間、原文語言、關鍵字／事件標籤、事件重要性與剩餘有效時間。規則不保存固定多空；方向留給統一 AI 依市場狀態、事件狀態與策略候選共同判斷。免費可讀不等於可大量保存全文或取得訓練授權；在確認來源條款前，歷史回補只保存 RSS 可提供的標題與摘要，不進行全文爬取。

資料量以「一個月資料鏈驗證 → 三個月時序與效果確認 → 一年基線訓練」依序完成；這是同一套完整契約的分段執行，不是另做最小版本。約一億參數的單一模型仍需真實雙語語料／分詞器或相容的雙語預訓練起點；一年新聞—市場配對資料負責教會它交易領域的對齊，不能單獨取代中英文語言能力。

---

## 7. 商用周邊：明確延後

以下 **不是** 當前「預設流程跑通」的阻塞項，**後續再加**即可（難度相對可控，但現在不做）：

- 多帳戶／多租戶  
- API 認證、rate limiting  
- 監控告警產品化、訂單 dead-letter 平台級方案  
- 多實例負載均衡  

長期產品仍以可商用為價值方向，但 **當前唯一主線是預設自主流程跑通**。  
文件中若將上述列為 P0，視為 **過時優先級**，應改為「延後／非本階段」。

### 7.1 商用實作參考與本專案取捨

- QuantConnect Algorithm Framework 將訊號、部位建構、風險與執行拆成不重疊的責任，資料由上一層流向下一層；本專案採用相同的責任分離精神，但保留「新聞記憶 + 策略候選共同輸入同一 AI」的既定融合方向。
  來源：<https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview>
- QuantConnect Scheduled Events 以明確時區、日期與時間規則觸發工作；本專案將它具體化為 `Asia/Taipei` 啟動一次及每小時 HH:05 新聞更新，而不是讓每個策略 tick 重抓新聞。
  來源：<https://www.quantconnect.com/docs/v2/writing-algorithms/scheduled-events>
- QuantConnect Order Events 以訂單狀態事件回報整個生命週期；本專案沿用既有 shared TradingEngine／ledger／平倉 callback，執行層回報結果但不覆寫 AI 方向。
  來源：<https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events>
- LSEG Machine Readable News 強調正規化、時間點一致的新聞、事件 metadata，以及與歷史行情對齊；本專案使用免費 RSS 能取得的事實集與 Binance 行情實作相同資料原則，不宣稱具備 LSEG 的商業資料覆蓋或授權。
  來源：<https://www.lseg.com/content/dam/data-analytics/en_us/documents/fact-sheets/lseg-machine-readable-news.pdf>

以上是工程做法的依據，不是產品需求來源；若商用平台的預設行為與本文第 1–6 節已確認方向不同，仍以本專案方向為準。

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
| 新聞抓不到＝中性、或改用其他來源 | **否**；正式兩來源任一失敗即錯誤，本輪不產生新的新聞戰略／下單判斷 |

---

## 9. 建議閱讀與操作順序

1. 本文 [`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md)  
2. [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — 模組完成度  
3. [`ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) — 架構  
4. [`TESTING_AND_VALIDATION_GUIDE.md`](TESTING_AND_VALIDATION_GUIDE.md) — 驗證細節  
5. [`manuals/03_QUICKSTART.md`](manuals/03_QUICKSTART.md) → [`manuals/04_CLI_OPERATION.md`](manuals/04_CLI_OPERATION.md) → [`manuals/14_TESTNET_AND_LIVE_TRADING.md`](manuals/14_TESTNET_AND_LIVE_TRADING.md)  
6. [`manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md`](manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md) — 手冊式驗收矩陣  

---

## 10. 自主 runtime 與單一產品面板

2026-07-20 確認的產品操作目標是：使用者手動開啟程式後，AI 載入既有狀態並運作；使用者停止程式或關機時，AI 安全保存並休息；下次開啟再接續同一份 paper 帳戶、決策帳本與記憶。這不是 Windows 開機自啟或 24 小時背景服務。

- **唯一自主線**：只能由 `AutonomousOperator` 產生 paper 執行意圖；UI、API、ticker observer 都不得繞過 Plan → PreTrade → Adaptation。
- **每日完整檢查**：依 `Asia/Taipei` 日曆日，當日第一次成功後才可略過；失敗不算完成，下次開啟必須重試。每次啟動仍必做資料、模型、持久化狀態及保護單的快速安全檢查。
- **唯一面板目標**：目前 `frontend/devops-d` 是唯一已接入 Docker／手冊的面板基底；完成 runtime API 與實測後，收斂為單一產品面板 `frontend/app`。`frontend/trading` 與 `frontend/admin-da` 僅能移植已驗證的顯示元件，之後封存，不再作啟動、Docker 或手冊入口。
- **禁止項**：面板不可提供直接送單／平倉、testnet／正式網自動下單、訓練啟動、模型 promotion 或 API playground 作為日常操作入口。

此為已確認的實作方向，尚未代表桌面啟動器、runtime REST API 或 `frontend/app` 已完成；實際狀態與驗收見 [`MODULE_INTEGRATION_AUDIT.md`](MODULE_INTEGRATION_AUDIT.md) 與 [`PROJECT_STATUS.md`](PROJECT_STATUS.md)。

---

## 修訂紀錄

| 日期 | 說明 |
|------|------|
| 2026-07-11 | 初版：固定優先級、預設流程、驗證哲學、學習終局、商用延後、舊文衝突表 |
| 2026-07-12 | 確認兩個正式新聞入口、抓取失敗語意，以及新聞—市場真實歷史回放訓練契約 |
| 2026-07-13 | 固定新聞／策略／AI／執行層責任、HH:05 濃縮事件記憶輸入，並加入商用官方實作參考與專案取捨 |
| 2026-07-20 | 確認手動啟動／停止的自主 runtime 生命週期、每日完整檢查語意，以及單一產品面板收斂與舊面板封存方向。 |
