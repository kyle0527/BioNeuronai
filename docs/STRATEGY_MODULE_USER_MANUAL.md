# 策略模組操作手冊

這份手冊只講策略模組怎麼操作，不覆蓋整個專案，也不重講分析模組或 AI 訓練模組。

定位很簡單：

1. 怎麼用 CLI 跑策略模組
2. 怎麼用 UI 跑策略模組
3. 跑完去哪裡看 10 個策略的比較結果與交易紀錄

---

## 適用範圍

目前這份手冊對應的是策略模組的「競爭 / 回放」操作：

- 10 個策略模板的正式 replay 評估
- `template_rules` 模式
- `hybrid` 模式
- 每個策略的模擬成交紀錄、統計與 runtime 輸出

不包含：

- 真實下單
- AI 權重訓練
- PhaseRouter / PortfolioOptimizer 的完整研究流程

---

## 這個功能實際在做什麼分析

策略模組的 `strategy-backtest` / `strategy-run` 功能，不是單純把策略跑過一次而已，它是在做「同標準策略競爭分析」。

它會把多個策略放在同一個比較框架下：

- 同一個 `symbol`
- 同一個 `interval`
- 同一段歷史資料
- 同一個初始資金
- 同一個 replay 撮合機制
- 同一個回測收尾規則

在這個前提下，系統會輸出每個策略的：

- 交易次數
- 勝率
- 總報酬率
- 實現損益
- 訂單與成交紀錄
- runtime 結果檔

這代表它不是只看「策略配置寫得漂不漂亮」，而是直接比較：

1. 哪個策略真的會進場
2. 哪個策略真的能出場
3. 哪個策略在同樣條件下表現較穩定
4. 哪些策略其實沒有訊號、沒有成交，或績效明顯不合理

---

## 預計會達到什麼效果

這個功能預期帶來的效果有三個層次。

### 1. 把策略比較從主觀變成可量化

原本如果只看策略名稱、模板參數或說明文字，很難知道哪個策略真的比較好。

加入這個功能後，可以直接得到：

- 排名
- 績效差異
- 每個策略的模擬進出場紀錄

這會把策略選擇從「感覺上哪個策略比較合理」改成「同資料下哪個策略實際比較有效」。

### 2. 提早找出有問題的策略

這個功能可以很快看出：

- 策略完全沒有進場
- 策略進場太頻繁
- 策略只會開倉不會正常出場
- 策略手續費吃掉大部分利潤
- 某些參數設定導致策略失真

也就是說，它除了做排名，也同時是策略模組的早期品質檢查工具。

### 3. 讓參數調整有明確回饋

配合 `--params` 或 API 的 `parameter_overrides`，你可以改單一策略的 entry / exit / risk 參數，再重新跑一次。

這樣就能直接回答：

- 止損改小之後，交易數是不是暴增
- 倉位改大之後，報酬有沒有提高，回撤是否變差
- RSI / MA / breakout 閾值調整後，策略是否更穩定

---

## 這個功能對整個專案有什麼幫助

這個功能對整個專案的幫助，不只在策略模組本身，而是在整條交易決策鏈上提供一個可重複、可比較、可追蹤的中介層。

### 1. 對策略模組本身

- 幫助 10 個策略維持在相同比較標準下競爭
- 讓策略不是停留在模板描述，而是變成可驗證的模擬交易結果
- 讓之後的策略淘汰、保留、調參有依據

### 2. 對上層決策模組

- 可以把策略競爭結果提供給 selector / strategy competition / 後續編排層當作參考
- 可以知道目前哪些策略值得保留到更高層，例如 fusion、router、optimizer
- 可以避免把一個其實沒有成交能力的策略錯誤送進上層流程

### 3. 對未來 AI / 權重訓練

- 它可以先提供乾淨的策略績效與交易紀錄基線
- 等未來要做 AI 權重訓練時，可以先知道哪些策略值得當作候選輸入
- 也能避免 AI 直接學到一堆實際上無法成交或表現失真的策略輸出

