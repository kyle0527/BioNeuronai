# BioNeuronai API 與整合架構基準文件
> 目的：建立 BioNeuronai 後續 API、外部資料源、使用者憑證流、UI 對接與內部模組整合的統一基準。
>
> 本文件以目前專案實作為基礎，結合 `CODE_FIX_GUIDE.md` 的原則，定義「什麼應該保留」、「什麼應該移除或收斂」、「後續如何改而不破壞現有架構」。


## 📑 目錄

1. 1. 核心結論
2. 2. 適用範圍
3. 3. 現況摘要
4. 4. 目標架構
5. 5. 外部 API 分層策略
6. 6. 為什麼不保留內部 API
7. 7. 對外入口的最小設計
8. 8. 目前 REST API 端點的重整建議
9. 9. Schema 改進方向
10. 10. Binance 憑證流的標準做法
11. 11. 系統級 provider 的標準做法
12. 12. 配置管理原則
13. 13. CLI、REST API、未來 UI 的共用方式
14. 14. 建議的改造順序
15. 15. 各檔案的後續角色建議
16. 16. 不建議做的事
17. 17. 驗證原則
18. 18. 外部參考做法
19. 19. 最終基準
20. 20. 後續執行建議

---

## 1. 核心結論

BioNeuronai 後續應採用以下整合原則：

1. **外部 API 集中接入，內部模組直接連結**
   - 對 Binance、新聞、外部市場資料等第三方服務，統一由外部連接層接入。
   - 進入系統內部後，`analysis/`、`trading/`、`core/`、`data/` 等模組一律直接 import / function call / object injection，不建立任何內部 HTTP API。

2. **`src/schemas/` 為單一事實來源**
   - 跨模組共用的 request / response / credentials / provider config / job state schema，應統一放在 `src/schemas/`。
   - `src/bioneuronai/api/` 不再自行成為資料模型的主定義位置。

3. **`api/` 僅作為對外入口殼**
   - `src/bioneuronai/api/` 的責任是接收請求、驗證輸入、建立外部 connector、呼叫內部模組、回傳結果。
   - 不將 `api/` 作為系統核心邏輯層，也不讓內部模組彼此透過 HTTP API 溝通。

4. **外部來源分為兩類**
   - 使用者級外部來源：目前核心只有 Binance。
   - 系統級外部來源：新聞、外部市場、鏈上與宏觀資料。

5. **先縮減複雜度，再擴展 UI**
   - 短期目標不是增加更多 endpoint，而是收斂責任邊界、打通憑證流、去除重複 schema、降低維護成本。
   - 這種做法不會阻礙後續 UI 化，反而讓 UI 可以穩定接到單一入口。

---

## 2. 適用範圍

本文件適用於以下模組與主題：

- `src/bioneuronai/api/`
- `src/bioneuronai/data/`
- `src/bioneuronai/core/`
- `src/bioneuronai/trading/`
- `src/bioneuronai/analysis/`
- `src/schemas/`
- `config/` 中與外部憑證、provider 設定相關項目
- 後續 UI / CLI / 自動化入口整合

---

## 3. 現況摘要

### 3.1 目前專案中的對外入口

目前已有兩種入口：

- CLI：`main.py`、`src/bioneuronai/cli/main.py`
- REST API：`src/bioneuronai/api/app.py`

其中 REST API 目前提供的主要端點包括：

