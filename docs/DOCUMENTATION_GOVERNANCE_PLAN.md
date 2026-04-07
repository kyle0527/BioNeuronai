# 文件治理與後續交接規範

**版本**: v2.1  
**更新日期**: 2026-04-06  
**用途**: 提供其他 AI / 開發者接手文件整理時的正式工作基準  
**適用範圍**: `README.md`、`docs/`、`backtest/docs/`、`src/*/README.md`

---

## 📑 目錄

1. 文件目的
2. 目前已確認的正式現況
3. 文件治理核心原則
4. 正式文件集合
5. 文件分類規則
6. 何時更新、何時歸檔
7. 重寫與歸檔操作流程
8. 撰寫規範
9. 目前已完成的文件整理
10. 建議後續工作順序
11. 文件驗收標準
12. 交接備註

---

## 1. 文件目的

本文件的目的不是再寫一份系統介紹，而是定義：

- 目前文件整理應該遵守的規範
- 哪些文件是正式主文件
- 哪些文件應更新、重寫、歸檔
- 後續文件工作應優先處理什麼
- 另一個 AI 接手時，應以什麼標準完成

這份文件應作為文件治理的單一工作說明書，避免再產生：

- 多份文件同時描述「當前正式主線」
- 舊文件局部修補後仍保留大量過時內容
- 新增更多重複文件，導致文件集合越來越亂
- 文件版本、路徑、模組責任彼此矛盾

---

## 2. 目前已確認的正式現況

其他 AI 接手前，請先以以下現況為準，不要再依據舊文假設判斷。

### 2.1 正式主版本

目前主系統正式版本為：

- `2.1`

已確認統一到 `2.1` 的主程式位置包括：

- `pyproject.toml`
- `src/bioneuronai/__init__.py`
- `src/bioneuronai/api/app.py`
- `backtest/__init__.py`
- `src/schemas/types.py`

### 2.2 正式模組分層

目前正式模組分層應理解為：

- `src/bioneuronai/core/`
  - 交易引擎與 AI 推理主線

- `src/bioneuronai/strategies/`
  - 固定策略
  - selector
  - fusion
  - strategy arena / optimizer / router

- `src/bioneuronai/planning/`
  - 高階計劃
  - 盤前檢查
  - 市場分析
  - pair selection

- `src/bioneuronai/trading/`
  - 訂單 / 帳戶 / 持倉 / 資金的事實層
  - 目前核心檔案為 `virtual_account.py`

- `backtest/`
  - replay / backtest 正式主路徑

### 2.3 已退出正式主線

以下內容已不再視為正式主路徑：

- 舊 `trading_strategies.py`
- `strategies/selector/evaluator_new.py`
- 舊 `trading/trading_plan_system.py`
- 舊 `trading/risk_manager.py`

### 2.4 文件處理原則上的現況

目前已採取的策略是：

- 若大型文件大部分內容已老舊，先歸檔原稿，再重寫正式版
- 正式文件前面要有目錄
- 文件描述必須對齊目前實際程式與實際驗證結果

---

## 3. 文件治理核心原則

### 3.1 以實際程式與實際驗證結果為準

- 不以舊文件互相引用作為真相來源
- 若文件與程式不一致，優先修文件
- 若文件與實測結果不一致，優先修文件

### 3.2 優先修改既有文件，不新增重複文件

- 能更新原文件，就更新原文件
- 不要為同一主題再多建一份平行文件
- 只有在原文件已不適合作為正式文件時，才採用「歸檔原稿 + 原路徑重寫」

### 3.3 主線文件應少而清楚

正式主線、正式入口、正式責任邊界，應集中在少數文件：

- 主手冊
- 操作手冊
- 接手地圖
- 回測系統指南
- 文件索引

其他文件只保留專題內容，不應重新描述整個系統。

### 3.4 大型正式文件一律有目錄

凡是正式主文件、且內容超過短篇說明者，前面都必須有：

- 文件用途
- 版本
- 更新日期
- 目錄

### 3.5 歷史版本與舊內容只留在歷史區

- 當前主版本統一寫 `v2.1`
- 舊版本只能留在：
  - 歷史章節
  - changelog
  - archive 文件

### 3.6 遵守 `docs/CODE_FIX_GUIDE.md`

文件工作也要遵守修復準則：

- 以實際架構為準
- 以修改既有檔案為主
- 已刪除、已搬移、已退出主線的路徑，不得在正式文件中繼續當成現況

---

## 4. 正式文件集合

目前應視為正式主文件集合，優先維護的有：

