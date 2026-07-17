# Unified v2 多模態模型訓練手冊

> **更新日期**：2026-07-12
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)
> **訓練方向權威**：[`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md) §6.4

## 1. 目標與目前狀態

`unified_v2_100m` 是唯一現役模型，約 98.4M 參數。同一個 checkpoint 同時處理市場數值、中英文脈絡、結構化交易決策與文字說明；它不是另一個通用大語言模型。

目前 `config/active_model.json` 仍是 `deterministic_untrained`。因此系統可端到端運作，但輸出尚非學得的交易能力。現有 `collect-signal-data` 可收集真實未來 K 線衍生的 v2 數值標籤，**尚未**完成新聞歷史回補、時間配對與兩來源契約；不可把現有收集器輸出當成完整多模態訓練資料。

## 2. 正式資料來源與保存邊界

訓練用新聞與日常新聞使用相同的兩個來源契約：

| 類別 | 來源 | 使用範圍 |
|------|------|----------|
| 幣圈 | CoinDesk RSS／年度文章索引 | 幣種、交易所、ETF、監管、駭客與產業事件 |
| 總經／地緣政治 | Google News RSS 固定宏觀查詢（`en-US`、`zh-TW`） | 戰爭、制裁、能源、Fed/FOMC、通膨、衰退、美國／歐洲經濟、ECB 等 |

歷史回補最小保存集為 `source_category`、實際發布者、`title`、`summary`、`url`、`published_at_utc`、`fetched_at_utc`、`language`、關鍵字／事件標籤與事件衰減資訊。未確認來源條款前，只保存 RSS 提供的標題與摘要；不以「免費可閱讀」推論可大量抓取及保存全文。

### 2.1 中英 BPE tokenizer

`nlp.bilingual_tokenizer.BilingualTokenizer` 使用 Hugging Face `tokenizers` 的 ByteLevel BPE 實作，且只以 `zh`、`en` 的正式新聞快照建立語料。它不是舊的逐字切分器：新幣名、機構名與事件名可拆成可重用子詞／位元組，而不需要為每個新詞寫規則。

- `model/tokenizer/vocab.json` 是 runtime、trainer 與 chat 共用的唯一 tokenizer artifact。
- `unified_v2_100m` 的詞彙上限固定為 **16,000**；不得直接替換成 110k／250k 多語模型詞彙。
- 每筆新聞記錄會保存 `language`、`source_id` 與 `summary`，作為原始歸檔、歷史訓練與 tokenizer corpus；平常交易決策不重讀這些原文。
- tokenizer 版本以 artifact content hash 記錄；正式 checkpoint 必須與建立它的 tokenizer 版本共同保存及切換。

## 3. 新聞—市場時間對齊（不可違反）

每筆回放樣本有一個決策時間 `T`。輸入只能包含：

1. 截止 `T` 已公開的 Binance 市場資料；
2. `published_at_utc <= T` 的兩類新聞；
3. 在 `T` 前已成立、且到 `T` 仍未衰減完的事件合約；
4. 截止 `T` 可由策略模組產生的戰術訊號。

模型接著預測固定的未來窗口，例如 `T+1h`、`T+4h`、`T+24h`。標籤由真實 Binance 後續 K 線計算，而不是由舊模型、人工猜測或當前模型輸出製造。文章在 `T` 後發布、更新，或無法可靠取得發布時間時，一律不可放入該筆樣本。

本節的完整新聞快照只用於歷史訓練／回放。日常自主交易的模型輸入使用截止當下仍有效的濃縮事件記憶（事件類型、衰減重要性、剩餘時間），完整文章只在 `HH:05` 新聞更新或重大新事件時處理一次。

```text
T 時刻的市場 patch + 截止 T 的新聞快照 + 尚有效事件 + 策略訊號
                              ↓
                  unified_v2_100m 預測方向／參數／說明
                              ↓
                   對照 T+1h / T+4h / T+24h 真實價格
                              ↓
                     形成可審計的訓練與評估紀錄
```

「來源抓取失敗」不是中性新聞。回補工作必須記錄失敗日期，不能以空集合取代；日常運作中任一正式來源失敗，該輪也不產生新的新聞戰略或下單判斷。

## 4. 訓練資料契約

原始 replay manifest 必須至少有下列欄位，並保留可追溯的新聞 ID／URL：

```json
{
  "decision_time_utc": "2025-07-11T07:00:00Z",
  "symbol": "BTCUSDT",
  "market_features": "16x64 numeric patch derived no later than T",
  "news_snapshot_ids": ["..."],
  "active_event_ids": ["..."],
  "strategy_context": "signals available at T",
  "future_outcomes": {"1h": "realized", "4h": "realized", "24h": "realized"},
  "source_manifest_version": "versioned"
}
```

餵給既有 trainer 的 JSONL 仍需符合 v2 契約：`features` 為 `(16,64)`、`signal` 為 `(65,)`、非空 `context_text` 與非空 `explanation`。`context_text` 必須由該筆真實新聞快照與策略事實組成；說明標籤必須可追溯到真實資料欄位，不能讓未訓練模型自我產生後再拿來訓練。

CoinDesk 提供英文幣圈語料；Google News 宏觀來源同時提供 `en-US` 與 `zh-TW` 文章。這些真實資料會持續累積到同一份 16k BPE corpus；其後再用本節的真實新聞—市場資料做領域對齊。這仍是**同一個**多模態模型與同一份 checkpoint。

## 5. 收集、切分與訓練順序

完整資料目標是一年，但依同一契約分三次執行：

1. **一個月**：驗證來源、時區、去重、事件衰減、新聞與 K 線時間對齊。
2. **三個月**：做連續時間的訓練／驗證與 walk-forward 評估，確認沒有未來資訊洩漏。
3. **一年**：建立基線 checkpoint，並在保留的最後時間區段評估。

訓練、驗證與測試只能按時間切分；不可隨機打散相鄰樣本，也不可讓未來預測窗口彼此重疊。正式訓練前必須先保留最後一段完全未看過的時間區間做最終評估。

### 5.1 知識蒸餾思想（從舊指南併入，對齊 v2）

舊版 `知識蒸餾訓練指南` + `train_with_ai_teacher.py` 已封存；**不要**再當現役入口。可保留的方法論如下：

| 舊說法 | v2 正確做法 |
|--------|-------------|
| 老師=大模型產生閒聊對話 | 老師標籤必須是 **真實市場結果**（T+1h/4h/24h）與可追溯新聞事實，不是 demo 對話 |
| 學生=TinyLLM v1 | 學生=`unified_v2_100m`，入口 `python -m nlp.training.unified_trainer` |
| 幾千句通用中英即可 | 雙語 tokenizer corpus 可輔助語言；**交易能力**仍靠新聞—市場配對 + 信號張量 |
| 內建 `AI_TEACHER_DATA` | 禁止當 ground truth；舊 512 維／未標時間戳樣本一律拒絕 |

蒸餾在本專案的合法形態：

```text
真實資料（新聞事實 + K 線 + 事件記憶）
        ↓  規則／市場結果標註（非 untrained 模型自標）
  v2 訓練 JSONL / signal_*.pt
        ↓
  unified_trainer（可雲端 GPU）
        ↓
  通過 paper / walk-forward 後再 promote active_model.json
```

考古全文：`docs/archive/recovered_from_git/old_docs/knowledge_distillation_guide.md`。  
雲端步驟見 [13_CLOUD_TRAINING_RUNBOOK.md](13_CLOUD_TRAINING_RUNBOOK.md)。

現有數值資料收集入口如下，僅可作為完整資料鏈中的市場數值部分：

```powershell
python main.py collect-signal-data `
  --symbol BTCUSDT `
  --interval 1h `
  --future-horizon 12 `
  --output data/unified_v2_training.jsonl
```

完整新聞—市場 replay collector 尚未實作；在它完成以前，不應手工混入不帶來源、發布時間或未來標籤的 JSONL。

## 6. 訓練與 promotion

既有 trainer 的正式入口如下：

```powershell
python -m nlp.training.unified_trainer `
  --signal-data data/unified_v2_training.jsonl `
  --signal-val-data data/unified_v2_validation.jsonl `
  --epochs 10 `
  --batch 2 `
  --grad-accum 8 `
  --output output/unified_v2_training
```

訓練會對方向、信心、槓桿、持有、體制、倉位、SL/TP、時間框架、不確定性、型態與市場脈絡說明計算對應 loss。promotion 只能接受模型名稱相同且含 TinyLLMv2 numeric encoder 的 checkpoint；成功後才寫入 `model/unified_v2_100m.pth` 並將 `active_model.json` 改為 `trained_checkpoint`。

本機 CPU 適合資料結構檢查與短區間驗證。完整訓練可按日期分批或使用外部 GPU，但不得以 mock、合成新聞或舊 512 維模型輸出代替真實資料。
