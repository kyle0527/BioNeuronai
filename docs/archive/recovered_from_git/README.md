# recovered_from_git — 考古原文（不可 import）

自 git commit `9f6e271` 的父版本抽出的舊 `archived/` 文件與腳本。

- **用途**：新舊比對、把有價值的設計「拿回家」  
- **不是**：現役模組路徑；勿 `from` 這裡 import  
- **對照決策**：見上層 [`../COMPARISON_REGISTER.md`](../COMPARISON_REGISTER.md)  
- **不做**：還原 `tests/`／pytest；正式驗收 = 實際 CLI／Paper／回測（階段 C，尚未開始）

## 目錄

| 路徑 | 內容 |
|------|------|
| `backtesting/` | 舊 walk_forward／cost／historical（WF 已接回現役） |
| `docs_v3/` | 舊 SOP、新聞指南、策略手冊等 |
| `old_docs/` | 蒸餾指南、權重分類等 |
| `tech/` | 關鍵字、TinyLLM、模組化指南 |
| `root_guides/` | DB／進化／Binance 實作報告 |
| `_full_rest/` | 其餘比對用全文（FEATURE_STATUS、TECH_DEBT…） |
| **`mirror/`** | purge 幾乎完整鏡像（步驟 1 檢查用，約 132 檔） |

已半套接回現役：多窗 Walk-Forward 窗格 → `backtest/walk_forward.py`（**param_grid 優化仍未移**）。  
步驟 1／2 真實狀態：[`../STEP1_STEP2_STATUS.md`](../STEP1_STEP2_STATUS.md)。
