# 🎓 知識蒸餾訓練指南

## 📋 目錄
- [什麼是知識蒸餾](#什麼是知識蒸餾)
- [為什麼使用蒸餾方式](#為什麼使用蒸餾方式)
- [數據準備](#數據準備)
- [訓練流程](#訓練流程)
- [實際操作步驟](#實際操作步驟)
- [進階配置](#進階配置)
- [常見問題](#常見問題)

---

## 🧠 什麼是知識蒸餾

**知識蒸餾 (Knowledge Distillation)** 是一種模型壓縮和訓練技術：

```
老師模型（大型AI/人類專家）
         ↓
    產生高質量數據
         ↓
學生模型（你的小型模型）學習
```

### 優點
✅ **不需要大量標註數據** - AI 老師可以生成高質量樣本  
✅ **訓練速度快** - 小模型在精選數據上學習  
✅ **質量高** - 老師提供的答案經過驗證  
✅ **成本低** - 不需要人工標註大量數據  

### 本項目中的實現
- **老師**: AI 生成的高質量英中雙語對話和知識
- **學生**: TinyLLM (124M 參數)
- **數據**: 精心設計的對話、知識、指令數據

---

## 💡 為什麼使用蒸餾方式

| 傳統訓練 | 知識蒸餾 |
|---------|---------|
| 需要數百萬標註數據 | 只需數千高質量樣本 |
| 訓練時間長（數週） | 訓練時間短（數小時） |
| 需要大量計算資源 | 普通電腦即可 |
| 數據質量參差不齊 | AI 老師保證質量 |

**對於個人或小團隊來說，知識蒸餾是最實際的選擇！**

---

## 📊 數據準備

### 1. 數據格式

在 `train_with_ai_teacher.py` 中，我們使用三種數據類型：

#### A. 對話數據 (Conversations)
```python
{
    "input": "問題或輸入",
    "output": "期望的回答"
}
```

**示例：**
```python
{"input": "你好，你是誰？", "output": "你好！我是一個人工智慧助手，很高興認識你。"}
{"input": "What is AI?", "output": "AI stands for Artificial Intelligence."}
```

#### B. 知識數據 (Knowledge)
直接提供完整的知識陳述：
```python
"人工智慧正在改變世界的方方面面。"
"Machine learning algorithms can learn from data."
```

#### C. 指令數據 (Instructions)
```python
{
    "instruction": "指令或要求",
    "response": "執行結果"
}
```

**示例：**
```python
{
    "instruction": "解釋什麼是深度學習",
    "response": "深度學習是機器學習的一個子領域..."
}
```

### 2. 數據質量要求

| 要求 | 說明 |
|------|------|
| **準確性** | 內容必須正確無誤 |
| **多樣性** | 涵蓋不同主題和句式 |
| **雙語平衡** | 英文和中文數量大致相等 |
| **適當長度** | 單條數據不超過 128 tokens |
| **自然語言** | 使用真實的對話方式 |

### 3. 如何擴充數據

#### 方法一：直接在代碼中添加

編輯 `train_with_ai_teacher.py`，在 `AI_TEACHER_DATA` 中添加：

```python
AI_TEACHER_DATA = {
    "conversations": [
        # 添加更多對話
        {"input": "新問題", "output": "新回答"},
        # ... 可以添加 100-1000 條
    ],
    "knowledge": [
        # 添加更多知識
        "新的知識陳述",
        # ...
    ],
    "instructions": [
        # 添加更多指令
        {"instruction": "做什麼", "response": "怎麼做"},
        # ...
    ],
}
```

#### 方法二：從文件載入

創建 `training_data.json`：
```json
{
  "conversations": [
    {"input": "...", "output": "..."}
  ],
  "knowledge": ["..."],
  "instructions": [
    {"instruction": "...", "response": "..."}
  ]
}
```

然後修改代碼載入：
```python
import json
with open('training_data.json', 'r', encoding='utf-8') as f:
    AI_TEACHER_DATA = json.load(f)
```

### 4. 數據量建議

| 階段 | 樣本數 | 效果 |
|------|--------|------|
| **演示** | 30-50 | 能看到基本學習效果 |
| **原型** | 100-500 | 模型開始有意義的輸出 |
| **實用** | 1,000-5,000 | 可以處理簡單任務 |
| **生產** | 10,000+ | 接近實際應用水準 |

**目前狀態**: 33 個樣本（演示階段）

---

## 🚀 訓練流程

### 完整流程圖

```
1. 準備數據 (AI 老師生成)
         ↓
2. 數據預處理 (分詞、編碼)
         ↓
3. 載入學生模型 (TinyLLM 124M)
         ↓
4. 設置優化器 (AdamW)
         ↓
5. 訓練循環 (20 輪)
    ├─ 前向傳播
    ├─ 計算損失
    ├─ 反向傳播
    └─ 更新權重
         ↓
6. 保存訓練後模型
         ↓
7. 測試生成效果
```

### 訓練參數說明

```python
train_with_ai_teacher(
    model_dir="models/tiny_llm_en_zh",        # 原始模型位置
    output_dir="models/tiny_llm_en_zh_trained", # 輸出位置
    epochs=20,           # 訓練輪數（越多越好，但注意過擬合）
    batch_size=4,        # 批次大小（越大越快，但需要更多記憶體）
    learning_rate=5e-5,  # 學習率（控制學習速度）
    max_length=128,      # 最大序列長度（文本截斷長度）
)
```

#### 參數調整建議

| 參數 | 小數據集 | 大數據集 | 說明 |
|------|---------|---------|------|
| `epochs` | 20-50 | 3-10 | 小數據需要多輪，大數據少輪 |
| `batch_size` | 2-4 | 8-16 | 根據記憶體調整 |
| `learning_rate` | 1e-4 | 5e-5 | 小數據可以高一點 |
| `max_length` | 64-128 | 256-512 | 根據文本長度 |

---

## 🔧 實際操作步驟

### 第一步：檢查環境

```powershell
# 1. 確認在正確目錄
cd C:\D\E\BioNeuronai

# 2. 檢查 Python 版本
python --version  # 應該是 3.8+

# 3. 確認模型存在
dir models\tiny_llm_en_zh\
# 應該看到 pytorch_model.bin, config.json 等 8 個檔案
```

### 第二步：準備數據（可選）

如果要添加自己的數據：

```powershell
# 編輯訓練腳本
code train_with_ai_teacher.py

# 或創建數據文件
code training_data.json
```

在 `AI_TEACHER_DATA` 中添加你的對話、知識或指令。

### 第三步：開始訓練

```powershell
# 執行訓練（使用默認參數）
python train_with_ai_teacher.py
```

**預期輸出：**
```
🎓 知識蒸餾訓練系統
👨‍🏫 AI 老師: 我會用高質量的英中雙語數據教導你的模型

1️⃣ 載入學生模型...
✅ 學生模型: 124,046,592 參數

2️⃣ 準備 AI 老師數據...
📚 AI老師數據: 33 個樣本

3️⃣ 設置訓練參數...
...

4️⃣ 開始訓練...
Epoch 1/20: 100% ... loss=7.45
Epoch 2/20: 100% ... loss=6.25
...
Epoch 20/20: 100% ... loss=1.90

✅ 訓練完成!
```

### 第四步：查看結果

訓練完成後：
```powershell
# 1. 檢查輸出目錄
dir models\tiny_llm_en_zh_trained\

# 應該看到：
# - pytorch_model.bin (訓練後的權重)
# - training_history.json (訓練歷史)
# - 其他配置文件

# 2. 查看訓練歷史
type models\tiny_llm_en_zh_trained\training_history.json
```

### 第五步：測試模型

創建測試腳本 `test_trained_model.py`：
```python
from pathlib import Path
import torch
import json
import sys
sys.path.insert(0, str(Path(__file__).parent / "src" / "bioneuronai"))

from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
from src.bioneuronai.bilingual_tokenizer import BilingualTokenizer

# 載入訓練後的模型
model_path = Path("models/tiny_llm_en_zh_trained")

with open(model_path / "config.json", 'r') as f:
    config_dict = json.load(f)

config = TinyLLMConfig(
    vocab_size=config_dict["vocab_size"],
    max_seq_length=config_dict["max_position_embeddings"],
    embed_dim=config_dict["hidden_size"],
    num_heads=config_dict["num_attention_heads"],
    num_layers=config_dict["num_hidden_layers"],
)

model = TinyLLM(config)
weights = torch.load(model_path / "pytorch_model.bin", map_location='cpu')
model.load_state_dict(weights)
model.eval()

tokenizer = BilingualTokenizer.load(model_path / "tokenizer.pkl")

# 測試
def test_generation(prompt, max_tokens=30):
    print(f"\n提示: {prompt}")
    ids = tokenizer.encode(prompt, add_special_tokens=False)[:20]
    input_tensor = torch.tensor([ids])
    
    with torch.no_grad():
        output = model.generate(input_tensor, max_new_tokens=max_tokens, temperature=0.7)
    
    text = tokenizer.decode(output[0].tolist(), skip_special_tokens=True)
    print(f"生成: {text}")

# 測試各種提示
test_generation("你好")
test_generation("Hello")
test_generation("What is")
test_generation("什麼是")
```

執行：
```powershell
python test_trained_model.py
```

---

## ⚙️ 進階配置

### 1. 繼續訓練（增量訓練）

如果想在現有模型上繼續訓練：

```python
train_with_ai_teacher(
    model_dir="models/tiny_llm_en_zh_trained",  # 使用已訓練的模型
    output_dir="models/tiny_llm_en_zh_trained_v2",
    epochs=10,  # 再訓練 10 輪
)
```

### 2. 調整訓練強度

#### 保守訓練（防止過擬合）
```python
epochs=10
learning_rate=1e-5  # 較低的學習率
```

#### 激進訓練（快速學習）
```python
epochs=50
learning_rate=1e-4  # 較高的學習率
```

### 3. 使用 GPU 加速

如果有 NVIDIA GPU：
```powershell
# 安裝 CUDA 版本的 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

代碼會自動檢測並使用 GPU。

### 4. 批次訓練大量數據

如果數據很多（如 10,000+ 樣本）：

```python
train_with_ai_teacher(
    epochs=5,          # 減少輪數
    batch_size=16,     # 增大批次（如果記憶體允許）
    max_length=256,    # 支持更長文本
)
```

---

## 📈 監控訓練進度

### 關鍵指標

1. **Loss (損失值)**
   - 初始值：通常 7-10
   - 目標值：< 2.0 表示模型在學習
   - 理想值：< 1.0 表示學習良好

2. **Perplexity (困惑度)**
   - 初始值：數百到數千
   - 目標值：< 20 表示基本可用
   - 理想值：< 10 表示質量不錯

### 訓練進度示例

```
Epoch 1  - Loss: 7.45, Perplexity: 1722.79  ⚪ 剛開始
Epoch 5  - Loss: 4.58, Perplexity: 97.26    🟡 開始學習
Epoch 10 - Loss: 3.50, Perplexity: 33.09    🟢 學習中
Epoch 15 - Loss: 2.65, Perplexity: 14.19    🟢 不錯
Epoch 20 - Loss: 1.90, Perplexity: 6.71     ✅ 很好
```

### 判斷訓練效果

✅ **訓練成功的標誌：**
- Loss 持續下降
- Perplexity 持續降低
- 生成的文本開始有意義
- 能回應簡單提示

⚠️ **需要調整的情況：**
- Loss 不下降 → 增加學習率或檢查數據
- Loss 震盪 → 降低學習率
- Loss 下降後上升 → 過擬合，停止訓練
- 生成重複內容 → 需要更多樣化的數據

---

## 🎯 最佳實踐

### 數據準備建議

1. **從小開始**
   - 先用 50-100 個高質量樣本測試
   - 確認模型能學習後再擴充

2. **注重質量而非數量**
   - 30 個精心設計的樣本 > 100 個低質量樣本
   - AI 老師提供的數據要檢查準確性

3. **保持雙語平衡**
   ```
   理想比例：
   - 英文：45-50%
   - 中文：45-50%
   - 混合：5-10%
   ```

4. **多樣化主題**
   - 日常對話 (30%)
   - 知識問答 (30%)
   - 指令執行 (20%)
   - 特定領域 (20%)

### 訓練策略

1. **分階段訓練**
   ```
   階段一：基礎對話 (100 樣本, 20 輪)
   階段二：增加知識 (+200 樣本, 10 輪)
   階段三：專業內容 (+300 樣本, 10 輪)
   ```

2. **定期檢查點**
   - 每 5-10 輪保存一次模型
   - 測試生成效果
   - 根據效果調整策略

3. **漸進式難度**
   - 簡單對話 → 複雜對話
   - 短句子 → 長句子
   - 單一主題 → 多主題

---

## ❓ 常見問題

### Q1: 訓練需要多長時間？
**A:** 取決於數據量和硬件：
- 33 樣本，20 輪：約 8-10 分鐘（CPU）
- 1000 樣本，10 輪：約 2-3 小時（CPU）
- 使用 GPU 可快 5-10 倍

### Q2: 記憶體不足怎麼辦？
**A:** 減小 `batch_size`：
```python
batch_size=2  # 或甚至 1
```

### Q3: Loss 不下降？
**A:** 可能原因：
1. 學習率太低 → 試試 `learning_rate=1e-4`
2. 數據太少 → 至少需要 50+ 樣本
3. 數據質量差 → 檢查 AI 老師數據

### Q4: 生成的文本很奇怪？
**A:** 這是正常的！
- 小數據量（< 100）：只能學到基本模式
- 需要 500-1000+ 樣本才能生成合理文本
- 繼續添加數據並訓練

### Q5: 如何知道訓練夠了？
**A:** 觀察指標：
- Loss < 2.0 且穩定
- Perplexity < 10
- 生成文本開始有意義
- 測試提示能得到合理回應

### Q6: 可以在訓練好的模型上繼續訓練嗎？
**A:** 可以！使用增量訓練：
```python
model_dir="models/tiny_llm_en_zh_trained"  # 已訓練的模型
```

### Q7: 如何評估模型質量？
**A:** 三個方法：
1. **數值指標**: Loss 和 Perplexity
2. **生成測試**: 用不同提示測試生成
3. **實際應用**: 嘗試真實任務

---

## 📚 參考資源

### 本項目文件
- [README.md](README.md) - 項目總覽
- [how_to_use.py](how_to_use.py) - 使用示例
- [train_with_ai_teacher.py](train_with_ai_teacher.py) - 訓練腳本

### 代碼結構
```
models/tiny_llm_en_zh/          # 原始模型
models/tiny_llm_en_zh_trained/  # 訓練後模型
src/bioneuronai/
  ├── tiny_llm.py               # 模型定義
  └── bilingual_tokenizer.py    # 分詞器
```

### 擴展學習
- 知識蒸餾論文: "Distilling the Knowledge in a Neural Network"
- Transformer 架構: "Attention Is All You Need"
- GPT 系列: OpenAI GPT-2/GPT-3 技術報告

---

## 🚀 下一步

現在你已經了解如何使用知識蒸餾訓練模型了！

**立即開始：**
```powershell
# 1. 執行基礎訓練
python train_with_ai_teacher.py

# 2. 測試結果
python test_trained_model.py

# 3. 添加更多數據（可選）
code train_with_ai_teacher.py  # 編輯 AI_TEACHER_DATA

# 4. 繼續訓練
python train_with_ai_teacher.py  # 在更多數據上訓練
```

**建議路徑：**
1. ✅ 完成基礎訓練（已完成）
2. 📝 添加 100-200 個高質量樣本
3. 🔄 再訓練 10-20 輪
4. 🧪 測試各種場景
5. 🎯 根據需求優化數據和參數

**祝訓練順利！** 🎓

---

*最後更新: 2026年1月19日*
