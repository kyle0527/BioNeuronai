# 分支對照分析報告

> **目的：** 對照 `copilot/research-analysis-tinyllm-model` 分支新增的文件與先前對話中完成的分析報告，  
> 確認議題覆蓋度、找出矛盾/衝突，並為每個「現有問題」給出明確判定。  
> **供對象：** 專案 owner 審查分支完整性與一致性。  
>  
> 最後更新：2026-04-08  
> 分析範圍：`docs/CODEBASE_STATUS_REPORT.md` + `docs/BINANCE_FUTURES_INTEGRATION_AUDIT.md`

---

## 一、分支新增文件摘要

| 檔案 | 大小（行數）| 主要內容 |
|------|-----------|---------|
| `docs/CODEBASE_STATUS_REPORT.md` | 282 行 | 16 項訓練流程 Bug 詳細說明（P0-P3 優先序）|
| `docs/BINANCE_FUTURES_INTEGRATION_AUDIT.md` | 327 行 | 費用計算整合、新聞信號時效性、`.env` 載入缺失的審計報告 |

---

## 二、分支文件涵蓋的各項議題（逐條摘錄）

### A. Tokenizer / 詞彙表問題

| # | 來源 | 摘錄 |
|---|------|------|
| 2.9 | `CODEBASE_STATUS_REPORT.md` §2.9 | `model/tokenizer/vocab.json` **不存在**；即使建立後，詞彙表僅 23 段硬編碼對話建立，覆蓋率 < 10%（UNK 率 > 90%） |
| 2.8 | `CODEBASE_STATUS_REPORT.md` §2.8 | `model/*/config.json` 使用 HuggingFace 欄位名稱（`hidden_size`/`num_hidden_layers`）但 `TinyLLMConfig.from_dict()` 讀取自訂欄位名（`embed_dim`/`num_layers`），導致所有超參數被靜默忽略、全部使用預設值 |

### B. 語料不足問題

| # | 來源 | 摘錄 |
|---|------|------|
| 2.7 | `CODEBASE_STATUS_REPORT.md` §2.7 | `--sig-only` 未提供真實資料時自動產生 1,000 筆純隨機資料；建議偵測到無真實資料時直接 `raise RuntimeError` |
| 2.10 | `CODEBASE_STATUS_REPORT.md` §2.10 | `train_with_ai_teacher.py` 訓練資料全為通用問答（「什麼是 AI？」），與交易任務完全無關 |

### C. Signal 標籤 / 訓練資料問題

| # | 來源 | 摘錄 |
|---|------|------|
| 2.11 | `CODEBASE_STATUS_REPORT.md` §2.11 | `backtest/service.py:397（實際 line 423）` — `collect_signal_training_data()` 在沒有已訓練模型時所有 signal 標籤填零，形成「模型先有雞還是先有蛋」的循環依賴；建議第一輪改用規則式標籤（MA 金叉/RSI） |

### D. `--sig-only` 崩潰

| # | 來源 | 摘錄 |
|---|------|------|
| 2.4 | `CODEBASE_STATUS_REPORT.md` §2.4 | `unified_trainer.py:334` — `--sig-only` DataLoader 只輸出 `feature_seq`/`signal_labels`，但共用的 `_train_epoch()` 無條件讀取 `batch['input_ids']`，拋出 `KeyError` |

### E. `auto_evolve.py` 致命錯誤（分支新增，先前未覆蓋）

| # | 來源 | 摘錄 |
|---|------|------|
| 2.1 | `CODEBASE_STATUS_REPORT.md` §2.1 | `auto_evolve.py:144` — `TinyLLM.forward()` 直接返回 `torch.Tensor`，但程式碼用 `outputs.logits`，第一個 batch 即 `AttributeError` |
| 2.2 | `CODEBASE_STATUS_REPORT.md` §2.2 | `auto_evolve.py:179,182` — 儲存時用到從未定義的 `config_dict` 和 `vocab_file`，必然 `NameError` |
| 2.3 | `CODEBASE_STATUS_REPORT.md` §2.3 | 存檔格式不相容：`load_llm()` 期望 `{'state_dict':..., 'config':...}`，但 `unified_trainer.py` 只存 `model.state_dict()`，交叉載入時拋出 `KeyError: 'config'` |

