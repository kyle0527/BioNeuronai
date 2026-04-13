# 自然語言處理（NLP）訓練指南

## 📑 目錄

1. 📁 訓練腳本位置
2. 🎯 訓練腳本說明
3. 🚀 快速開始訓練
4. 📊 訓練數據準備
5. 🔧 訓練配置優化
6. 📈 監控訓練進度
7. 🎯 訓練最佳實踐
8. 🔗 相關資源
9. ⚠️ 常見問題
10. 📞 技術支援

---

## 📁 訓練腳本位置

### 活躍的訓練模組
位於：`src/nlp/training/`

```
src/nlp/training/
├── unified_trainer.py            # ⭐ 統一訓練入口（推薦，語言+訊號多任務）
├── advanced_trainer.py           # 底層 Trainer 類別（由 unified_trainer 呼叫）
├── build_vocab.py                # 詞彙建立腳本（訓練前必須先執行）
├── trading_dialogue_data.py      # 語言任務訓練語料（QA 對）
├── train_with_ai_teacher.py      # AI 教師知識蒸餾訓練（補充用）
├── auto_evolve.py                # 增量進化訓練（補充用）
├── data_manager.py               # 訓練數據管理
├── view_training_history.py      # 查看訓練歷史
└── training_log.json             # 訓練日誌
```

### 歸檔的訓練資源
位於：`archived/llm_development/training/`
（包含早期版本和實驗性訓練腳本）

## 🎯 訓練腳本說明

### 1. advanced_trainer.py ⭐ 推薦使用

**最完整的訓練系統，包含所有高級功能**

**功能特性：**
- ✅ 梯度累積（Gradient Accumulation）
- ✅ 混合精度訓練（AMP）
- ✅ 學習率調度器（Cosine/Linear/Constant）
- ✅ 梯度裁剪（Gradient Clipping）
- ✅ 自動保存檢查點
- ✅ TensorBoard 日誌
- ✅ 訓練/驗證評估

**使用方法：**

```python
from src.nlp.training.advanced_trainer import Trainer, TrainingConfig
from src.nlp.tiny_llm import TinyLLM, TinyLLMConfig
from torch.utils.data import DataLoader

# 1. 配置訓練參數
train_config = TrainingConfig(
    batch_size=8,
    gradient_accumulation_steps=4,  # 有效批次大小 = 8 * 4 = 32
    max_epochs=10,
    learning_rate=3e-4,
    use_amp=True,                   # 混合精度加速
    lr_scheduler_type="cosine",     # 餘弦學習率調度
    warmup_steps=500,
    eval_steps=500,
    save_steps=1000
)

# 2. 初始化模型
model_config = TinyLLMConfig(vocab_size=30000)
model = TinyLLM(model_config)

# 3. 準備數據加載器
# train_dataloader = DataLoader(...)
# eval_dataloader = DataLoader(...)

# 4. 開始訓練
trainer = Trainer(
    model=model,
    train_config=train_config,
    train_dataloader=train_dataloader,
    eval_dataloader=eval_dataloader,
    output_dir="models/trained_model"
)

trainer.train()
```

### 2. train_with_ai_teacher.py

**知識蒸餾訓練（使用 AI 教師）**

**功能特性：**
- 使用大型模型（教師）指導小型模型（學生）
- 自動生成高質量訓練數據
- 適合冷啟動訓練

**使用方法：**

```python
from src.nlp.training.train_with_ai_teacher import train_with_ai_teacher

# 執行 AI 教師訓練
train_with_ai_teacher(
    model_dir="src/nlp/models/tiny_llm_en_zh",           # 基礎模型
    output_dir="src/nlp/models/tiny_llm_en_zh_trained",  # 輸出目錄
    epochs=10,
    batch_size=4,
    learning_rate=5e-5,
    max_length=128,
    force_retrain=False  # True = 重新訓練
)
```

**訓練數據來源：**
- 內建英中雙語知識庫
- AI 生成的對話數據
- 領域知識蒸餾

### 3. auto_evolve.py

**自動進化訓練（增量學習）**

**功能特性：**
- 基於已訓練模型繼續訓練
- 使用新數據進行增量更新
- 保留原有知識，學習新知識

**使用方法：**

