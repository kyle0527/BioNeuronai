# Analysis 模組驗證報告
> 日期: 2026-03-24
> 範圍基準: `tools/PROJECT_REPORT_20260322_221527.txt` 第 375-401 行 `src/bioneuronai/analysis/`
> 驗證方式: 實際執行 `main.py news`、`python -m bioneuronai.analysis --kw`、`python -m bioneuronai.analysis`


## 📑 目錄

1. 1. 結論摘要
2. 2. 本次實際執行的驗證命令
3. 3. 已驗證範圍
4. 4. 已確認修復的問題
5. 5. 仍存在的問題
6. 6. 尚未驗證到的能力
7. 7. 本次驗證邊界
8. 8. 後續建議

---

## 1. 結論摘要

本次已對 `analysis/` 目錄下的 **22 個 Python 腳本**完成實際執行覆蓋驗證。

驗證結果：

- `BUG_REPORT_NEWS_MODULE.md` 提出的 `dynamic_bias` 問題：**已修復**
- `analysis/` 主體功能：**可執行**
- 仍存在的執行期問題：**Windows 預設 `cp950` 主控台下，`main.py news` 會因 emoji 輸出失敗**

不在本次完整驗證範圍內的能力：

- `api/`
- `core/`
- `risk_management/`
- `strategies/`
- `trading/`
- `nlp/`
- `rag/`
- `analysis/README.md` 這類非腳本文件

---

## 2. 本次實際執行的驗證命令

### 2.1 關鍵字系統驗證

```powershell
python -m bioneuronai.analysis --kw
```

用途：

- 驗證 `KeywordManager`
- 驗證 `KeywordLoader`
- 驗證 `config/keywords/*.json` 載入
- 驗證關鍵字統計、分類統計與權重輸出

### 2.2 新聞命令驗證

```powershell
python main.py news --symbol BTCUSDT
```

用途：

- 驗證 CLI `cmd_news`
- 驗證 `CryptoNewsAnalyzer`
- 驗證新聞抓取
- 驗證關鍵字系統與新聞分析整合

結果：

- 預設 Windows `cp950` 輸出環境下失敗
- UTF-8 環境下可成功執行並產出 `NewsAnalysisResult`

### 2.3 analysis 模組完整入口驗證

```powershell
python -m bioneuronai.analysis
```

用途：

- 驗證 `analysis/__main__.py`
- 驗證 `daily_report`
- 驗證 `feature_engineering`
- 驗證 `market_regime`
- 驗證 `news/evaluator`
- 驗證 `news/prediction_loop`
- 驗證 `keywords/learner`
- 驗證 `static_utils`

結果：

- 成功
- 執行完成後輸出「全部 22 個 analysis 模組已驗證完畢（匯入 + 實際執行）」

---

## 3. 已驗證範圍

以下檔案屬於 `analysis/` 範圍內，且本次已被實際執行路徑覆蓋。

### 3.1 analysis 根層

| 檔案 | 狀態 | 驗證方式 |
|------|------|----------|
| `src/bioneuronai/analysis/__init__.py` | 已驗證 | 匯入與模組入口執行 |
| `src/bioneuronai/analysis/__main__.py` | 已驗證 | `python -m bioneuronai.analysis` |
| `src/bioneuronai/analysis/feature_engineering.py` | 已驗證 | 完整報告技術分析流程 |
| `src/bioneuronai/analysis/market_regime.py` | 已驗證 | 完整報告技術分析流程 |

### 3.2 daily_report

| 檔案 | 狀態 | 驗證方式 |
|------|------|----------|
| `src/bioneuronai/analysis/daily_report/__init__.py` | 已驗證 | 完整報告流程 |
| `src/bioneuronai/analysis/daily_report/market_data.py` | 已驗證 | 全球市場資料流程 |
| `src/bioneuronai/analysis/daily_report/models.py` | 已驗證 | 報告資料模型建立 |
| `src/bioneuronai/analysis/daily_report/news_sentiment.py` | 已驗證 | 新聞情緒整合流程 |
| `src/bioneuronai/analysis/daily_report/report_generator.py` | 已驗證 | SOP 報告輸出 |
| `src/bioneuronai/analysis/daily_report/risk_manager.py` | 已驗證 | 每日報告風控計算 |
| `src/bioneuronai/analysis/daily_report/strategy_planner.py` | 已驗證 | 策略規劃流程 |

### 3.3 keywords

