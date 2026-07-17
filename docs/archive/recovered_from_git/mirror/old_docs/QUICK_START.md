# TinyLLM 快速開始指南

## 安裝依賴

```bash
pip install torch transformers
```

## 1. 基礎使用

### 創建和使用模型

```python
from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
import torch

# 創建模型配置
config = TinyLLMConfig(
    vocab_size=50257,      # 詞彙表大小
    max_seq_length=512,    # 最大序列長度
    embed_dim=768,         # 嵌入維度
    num_layers=12,         # Transformer 層數
    num_heads=12,          # 注意力頭數
    dropout=0.1            # Dropout 率
)

# 創建模型
model = TinyLLM(config)
print(f"模型參數: {model.count_parameters():,}")  # 約 124M 參數

# 準備輸入（示例）
input_ids = torch.randint(0, config.vocab_size, (1, 10))

# 生成文本
model.eval()
output = model.generate(
    input_ids,
    max_new_tokens=50,
    temperature=0.8,
    top_k=50,
    top_p=0.95,
    use_cache=True  # 使用 KV Cache 加速
)

print(f"生成的序列形狀: {output.shape}")
```

## 2. 高級生成選項

### 控制生成質量

```python
# 更確定的輸出（低溫度）
output = model.generate(
    input_ids,
    max_new_tokens=50,
    temperature=0.5,  # 更確定
    do_sample=True
)

# 更隨機的輸出（高溫度）
output = model.generate(
    input_ids,
    max_new_tokens=50,
    temperature=1.2,  # 更隨機
    do_sample=True
)

# 貪婪搜索（最確定）
output = model.generate(
    input_ids,
    max_new_tokens=50,
    do_sample=False  # 總是選擇最高概率
)
```

### 減少重複

```python
# 使用重複懲罰
output = model.generate(
    input_ids,
    max_new_tokens=50,
    repetition_penalty=1.2,  # 降低重複
    temperature=0.8,
    use_cache=True
)
```

### 組合使用多種策略

```python
# 最佳實踐配置
output = model.generate(
    input_ids,
    max_new_tokens=100,
    temperature=0.8,           # 適中的隨機性
    top_k=50,                  # Top-K 採樣
    top_p=0.95,                # Nucleus 採樣
    repetition_penalty=1.2,    # 輕度重複懲罰
    use_cache=True,            # 使用 KV Cache
    do_sample=True             # 啟用採樣
)
```

## 3. 訓練模型

### 簡單訓練

```python
from training.advanced_trainer import Trainer, TrainingConfig
from torch.utils.data import DataLoader

# 準備數據（示例）
train_dataloader = ...  # 你的數據加載器

# 配置訓練
train_config = TrainingConfig(
    batch_size=8,
    gradient_accumulation_steps=4,  # 有效批次 = 32
    max_epochs=10,
    learning_rate=3e-4,
    use_amp=True,  # 混合精度
    output_dir="./output"
)

# 創建訓練器
trainer = Trainer(
    model=model,
    train_config=train_config,
    train_dataloader=train_dataloader
)

# 開始訓練
trainer.train()
```

### 自定義訓練配置

```python
train_config = TrainingConfig(
    # 批次和累積
    batch_size=8,
    gradient_accumulation_steps=4,
    
    # 訓練參數
    max_epochs=10,
    learning_rate=3e-4,
    weight_decay=0.01,
    
    # 學習率調度
    warmup_steps=500,
    lr_scheduler_type="cosine",  # "cosine", "linear", "constant"
    
    # 優化
    use_amp=True,                # 混合精度
    max_grad_norm=1.0,           # 梯度裁剪
    
    # 評估和保存
    eval_steps=500,
    save_steps=1000,
    logging_steps=100,
    
    # 設備和輸出
    device="cuda" if torch.cuda.is_available() else "cpu",
    output_dir="./training_output"
)
```

## 4. 保存和加載模型

### 保存模型

```python
import torch
from pathlib import Path

# 保存完整模型
save_dir = Path("./my_model")
save_dir.mkdir(exist_ok=True)

torch.save(model.state_dict(), save_dir / "model.pth")

# 保存配置
import json
with open(save_dir / "config.json", 'w') as f:
    json.dump(model.config.to_dict(), f, indent=2)
```

