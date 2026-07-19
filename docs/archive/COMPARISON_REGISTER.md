# 新舊比對登錄表（終版盤點）

> **更新日期**：2026-07-17  
> **工作順序（使用者約定 · 見 [`WORK_ORDER.md`](WORK_ORDER.md)）**：  
> 1. 全部檢查完 → 2. 該移的移回來 → 3. 調整完 → 4. **修使用者手冊** → 5. **才**照手冊真實操作（虛擬帳戶 OK；不用 pytest）

**考古原文**：`docs/archive/recovered_from_git/`  
**v1 封存（磁碟）**：`archived/legacy_v1_20260711/`  
**purge 來源 commit**：`9f6e271` 父版 `archived/`（約 124 個文字路徑已枚舉）

---

## 決策代碼

| 代碼 | 意義 |
|------|------|
| **HOME** | 已接回現役程式或正式手冊 |
| **MERGE** | 思想／清單併入現役，不原樣掛回 |
| **KEEP-NEW** | 現役已優於或已取代舊版；舊文僅考古 |
| **NEVER** | 禁止當現役（架構／方向衝突） |
| **SKIP** | 明確不做（含全部 tests、一次性 JSON 快照） |
| **ARCH** | 已抽出到 recovered 供考古；無需進主線 |

---

## 五步進度（與 WORK_ORDER 一致）

| 步驟 | 內容 | 狀態 |
|:----:|------|:----:|
| 1 | 全部檢查 | ✅ 完成（`STEP1_DECISIONS_COMPLETE.md`） |
| 2 | 該移回 | ✅ 完成（WF+param_grid） |
| 3 | **調整** | 🔄 進行中（見 `WORK_ORDER.md` 步驟 3；CODE_FIX_GUIDE） |
| 4 | 修使用者手冊 | ⏸ |
| 5 | 照手冊操作 | ⏸ |

---

## 1. 已接回現役（HOME）

| 項目 | 落點 |
|------|------|
| 多窗 Walk-Forward | `backtest/walk_forward.py` + CLI `--walk-forward`（rolling）；readiness 用 single |
| SOP 應急清單 | `manuals/14` §9、`18` §9 |
| 知識蒸餾方法論 | `manuals/12` §5.1（禁止 demo 語料） |
| 宏觀資料源表 | `manuals/15` §3.1 |
| 新聞風控語意 | pretrade／plan／fusion／analyzer 修正 |
| 盤點總表 | 本檔 + `recovered_from_git/` |

---

## 2. 程式能力核對（無需再抓回）

| 舊物 | 現役 | 決策 |
|------|------|------|
| `cost_calculator.py` | `config/trading_costs.py` | KEEP-NEW |
| `historical_backtest.py` | `backtest/` 全套 | KEEP-NEW |
| `Dockerfile.train` | `Dockerfile` training target | KEEP-NEW |
| Binance 四 API + 限流 | `binance_futures.py` | KEEP-NEW |
| 關鍵字 98 | config 505 | KEEP-NEW |
| FNG／經濟日曆 stub | daily_report 已實作 | KEEP-NEW |
| `StrategyArena` 願景基因庫 | Arena + Meta + WF；基因混搭 LATER | MERGE |
| `nlp/rag_system.py` | `src/rag/` | KEEP-NEW |
| `tiny_llm.py` / v1 `.pth` | v2 untrained | NEVER |
| `train_with_ai_teacher` / `auto_evolve` | `unified_trainer` | NEVER |
| 全部 tests 還原 | — | SKIP |

---

## 3. 文件類（124 路徑歸類）

### 3.1 KEEP-NEW — 已被 manuals／現行 docs 取代

- `docs_v2_1_legacy/*`（MASTER、QUICKSTART、OPERATION、BACKTEST、RISK、HANDOVER、SRC…）  
- `docs_v3/USER_MANUAL`、`CRYPTO_TRADING_README`、`TRADING_STRATEGIES_GUIDE`  
- 舊 `PROJECT_STATUS_*`、`PROJECT_COMPLETION_*`、`FEATURE_STATUS`、`MANUAL_IMPLEMENTATION_STATUS`  
- `old_docs/*` 狀態報告（HONESTY、FINAL_REPORT、SUMMARY、CAPABILITIES…）  
- `reports/*`、`reports_20260215/*` 歷史報告  
- `MOCK_ANALYSIS_REPORT`、`jules_session/*` 分析文  