- `README.md`
- `docs/README.md`
- `docs/BIONEURONAI_MASTER_MANUAL.md`
- `docs/OPERATION_MANUAL.md`
- `docs/PROJECT_HANDOVER_MAP.md`
- `docs/BACKTEST_SYSTEM_GUIDE.md`
- `docs/STRATEGY_COMPETITION_REMEDIATION_PLAN.md`
- `src/bioneuronai/README.md`
- `src/bioneuronai/trading/README.md`
- `backtest/README.md`
- `backtest/docs/USER_MANUAL.md`

這些文件的角色如下：

- 系統總覽：
  - `README.md`
  - `docs/BIONEURONAI_MASTER_MANUAL.md`

- 操作與使用：
  - `docs/OPERATION_MANUAL.md`
  - `backtest/docs/USER_MANUAL.md`

- 接手與架構：
  - `docs/PROJECT_HANDOVER_MAP.md`
  - `docs/BACKTEST_SYSTEM_GUIDE.md`

- 策略與修復現況：
  - `docs/STRATEGY_COMPETITION_REMEDIATION_PLAN.md`

- 子模組入口：
  - `src/bioneuronai/README.md`
  - `src/bioneuronai/trading/README.md`
  - `backtest/README.md`

---

## 5. 文件分類規則

### A. 正式主文件

特徵：

- 描述目前正式主線
- 對接手開發有直接價值
- 必須持續維護

### B. 專題文件

特徵：

- 專注單一主題
- 不應重新定義整體系統現況
- 可持續保留，但不應和主手冊衝突

例如：

- `RISK_MANAGEMENT_MANUAL.md`
- `TRADING_COSTS_GUIDE.md`
- `DATA_SOURCES_GUIDE.md`
- `RAG_TECHNICAL_MANUAL.md`

### C. 草案 / 規劃文件

特徵：

- 內容偏未來規劃
- 尚未完全落地
- 不應被當成正式現況說明

例如：

- `EVOLUTION_SYSTEM_PLAN.md`
- `STRATEGY_EVOLUTION_WEB_INTEGRATION_PLAN.md`

### D. 歸檔文件

特徵：

- 大部分內容已脫離現況
- 保留只是為了追溯或對照
- 不應再作為正式參考

目前已歸檔示例：

- `archived/docs_v2_1_legacy/BIONEURONAI_MASTER_MANUAL.legacy_20260405.md`
- `archived/docs_v2_1_legacy/MANUAL_IMPLEMENTATION_STATUS.legacy_20260405.md`
- `archived/docs_v2_1_legacy/FEATURE_STATUS.legacy_20260405.md`

---

## 6. 何時更新、何時歸檔

### 6.1 適合直接更新的情況

如果文件只有局部過時，直接更新原文件即可，例如：

- 版本號落後
- 少量路徑搬移
- 少量章節需要依新主線改寫
- 文件整體結構仍然可用

### 6.2 適合先歸檔再重寫的情況

若符合下列任一條件，建議直接歸檔原稿，再重寫正式版：

1. 文件大部分章節都建立在舊架構假設上
2. 仍大量引用已刪除檔案
3. 仍把已退出主線的模組當正式能力
4. 主要架構圖、主要路徑、主入口大多失真
5. 局部修補成本已高於重寫

### 6.3 不應再繼續維護為正式現況文件的典型情況

若文件本質上是：

- 歷史報告
- 一次性驗證報告
- 舊版演進說明
- 已失效草案

則應歸檔或降級，不應再嘗試把它修成主文件。

---

## 7. 重寫與歸檔操作流程

若某大型文件需要重寫，請按以下流程：

1. 先完整閱讀舊稿
2. 判斷哪些內容仍有價值
3. 若整體已過時：
   - 先複製到 `archived/docs_v2_1_legacy/`
   - 檔名格式建議：
     - `<原檔名>.legacy_YYYYMMDD.md`
4. 再在原路徑重寫正式版
5. 新正式版必須補目錄
6. 若新正式版仍需吸收舊內容：
   - 以「重新轉譯到目前實際架構」方式吸收
   - 不可直接原樣搬回舊描述
7. 更新 `docs/README.md` 的索引與歸檔清單

---

## 8. 撰寫規範

### 8.1 路徑規範

- 只使用目前實際存在的正式路徑
- 不得在正式文件中保留已刪除或已搬移路徑，除非是在歷史段落中明確說明

目前正式路徑示例：

- `src/bioneuronai/planning/...`
- `src/bioneuronai/trading/virtual_account.py`
- `src/bioneuronai/risk_management/...`
- `src/bioneuronai/strategies/...`
- `backtest/...`

### 8.2 版本規範

- 當前系統版本一律寫 `v2.1`
- 若文件要提歷史版本，必須明確寫成歷史資訊

### 8.3 內容規範

文件在描述現況時，應明確區分：