```python
from src.nlp.training.auto_evolve import auto_evolve_training

# 進化訓練
auto_evolve_training(
    model_path="src/nlp/models/tiny_llm_en_zh_trained",
    evolution_data_file="evolution_data/new_training_data.json",
    output_path="src/nlp/models/tiny_llm_evolved",
    num_epochs=3,
    batch_size=4,
    learning_rate=1e-5  # 更小的學習率保護已有知識
)
```

**evolution_data 格式：**
```json
[
    {
        "prompt": "什麼是加密貨幣？",
        "response": "加密貨幣是使用加密技術保護交易的數字貨幣..."
    },
    {
        "prompt": "Explain blockchain",
        "response": "Blockchain is a distributed ledger technology..."
    }
]
```

### 4. view_training_history.py

**查看訓練歷史和進度**

```bash
# 查看訓練歷史
cd src/nlp/training
python view_training_history.py
```

**顯示信息：**
- 訓練版本歷史
- Loss 和 Perplexity 變化
- 訓練時長統計
- 數據集信息
- 性能改進趨勢

## 🚀 快速開始訓練

### 方案 A（推薦）：統一訓練入口

`unified_trainer.py` 是目前的正式訓練入口，同時訓練語言對話與交易訊號兩個任務，使用同一份 TinyLLM 權重。

```bash
# 步驟 0：建立詞彙（首次訓練必做，約 10 秒）
python -m nlp.training.build_vocab

# 步驟 1：語言任務預熱（讓 backbone 先學語言結構）
python -m nlp.training.unified_trainer --lm-only --epochs 20

# 步驟 2（可選）：產生訊號訓練資料（需要有歷史 K 線）
python -m bioneuronai.cli.main collect-signal-data --symbol BTCUSDT --interval 1h

# 步驟 3：多任務精調（語言 + 訊號同時優化）
python -m nlp.training.unified_trainer \
    --signal-data data/signal_history.jsonl --epochs 10

# 輸出：model/my_100m_model.pth（正式交易 checkpoint）
```

**完整 CLI 參數：**
```bash
python -m nlp.training.unified_trainer --help
  --lm-only          只訓練語言任務
  --sig-only         只訓練訊號任務
  --epochs N         訓練輪數（預設 10）
  --batch N          批次大小（預設 8）
  --lr FLOAT         學習率（預設 3e-4）
  --signal-data PATH 訊號 JSONL 路徑（正式訓練必填）
  --no-save          不覆寫 model/my_100m_model.pth
```

### 方案 B：使用 AI 教師知識蒸餾（補充用）

```bash
cd src/nlp/training
python train_with_ai_teacher.py --allow-demo-data
```

**注意：** 這條目前只適合開發驗證。內建資料是通用示範樣本，不應視為正式交易語料。

### 方案 C：使用自定義數據訓練（進階）

```python
# train_custom.py
from src.nlp.training.advanced_trainer import Trainer, TrainingConfig
from src.nlp.tiny_llm import TinyLLM, TinyLLMConfig
from src.nlp.bilingual_tokenizer import BilingualTokenizer
from torch.utils.data import Dataset, DataLoader
import torch

# 1. 準備自定義數據集
class CustomDataset(Dataset):
    def __init__(self, texts, tokenizer, max_length=128):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        tokens = self.tokenizer.encode(text)[:self.max_length]
        return torch.tensor(tokens)

# 2. 載入數據
with open("training_data/my_texts.txt", "r", encoding="utf-8") as f:
    texts = [line.strip() for line in f if line.strip()]

# 3. 初始化 tokenizer
tokenizer = BilingualTokenizer(vocab_size=30000)
tokenizer.build_vocab(texts)

# 4. 創建數據集
train_dataset = CustomDataset(texts[:int(len(texts)*0.9)], tokenizer)
eval_dataset = CustomDataset(texts[int(len(texts)*0.9):], tokenizer)

train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
eval_loader = DataLoader(eval_dataset, batch_size=8)

# 5. 訓練
config = TinyLLMConfig(vocab_size=30000)
model = TinyLLM(config)

trainer = Trainer(
    model=model,
    train_config=TrainingConfig(
        batch_size=8,
        max_epochs=5,
        learning_rate=3e-4,
        use_amp=True
    ),
    train_dataloader=train_loader,
    eval_dataloader=eval_loader,
    output_dir="models/my_trained_model"
)

trainer.train()
```