### F. Inference Engine 錯誤（分支新增，先前未覆蓋）

| # | 來源 | 摘錄 |
|---|------|------|
| 2.5 | `CODEBASE_STATUS_REPORT.md` §2.5 | `inference_engine.py:231` warmup 用 `torch.randn(1,1024)`（浮點），但 `forward()` 需要整數 token ID，拋出 `RuntimeError` |
| 2.12 | `CODEBASE_STATUS_REPORT.md` §2.12 | `inference_engine.py:~727` MACD 信號線用 `macd * (2/(n+1))` 一次乘法近似，非真正 EMA，影響 1024 維特徵向量準確度 |

### G. RAG 系統問題（分支新增，先前未覆蓋）

| # | 來源 | 摘錄 |
|---|------|------|
| 2.13 | `CODEBASE_STATUS_REPORT.md` §2.13 | `rag/core/retriever.py:274` — `_retrieve_trading_rules()` 直接 `return []`，交易規則 RAG 檢索完全未實作 |
| 2.14 | `CODEBASE_STATUS_REPORT.md` §2.14 | `rag/core/embeddings.py:229` — 缺少 `sentence-transformers` 時 fallback 為 hash-seeded 隨機向量，相似度計算完全失效，且不發出任何警告 |

### H. 其他技術債（分支新增）

| # | 來源 | 摘錄 |
|---|------|------|
| 2.6 | `CODEBASE_STATUS_REPORT.md` §2.6 | `auto_evolve.py:115` — `input()` 呼叫在非互動環境（Docker/CI）永久阻塞 |
| 2.15 | `CODEBASE_STATUS_REPORT.md` §2.15 | `tiny_llm.py:149` — `use_cache=False` 路徑永遠不會執行（死程式碼） |
| 2.16 | `CODEBASE_STATUS_REPORT.md` §2.16 | `unified_trainer.py:257` — `strict=False` 載入時 embedding 層靜默重新初始化，不輸出警告 |

### I. Binance 費用整合（分支新增，先前完全未提及）

| # | 來源 | 摘錄 |
|---|------|------|
| F-1 | `BINANCE_FUTURES_INTEGRATION_AUDIT.md` §1.2 | `TradingCostCalculator` 已完整定義於 `config/trading_costs.py`，但 `trading_engine.py`、`position_manager.py`、`base_strategy.py`、`pretrade_automation.py` **完全未引用**，系統無法識別「成本超過預期獲利」的情況 |
| F-2 | `BINANCE_FUTURES_INTEGRATION_AUDIT.md` §1.3 | `BinanceFuturesConnector.get_funding_rate()` 已實作，但僅供顯示，未整合進持倉成本估算或持倉繼續持有判斷 |
| F-3 | `BINANCE_FUTURES_INTEGRATION_AUDIT.md` §1.4 | 強制平倉價只在費用計算器內部計算，**未傳遞給止損設定邏輯**，可能造成止損距離大於強制平倉距離 |
| F-4 | `BINANCE_FUTURES_INTEGRATION_AUDIT.md` §2 | `NewsAnalysisResult` 缺少 `signal_valid_hours` / `signal_expires_at` / `signal_urgency` 欄位；現有 `evaluation_window_hours=24` 是事後評估用途，非給交易決策的前瞻性有效期 |
| F-5 | `BINANCE_FUTURES_INTEGRATION_AUDIT.md` §3（表格）| `main.py` 缺少 `load_dotenv()` 呼叫，所有 `.env` 環境變數在生產環境下無法自動載入（阻擋所有 Testnet 測試）|

---

## 三、新議題（分支文件提出，先前分析未列入）

以下議題在先前對話分析報告中**完全沒有提到**，由分支文件首次揭露：