### 4. 對專案維護

- 每次修改策略邏輯後，可以重新跑同一段資料，比對結果是否退化
- runtime 檔案可以保留證據鏈，方便追查問題
- CLI、API、UI 共用同一套回放邏輯，降低「不同入口測出不同結果」的風險

簡單講，這個功能的價值是：

- 把策略模組從靜態配置，推進到可操作的競爭系統
- 把策略比較從主觀判斷，推進到有交易紀錄的量化分析
- 幫整個專案建立策略層的正式驗證入口

---

## 先知道兩個模式

### `template_rules`

這是目前策略競爭的主操作模式。

- 直接把 selector 內的 10 個策略模板全部轉成可執行的 replay 策略
- 每個策略都會用同一段歷史資料、同一個初始資金、同一組回放機制進行比較
- 會產生每個策略自己的模擬訂單、交易紀錄、績效統計

### `hybrid`

- 若某策略已有完整 Python 策略類，優先跑策略類
- 其餘沒有實體策略類的模板，仍用 template rule 補上

如果你的目的是「策略競爭要在同樣標準下比較」，建議先用 `template_rules`。

---

## CLI 操作

### 最基本指令

```powershell
python main.py strategy-backtest --symbol BTCUSDT --interval 1h
```

這會：

- 執行 10 個策略模板的回放比較
- 使用 replay 歷史資料
- 不會真實下單
- 產生每個策略的 runtime 目錄

<!-- toc -->