### 方案 D：增量訓練（基於已有模型）

```bash
# 1. 準備新的訓練數據
# 創建 evolution_data/new_data.json

# 2. 執行進化訓練
cd src/nlp/training
python -c "
from auto_evolve import auto_evolve_training
auto_evolve_training(
    model_path='model/my_100m_model.pth',
    evolution_data_file='../../evolution_data/new_data.json',
    output_path='model/my_100m_model_evolved.pth'
)
"

# 3. 測試進化模型
python -c "
import torch
from nlp.tiny_llm import TinyLLM, TinyLLMConfig
cfg = TinyLLMConfig(use_numeric_mode=True)
model = TinyLLM(cfg)
state = torch.load('model/my_100m_model.pth', map_location='cpu', weights_only=True)
model.load_state_dict(state, strict=False)
model.eval()
print('模型載入成功')
"
```

## 📊 訓練數據準備

### 數據格式要求

#### 1. 純文本數據（用於語言建模）
```
training_data/texts.txt
---
這是第一個句子。
這是第二個句子。
This is an English sentence.
這是中英混合 mixed text。
```

#### 2. 對話數據（用於知識蒸餾）
```json
// training_data/conversations.json
[
    {
        "prompt": "什麼是 AI？",
        "response": "AI（人工智慧）是讓機器模擬人類智能的技術..."
    },
    {
        "prompt": "How to train a model?",
        "response": "Training a model involves feeding data..."
    }
]
```

#### 3. 交易領域特定數據（推薦）
```json
// training_data/trading_knowledge.json
[
    {
        "prompt": "什麼是趨勢跟隨策略？",
        "response": "趨勢跟隨策略是順著市場主要趨勢方向交易..."
    },
    {
        "prompt": "解釋 MACD 指標",
        "response": "MACD 是移動平均收斂發散指標，用於判斷趨勢強度..."
    },
    {
        "prompt": "如何設置止損？",
        "response": "止損設置應考慮：1) ATR波動率 2) 支撐位/壓力位..."
    }
]
```

### 數據採集建議

**針對交易系統：**
1. **市場分析報告**: 收集技術分析、基本面分析文章
2. **交易策略文檔**: 各種交易策略的說明和案例
3. **風險管理知識**: 資金管理、倉位管理相關內容
4. **指標解釋**: MACD、RSI、EMA 等技術指標說明
5. **交易日誌**: 實際交易的分析和總結

**數據來源：**
- 交易論壇和社區
- 技術分析書籍
- 交易課程講義
- 專業交易員的分享
- 本項目的 `docs/` 目錄

## 🔧 訓練配置優化

### GPU 記憶體優化

```python
# 小顯存 GPU (< 8GB)
TrainingConfig(
    batch_size=2,
    gradient_accumulation_steps=16,  # 有效批次大小 = 32
    use_amp=True,                    # 混合精度減少顯存
    max_grad_norm=1.0
)

# 中等顯存 GPU (8-16GB)
TrainingConfig(
    batch_size=8,
    gradient_accumulation_steps=4,
    use_amp=True
)

# 大顯存 GPU (> 16GB)
TrainingConfig(
    batch_size=16,
    gradient_accumulation_steps=2,
    use_amp=False  # 可不用混合精度
)
```

### 學習率調度策略

```python
# Cosine 調度（推薦）- 平滑下降
TrainingConfig(
    learning_rate=3e-4,
    lr_scheduler_type="cosine",
    warmup_steps=500
)

# Linear 調度 - 線性下降
TrainingConfig(
    learning_rate=3e-4,
    lr_scheduler_type="linear",
    warmup_steps=500
)

# Constant - 固定學習率
TrainingConfig(
    learning_rate=1e-4,
    lr_scheduler_type="constant"
)
```

## 📈 監控訓練進度

### TensorBoard 監控

```bash
# 啟動 TensorBoard
tensorboard --logdir=runs/

# 瀏覽器訪問
# http://localhost:6006
```

### 訓練日誌

