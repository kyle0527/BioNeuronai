# BioNeuronAI 技術白皮書 / Technical Whitepaper

## 1. Hebbian 學習核心 / Hebbian Learning Core

- **動機 Motivation**：模擬突觸可塑性以強化模式關聯，採用乘法式更新將輸入與輸出共現對應到權重調整。
- **公式 Formulation**：`Δw = η * x * y`，內建權重裁剪以維持可解釋性與數值穩定。
- **記憶 Memory Handling**：短期記憶佇列保留最近輸入，提供新穎性評估的基準樣本。

## 2. 新穎性計算 / Novelty Computation

1. 緩存最近兩筆輸入樣本。
2. 計算平均絕對差並相對於前一樣本的平均強度進行歸一化。
3. 將結果裁剪至 0~1 之間提供簡潔的風險量測。

This mechanism powers curiosity-driven exploration while remaining interpretable
for safety reviews.

## 3. 架構決策 / Architecture Decisions

- **模組化 / Modular**：`BioNeuron` → `BioLayer` → `BioNet` 的層級結構便於嵌入到更大型代理系統。
- **CLI 與工具閘門 / CLI & Tool Gating**：命令列工具提供即時檢測與示範；工具閘門案例確保在多工具代理內遵守安全流程。
- **擴充性 / Extensibility**：`improved_core` 與安全模組使用相同匯出方式，讓新版演算法可快速切換。

## 4. 安全模組流程 / Security Module Pipelines

| 模組 Module | 流程概述 Pipeline Summary |
|-------------|---------------------------|
| 認證強化 Enhanced Auth | 建立弱密碼字典 → 偵測登入欄位 → 嘗試驗證 → 回報弱憑證證據 |
| SQLi 偵測 Production SQLi | 掃描輸入欄位 → 自動產生測試 payload → 分析回應異常 → 評分風險 |
| IDOR 偵測 Production IDOR | 映射資源識別碼 → 產生相鄰請求 → 比較授權與內容差異 |

Each module publishes structured `FindingPayload` objects consumed by the unified
safety manager, enabling consistent logging and human review.

## 5. 整合策略 / Integration Strategy

- 將 Hebbian 新穎性分數輸出至儀表板與安全報表，協助人工審查。
- 利用 RAG 管線提供上下文提示與安全指引，搭配工具閘門減少誤用。
- 強化學習循環以新穎性信號作為探索獎勵，與安全模組的高風險回報互斥。

## 6. 後續工作 / Future Work

1. 引入可塑性疲乏（fatigue）模型以避免過度適應。
2. 與事件驅動型監控整合，提高安全模組的即時性。
3. 建立跨語系資料集以進一步測試多語代理。