| 新議題代號 | 說明 | 嚴重度 |
|-----------|------|-------|
| **N-1** | `auto_evolve.py` 有 3 個立即崩潰 Bug（2.1/2.2/2.3） | 🔴 P0 |
| **N-2** | `inference_engine.py` warmup 型別錯誤（2.5） | 🔴 P0 |
| **N-3** | `config.json` HuggingFace 欄位名稱 vs TinyLLMConfig 自訂名稱不對齊（2.8） | 🟠 P1 |
| **N-4** | `auto_evolve.py:115` 非互動 `input()` 阻塞（2.6） | 🟠 P1 |
| **N-5** | `rag/core/retriever.py` 交易規則檢索為空殼（2.13） | 🟡 P2 |
| **N-6** | `rag/core/embeddings.py` 無效 fallback 嵌入（2.14） | 🟡 P2 |
| **N-7** | `TradingCostCalculator` 定義存在但完全未整合進交易決策流程（F-1）| 🟠 P1 |
| **N-8** | 強制平倉價未傳遞給止損設定邏輯（F-3）| 🟠 P1 |
| **N-9** | `NewsAnalysisResult` 缺少信號有效期欄位（F-4）| 🟡 P2 |
| **N-10** | `main.py` 缺少 `load_dotenv()` — `.env` 環境變數無法自動載入（F-5）| 🔴 P0 |
| **N-11** | MACD 信號線計算使用一次乘法近似而非標準 EMA（2.12）| 🟡 P2 |
| **N-12** | `train_with_ai_teacher.py` 訓練資料與交易任務無關（2.10）| 🟠 P1 |
| **N-13** | `backtest/service.py` 信號標籤循環依賴，冷啟動問題（2.11）| 🟠 P1 |

---

## 四、對照比較：衝突、不符與矛盾

### 4.1 ⚠️ 檔案路徑錯誤（CODEBASE_STATUS_REPORT.md vs 實際程式碼）

CODEBASE_STATUS_REPORT.md 在「已完成的核心架構」章節列出了**不正確的路徑**：

| 文件描述路徑 | 實際路徑 | 影響 |
|------------|---------|------|
| `src/auto_evolve.py` | `src/nlp/training/auto_evolve.py` | 讀者無法找到對應檔案 |
| `src/unified_trainer.py` | `src/nlp/training/unified_trainer.py` | 同上 |
| `src/inference_engine.py` | `src/bioneuronai/core/inference_engine.py` | 同上 |
| `backtest/service.py:397`（函數位置）| 實際行號 **423**（`collect_signal_training_data` 函數從此行開始）| 行號與文件不符 |

**結論：C（分支文件與主 repo 現況衝突）—路徑描述錯誤。**

---

### 4.2 ⚠️ vocab.json 路徑描述不正確

| 項目 | 分支文件描述 | 實際情況 |
|------|-----------|---------|
| `model/tokenizer/vocab.json` 是否存在 | 文件說「不存在，導致 FileNotFoundError」 | 主目錄 `model/tokenizer/` 確實不存在，但 `model/tiny_llm_en_zh/vocab.json` 和 `model/tiny_llm_en_zh_trained/vocab.json` **都存在且各含 238 個詞彙**（僅 4KB，覆蓋率極低） |
| 詞彙表建立語料 | 「23 段硬編碼對話」| 先前分析指出 `create_bilingual_tokenizer()` 使用 14 句範例文本 × 10 重複；`auto_evolve.py` 讀取的路徑是 `model/tokenizer/vocab.json`（不存在），`unified_trainer.py` 讀取的也是相同路徑 — **兩個訓練腳本都無法找到已有的 vocab.json** |

**結論：A（大方向與分支描述相符，但細節有差異）—修復方案一致（需建立 `model/tokenizer/` 目錄並放入 vocab.json），文件的「23 段」描述與先前分析的「14 句」略有出入，但都指向詞彙覆蓋率極低。** 本次已修復：將 `model/tiny_llm_en_zh/vocab.json` 複製至 `model/tokenizer/vocab.json`。

---

### 4.3 ⚠️ 訓練資料 QA 數量描述差異

| 項目 | 先前分析 | 分支文件 | 實際 |
|------|---------|---------|------|
| `ALL_TRADING_DATA` QA 數量 | 「31 KB，估計 200-400 組」 | 未直接提及此數字（提到詞彙建立用「23 段對話」）| 程式碼驗證：**33 組** |