- `GET /api/v1/status`
- `POST /api/v1/plan`
- `POST /api/v1/news`
- `POST /api/v1/pretrade`
- `POST /api/v1/backtest`
- `POST /api/v1/simulate`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/trade/start`
- `POST /api/v1/trade/stop`

### 3.2 目前專案中的外部資料源 / 外部操作 API

根據目前程式碼，外部來源可分為：

#### A. 使用者級 API

- Binance Futures REST / WebSocket

用途：
- 市價、K 線、深度、Open Interest、Funding Rate
- 帳戶資訊
- 下單
- 持倉與風險相關檢查

主要實作位置：
- `src/bioneuronai/data/binance_futures.py`
- `src/bioneuronai/core/trading_engine.py`
- `src/bioneuronai/trading/pretrade_automation.py`
- `src/bioneuronai/analysis/daily_report/__init__.py`

#### B. 系統級 API

- CryptoPanic
- Alternative.me Fear & Greed
- CoinGecko
- DefiLlama
- Yahoo Finance 類市場資料來源

用途：
- 新聞蒐集與情緒分析
- 全球市場 / 宏觀環境分析
- 恐慌貪婪、DeFi TVL、穩定幣供應、整體市值等輔助資訊

主要實作位置：
- `src/bioneuronai/analysis/news/analyzer.py`
- `src/bioneuronai/data/web_data_fetcher.py`
- `src/bioneuronai/analysis/daily_report/market_data.py`

### 3.3 目前已觀察到的架構不一致

#### 問題 1：`src/schemas/` 與 `api/models.py` 雙軌

目前 `src/schemas/api.py` 已有：

- `ApiCredentials`
- `ApiResponse`
- `BinanceApiError`
- `ApiStatusInfo`
- `ExchangeInfo`

但 `src/bioneuronai/api/models.py` 又自行定義：

- `ApiResponse`
- `StatusResponse`
- `TradeStartRequest`
- `PreTradeRequest`
- `BacktestRequest`
- `SimulateRequest`

這違反 `CODE_FIX_GUIDE.md` 中「`src/schemas/` 為單一事實來源」的原則。

#### 問題 2：Binance 憑證流尚未打通

目前不同模組使用不同方式取得 Binance 憑證：

- `src/bioneuronai/core/trading_engine.py`
  - 可透過建構子傳入 `api_key` / `api_secret`
- `src/bioneuronai/trading/pretrade_automation.py`
  - 多處直接讀 `config.trading_config`
- `src/bioneuronai/analysis/daily_report/__init__.py`
  - 直接讀環境變數
- `src/bioneuronai/api/app.py`
  - `trade/start` 目前不接受使用者憑證

這表示目前尚未形成一致的「使用者級憑證進入系統」路徑。

#### 問題 3：REST API 目前偏向包 CLI，而非穩定 facade

目前 `src/bioneuronai/api/app.py` 的設計接近：

- 路由直接初始化大型模組
- 路由直接掌握背景任務狀態
- 全域狀態 `_jobs`、`_trade_task`、`_trade_engine`

這對單機測試可用，但對後續維護、收斂與 UI 對接來說，責任仍過於分散。

---

## 4. 目標架構

### 4.1 總體原則

BioNeuronai 應維持以下資料流：

```text
外部世界
  ├─ 使用者輸入（CLI / UI）
  ├─ Binance
  └─ 新聞 / 市場 / 宏觀 provider
          ↓
入口殼（CLI / REST API）
          ↓
內部高層流程編排
          ↓
analysis / trading / core / data
          ↓
