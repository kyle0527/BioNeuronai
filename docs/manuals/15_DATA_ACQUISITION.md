# 資料取得與資料目錄操作手冊

> **套件版本**：v2.1
> **更新日期**：2026-07-12
> **範圍**：確認、取得與檢查歷史市場與新聞—市場 replay 資料
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)

---

## 目錄

1. [確認本地資料](#1-確認本地資料)
2. [市場資料根目錄與相容搜尋順序](#2-市場資料根目錄與相容搜尋順序)
3. [下載歷史資料](#3-下載歷史資料)
4. [即時新聞與事件記憶](#4-即時新聞與事件記憶)
5. [歷史新聞回補（已確認規格）](#5-歷史新聞回補已確認規格)
6. [新聞與市場時間配對](#6-新聞與市場時間配對)
7. [API / CLI 查詢](#7-api--cli-查詢)
8. [短回測驗收](#8-短回測驗收)
9. [缺失排查](#9-缺失排查)
10. [勿手動修改的資料](#10-勿手動修改的資料)

---

## 1. 確認本地資料

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

成功標準：顯示 `resolved_root`、至少一組 dataset、日期範圍與檔案數量。

---

## 2. 市場資料根目錄與相容搜尋順序

`backtest/paths.py` 的 `candidate_data_roots()` 搜尋順序：

| 優先 | 路徑 | 說明 |
|------|------|------|
| 1 | `--data-dir` 指定 | CLI/API 覆寫 |
| 2 | `backtest/data/binance_historical/` | **正式規格** |
| 3 | `data/bioneuronai/historical/data_downloads/binance_historical/` | 專案相容路徑 |
| 4 | `data_downloads/binance_historical/` | 舊路徑 |
| 5 | `training_data/data_downloads/binance_historical/` | 訓練用相容路徑 |

常見檔案結構：

```text
.../binance_historical/data/futures/um/daily/klines/<SYMBOL>/<INTERVAL>/
```

詳見 [`backtest/data/README.md`](../../backtest/data/README.md)。

---

## 3. 下載歷史資料

資料缺失時，使用 repo 內下載工具（路徑依專案設定，常見為 `tools/data_download/`）。下載完成後重新執行 `backtest-data` 確認 catalog。

readiness-gate 需要 BTC/ETH 多週期（如 `1h`、`4h`）資料齊全時，請依 [`config/trading_readiness_gate.json`](../../config/trading_readiness_gate.json) 矩陣補齊。

---

## 3.1 宏觀輔助資料來源（舊 DATA_SOURCES 指南併入）

日報／plan 可選用（非新聞 fail-fast 契約）：

| 指標 | 來源 | 現役 |
|------|------|------|
| 恐慌貪婪指數 | Alternative.me | `MarketDataCollector` + external_fetcher |
| 全球市值／BTC 占比 | CoinGecko | plan／daily_report 路徑 |
| DeFi TVL | DefiLlama | 視 fetcher 注入 |
| 資金費率／交割 | Binance public API | `check_economic_calendar` |

突發事件**不**另建第三新聞來源；靠正式雙 RSS + 事件合約。考古全文：`docs/archive/recovered_from_git/docs_v3/DATA_SOURCES_GUIDE.legacy.md` 與 `_full_rest/`。

## 4. 即時新聞與事件記憶

日常自主運作只使用以下正式位置：

```text
data/bioneuronai/trading/sop/news_records.json          # 原始 RSS 標題／摘要歸檔
data/bioneuronai/trading/sop/news_event_contracts.json # 濃縮事件、重要性、衰減與有效期
```

舊 `src/data/bioneuronai/trading/sop/` 會由新聞分析器一次性合併搬移後移除，不能再作第二資料來源。啟動時先更新一次；持續自主運作對齊本地時間 `HH:05`。平常策略／AI 循環只讀事件記憶，不重讀 `news_records.json`。

---

## 5. 歷史新聞回補（已確認規格）

> 本節是已確認的資料規格。新聞來源切換與 replay collector 尚待實作；目前不可把它當成已有 CLI 指令。

新聞歷史資料只使用兩個入口：

| 類別 | 來源 | 回補方式 |
|------|------|----------|
| 幣圈 | CoinDesk RSS／年度文章索引 | 依年份、月份或日期索引列出文章，再按發布時間保存 RSS 標題／摘要與來源事實 |
| 宏觀／地緣政治 | Google News RSS 固定宏觀查詢 | 以固定歷史日期窗口查詢；關鍵字涵蓋戰爭、制裁、能源、Fed/FOMC、通膨、衰退、美國／歐洲經濟與 ECB |

這是「一個幣圈入口＋一個宏觀入口」，不是一串主備來源。任一來源在某日期窗口抓取失敗，collector 必須留下錯誤紀錄，該窗口不得以空資料補齊，也不得改抓未列入規格的第三方網站。

正式實作時，新聞 replay 的唯一資料根目錄定為：

```text
data/bioneuronai/historical/news_market_replay/
```

其下資料應以版本化 manifest、原始新聞快照與配對後樣本分層保存；不得與即時 RAG 快取、`news_records.json` 或模型 checkpoint 混放。來源條款尚未確認前，只保存 RSS 可提供的標題、摘要、URL 與 metadata，不大量抓取全文。

建議依同一份完整資料契約回補：先一個月確認時區／去重／事件衰減，再三個月做 walk-forward 檢查，最後擴至一年。這是避免未來資訊洩漏的資料品質關卡，不是另一套簡化版訓練。

---

## 6. 新聞與市場時間配對

每個訓練或回放決策時間點為 `T`（全部以 UTC 保存）：

1. 選用截止 `T` 可用的 Binance K 線與市場特徵。
2. 選用 `published_at_utc <= T` 的新聞；以實際發布時間而非抓取時間決定資格。
3. 把在 `T` 尚未過期的事件合約及其衰減強度加入快照。
4. 僅在上述輸入固定後，才讀取 `T+1h`、`T+4h`、`T+24h` 的真實 K 線生成結果標籤。

禁止：把未來文章、後來修訂的內容、沒有可靠發布時間的文章，或下一個樣本窗口的資料放回 `T`。訓練、驗證、測試也必須依時間切分，不能隨機洗牌相鄰樣本。

---

## 7. API / CLI 查詢

**CLI：**

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h --json
```

**API**（需先啟動 uvicorn）：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/backtest/catalog?symbol=BTCUSDT&interval=1h"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/data/catalog"
```

---

## 8. 短回測驗收

```powershell
python main.py backtest `
  --symbol BTCUSDT `
  --interval 1h `
  --start-date 2020-01-01 `
  --end-date 2020-01-03 `
  --balance 10000 `
  --warmup-bars 10
```

成功標準：終端印出 Run ID；`backtest/runtime/<run_id>/` 有輸出。詳見 [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)。

---

## 9. 缺失排查

| 現象 | 可能原因 | 處理 |
|------|----------|------|
| catalog 0 組 | 未下載或路徑錯 | 檢查 §2 各路徑；執行下載工具 |
| symbol 找不到 | 無該交易對 | 換現有 symbol 或補資料 |
| interval 找不到 | 無該週期 | readiness 常需補 `4h` 等 |
| 回測日期超出範圍 | start/end 不在 catalog | 依 catalog 日期重設 |
| 歷史新聞窗口缺失 | 指定來源 HTTP／RSS／日期解析失敗 | 記錄失敗窗口並修復來源；不可當作沒有新聞或用第三來源補齊 |
| 新聞與價格無法對齊 | 時區、`published_at` 或 K 線窗口錯 | 全部轉 UTC，重新建立該窗口；不可人工猜測時間 |

---

## 10. 勿手動修改的資料

```text
backtest/data/binance_historical/   # 唯讀歷史來源
data/processed/*.pt
model/*.pth
data/bioneuronai/historical/news_market_replay/  # 實作後的唯讀原始／manifest 層
```

手動改動會使回測/訓練不可重現。