**結論：B（分支文件未直接覆蓋此數字；先前估計 200-400 組也不準確，實際只有 33 組）。**

---

### 4.4 ⚠️ `TradingCostCalculator` 存在位置描述不完整

| 項目 | 分支文件描述 | 實際 |
|------|-----------|------|
| `TradingCostCalculator` 出現位置 | 只在 `config/__init__.py` 和 `config/trading_costs.py` | 另有 `archived/backtesting/cost_calculator.py` 定義了同名類，且被 `archived/backtesting/historical_backtest.py` 使用；但 `archived/` 不在主交易流程中，結論與分支文件一致（主流程未使用）|

**結論：A（實質結論相符，分支文件描述欠完整但不影響正確性）。**

---

### 4.5 ✅ sig_only 崩潰描述差異（細節補充）

| 項目 | 先前分析（T-6）| 分支文件（2.4）|
|------|-------------|-------------|
| 崩潰原因 | `trainer._run_sig_only = True` 動態注入屬性，但 `_train_epoch()` 完全不檢查此屬性 | `_train_epoch()` 迴圈無條件讀取 `batch['input_ids']`，sig-only DataLoader 沒有此鍵 |

兩者描述同一個崩潰的**不同層面**，實際上都正確且互補：
- T-6 指出根本原因（旗標注入未被讀取）
- 2.4 描述直接現象（KeyError）

**結論：A（相符且互補）。**

---

### 4.6 ✅ `strict=False` 靜默遺失問題

| 項目 | 先前分析（T-7，T-8）| 分支文件（2.16）|
|------|-----------------|--------------|
| 先前 T-7 | ModelLoader 使用 `TinyLLMConfig()` 預設 vocab_size=50257，訓練時用 30000，embedding 不匹配 | — |
| 先前 T-8 | model weights 是 LFS pointer（134 bytes），尚未訓練 | — |
| 分支 2.16 | `strict=False` 載入時 vocab 尺寸不符，embedding 靜默重初始化 | ✅ 新增警告機制 |

**結論：B（分支文件提供了比先前分析更深入的描述，並明確給出解法）。**

---

## 五、A/B/C/D 判定總表

> **判定說明：**  
> **A** = 分支文件與先前分析描述相符  
> **B** = 分支文件提供不同（更深入/補充）的解決思路  
> **C** = 分支文件與主 repo 現況有衝突（路徑錯誤、描述矛盾）  
> **D** = 其他（分支新增議題，先前未提及）