```python
# 查看實時訓練日誌
tail -f training_log.json

# Python 查看
from src.nlp.training.view_training_history import load_training_log
log = load_training_log()
print(f"當前版本: v{log['current_version']}")
print(f"總訓練次數: {len(log['training_history'])}")
```

## 🎯 訓練最佳實踐

### 1. 訓練前檢查清單

- [ ] 確認有足夠的訓練數據（建議 > 1000 樣本）
- [ ] 檢查數據質量（無亂碼、格式正確）
- [ ] 選擇合適的批次大小和學習率
- [ ] 確保有足夠的磁碟空間保存檢查點
- [ ] 設置合理的評估和保存間隔

### 2. 訓練中監控指標

- **Loss**: 應該持續下降
- **Perplexity**: 越低越好（< 10 為佳）
- **Gradient Norm**: 避免梯度爆炸
- **Learning Rate**: 觀察調度是否正常

### 3. 訓練後評估

```python
# 測試生成質量
import torch
from nlp.tiny_llm import TinyLLM, TinyLLMConfig
from nlp.bilingual_tokenizer import BilingualTokenizer

cfg = TinyLLMConfig(use_numeric_mode=True)
model = TinyLLM(cfg)
state = torch.load("model/my_100m_model.pth", map_location="cpu", weights_only=True)
model.load_state_dict(state, strict=False)
model.eval()

test_prompts = [
    "什麼是趨勢？",
    "如何使用 MACD？",
    "止損設置建議"
]

for prompt in test_prompts:
    output = model.generate(prompt, max_length=50)
    print(f"輸入: {prompt}")
    print(f"輸出: {output}\n")
```

## 🔗 相關資源

### 模型文件位置
- **交易模型權重**: `model/my_100m_model.pth`（目前正式交易 checkpoint）
- **Chat / TinyLLM 權重**: `model/tiny_llm_100m.pth`
- **分詞器詞彙**: `model/tokenizer/vocab.json`（由 `build_vocab.py` 產生）

### 工具腳本
- **模型導出**: `src/nlp/model_export.py`
- **量化工具**: `src/nlp/quantization.py`
- **推理工具**: `src/nlp/inference_utils.py`

### 文檔
- **NLP 模組說明**: `src/nlp/README.md`
- **模型架構**: `src/nlp/tiny_llm.py`
- **分詞器**: `src/nlp/bilingual_tokenizer.py`

## ⚠️ 常見問題

### Q: 訓練過程中 Loss 不下降？
**A:** 
- 檢查學習率是否過小（嘗試 3e-4）
- 增加訓練數據量
- 確認數據質量
- 檢查梯度是否正常更新

### Q: Out of Memory 錯誤？
**A:**
- 減小 `batch_size`
- 增加 `gradient_accumulation_steps`
- 啟用 `use_amp=True`
- 減小 `max_length`

### Q: 訓練速度太慢？
**A:**
- 啟用混合精度訓練 (`use_amp=True`)
- 使用 GPU 而非 CPU
- 增大批次大小
- 減少評估頻率

### Q: 如何在交易系統中使用訓練的模型？
**A:**
訓練完成後，`model/my_100m_model.pth` 目前主要供交易訊號推論使用：

- **交易訊號推論**：`InferenceEngine` 在 `trading_engine.py` 啟動時自動載入，透過 16 步滾動視窗輸出 512 維訊號向量
- **自然語言對話**：`ChatEngine` 預設載入 `model/tiny_llm_100m.pth`；若要測試其他 TinyLLM checkpoint，需顯式指定

手動驗證：
```python
from nlp.chat_engine import create_chat_engine

engine = create_chat_engine(model_path="model/tiny_llm_100m.pth", language="zh")
if engine:
    response = engine.chat("BTC 現在適合做多嗎？")
    print(response.text)
else:
    print("模型未載入，請先確認 model/tiny_llm_100m.pth 存在")
```

## 📞 技術支援

遇到訓練問題：
1. 查看訓練日誌 `training_log.json`
2. 運行 `python view_training_history.py` 診斷
3. 檢查數據格式是否正確
4. 參考 `archived/llm_development/` 中的範例

---

**最後更新**: 2026-04-07
**版本**: v2.1
**維護者**: BioNeuronAI Team