結果回傳 / 狀態輸出
```

重點如下：

- **外部通訊集中**
- **內部直連**
- **schema 單一**
- **入口薄化**

### 4.2 邊界定義

#### `src/schemas/`

責任：
- 定義跨模組共用的資料模型
- 定義 request / response / credentials / provider config / job state

原則：
- 所有跨模組 schema 必須由此統一導出
- 不在其他模組再定義本質相同的類別

#### `src/bioneuronai/data/`

責任：
- 封裝所有第三方外部 API
- 負責外部連線、認證、request 組裝、response 轉換

原則：
- 只負責外部互動，不負責交易決策
- 對內提供乾淨、可注入、可替換的 connector 介面

#### `src/bioneuronai/analysis/`

責任：
- 新聞、情緒、市場體制、特徵工程、日報分析

原則：
- 依賴 `data/` 提供的資料
- 不自行在內部再建立 HTTP 介面

#### `src/bioneuronai/trading/` / `src/bioneuronai/core/`

責任：
- pretrade、風控、計劃生成、交易引擎、執行編排

原則：
- 透過參數注入 connector / credentials / config
- 不直接綁死在某個 config 檔或環境變數

#### `src/bioneuronai/api/`

責任：
- 對 UI / 外部客戶端提供統一入口
- 驗證請求
- 呼叫內部服務
- 回傳結果

不負責：
- 定義主 schema
- 實作主要商業邏輯
- 成為內部模組間的溝通協議層

---

## 5. 外部 API 分層策略

### 5.1 使用者級 API：Binance

Binance 屬於使用者級外部來源，因為它代表：

- 某個人的交易授權
- 某個人的帳戶資料
- 某個人的持倉與下單權限

因此 Binance 相關設定應視為：

- 使用者級憑證
- 非系統共用設定

#### 使用者級資料應包含

- `api_key`
- `secret_key`
- `testnet`
- `environment`
- 選配：風險限制、只讀模式、session scope 標記

#### 使用者級處理原則

- 不硬編碼在 repo
- 不散落在各模組各自讀取
- 由入口層收進來後，透過 schema 統一傳入內部
- 由 connector 或高層流程按需注入

### 5.2 系統級 API：新聞 / 市場 / 宏觀 / 鏈上

這些 provider 不應與單一使用者綁定：

- CryptoPanic
- CoinGecko
- Alternative.me
- DefiLlama
- Yahoo Finance 類資料

這些資料源應由系統統一管理，因為：

- 所有使用者看到的市場資訊應一致
- 這些 provider 多半不是每位使用者各自擁有授權
- 集中管理可以降低設定數量與維護成本

#### 系統級 provider 原則

- 統一放在 `data/`
- 使用系統級 config
- 對內部暴露一致資料格式
- 集中快取與重試策略

---

## 6. 為什麼不保留內部 API

這是本文件最重要的決策之一。

### 6.1 原因

內部 API 不保留，理由如下：

1. **沒有必要**
   - 專案目前不是微服務部署架構。
   - `analysis/`、`trading/`、`core/`、`data/` 本來就在同一個 repo、同一個 runtime。

2. **會增加維護成本**
   - 要維護路由、序列化、錯誤處理、版本相容、測試矩陣。
   - 這些對目前專案沒有額外收益。

3. **會增加開發成本**
   - 內部模組呼叫變成網路呼叫，會放大耦合面、除錯難度與效能成本。

4. **對 UI 化沒有實質幫助**
   - UI 只需要一個穩定入口，不需要每個內部模組各自暴露 API。

### 6.2 例外情況

只有在以下情況，才考慮增加額外對外協議：

- 需要即時推播交易狀態
- 需要前端持續接收監控更新
- 需要長任務狀態推送

即使如此，也應理解為：

- 對外通訊協議擴充
- 不是內部模組 API 化

---

## 7. 對外入口的最小設計

### 7.1 入口數量原則

以目前專案定位，對外入口應盡量少：

#### 最小版本

- CLI：主要操作入口
- REST API：供 UI 或外部客戶端呼叫

#### 可選版本

- 再加一個狀態輸出通道
  - WebSocket
  - SSE
  - 或簡單 polling

不建議一開始就做：

- 多層 API gateway
- 內部服務間 HTTP 呼叫
- GraphQL
- 多個彼此重疊的 API 殼

### 7.2 REST API 的正確定位

REST API 的用途應是：

- 給 UI
- 給本地前端或桌面應用
- 給外部客戶端

不是用途：

- 讓內部模組互相呼叫
- 取代 Python 函式調用
- 成為主邏輯所在

---

## 8. 目前 REST API 端點的重整建議

### 8.1 目前端點不代表都要保留

現有端點可以視為「已有對外功能包裝」，但不應被理解為「每一項都必須成為長期 API 契約」。

### 8.2 建議保留的高價值端點

#### `GET /api/v1/status`

用途：
- 健康檢查
- UI 啟動時探測系統可用性

建議：
- 保留

#### `POST /api/v1/binance/validate`

用途：
- 驗證 API key / secret
- 檢查 testnet / mainnet 配置
- 檢查讀取權限與 Futures 權限

建議：
- 新增
- 優先級最高

#### `POST /api/v1/pretrade`

用途：
- UI 端取得單筆交易前評估

建議：
- 保留
- 改為支援注入 Binance 憑證或使用既有 session/config

#### `POST /api/v1/trade/start`

用途：
- 啟動監控 / 自動交易

建議：
- 保留
- 改為可接收 Binance 憑證或 credential reference

#### `POST /api/v1/trade/stop`

用途：
- 停止交易監控

建議：
- 保留

#### `POST /api/v1/news`

用途：
- UI 取得新聞分析結果

建議：
- 可保留
- 因其屬於系統級資料，不依賴使用者帳戶

### 8.3 可延後處理的端點

#### `POST /api/v1/plan`

理由：
- 不是最先卡住交易功能的缺口
- 可作為後續 UI 的高階功能

#### `POST /api/v1/backtest`
#### `POST /api/v1/simulate`
#### `GET /api/v1/jobs/{job_id}`

理由：
- 有價值，但不屬於你目前「單人實用化 + 低維護」的最低必要集合

---

## 9. Schema 改進方向

### 9.1 原則

所有跨模組 API / connector / provider 相關 schema 統一由 `src/schemas/` 管理。

### 9.2 需要收斂的項目

應逐步將以下類別收斂回 `src/schemas/`：

- `TradeStartRequest`
- `PreTradeRequest`
- `BacktestRequest`
- `SimulateRequest`
- `StatusResponse`
- 若需要，統一版 `ApiResponse`

### 9.3 不建議的做法

- 在 `src/bioneuronai/api/models.py` 持續擴充另一套共用 schema
- 在 `api/`、`trading/`、`analysis/` 各自定義相同概念

### 9.4 允許的例外

若某資料模型只在單一模組內部短距離使用，且不跨模組傳遞，可保留在模組內。

但只要滿足以下任一條件，就應放入 `src/schemas/`：

- 會跨模組使用
- 會作為對外 request / response
- 會成為 UI / CLI / API 共用輸入格式
- 會被多個入口共同使用

---

## 10. Binance 憑證流的標準做法

### 10.1 基本原則

Binance API key / secret 不是一般登入帳密，而是交易授權憑證。

因此本專案不一定要建立傳統「帳號 / 密碼登入系統」，但必須建立「Binance 憑證輸入與驗證流程」。

### 10.2 建議模式

依實際使用情境，建議以下三種模式：

#### 模式 A：本地單人模式

適用：
- 個人使用
- CLI 為主
- 單機部署

做法：
- 使用環境變數或本地 secrets 檔
- 啟動時由系統載入

優點：
- 最簡單
- 維護成本最低

缺點：
- 不適合多人共用

#### 模式 B：單人 UI 模式

適用：
- 有 UI
- 仍是單一操作者

做法：
- 第一次由 UI 輸入 key / secret
- 僅存在記憶體 session 或本地加密存放

優點：
- 使用體驗較好
- 不需每次重填

缺點：
- 需補 session / local secret 管理

#### 模式 C：多人服務模式

適用：
- SaaS / 多帳戶並行

做法：
- 每位使用者管理自己的憑證
- 需要 session / auth scope / 安全儲存

優點：
- 可擴充

缺點：
- 額外成本很高

### 10.3 本專案建議採用模式

以目前需求與維護成本考量，建議先採：

- **模式 A 或模式 B**

不建議一開始就為不存在的多人場景設計複雜機制。

---

## 11. 系統級 provider 的標準做法

### 11.1 集中設定

新聞與市場資料 provider 應由系統統一管理，不由每位使用者自行輸入。

建議統一管理以下資訊：

- provider base url
- token / api key（若有）
- timeout
- retry
- cache TTL

### 11.2 集中封裝

所有 provider 呼叫都應由 `data/` 封裝，而不是在 `analysis/` 或 `trading/` 中散落直接 `requests.get(...)`。

### 11.3 穩定性策略

系統級 provider 建議統一具備：

- timeout
- retry
- 結構化錯誤
- 快取
- 來源標記
- fallback / graceful handling

注意：
- 這裡的 graceful handling 只適用於「輔助資料源」
- 若是交易授權或關鍵帳戶資料，應 fail-fast，而不是靜默降級

---

## 12. 配置管理原則

### 12.1 高優先級原則

依 `CODE_FIX_GUIDE.md` 與業界實務，會隨部署環境改變的敏感設定不應硬編碼在 repo。

包括：

- Binance API Key
- Binance API Secret
- CryptoPanic token
- CoinGecko key
- 其他外部 token

### 12.2 優先順序

建議優先順序：

1. 環境變數
2. 本地 secrets 檔（不進版控）
3. 受控的 UI 輸入存放

最不建議：

- 寫死在 `config/trading_config.py`

### 12.3 專案現況的具體問題

目前 `config/trading_config.py` 內存在寫死的 Binance demo key / secret。

這在後續應視為需移除的技術債，而不是長期方案。

---

## 13. CLI、REST API、未來 UI 的共用方式

### 13.1 基本原則

CLI、REST API、未來 UI 都不應各自重寫一套業務流程。

### 13.2 正確做法

應形成：

```text
CLI / API / UI
   ↓