| 檔案 | 狀態 | 驗證方式 |
|------|------|----------|
| `src/bioneuronai/analysis/keywords/__init__.py` | 已驗證 | 匯入與 manager/static_utils 路徑 |
| `src/bioneuronai/analysis/keywords/learner.py` | 已驗證 | `KeywordLearner` 初始化 |
| `src/bioneuronai/analysis/keywords/loader.py` | 已驗證 | 分類 JSON 載入 |
| `src/bioneuronai/analysis/keywords/manager.py` | 已驗證 | `KeywordManager()` 與報告輸出 |
| `src/bioneuronai/analysis/keywords/models.py` | 已驗證 | `Keyword` 建構與 `dynamic_bias` 欄位 |
| `src/bioneuronai/analysis/keywords/static_utils.py` | 已驗證 | `MarketKeywords.get_importance_score/get_sentiment_bias` |

### 3.4 news

| 檔案 | 狀態 | 驗證方式 |
|------|------|----------|
| `src/bioneuronai/analysis/news/__init__.py` | 已驗證 | 匯入與主命令路徑 |
| `src/bioneuronai/analysis/news/analyzer.py` | 已驗證 | `main.py news` 與完整報告 |
| `src/bioneuronai/analysis/news/evaluator.py` | 已驗證 | `RuleBasedEvaluator.evaluate_news_batch()` |
| `src/bioneuronai/analysis/news/models.py` | 已驗證 | `NewsAnalysisResult` 實際建立 |
| `src/bioneuronai/analysis/news/prediction_loop.py` | 已驗證 | `NewsPredictionLoop().get_statistics()` |

---

## 4. 已確認修復的問題

### 4.1 `dynamic_bias` 問題

來源：

- `docs/BUG_REPORT_NEWS_MODULE.md`

原始問題：

```text
Keyword.__init__() got an unexpected keyword argument 'dynamic_bias'
```

本次確認結果：

- `Keyword` dataclass 已加入 `dynamic_bias`
- `config/keywords/*.json` 可正常載入
- 帶有 `dynamic_bias` 的實際資料可成功建構，例如 `bybit`

判定：

- **已修復**

---

## 5. 仍存在的問題

### 5.1 `main.py news` 在 Windows 預設編碼下失敗

現象：

```text
'cp950' codec can't encode character ...
```

原因：

- 新聞結果輸出中包含 emoji / Unicode 字元
- Windows 主控台預設 `cp950` 無法編碼部分字元

影響：

- 新聞分析邏輯本身其實已完成
- 但 CLI 輸出階段會因編碼錯誤而中止

判定：

- **仍未修復**

---

## 6. 尚未驗證到的能力

以下能力不屬於本次 `analysis/` 完整驗證範圍，或雖被間接依賴，但沒有逐檔獨立驗證。

### 6.1 非 analysis 區域

- `src/bioneuronai/api/`
- `src/bioneuronai/core/`
- `src/bioneuronai/risk_management/`
- `src/bioneuronai/strategies/`
- `src/bioneuronai/trading/`
- `src/nlp/`
- `src/rag/`

### 6.2 analysis 內未以逐檔獨立案例驗證的事項

雖然腳本有被執行鏈路涵蓋，但以下仍不等於「每個函式、每個分支都測過」：

- `news/prediction_loop.py` 的定時排程與長時間回寫驗證
- `daily_report/market_data.py` 的所有外部來源分支
- `keywords/learner.py` 的完整長期學習回寫流程
- `news/analyzer.py` 在不同 API token、不同新聞來源故障情境下的錯誤處理

---

## 7. 本次驗證邊界

本報告中的「已驗證」代表：

- 該腳本已經被真實執行路徑載入並跑到主要功能

不代表：

- 所有函式與例外分支都已覆蓋
- 已具備完整單元測試覆蓋率
- 與整個 `373-500` 行範圍的所有子系統都完成驗證

---

## 8. 後續建議

1. 修復 `cp950` / Unicode 輸出問題，讓 `main.py news` 在 Windows 預設主控台下也能成功。
2. 若要擴大驗證範圍，下一步應依序驗證：
   - `trading/`
   - `core/`
   - `strategies/`
   - `api/`
   - `rag/`
   - `nlp/`
3. 若要把「已驗證」提升為更嚴格結論，應補：
   - 單元測試
   - 分支覆蓋
   - 外部 API 異常情境
   - 長時間排程流程驗證
