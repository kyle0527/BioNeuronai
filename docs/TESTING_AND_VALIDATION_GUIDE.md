# BioNeuronAI 測試與驗證指南（Testing & Validation Guide）

> **套件版本**：v2.1  
> **更新日期**：2026-07-11  
> **方向權威**：[`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md)  
> **模組現況**：[`PROJECT_STATUS.md`](PROJECT_STATUS.md)  
> **目的**：規範正式如何證明「功能可用／預設流程跑通」。  
> **不是**：用 `tests/`、pytest、mock 單元測試當作完成標準。

---

## 目錄

1. [驗證哲學](#1-驗證哲學)
   - [1.1 一句話](#11-一句話)
   - [1.2 為什麼不用單元測試當正式驗收](#12-為什麼不用單元測試當正式驗收)
   - [1.3 工程自主 vs 智能自主](#13-工程自主-vs-智能自主)
2. [兩種時間尺度](#2-兩種時間尺度)
   - [2.1 日常／預設：真實情境操作](#21-日常預設真實情境操作)
   - [2.2 長期／大區間：先下載歷史再驗證](#22-長期大區間先下載歷史再驗證)
3. [與專案階段的對應](#3-與專案階段的對應)
4. [核心驗證路徑（真實入口）](#4-核心驗證路徑真實入口)
   - [4.1 status](#41-系統健康status)
   - [4.2 pretrade](#42-盤前pretrade)
   - [4.3 news](#43-新聞news)
   - [4.4 strategy-backtest](#44-策略歷史邏輯長期尺度)
   - [4.5 readiness-gate](#45-回測與-readiness-gate長期尺度)
   - [4.6 paper-live](#46-paper-live主線-atick)
   - [4.7 testnet](#47-testnet有金鑰時)
   - [4.8 Dashboard](#48-dashboard可選)
5. [預設自主流程專用驗收](#5-預設自主流程專用驗收)
   - [5.1 單輪](#51-單輪不執行訂單)
   - [5.2 持續閉環 + Paper](#52-持續閉環--paper-執行預設流程核心)
   - [5.3 與主線 A 分工](#53-與主線-a-的分工驗收時勿混標)
6. [正確證據（記帳）檢查](#6-正確證據記帳檢查)
7. [學習寫入分級](#7-學習寫入分級)
8. [明確不做的事](#8-明確不做的事)
9. [相關文件](#9-相關文件)
10. [修訂紀錄](#修訂紀錄)

---

## 1. 驗證哲學

### 1.1 一句話

**若功能無法在真實 CLI／Paper 虛擬帳戶／歷史回測入口被觸發並留下可觀察產物，就不算完成。**

### 1.2 為什麼不用單元測試當正式驗收

本專案早期曾散落大量 `test_xxx.py`。這類檔案：

- 容易因 Schema／架構升級而過期  
- **無法反映** WebSocket 時序、虛擬帳戶成交節奏、新聞與盤面交錯  
- 容易造成「測試全綠但真實操作不通」的假安全感  

因此 **v2.1 起正式立場**：

| 正式驗收 | 非正式（可選開發防呆） |
|----------|------------------------|
| `python main.py ...` 真實命令 | 本機 `pytest`（若存在） |
| 幣安虛擬帳戶／Paper 操作 | mock 物件單元測試 |
| 下載歷史後的 backtest／readiness-gate | 臨時一次性腳本 |
| ledger、runtime、帳戶狀態檔 | 只看 assert 通過 |

**手冊與進度報告不得寫成「已用 pytest 完成功能驗收」。**

### 1.3 工程自主 vs 智能自主

| 驗證對象 | 通過標準 | 未訓練模型時 |
|----------|----------|--------------|
| **工程自主** | 會跑、會下單／平倉、帳對、不崩 | ✅ 可以且應該驗 |
| **智能自主** | 決策品質、可解釋績效 | ❌ **不可**用當前 PnL 宣稱 AI 已可用 |

未訓練（`trained: false`）只表示 **智能未成立**，不表示 **禁止驗證流程**。

---

## 2. 兩種時間尺度

依 2026-07-11 已確認方向：

### 2.1 日常／預設：真實情境操作

- 使用 **幣安虛擬帳戶 API** 或本機 **Paper**（主網行情 + 虛擬成交）。  
- 有真實行情時序與規則觸發（含 SL/TP 等）。  
- 主要命令：`autonomous`（自主主路徑）、`trade --paper-live`（tick 觀測）。

### 2.2 長期／大區間：先下載歷史再驗證

- **先**取得歷史 K 線資料（見 [`manuals/15_DATA_ACQUISITION.md`](manuals/15_DATA_ACQUISITION.md)）。  
- **再**跑 `backtest`／`strategy-backtest`／`readiness-gate`。  
- 用途：長區間壓力、門檻矩陣、與 live paper **互補**，不是用假資料取代日常 paper。

兩種尺度都算「真實驗證」；**都不是** pytest。

---

## 3. 與專案階段的對應

| 階段 | 驗證重點 | 典型入口 |
|------|----------|----------|
| 0 健康 | 模組能起來 | `status` |
| **1 工程自主** | 預設流程跑通、記帳正確 | `autonomous --mode paper_auto --execute-paper --cycles N` |
| 2 穩定 | 長跑、重啟、卡單、重複進場 | 同上 + 重啟抽查 |
| 3 訓練改善 | 基線訓練、再開滿在線學習 | 訓練 runbook + paper 長跑 |
| 終局 | 自主時即改善 | paper 平倉後 Hub／LoRA 有變化可觀察 |

**多帳戶、API 認證等商用周邊：不納入本階段驗收阻塞項。**

---

## 4. 核心驗證路徑（真實入口）

以下皆在 **repo 根目錄** 執行。PowerShell／bash 均可（路徑依 OS）。

### 4.1 系統健康（`status`）

```bash
python main.py status
```

- **用途**：核心模組能否初始化。  
- **成功**：相關模組 `[OK]` 或文件化的降級原因；非靜默崩潰。

### 4.2 盤前（`pretrade`）

```bash
python main.py pretrade --symbol BTCUSDT --action long
```

- **用途**：技術／基本／風險盤前鏈。  
- **成功**：明確 PROCEED／CAUTION／REJECT 與理由。

### 4.3 新聞（`news`）

```bash
python main.py news --symbol BTCUSDT
```

- **用途**：新聞鏈與 RAG 寫入是否可運作或可解釋降級。

### 4.4 策略／歷史邏輯（長期尺度）

```bash
python main.py strategy-backtest --symbol BTCUSDT --interval 1h
```

- **用途**：改策略後用**真實歷史 K** 看進出場與統計，**不要**寫單元測試 assert 小數點。  
- **成功**：有可讀輸出／runtime 產物；行為可解釋。

### 4.5 回測與 readiness-gate（長期尺度）

```bash
python main.py backtest-data --symbol BTCUSDT --interval 1h
python main.py readiness-gate --dry-run
# 資料與設定齊備後：
python main.py readiness-gate --output output/readiness_gate.json
```

- **用途**：正式交易前的矩陣與門檻（資料覆蓋、walk-forward 等依設定）。  
- **成功**：dry-run 設定可讀；完整跑時 PASS／FAIL 有報告檔。

### 4.6 Paper-live（主線 A，tick）

```bash
python main.py trade --paper-live --paper-balance 10000
```

- **用途**：主網行情 + 本機虛擬成交；觀測融合信號與（若 auto）成交。  
- **成功**：穩定接收行情；信號／成交行為可觀察；**非**以未訓練 PnL 論成敗。

### 4.7 Testnet（有金鑰時）

```bash
python main.py trade --testnet
```

- **用途**：測試網真實下單路徑。  
- **注意**：仍屬真實入口；進 live 前另循 readiness 與手冊 14。

### 4.8 Dashboard（可選）

```bash
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
# 另開終端
cd frontend/devops-d
npm run dev
```

- **用途**：UI 與 API 整合。  
- **本階段**：不取代 CLI 對「自主流程跑通」的判定；CLI 仍是主證據。

---

## 5. 預設自主流程專用驗收

### 5.1 單輪（不執行訂單）

```bash
python main.py autonomous --mode advisor --symbol BTCUSDT
```

- **成功**：終端有 mode／final_action 等摘要；`decision_ledger.jsonl`（預設路徑見 runtime 手冊）追加一筆。  
- **說明**：驗證規劃鏈；**尚未**證明 paper 下單閉環。

### 5.2 持續閉環 + Paper 執行（預設流程核心）

```bash
python main.py autonomous --mode paper_auto --execute-paper --cycles 5 --symbol BTCUSDT --paper-balance 10000
```

可依需要加上（以 `python main.py autonomous -h` 為準）：

- `--max-position-hold-cycles N`：卡單平倉  
- `--reflect-every N`：每 N 輪反思（需記憶樣本）  
- `--paper-notional-fraction`：quantity 無效時的 fallback 比例  

**成功標準（工程自主）**：

1. 多輪可跑完或依 adaptation STOP 合理停機。  
2. 若 adaptation 允許執行：虛擬帳戶出現委託／持倉或明確 `skipped=existing_position`。  
3. ledger 含規劃、adaptation、paper_execution（或跳過原因）。  
4. 若發生平倉：outcome／引擎學習鏈路徑有對應紀錄（見第 6 節）。  
5. 模型若 untrained：不得將本輪盈虧解釋為「AI 已學會」。

### 5.3 與主線 A 的分工（驗收時勿混標）

| 要證明的事 | 優先入口 |
|------------|----------|
| AI 自主規劃閉環長跑 | `autonomous` |
| Tick 級融合與 T0–T2 觀測 | `trade --paper-live` |
| 長期區間 | 歷史 + backtest |

兩者現役應共用 **同一模型服務**；B 的 paper 應走 **TradingEngine 執行與 shared 平倉回調**（見 PROJECT_STATUS §1.4）。

---

## 6. 正確證據（記帳）檢查

自主／paper 跑完後，**不要**只看「有沒有報錯」。請抽查：

| 檢查項 | 看什麼 |
|--------|--------|
| 決策是否留下 | ledger 該輪 record；或 ActionRecord T0 |
| 進場是否留下 | paper_execution／T1；虛擬帳戶持倉或餘額變化 |
| 出場是否掛回 | T2／ledger trade_outcome；pnl 與帳戶一致 |
| 跳過是否誠實 | `skipped=true`、`reason=existing_position` 等 |
| 模型狀態 | log 或 stats 中 `trained: false` 是否誠實 |

詳細路徑：[`manuals/16_RUNTIME_ARTIFACTS.md`](manuals/16_RUNTIME_ARTIFACTS.md)。

**這就是「正確證據」**：給以後（或當下）在線學習用的真實日記，不是額外考試作業。

---

## 7. 學習寫入分級

| 級別 | 行為 | 何時用 |
|------|------|--------|
| 只記錄 | 寫 ledger／ActionRecord，限制或關閉權重／LoRA 持久更新 | 流程未穩、對帳中 |
| 記錄 + Hub | 平倉更新 AdaptiveLearningHub | 流程通、觀察權重變化 |
| 記錄 + Hub + LoRA | 交易即訓練終局 | 記帳穩定後；基線訓練後更佳 |

終局目標是 **自主時直接改善**；分級是為了避免未穩階段把錯誤事實寫進長期狀態。

---

## 8. 明確不做的事

1. **不要**用新建 `tests/` 檔作為「本功能驗收完成」的唯一證據。  
2. **不要**用 mock 行情宣稱 paper 閉環已在真實時序驗證。  
3. **不要**把多帳戶／認證／限流列為本階段驗收失敗原因。  
4. **不要**在 `trained: false` 時用短線盈虧對外宣稱模型能力。  
5. **不要**在記帳未對之前強制開滿 LoRA 並把結果當智能進步。

---

## 9. 相關文件

| 文件 | 用途 |
|------|------|
| [`CURRENT_DIRECTION.md`](CURRENT_DIRECTION.md) | 優先級與哲學 |
| [`PROJECT_STATUS.md`](PROJECT_STATUS.md) | 模組完成度 |
| [`manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md`](manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md) | 手冊式 Level 驗收矩陣 |
| [`manuals/03_QUICKSTART.md`](manuals/03_QUICKSTART.md) | 快速上手 |
| [`manuals/04_CLI_OPERATION.md`](manuals/04_CLI_OPERATION.md) | CLI 全參數 |
| [`manuals/14_TESTNET_AND_LIVE_TRADING.md`](manuals/14_TESTNET_AND_LIVE_TRADING.md) | paper／testnet／live／autonomous |
| [`manuals/08_BACKTEST_SYSTEM.md`](manuals/08_BACKTEST_SYSTEM.md) | 歷史回測 |
| [`manuals/16_RUNTIME_ARTIFACTS.md`](manuals/16_RUNTIME_ARTIFACTS.md) | 產物路徑 |

---

## 修訂紀錄

| 日期 | 說明 |
|------|------|
| 2026-06-09 | 初版：E2E > 單元測試 |
| 2026-07-11 | 對齊 CURRENT_DIRECTION：雙時間尺度、預設自主驗收、記帳證據、學習分級、pytest 非正式標準、商用延後 |