| # | 問題代號 | 問題說明 | 判定 | 備註 |
|---|---------|---------|------|------|
| 1 | T-1 | `create_bilingual_tokenizer()` 14 句硬編碼語料 | **A** | 分支 2.9 描述相符（詞彙覆蓋率極低），數字略有出入（14 vs 23 句）|
| 2 | T-2 | `build_vocab()` 非真正 BPE | **B** | 分支文件未直接提 BPE 問題，但透過 2.9「UNK 率 > 90%」指向同一症狀；解法更聚焦於補充 vocab.json |
| 3 | T-3 | `__main__` save 路徑後綴 `.pkl` | **A** | 分支文件未單獨列出，屬低優先項 |
| 4 | T-4 | 訓練資料 QA 數量不足（先前估 200-400，實際 33） | **B** | 分支文件透過 2.10（`train_with_ai_teacher.py` 資料無關）指出不同面向的資料問題，但未直接提及 33 組這個數字 |
| 5 | T-5 | SignalDataset 合成資料為純隨機噪音 | **A** | 分支 2.7 完全相符，且提供更強的建議（拋 RuntimeError 而非靜默繼續）|
| 6 | T-6 | `--sig-only` 模式 crash（KeyError: input_ids）| **A** | 分支 2.4 相符（互補描述）|
| 7 | T-7 | `ModelLoader` vocab_size 不一致 | **B** | 分支 2.8（config.json 欄位不對齊）和 2.16（strict=False 靜默）提供了更完整的問題描述和解法 |
| 8 | T-8 | 模型權重為 LFS pointer（未訓練）| **A** | 分支文件表 §3 整合度評估中標記 `model/my_100m_model.pth` ✅ 可直接載入（但這個評估可能不準確，因為 LFS pointer 無法正常載入）— 屬 **C（輕微衝突）** |
| 9 | N-1 | `auto_evolve.py` 3 個立即崩潰 Bug | **D** | 先前分析未提及 `auto_evolve.py` |
| 10 | N-2 | `inference_engine.py` warmup 型別錯誤 | **D** | 先前分析提到 `ModelLoader` 問題但未提 warmup RuntimeError |
| 11 | N-3 | `config.json` 欄位名稱不對齊 | **D** | 先前分析未提及 |
| 12 | N-4 | `auto_evolve.py` `input()` 非互動阻塞 | **D** | 先前分析未提及 |
| 13 | N-5 | RAG 交易規則檢索為空殼 | **D** | 先前分析標記 RAG ✅ 完整，實際有空殼函數 |
| 14 | N-6 | RAG embeddings 無效 fallback | **D** | 先前分析未提及 |
| 15 | N-7 | TradingCostCalculator 未整合進交易決策 | **D** | 先前分析未提及 |
| 16 | N-8 | 強制平倉價未傳遞給止損設定 | **D** | 先前分析未提及 |
| 17 | N-9 | NewsAnalysisResult 缺少信號有效期欄位 | **D** | 先前分析未提及 |
| 18 | N-10 | `main.py` 缺少 `load_dotenv()` | **D** | 先前分析未提及 |
| 19 | N-11 | MACD 信號線計算公式錯誤 | **D** | 先前分析未提及 |
| 20 | N-12 | `train_with_ai_teacher.py` 資料與任務無關 | **D** | 先前分析未直接提及（僅說明此腳本是替代方案）|
| 21 | N-13 | 信號標籤冷啟動循環依賴 | **D** | 先前分析描述為「合成資料無實際價值」，分支更精確指出循環依賴根本原因 |

---

## 六、分支文件 vs 先前分析 — 衝突/矛盾彙整

| 衝突項目 | 分支文件描述 | 先前分析描述 | 實際情況 | 哪個正確 |
|---------|-----------|-----------|---------|---------|
| 模組路徑（auto_evolve/unified_trainer/inference_engine） | `src/auto_evolve.py` 等錯誤路徑 | 正確路徑 `src/nlp/training/auto_evolve.py` 等 | 先前分析正確 | **先前分析** |
| `backtest/service.py` 函數行號 | 行號 397 | 先前分析未提行號 | 實際函數在 line 423 | **都不準確，以原始碼為準** |
| `model/my_100m_model.pth` 狀態 | 整合評估表格標記 ✅ 可直接載入 | 標注為 LFS pointer（134 bytes），不可載入 | `model/` 目錄下 `.pth` 是 Git LFS pointer | **先前分析正確** |
| QA 對話資料數量 | 未直接提及 ALL_TRADING_DATA 數量 | 估計 200-400 組 | 實際驗證：**33 組** | **均不準確，以程式碼驗證值 33 為準** |
| vocab.json 描述 | 說 `model/tokenizer/vocab.json` 不存在（正確） | 提到 `create_bilingual_tokenizer()` 用 14 句建詞彙 | `model/tiny_llm_en_zh/vocab.json` 存在（238 詞），`model/tokenizer/vocab.json` 不存在 | **兩者部分正確，各描述了不同層面** |

---

## 七、已完成修復（本 PR 的代碼改動）

依據分支文件揭露的問題，本 PR 已對主要 Bug 進行修復：

