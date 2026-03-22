# 新聞與分析模組 (News & Analysis) - 執行期驗證與 Bug 報告

**報告生成時間:** 2026-03-22
**問題模組:** `src/bioneuronai/analysis/keywords/loader.py` 與 `models.py`

## 1. 錯誤現象 (Error Description)
當執行 `python main.py news --symbol BTCUSDT` 以單獨啟動新聞分析模組時，雖然新聞抓取功能（`analyzer.py`）成功運作，但在底層載入關鍵字庫時，系統拋出了以下錯誤：

```text
ERROR:bioneuronai.analysis.keywords.loader: 載入分類檔案失敗: Keyword.__init__() got an unexpected keyword argument 'dynamic_bias'
```

## 2. 根本原因分析 (Root Cause)
這個錯誤來自於 **「資料設定檔 (JSON)」** 與 **「程式碼資料模型 (Dataclass)」** 之間的不匹配：
1. **JSON 設定檔超載**：在 `config/keywords/` 目錄下的 JSON 分類檔（例如 `institution.json` 或其他配置）中，某些關鍵字物件被加入了 `"dynamic_bias"` 這個新屬性欄位。
2. **Models 定義過時**：在 `src/bioneuronai/analysis/keywords/models.py` 裡面所定義的 `Keyword` 資料類別（Dataclass），其建構子 `__init__()` 並沒有宣告接受 `dynamic_bias` 這個參數。
3. **發生崩潰**：當 `loader.py` 嘗試使用動態展開 (`**json_data`) 將 JSON 轉換成 `Keyword` 的 Python 物件時，Python 直譯器抓到未知參數，於是拋出例外，導致該分類檔案的載入直接被中斷。

## 3. 影響範圍 (Impact)
*   **部分關鍵字庫癱瘓**：因為載入過程拋出例外，所有帶有 `dynamic_bias` 屬性的關鍵字陣列都無法被正確讀取進記憶體，這導致目前 NLP 在算情緒分數時，可能會漏掉很多重要的市場關鍵字（雖然總數顯示載入了 199 個，但實際上可能有整個類別被排除了）。
*   **後續自學系統 (`learner.py`) 可能失效**：若關鍵字物件破斷，未來 AI 自主調整權重時會抓不到正確的關鍵字關聯。

## 4. 修復建議 (Solution)
**方法一：更新 Models (推薦)**
請打開 `src/bioneuronai/analysis/keywords/models.py`，找到 `Keyword` 的類別宣告，並加入 `dynamic_bias` 屬性（可以設定預設值以防舊資料報錯）：
```python
@dataclass
class Keyword:
    word: str
    weight: float
    sentiment: float
    category: str
    # ----- 加入這行來修復 -----
    dynamic_bias: float = 0.0  # 或設定為 Optional[float] = None
    # -------------------------
    ...
```

**方法二：清理 JSON**
如果您其實沒有打算使用 `dynamic_bias` 這個功能，請寫一支小腳本（或手動）將 `config/keywords/` 目錄下所有 JSON 檔案裡的 `"dynamic_bias"` 鍵值對刪除。

---

## 附錄：為什麼「分析層 (Analysis)」有超過 80% 的腳本未被驗證？

在剛才的執行測試中，整個 `src/bioneuronai/analysis/` 資料夾下，我們**實際上只驗證到了 `news` 模組中的 3 支腳本** (`analyzer.py`, `evaluator.py`, `models.py`)。其餘高達十幾支腳本完全沒有被觸發，原因可歸咎於此專案優良的**「模組化解耦機制」**與**「防呆阻擋」**：

### 原因一：缺乏連續 K 線行情 (歷史資料阻斷)
分析層中的核心技術分析，例如「特徵工程」(`feature_engineering.py`) 以及「市場狀態識別」(`market_regime.py`)，全都是**基於 K 線跳動 (Tick/Candle)** 才會開始執行數學運算。
因為我們目前的硬碟裡缺乏事前下載的歷史訓練資料 (如 `ETHUSDT 15m`)，系統在資料源頭就觸發了「防呆中斷」，這導致引擎直接停機，後面那些仰賴盤面資料輸入的分析模組自然連一行代碼都沒有跑過。

### 原因二：特定迴圈與排程器未被「一次性指令」喚醒
在 `news/` 與 `keywords/` 資料夾中，有兩支未被驗證的最強腳本：
- `prediction_loop.py` (新聞預測的自我驗證循環)
- `learner.py` (關鍵字權重動態更新器)

這兩支程式在設計上屬於 **「背景排程器 (Scheduler Daemon)」** 或是 **「盤後結算系統」**。它們的功能是讓 AI 把預測的結果存進資料庫，並在「4 小時後」抓取新價格去比對準確率。也就是說，我們剛才下的 `python main.py news` 指令就像是一次性的「即時算命」，並不足以喚醒這些需要在未來常駐跑循環、甚至需要人工介入的反饋腳本。 

### 原因三：每日報告產生器屬於「關盤後任務」
在 `analysis/daily_report/` 目錄下的所有 6 支報表產生程式，都被設計成要等「今日所有交易紀錄結算」後才會執行統整並輸出市況。因為我們根本還沒完成任何一筆模擬交易，當然也不會觸發撰寫當日出金、盈虧報表的流程，因此整個資料夾都處於沒被驗證的待機狀態。

**總結來說：** 分析模組沒被完整掃過，正是因為系統架構保護得很好，沒有為了「無中生有的測試」去硬跑沒意義的空資料。一旦您補足了歷史資料池並啟動回測大迴圈，所有的腳本就會一一醒來加入運算。