- 已完成
- 部分完成
- 仍待完成
- 已歸檔 / 已退出主線

避免把：

- 規劃中
- 研究中
- 曾經存在過

寫成當前正式能力。

### 8.4 結構規範

大型正式文件至少應包含：

- 文件用途
- 版本
- 更新日期
- 目錄
- 明確章節分工

### 8.5 避免重複規範

若主手冊已經定義：

- 正式主線
- 主模組分工
- 正式入口

則其他文件不應再次用不同口徑重述，只需引用或聚焦該文件自己的主題。

---

## 9. 目前已完成的文件整理

截至目前，已完成的主要文件治理工作包括：

### 9.1 已歸檔並重寫

- `BIONEURONAI_MASTER_MANUAL.md`
- `MANUAL_IMPLEMENTATION_STATUS.md`
- `FEATURE_STATUS.md`

對應 archive：

- `archived/docs_v2_1_legacy/BIONEURONAI_MASTER_MANUAL.legacy_20260405.md`
- `archived/docs_v2_1_legacy/MANUAL_IMPLEMENTATION_STATUS.legacy_20260405.md`
- `archived/docs_v2_1_legacy/FEATURE_STATUS.legacy_20260405.md`

### 9.2 已清理的正式主線誤導內容

文件中不再應把下列內容當成正式主線：

- 舊 `trading_strategies.py`
- `selector/evaluator_new.py`
- 舊 `trading/trading_plan_system.py`
- 舊 `trading/risk_manager.py`

### 9.3 已新增的治理文件

- 本文件 `docs/DOCUMENTATION_GOVERNANCE_PLAN.md`

---

## 10. 建議後續工作順序

以下是目前最建議其他 AI 接手的文件工作順序。

### 第一優先

1. `docs/ARCHITECTURE_OVERVIEW.md`
   - 高機率應採「先歸檔，再重寫」
   - 原因：仍有大量舊 `trading_strategies.py` 與舊 `trading/` 路徑描述

2. `docs/SRC_DIRECTORY_ANALYSIS.md`
   - 高機率應採「先歸檔，再重寫」
   - 原因：src 樹狀與目前 `planning/` / `trading/` 分層已有落差

### 第二優先

3. `docs/PROJECT_HANDOVER_MAP.md`
   - 大方向仍有價值
   - 但需改掉舊 `trading/` 依賴圖與風控路徑描述

4. `docs/OPERATION_MANUAL.md`
   - 應保留並更新
   - 對齊 `planning/`、`trading/`、`backtest/` 新分層

### 第三優先

5. `docs/QUICKSTART_V2.1.md`
   - 檢查死連結與不存在路徑
   - 若錯誤比例過高，可考慮歸檔後重寫

6. `docs/BACKTEST_SYSTEM_GUIDE.md`
   - 已較接近現況
   - 主要是清理舊歷史描述與補齊當前正式做法

### 第四優先

7. 專題文件逐步校正版本與路徑
   - `RISK_MANAGEMENT_MANUAL.md`
   - `RAG_TECHNICAL_MANUAL.md`
   - `DATA_STORAGE_INTEGRATION.md`
   - `STRATEGY_EVOLUTION_GUIDE.md`

---

## 11. 文件驗收標準

其他 AI 完成一份文件整理後，至少應符合以下標準。

### 11.1 內容正確性

- 與目前實際程式路徑一致
- 與目前正式主線描述一致
- 未把已退出主線內容寫成當前能力

### 11.2 結構完整性

- 大型正式文件有目錄
- 用途、版本、更新日期齊全
- 章節劃分清楚

### 11.3 治理一致性

- 若原文件大多過時，已先 archive 再重寫
- `docs/README.md` 已更新索引
- 未新增不必要的平行文件

### 11.4 版本一致性

- 當前系統版本表述統一為 `v2.1`
- 歷史版本只留在歷史段落或 archive

---

## 12. 交接備註

其他 AI 接手文件工作時，請特別注意：

1. 先看本文件，再看 `docs/README.md`
2. 再看目前正式主文件：
   - `docs/BIONEURONAI_MASTER_MANUAL.md`
   - `docs/PROJECT_HANDOVER_MAP.md`
   - `docs/OPERATION_MANUAL.md`
   - `docs/BACKTEST_SYSTEM_GUIDE.md`
3. 再決定某份舊文件要「更新」還是「歸檔後重寫」
4. 若發現文件與程式不一致，以程式與實測為準
5. 若文件已經大部分老舊，不要花太多時間做局部修補

本文件的核心目的只有一個：

**讓文件集合收斂成少量正式文件，避免重複、避免衝突、避免把歷史包袱繼續當成現況。**
