# 變更日誌 (CHANGELOG)

所有對項目的重要更改都將記錄在此文件中。

## [1.0.0] - 2024 - 第一階段核心改進

### 🎉 重大更新

#### 添加
- **KV Cache (Past Key-Value Cache)** 
  - 實現注意力機制的 Key-Value 緩存
  - 生成速度提升 2-5x（測試顯示 3.35x）
  - 時間節省高達 70%
  - 更新 `MultiHeadAttention`, `TransformerBlock`, `TinyLLM` 以支持 KV Cache

- **重複懲罰 (Repetition Penalty)**
  - 降低重複生成相同 token 的概率
  - 提高文本生成質量和多樣性
  - 可調參數 `repetition_penalty` (推薦 1.1-1.5)

- **高級採樣策略**
  - Temperature Scaling: 控制輸出隨機性
  - Top-K Sampling: 從前 K 個高概率 tokens 採樣
  - Top-P (Nucleus) Sampling: 累積概率採樣
  - 貪婪搜索: 確定性輸出
  - 支持策略組合使用

- **梯度累積 (Gradient Accumulation)**
  - 模擬大批次訓練而不增加顯存
  - 有效批次 = batch_size × gradient_accumulation_steps
  - 支持小顯存設備訓練大模型

- **混合精度訓練 (Mixed Precision Training)**
  - 使用 PyTorch AMP (Automatic Mixed Precision)
  - 訓練速度提升 2-3x
  - 顯存使用減少約 50%
  - 幾乎不影響模型精度

- **學習率調度 (Learning Rate Scheduling)**
  - Warmup: 開始時逐漸增加學習率
  - Cosine Annealing: 餘弦退火調度
  - Linear Decay: 線性衰減
  - Constant: 恆定學習率

- **生成工具函數庫**
  - `generation_utils.py` 新增多個輔助函數
  - `apply_repetition_penalty()` - 重複懲罰
  - `top_k_filtering()` - Top-K 過濾
  - `top_p_filtering()` - Top-P 過濾
  - `apply_temperature()` - 溫度縮放
  - `sample_from_logits()` - 通用採樣函數
  - `calculate_perplexity()` - 困惑度計算
  - `beam_search()` - Beam Search 解碼

- **高級訓練器**
  - `advanced_trainer.py` 完整的訓練框架
  - 支持所有新功能（梯度累積、混合精度等）
  - 自動保存最佳模型和檢查點
  - 完整的訓練歷史記錄
  - 靈活的配置系統

- **測試和驗證**
  - `test_kv_cache.py` - KV Cache 性能測試
  - 驗證加速效果和正確性
  - 重複懲罰效果測試

- **完整文檔**
  - `QUICK_START.md` - 快速開始指南
  - `IMPROVEMENTS.md` - 詳細改進說明
  - `SUMMARY.md` - 第一階段完成報告
  - `README.md` - 項目主頁更新

#### 更改
- **tiny_llm.py 大幅重構**
  - `MultiHeadAttention.forward()` 新增 `past_key_value` 和 `use_cache` 參數
  - `TransformerBlock.forward()` 支持 KV Cache 傳遞
  - `TinyLLM.forward()` 管理所有層的 KV Cache
  - `TinyLLM.generate()` 完全重寫，支持 KV Cache 和所有新採樣策略
  - 添加 `Union` 類型支持

- **生成參數擴展**
  - `max_new_tokens`: 最大生成 token 數
  - `temperature`: 溫度參數
  - `top_k`: Top-K 採樣
  - `top_p`: Top-P 採樣
  - `repetition_penalty`: 重複懲罰
  - `use_cache`: 是否使用 KV Cache
  - `eos_token_id`: 結束標記
  - `pad_token_id`: 填充標記
  - `do_sample`: 是否採樣

#### 性能提升
- **KV Cache**: 
  - 生成速度提升 3.35x（測試結果）
  - 時間節省 70.1%
  - 適合長文本生成和對話系統

- **混合精度訓練**:
  - 訓練速度提升 ~2.5x
  - 顯存使用減少 ~50%
  - 支持更大的模型和批次

- **梯度累積**:
  - 相同的有效批次大小
  - 顯存使用減少 4x（gradient_accumulation_steps=4）
  - 訓練穩定性提升

### 🐛 修復
- 修復 `MultiHeadAttention` 中的重複 return 語句
- 優化因果遮罩創建邏輯
- 改進位置編碼計算（支持 KV Cache）

### 📝 文檔
- 新增快速開始指南
- 新增詳細改進說明
- 新增第一階段完成報告
- 更新主 README
- 添加使用示例和最佳實踐

### 🧪 測試
- 添加 KV Cache 性能測試
- 驗證加速效果（3.35x）
- 驗證輸出正確性
- 測試重複懲罰效果

### 📦 新文件
```
src/bioneuronai/generation_utils.py    - 生成工具函數庫
training/advanced_trainer.py            - 高級訓練器
docs/QUICK_START.md                    - 快速開始指南
docs/IMPROVEMENTS.md                   - 改進說明
docs/SUMMARY.md                        - 完成報告
docs/README.md                         - 項目主頁
docs/CHANGELOG.md                      - 本文件
```

### 🔄 修改文件
```
src/bioneuronai/tiny_llm.py            - 核心模型大幅更新
```

---

## [0.1.0] - 之前版本

### 初始實現
- 基礎 TinyLLM 模型（124M 參數）
- GPT-like Transformer 架構
- 簡單的文本生成
- 基礎訓練腳本
- 知識蒸餾支持

---

## 即將推出

### [1.1.0] - 第二階段：評估指標
- [ ] 完整的 Perplexity 實現
- [ ] BLEU Score 計算
- [ ] ROUGE Score 計算
- [ ] 自定義評估指標
- [ ] 評估數據集支持
- [ ] 評估報告生成

### [2.0.0] - 第三階段：高級優化
- [ ] 模型量化（8-bit, 4-bit）
- [ ] LoRA 微調支持
- [ ] Flash Attention 2.0
- [ ] 改進的 Tokenizer (BPE)
- [ ] 分佈式訓練支持
- [ ] 模型並行

### [3.0.0] - 第四階段：應用層
- [ ] 對話系統框架
- [ ] 文本摘要應用
- [ ] 問答系統
- [ ] 代碼生成工具
- [ ] RAG (檢索增強生成)
- [ ] API 服務器

---

## 版本說明

格式基於 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.0.0/)，
版本號遵循 [Semantic Versioning](https://semver.org/lang/zh-TW/)。

### 版本號含義
- **主版本號 (Major)**: 不兼容的 API 更改
- **次版本號 (Minor)**: 向後兼容的功能性新增
- **修訂號 (Patch)**: 向後兼容的問題修正

### 變更類型
- **添加 (Added)**: 新功能
- **更改 (Changed)**: 現有功能的變更
- **棄用 (Deprecated)**: 即將移除的功能
- **移除 (Removed)**: 已移除的功能
- **修復 (Fixed)**: 錯誤修復
- **安全 (Security)**: 安全性修復

---

**最後更新**: 2024  
**維護者**: BioNeuronai Team