| 修復 | 檔案 | 對應問題 |
|------|------|---------|
| `outputs.logits` → `outputs`（直接 tensor）| `src/nlp/training/auto_evolve.py:144` | 2.1 |
| 補上 `config_dict = model.config.__dict__` 和 `vocab_file = tok_file` | `src/nlp/training/auto_evolve.py:170+` | 2.2 |
| 存檔格式改為 `{'state_dict':..., 'config':...}` | `src/nlp/training/auto_evolve.py:175` | 2.3 |
| `unified_trainer.py` 存檔改用 load_llm 相容格式 | `src/nlp/training/unified_trainer.py:357` | 2.3 |
| `unified_trainer.py` 載入時支援新舊兩種格式並輸出警告 | `src/nlp/training/unified_trainer.py:256-268` | 2.16 |
| `_train_epoch()` 支援 sig_only batch 格式 | `src/nlp/training/advanced_trainer.py:213-270` | T-6 / 2.4 |
| `TinyLLMConfig.from_dict()` 加入 HuggingFace 欄位名稱映射 | `src/nlp/tiny_llm.py:80-100` | 2.8 |
| warmup 改用 `torch.zeros(..., dtype=torch.long)` | `src/bioneuronai/core/inference_engine.py:231` | 2.5 |
| MACD 信號線改用標準滾動 EMA | `src/bioneuronai/core/inference_engine.py:735` | 2.12 |
| 建立 `model/tokenizer/vocab.json` | `model/tokenizer/vocab.json` | 2.9 |

---

## 八、未修復項目（需後續處理）

### 仍需修復（中優先）

| 問題 | 建議解法 |
|------|---------|
| `ALL_TRADING_DATA` 只有 33 組 QA 對（T-4）| 擴充至 2,000+ 組，或執行 `train_with_ai_teacher.py` 自動蒸餾 |
| `train_with_ai_teacher.py` 資料與交易任務無關（N-12）| 替換為包含 K 線分析、MACD 信號、倉位管理的領域資料集 |
| `backtest/service.py` 信號標籤循環依賴（N-13）| 第一輪改用規則式標籤（MA 金叉/RSI 超買超賣）冷啟動 |
| `auto_evolve.py:115` `input()` 非互動阻塞（N-4）| 加入 `--non-interactive` 參數或 `sys.stdin.isatty()` 偵測 |
| `rag/core/retriever.py` 交易規則檢索空殼（N-5）| 實作 `_retrieve_trading_rules()` 向量相似度邏輯 |
| `rag/core/embeddings.py` 無效 fallback（N-6）| 缺少依賴時拋出 `ImportError` 或改用 TF-IDF fallback |
| `TradingCostCalculator` 未整合（N-7）| 在 `execute_trade()` 加入最小獲利驗證 |
| 強制平倉價未傳遞給止損（N-8）| 確保止損必須在強制平倉價之前 |
| `NewsAnalysisResult` 缺少信號有效期（N-9）| 新增 `signal_valid_hours` / `signal_expires_at` 欄位 |
| `main.py` 缺少 `load_dotenv()`（N-10）| 加入 `python-dotenv` 並在 `main.py` 呼叫 `load_dotenv()` |

---

## 九、結論摘要

1. **分支文件品質高**：`CODEBASE_STATUS_REPORT.md` 詳細揭露了 16 項 Bug，其中 9 項是先前分析完全未提及的新議題（`auto_evolve.py` 崩潰、`inference_engine.py` warmup 型別錯誤、RAG 空殼、MACD 計算錯誤等）。

2. **主要衝突**：分支文件中的模組路徑全部錯誤（`src/auto_evolve.py` 等），實際路徑為 `src/nlp/training/` 和 `src/bioneuronai/core/`。對使用文件查找程式碼的開發者而言，這些錯誤會造成困惑，建議修正文件中的路徑描述。

3. **分支新增的最高優先事項**（先前未覆蓋但對訓練至關重要）：
   - `auto_evolve.py` 3 個立即崩潰 Bug（**已修復**）
   - `inference_engine.py` warmup 型別錯誤（**已修復**）
   - `main.py` 缺少 `load_dotenv()`（**待修復**）
   - 交易費用計算從未整合進交易決策（**待修復**）

4. **訓練所需最小工作量**（P0 修復後可啟動訓練）：
   - 所有 P0 致命錯誤（2.1/2.2/2.3/2.4/2.5）**已通過本 PR 修復**
   - 仍需：擴充訓練語料 + 執行 `collect-signal-data` 產生真實標籤

---

*本報告由靜態代碼分析與交叉對照產生，建議在修復完成後進行完整整合測試。*