### 加載模型

```python
# 加載配置
with open("./my_model/config.json", 'r') as f:
    config_dict = json.load(f)

config = TinyLLMConfig(**config_dict)

# 創建模型
model = TinyLLM(config)

# 加載權重
model.load_state_dict(
    torch.load("./my_model/model.pth", map_location='cpu')
)
model.eval()
```

## 5. 性能測試

### KV Cache 加速

KV Cache 在模型內部自動啟用，可顯著提升生成速度：
```
==========================================
KV Cache 加速效果
==========================================
模型參數: 33,087,744
設備: cuda

輸入序列長度: 10
生成 tokens 數: 50

測試 1: 不使用 KV Cache
生成時間: 2.345 秒
生成速度: 21.32 tokens/秒

測試 2: 使用 KV Cache
生成時間: 0.812 秒
生成速度: 61.58 tokens/秒

性能比較
加速比: 2.89x
時間節省: 65.4%
✓ 驗證通過: KV Cache 正確實現!
```

## 6. 常見問題

### Q: 如何選擇生成參數？

**A: 推薦配置：**
- **創意文本生成**（故事、詩歌）:
  ```python
  temperature=1.0, top_p=0.95, repetition_penalty=1.2
  ```
- **事實性文本**（回答問題）:
  ```python
  temperature=0.7, top_k=40, repetition_penalty=1.1
  ```
- **代碼生成**:
  ```python
  temperature=0.2, top_p=0.9, do_sample=False
  ```

### Q: 顯存不足怎麼辦？

**A: 嘗試以下方法：**
1. 減小批次大小：`batch_size=4`
2. 使用梯度累積：`gradient_accumulation_steps=8`
3. 啟用混合精度：`use_amp=True`
4. 減小模型大小：減少 `embed_dim` 或 `num_layers`

### Q: 如何加快訓練速度？

**A: 優化建議：**
1. 使用混合精度訓練：`use_amp=True`
2. 增加批次大小（如果顯存允許）
3. 使用 GPU：`device="cuda"`
4. 使用多 GPU：實現 DataParallel 或 DistributedDataParallel

### Q: KV Cache 何時使用？

**A: 使用場景：**
- ✅ **推薦使用**：生成長文本（>20 tokens）
- ✅ **推薦使用**：實時對話系統
- ❌ **不推薦**：只生成 1-2 個 tokens
- ❌ **不推薦**：顯存極度受限的環境

## 7. 進階話題

### 使用 Beam Search

```python
from src.bioneuronai.generation_utils import beam_search

best_sequence, best_score = beam_search(
    model,
    input_ids,
    num_beams=5,
    max_length=50,
    early_stopping=True
)
```

### 計算困惑度

```python
from src.bioneuronai.generation_utils import calculate_perplexity

perplexity = calculate_perplexity(model, input_ids)
print(f"Perplexity: {perplexity:.2f}")
```

### 自定義採樣邏輯

```python
from src.bioneuronai.generation_utils import (
    apply_temperature,
    top_k_filtering,
    top_p_filtering
)

# 獲取 logits
logits = model(input_ids)
next_token_logits = logits[:, -1, :]

# 自定義處理
next_token_logits = apply_temperature(next_token_logits, 0.8)
next_token_logits = top_k_filtering(next_token_logits, 50)
next_token_logits = top_p_filtering(next_token_logits, 0.95)

# 採樣
probs = torch.softmax(next_token_logits, dim=-1)
next_token = torch.multinomial(probs, num_samples=1)
```

## 9. 更多資源

- [改進說明](./IMPROVEMENTS.md) - 詳細的改進文檔
- [知識蒸餾訓練指南](./知識蒸餾訓練指南.md) - 高級訓練技巧
- [LLM 指南](./LLM_GUIDE.md) - 語言模型基礎

---

**需要幫助？** 查看 [GitHub Issues](https://github.com/yourusername/BioNeuronai/issues)
