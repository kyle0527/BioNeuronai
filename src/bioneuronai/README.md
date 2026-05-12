# BioNeuronai 核心交易系統

> 路徑：`src/bioneuronai/`
> 版本：v2.2
> 更新日期：2026-05-13

`bioneuronai` 是交易系統主體，負責把資料接入、分析、策略選擇、AI 融合、風險管理、交易規劃、API 與 CLI 串成可操作的主流程。這一層只維護系統概念、分層與主線；具體 API、方法與限制請看各子模組 README。

---

## 目錄

1. [子模組導覽](#子模組導覽)
2. [正式主線](#正式主線)
3. [分層概念](#分層概念)
4. [文件層級](#文件層級)

---

## 子模組導覽

| 模組 | 層級定位 | 詳細文件 |
|------|----------|----------|
| `data/` | Layer 0：交易所、paper-live connector、DB、匯率、新聞與外部資料 fetcher | [data README](data/README.md) |
| `core/` | Layer 1：TradingEngine、InferenceEngine、自我改進 | [core README](core/README.md) |
| `risk_management/` | Layer 1：風險參數與倉位計算 | [risk README](risk_management/README.md) |
| `strategies/` | Layer 2：基礎策略、selector、AI fusion、競技場/路由/優化 | [strategies README](strategies/README.md) |
| `planning/` | Layer 3：plan controller、market analyzer、pair selector、pretrade | [planning README](planning/README.md) |
| `trading/` | Layer 3：虛擬帳戶與交易事實層 | [trading README](trading/README.md) |
| `analysis/` | Layer 4：新聞、關鍵字、daily report、特徵工程、市場 regime | [analysis README](analysis/README.md) |
| `api/` | 對外入口：FastAPI app 與 API models | [api README](api/README.md) |
| `cli/` | 對外入口：CLI commands | [cli README](cli/README.md) |
| `models/` | legacy checkpoint 相容模型 | [models README](models/README.md) |

---

## 正式主線

目前支援三種策略主線模式（由 `strategy_type` 參數指定）：

```text
[fusion 模式 — 預設]
TradingEngine
  -> StrategySelector (啟動時熱載入 Golden Profile 歷史優化權重)
  -> AIStrategyFusion
  -> 基礎策略 signal
  -> risk / cost / execution

[phase_router 模式]
TradingEngine
  -> TradingPhaseRouter
  -> 主線階段分別路由
  -> risk / cost / execution

[rl_fusion 模式]
TradingEngine
  -> StrategySelector (RL Meta-Agent 後處理)
  -> PPO RLMetaAgent
  -> risk / cost / execution
```

說明：

1. `fusion` 是預設主線，不需額外環境依賴。
2. `phase_router` 與 `rl_fusion` 為已完整實作的次要模式，系統已完備启動機制，但現役部署對象為 fusion。
3. `StrategyArena`、`StrategyPortfolioOptimizer` 已改接 replay，但不是正式交易執行主線。
4. `trading/` 不承載 SOP、pretrade 或高階規劃；這些已歸入 `planning/`。

---

## 分層概念

```text
Layer 4  analysis        新聞、關鍵字、特徵、市場 regime、daily report
Layer 3  planning        計劃控制、pretrade、交易對選擇
Layer 3  trading         交易事實、虛擬帳戶、paper / replay execution 狀態
Layer 2  strategies      策略選擇、基礎策略、AI fusion、研究型競技/路由
Layer 1  core/risk       交易引擎、推理引擎、風險與倉位
Layer 0  data/schemas    外部資料、DB、交易所 API、共用 schema
```

---

## 文件層級

1. 本文件維護系統概念與主線。
2. 子模組 README 維護該模組責任、公開 API、重要限制。
3. 更深層 README 維護檔案級細節、方法、資料路徑與實作邊界。
4. 不在上層文件保留固定行數、覆蓋率或不可由目前 smoke test 證明的品質宣稱。

### 文件鏈

1. `src/bioneuronai/README.md`
   -> [analysis README](analysis/README.md)
   -> [api README](api/README.md)
   -> [cli README](cli/README.md)
   -> [core README](core/README.md)
   -> [data README](data/README.md)
   -> [models README](models/README.md)
   -> [planning README](planning/README.md)
   -> [risk README](risk_management/README.md)
   -> [strategies README](strategies/README.md)
   -> [trading README](trading/README.md)
2. `analysis/README.md`
   -> [daily_report README](analysis/daily_report/README.md)
   -> [keywords README](analysis/keywords/README.md)
   -> [news README](analysis/news/README.md)
3. `strategies/README.md`
   -> [selector README](strategies/selector/README.md)

---

> 上層目錄：[src README](../README.md)