- [UI 操作](#ui-%E6%93%8D%E4%BD%9C)
  * [1. 啟動 API](#1-%E5%95%9F%E5%8B%95-api)
  * [2. 打開 UI](#2-%E6%89%93%E9%96%8B-ui)
  * [3. UI 裡和策略模組有關的欄位](#3-ui-%E8%A3%A1%E5%92%8C%E7%AD%96%E7%95%A5%E6%A8%A1%E7%B5%84%E6%9C%89%E9%97%9C%E7%9A%84%E6%AC%84%E4%BD%8D)
  * [4. 執行策略模組](#4-%E5%9F%B7%E8%A1%8C%E7%AD%96%E7%95%A5%E6%A8%A1%E7%B5%84)
  * [5. UI 裡怎麼看每次執行結果](#5-ui-%E8%A3%A1%E6%80%8E%E9%BA%BC%E7%9C%8B%E6%AF%8F%E6%AC%A1%E5%9F%B7%E8%A1%8C%E7%B5%90%E6%9E%9C)
- [API 操作](#api-%E6%93%8D%E4%BD%9C)
  * [執行策略模組](#%E5%9F%B7%E8%A1%8C%E7%AD%96%E7%95%A5%E6%A8%A1%E7%B5%84)
- [跑完之後去哪裡看結果](#%E8%B7%91%E5%AE%8C%E4%B9%8B%E5%BE%8C%E5%8E%BB%E5%93%AA%E8%A3%A1%E7%9C%8B%E7%B5%90%E6%9E%9C)
- [建議操作順序](#%E5%BB%BA%E8%AD%B0%E6%93%8D%E4%BD%9C%E9%A0%86%E5%BA%8F)
  * [第一次跑策略模組](#%E7%AC%AC%E4%B8%80%E6%AC%A1%E8%B7%91%E7%AD%96%E7%95%A5%E6%A8%A1%E7%B5%84)
  * [要做參數微調時](#%E8%A6%81%E5%81%9A%E5%8F%83%E6%95%B8%E5%BE%AE%E8%AA%BF%E6%99%82)
- [注意事項](#%E6%B3%A8%E6%84%8F%E4%BA%8B%E9%A0%85)
- [相關文件](#%E7%9B%B8%E9%97%9C%E6%96%87%E4%BB%B6)

<!-- tocstop -->

---

## UI 操作

### 1. 啟動 API

```powershell
uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

### 2. 打開 UI

瀏覽器開：

- `http://127.0.0.1:8000/backtest/ui`

### 3. UI 裡和策略模組有關的欄位

在左側控制面板中，策略模組會用到：

- `Symbol`
- `Interval`
- `Start Date`
- `End Date`
- `Balance`
- `Warmup Bars`
- `Strategy Execution Mode`
- `Close Open Positions On End`
- `Strategy Params JSON`

### 4. 執行策略模組

按：

- `Run Strategy Module`

UI 會呼叫：

- `POST /api/v1/backtest/strategy-run`

完成後會把回傳 JSON 顯示在下方結果區，內容包含：

- `execution_mode`
- `ranking`
- 每個策略的 `run_id`
- 每個策略的 `run_dir`
- 每個策略的 `stats`

### 5. UI 裡怎麼看每次執行結果

下方 `Recent Runs` 區塊會列出最近 replay/runtime run。

點其中一筆 run，右側結果視窗會顯示：

- `summary`
- `account`
- `result`
- `runtime_state`
- `orders`

---

## API 操作

如果你不想走 CLI 或 UI，也可以直接打 API。

### 執行策略模組

`POST /api/v1/backtest/strategy-run`

範例 body：

```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "start_date": "2026-01-01",
  "end_date": "2026-04-20",
  "balance": 10000,
  "warmup_bars": 100,
  "execution_mode": "template_rules",
  "close_open_positions_on_end": true,
  "parameter_overrides": null,
  "commission_bps": 4.0,
  "slippage_bps": 1.0,
  "walk_forward": false
}
```

`commission_bps` 與 `slippage_bps` 均以基點（bps）為單位（1 bps = 0.01%）；`walk_forward` 設為 `true` 時需同時提供 `start_date` 與 `end_date`。

---

## 跑完之後去哪裡看結果

每次策略競爭回放都會在這裡生成 runtime：

- `backtest/runtime/<run_id>/`

常見檔案：

- `summary.json`
  - 單次策略 run 摘要
- `status.json`
  - 執行狀態
- `account.json`
  - 模擬帳戶與成交紀錄
- `result.json`
  - 回測結果
- `runtime_state.json`
  - runtime 狀態
- `orders.jsonl`
  - 逐筆訂單記錄

如果你有用 `--output`，另外還會有一份聚合比較檔，例如：

- `output/strategy_backtest_BTCUSDT_1h.json`

這份聚合檔最適合拿來看 10 個策略的最終排名。

---

## 建議操作順序

### 第一次跑策略模組

1. 先確認歷史資料可用：

```powershell
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

2. 再跑策略模組：

```powershell
python main.py strategy-backtest --symbol BTCUSDT --interval 1h
```

3. 最後查看 runtime：

```powershell
python main.py backtest-runs --limit 10
```

### 要做參數微調時

1. 先保留原始參數跑一版
2. 再用 `--params` 只覆蓋你要改的策略
3. 把兩次的 `output/*.json` 與 `backtest/runtime/<run_id>/summary.json` 對比

---

## 注意事項

1. 這裡的策略競爭是 replay 模擬，不是真實下單。
2. `template_rules` 的目標是統一比較標準，不代表所有模板參數都已經完整落地成高階策略功能。
3. `Close Open Positions On End=true` 建議保持開啟，不然最後一段未平倉會讓策略比較失真。
4. 如果要做正式策略比較，請固定：
   - 同一個 `symbol`
   - 同一個 `interval`
   - 同一段 `start_date ~ end_date`
   - 同一個 `balance`
   - 同一個 `warmup_bars`

---

## 相關文件

- [策略模組 README](C:/D/E/BioNeuronai/src/bioneuronai/strategies/README.md)
- [Backtest Replay 使用者手冊](C:/D/E/BioNeuronai/backtest/docs/USER_MANUAL.md)
- [API 模組 README](C:/D/E/BioNeuronai/src/bioneuronai/api/README.md)