→ 全文可在 git `9f6e271^:archived/...` 或已抽出之 recovered 查看；**勿當現況**。

### 3.2 MERGE — 有用段落已併入

| 舊 | 併入 |
|----|------|
| CRYPTO_TRADING_SOP 應急 | manuals 14／18 |
| 知識蒸餾指南 | manuals 12 |
| DATA_SOURCES_GUIDE | manuals 15 §3.1 |
| MARKET_KEYWORDS 手冊數字 | keywords README |
| BINANCE_API 方法表 | data README |
| DAILY_REPORT_CHECKLIST | daily_report README |
| EVOLUTION_SYSTEM_PLAN | strategies README |
| TRADING_COSTS 說明 | 已有 trading_costs + manuals 成本敘述 |

### 3.3 NEVER — 不可當現役

| 舊 | 原因 |
|----|------|
| NEWS_ANALYZER_GUIDE（多源 CryptoPanic） | 與 fail-fast 雙來源衝突 |
| TINYLLM_MODEL_GUIDE（512 維 v1） | 與 unified v2 衝突 |
| core.py / hundred_million_net / pytorch_100m | 舊神經元實驗 |
| 規則情緒決定多空的任何 SOP | 與 CURRENT_DIRECTION 衝突 |
| v1 權重 promote | loader 拒絕 |

### 3.4 SKIP

- 全部 `old_scripts/test_*`、`use_*`、一次性 validate（由 `main.py` CLI 取代）  
- jules 的 pretrade/sop JSON 快照、old_data db  
- **任何 pytest 還原或「用 tests 當完成證明」**

### 3.5 ARCH — 已抽出供考古

優先集：`recovered_from_git/{backtesting,docs_v3,old_docs,tech,root_guides}/`  
補充：`recovered_from_git/_full_rest/`（FEATURE_STATUS、EVENT_SYSTEM、TECH_DEBT、DATAFLOW…）

---

## 4. 本輪程式變更清單

| 檔案 | 作用 |
|------|------|
| `backtest/walk_forward.py` | 多窗 rolling + single |
| `backtest/service.py` | 整合 WF |
| `backtest/readiness_gate.py` | WF mode=single |
| `src/.../cli/main.py` | WF CLI 參數與輸出 |
| `pretrade_automation.py` | 重要性／風險類型 |
| `strategy_fusion.py` | bias 永不多空 |
| `plan_controller.py` | 風險看重要性 |
| `news/analyzer.py` | should_trade legacy |

---

## 5. 明確不阻塞實測的 LATER 項

（已登錄，**不**在「抓回」階段再做）

1. 全球股指真實資料（非 NEUTRAL 降級）  
2. 基因級策略混搭引擎  
3. NewsPredictionLoop 改驗 AI 結果  
4. 新聞—市場 historical replay collector + v2 訓練權重  
5. GoalTracker 自動風險回饋  

---

## 6. 步驟 5（照手冊操作）— 僅在步驟 4 完成後

以 `docs/manuals/` 為準（建議 03→04→14→16→01），虛擬帳戶／Paper 可真跑。  
**現在不執行。** 不宣稱 paper 長跑或智能已驗證。

---

## 7. 盤點結論

| 問題 | 答案 |
|------|------|
| 舊 purge 有沒有漏網該接回的主線能力？ | **多窗 WF 已接回**；其餘 KEEP-NEW／NEVER／SKIP |
| 新聞舊方向語意有沒有清？ | **步驟 3 已清** pretrade／plan／fusion／should_trade |
| 使用者手冊是否可整本照做？ | **否** — 步驟 4 未完成 |
| 可以開始照手冊實操嗎？ | **否** — 等步驟 4 完成 |

---

## 修訂紀錄

| 日期 | 說明 |
|------|------|
| 2026-07-17 | 初版 + HOME WF／新聞；終版補 124 路徑歸類與 A→B→C 階段 |