統一高層流程呼叫
   ↓
trading / core / analysis / data
```

### 13.3 實務意義

這樣可以避免：

- CLI 一套邏輯
- API 一套邏輯
- UI 再複製一套邏輯

造成：

- 修一邊壞兩邊
- 行為不一致
- 維護成本飆高

---

## 14. 建議的改造順序

以下順序以「不破壞現有功能」、「維持現有架構」、「優先改現有檔案」為原則。

### 第 1 階段：建立單一 schema 基礎

目標：
- 確立 `src/schemas/` 為唯一共用 schema 來源

工作：
- 盤點 `src/bioneuronai/api/models.py`
- 將跨模組 request / response schema 移入或對齊 `src/schemas/`
- 保留 `api/models.py` 只作薄包裝或逐步淘汰

### 第 2 階段：打通 Binance 憑證流

目標：
- 讓使用者級憑證有一致進入路徑

工作：
- 新增或調整 credentials schema
- 增加 Binance validate 流程
- 讓 `trade/start` 可接憑證
- 讓 `pretrade` 可接憑證或 injected connector

### 第 3 階段：移除 config 綁死依賴

目標：
- 減少模組對 `config.trading_config` 的直接綁定

工作：
- 重構 `pretrade_automation.py`
- 重構 `daily_report/__init__.py`
- 讓憑證與 provider config 透過注入取得

### 第 4 階段：收斂 REST API 角色

目標：
- 讓 `api/app.py` 只作入口殼

工作：
- 保留高價值端點
- 延後次要端點
- 將流程編排移向內部高層函式

### 第 5 階段：準備 UI 對接

目標：
- UI 不需要知道內部細節

工作：
- 讓 UI 只依賴少數穩定 endpoint 或 CLI wrapper
- 若需要即時狀態，再考慮 WebSocket / SSE

---

## 15. 各檔案的後續角色建議

### `src/bioneuronai/api/app.py`

建議角色：
- 對外入口殼

後續方向：
- 保留
- 減少直接堆疊邏輯
- 改為使用統一 schema 與高層流程

### `src/bioneuronai/api/models.py`

建議角色：
- 過渡層

後續方向：
- 不再成為主 schema 定義點
- 逐步向 `src/schemas/` 收斂

### `src/schemas/api.py`

建議角色：
- API / credentials / response 類共用模型主來源

後續方向：
- 擴充必要 request / response schema
- 作為 CLI / API / UI 共用約定

### `src/bioneuronai/data/binance_futures.py`

建議角色：
- Binance 單一主要 connector

後續方向：
- 保持作為唯一主要 Binance API 封裝
- 不讓其他模組再自行重造 Binance 呼叫流程

### `src/bioneuronai/trading/pretrade_automation.py`

建議角色：
- pretrade 核心流程

後續方向：
- 改為接受 injected connector / credentials
- 去除多處直接讀 `config.trading_config`

### `src/bioneuronai/analysis/daily_report/__init__.py`

建議角色：
- 系統級分析流程

後續方向：
- 允許接收 connector 或 config 物件
- 避免硬綁環境變數為唯一來源

### `config/trading_config.py`

建議角色：
- 靜態交易參數配置

不建議角色：
- 敏感憑證長期存放位置

後續方向：
- 移除硬編碼敏感金鑰

---

## 16. 不建議做的事

以下做法不符合本文件基準：

1. 把每個內部模組都包成 REST API
2. 在 `api/` 中持續擴充重複 schema
3. 讓 `pretrade`、`trade`、`daily_report` 各自用不同方法取 Binance 憑證
4. 將敏感金鑰寫死在版本控制中的 config 檔
5. 為尚未存在的多人場景先引入重型 session / auth 架構
6. 為了 UI 而重寫一套新邏輯，導致 CLI / API / UI 各走各的

---

## 17. 驗證原則

所有後續改造應符合以下驗證要求：

1. **遵循 `CODE_FIX_GUIDE.md`**
   - 單一事實來源
   - 優先修改現有檔案
   - 直接運作驗證
   - 路徑與配置清晰

2. **改完要做實際運行驗證**
   - CLI
   - REST API
   - Binance connector 驗證
   - 無憑證 / 有憑證兩種情境

3. **不能只做文件級設計，不驗證主鏈**
   - `pretrade`
   - `trade/start`
   - `news`
   - `plan` 若有被影響也要檢查

---

## 18. 外部參考做法

本節列出可參考的外部做法，作為方向參考，而非要求逐字照搬。

### 18.1 FastAPI 官方：較大應用程式的做法

方向重點：
- route / app 層保持薄
- 將邏輯拆到其他模組
- 入口層不成為核心邏輯承載點

可參考：
- https://fastapi.tiangolo.com/tutorial/bigger-applications/

### 18.2 Twelve-Factor：配置應與程式碼分離

方向重點：
- 會隨部署改變的設定應從環境提供
- 不應寫死在原始碼中

可參考：
- https://www.12factor.net/config

### 18.3 Pydantic Settings：型別化設定管理

方向重點：
- 使用 schema 管理環境變數與 secrets
- 適合本專案「單一 schema + 集中設定」方向

可參考：
- https://docs.pydantic.dev/latest/concepts/pydantic_settings/

### 18.4 Binance Futures 權限檢查

方向重點：
- 實際交易前，應先驗證 API key 權限與期貨權限
- 先做 validate，再做 trade

可參考：
- https://developers.binance.com/docs/derivatives/usds-margined-futures/
- https://dev.binance.vision/t/what-are-the-prerequisites-for-futures-trading-with-the-binance-api/8497

### 18.5 FastAPI WebSocket

方向重點：
- 若未來 UI 需要即時監控，再加狀態輸出通道
- 不必作為當前最低必要項

可參考：
- https://fastapi.tiangolo.com/advanced/websockets/

---

## 19. 最終基準

後續所有相關改動，以以下五條作為最高優先級判準：

1. **外部 API 集中，內部模組直連**
2. **`src/schemas/` 是共用 schema 唯一來源**
3. **`api/` 是薄入口，不是核心邏輯層**
4. **Binance 是使用者級憑證來源，其他資料源是系統級 provider**
5. **優先降低維護成本與責任分裂，不為不存在的複雜場景過度設計**

---

## 20. 後續執行建議

建議以本文件為基準，後續工作分為三批：

### 批次 A：基礎整頓

- 收斂 schema
- 盤點 `api/models.py`
- 整理 Binance credentials schema

### 批次 B：主鏈修正

- `pretrade_automation.py` 注入化
- `trade/start` 憑證流打通
- 新增 validate 流程

### 批次 C：入口收斂

- `api/app.py` 薄化
- 延後低優先級 endpoint
- 為 UI 保留最小穩定入口

---

本文件建立日期：2026-03-28  
適用版本：以目前工作樹為準  
維護原則：若後續架構方向變更，應更新本文件而非另立互相衝突的新規格
