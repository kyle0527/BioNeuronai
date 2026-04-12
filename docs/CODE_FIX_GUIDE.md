# BioNeuronai CODE_FIX_GUIDE

> **版本**: v2.2 | **更新**: 2026-04-12  
> 本文件列出所有已知問題、修正規範及已完成修正紀錄，作為開發者的單一修正參考來源。

---

## 修正原則

1. **優先修改現有檔案**：確認無此檔案時才新建，不允許為同一功能建立重複主程式。
2. **維持現有目錄與架構**：不做不必要的目錄重組，模組層次不改動。
3. **程式可運行原則**：每個修改後的模組應包含 `__main__` 區塊或可直接被 import 無 ImportError。
4. **直接運作驗證原則**：每個命令函數應可獨立驗證（CLI 命令可直接 `python main.py <cmd>` 執行）。
5. **單一數據來源**：Schema 導入遵循 `src/schemas/` 規範，不重複定義資料結構。
6. **改動標記**：每個修正區應在行尾或函數 docstring 中加註 `# CODE_FIX:` 說明改動原因。

---

## 已完成修正項目

### 【一】整合 CryptoNewsAnalyzer 於 market_analyzer.py

**檔案**: `src/bioneuronai/planning/market_analyzer.py`

**問題**: `_analyze_news_sentiment()` 與 `_analyze_social_sentiment()` 方法均硬編碼回傳
`{'score': 0.0}`，導致 `analyze_fundamental_environment()` 的 `news_sentiment` 欄位永遠為
0.0，失去真實新聞情緒分析能力。

**修正內容**:
- `_analyze_news_sentiment(self, symbol: str = "BTCUSDT")` 改為呼叫
  `CryptoNewsAnalyzer().analyze_news(symbol)` 取得真實情緒分數。
- 加入 `try/except` 以確保 API 失敗時 graceful fallback 至 `0.0`（中性值）。
- 方法標記 `# CODE_FIX: 移除硬編碼 0.0，接入真實分析器`。

**注意**: `calculate_comprehensive_sentiment()` 方法（第 874 行起）已正確整合
`CryptoNewsAnalyzer`，本修正統一兩條路徑，消除不一致。

---

### 【二】CLI 新增 `phase` 命令（市場階段路由）

**檔案**: `src/bioneuronai/cli/main.py`

**問題**: `TradingPhaseRouter` 已完整實作（`src/bioneuronai/strategies/phase_router.py`），
但 CLI 缺少對應命令，使用者無法直接從命令列查詢當前市場交易階段。

**修正內容**:
- 新增 `cmd_phase(args)` 函數，呼叫 `TradingPhaseRouter.route_trading_decision()` 顯示：
  - 當前時間
  - 交易階段（phase）
  - 動作階段（action_phase）
  - 使用策略（strategy_used）
  - 倉位倍數 / 風險倍數 / 建議動作
- 在 `_build_parser()` 中新增 `phase` subparser，支援 `--timeframe` 參數（預設 `1h`）。
- 更新模組 docstring 命令總覽與 argparse epilog。
- 命令標記 `# CODE_FIX: 新增市場階段路由命令（整合 TradingPhaseRouter）`。

**使用範例**:
```bash
python main.py phase
python main.py phase --timeframe 4h
```

**說明**: 策略競技場命令 `evolve` 已於 v2.2 加入 CLI（對應 `StrategyArena`），本次
僅補充 `phase` 命令，不重複新建 `evolve`。

---

## 待完成項目（Backlog）

| 優先級 | 項目 | 說明 |
|--------|------|------|
| 🔴 最高 | AI 模型首次完整訓練 | 語言預熱 → 訊號對齊 → 多任務精調 |
| 🔴 最高 | 歷史數據下載 | BTCUSDT 2年 1h K線 |
| 🟡 高 | 語言訓練資料擴充 | 31 → 500+ QA 對 |
| 🟡 高 | collect-signal-data | 執行回測產生真實訊號標籤 |
| 🟠 中 | SOP 回測驗證 | 啟用 `_perform_plan_backtest()` |
| 🟠 中 | Walk-Forward 測試框架 | 滾動時間窗 OOS 測試 |
| 🔵 低 | DRL 策略（PPO） | 長期計劃 |
| 🔵 低 | 實盤小資金測試 | 長期計劃 |

---

## GitHub Spark UI 整合說明

若使用 GitHub Spark 產生新版 Dashboard UI，建議整合流程如下：

### 方式 A：分開部署（推薦）
Spark 產生的前端（React/Next.js）獨立部署，透過環境變數指向現有 FastAPI API：
```
VITE_API_BASE=http://localhost:8000/api/v1
```
FastAPI 已啟用 `CORS *`，直接跨域呼叫即可。

### 方式 B：整合 Build 結果至 FastAPI 靜態服務
1. 將 Spark app `build/` 靜態檔案拷貝至 `frontend/build/`
2. 在 `src/bioneuronai/api/app.py` 新增 StaticFiles mount：
```python
from fastapi.staticfiles import StaticFiles
app.mount("/dashboard", StaticFiles(directory="frontend/build", html=True), name="dashboard")
```
3. 瀏覽 `http://localhost:8000/dashboard` 即可存取新 UI。

---

## 現有 AI 與 UI 能力確認

| 能力 | 狀態 | 說明 |
|------|------|------|
| TinyLLM / InferenceEngine | ✅ 具備 | 111.6M 參數架構就緒，待首次訓練 |
| ChatEngine | ✅ 具備 | CLI `chat` 命令 + API `/api/v1/chat` |
| 回測/Replay UI | ✅ 具備 | `backtest/ui/index.html` + FastAPI 端點 |
| FastAPI REST API | ✅ 完整 | `/api/v1/status`, `/api/v1/backtest/*`, `/api/v1/chat` 等 11+ 端點 |
| CryptoNewsAnalyzer | ✅ 已整合 | 181 關鍵字，47 文章源；已接入 market_analyzer |
| StrategyArena CLI | ✅ 已整合 | `python main.py evolve` |
| TradingPhaseRouter CLI | ✅ 已整合 | `python main.py phase`（本次修正新增） |
