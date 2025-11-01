# 逐步教程：RAG 整合 / Step-by-step: RAG Integration

1. **準備向量索引 Prepare Vector Index**
   - 建立 `retriever.load_index()` 流程，將專有知識轉換為 embedding。
2. **定義檢索節點 Define Retrieval Node**
   - 在代理回合中於新穎性分數高於 0.6 時觸發檢索。
3. **融合 Hebbian 記憶 Fuse Hebbian Memory**
   - 使用 `BioNeuron.novelty_score()` 判斷是否需要擴增上下文。
4. **語境生成 Context Composition**
   - 將檢索結果與工具輸出轉換為多語提示（`[ZH]/[EN]` label）。
5. **驗證與監控 Validate & Monitor**
   - 將 RAG 回應傳送至安全模組進行敏感資訊檢查。
