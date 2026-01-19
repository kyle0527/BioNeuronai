# 🚀 快速開始指南

## 5 分鐘上手 BioNeuronAI

---

## 第一步：使用現有模型

### 交互模式（最簡單）
```bash
python use_model.py
```

然後輸入你的問題開始對話！

### 單次生成
```bash
python use_model.py --mode single --prompt "你好，請介紹AI"
```

---

## 第二步：訓練自己的模型

```bash
cd training
python train_with_ai_teacher.py
```

**系統會自動：**
- ✅ 檢查是否已訓練過
- ✅ 使用 AI 生成的高質量數據
- ✅ 記錄完整訓練歷史
- ✅ 保存訓練後的模型

**預計時間**: 約 20 分鐘

---

## 第三步：查看結果

```bash
cd training
python view_training_history.py
```

選擇選項查看：
- 訓練歷史
- 模型對比
- 進度趨勢

---

## 高級功能

### 性能測試
```bash
python use_model.py --mode benchmark
```

### 批次處理
創建 `prompts.txt`:
```
你好
Hello
什麼是AI
```

然後運行：
```bash
python use_model.py --mode batch --prompts-file prompts.txt --output results.json
```

### 質量評估
```bash
python use_model.py --mode eval --prompts-file test_prompts.txt
```

---

## 生成更多訓練數據

```bash
cd training
python data_manager.py
```

自動生成：
- 對話數據
- 知識數據
- 功能性數據（搜索、判斷、推理等）

---

## 自定義訓練

### 編輯訓練數據
```bash
code training/train_with_ai_teacher.py
```

在 `AI_TEACHER_DATA` 中添加你的數據：
```python
"conversations": [
    {"input": "你的問題", "output": "期望回答"},
    # 添加更多...
],
```

### 調整訓練參數
```python
train_with_ai_teacher(
    epochs=30,           # 增加訓練輪數
    batch_size=8,        # 如果記憶體充足
    learning_rate=1e-4,  # 調整學習率
)
```

---

## 常用命令

| 命令 | 功能 |
|------|------|
| `python use_model.py` | 交互對話 |
| `python use_model.py --mode benchmark` | 性能測試 |
| `cd training && python train_with_ai_teacher.py` | 訓練模型 |
| `cd training && python view_training_history.py` | 查看歷史 |
| `cd training && python data_manager.py` | 生成數據 |

---

## 目錄說明

| 目錄 | 說明 | 重要性 |
|------|------|--------|
| `models/tiny_llm_en_zh_trained/` | 訓練後的模型 | ⭐⭐⭐ |
| `training/` | 訓練腳本和記錄 | ⭐⭐⭐ |
| `use_model.py` | 模型使用工具 | ⭐⭐⭐ |
| `weights/` | 權重文件 | ⭐⭐ |
| `src/bioneuronai/` | 核心代碼 | ⭐⭐ |
| `docs/` | 詳細文檔 | ⭐ |

---

## 下一步

1. **如果模型效果不夠好**：
   - 添加更多訓練數據（500-1000 個樣本）
   - 增加訓練輪數（30-50 輪）
   - 使用 `data_manager.py` 生成更多數據

2. **如果想了解更多**：
   - 閱讀 [知識蒸餾訓練指南](docs/知識蒸餾訓練指南.md)
   - 查看 [README.md](README.md) 完整文檔

3. **如果遇到問題**：
   - 檢查 `model_usage.log` 日誌
   - 查看 `training/training_log.json` 訓練記錄

---

## 故障排除

### 問題：記憶體不足
```bash
# 減小批次大小
python training/train_with_ai_teacher.py
# 修改 batch_size=2
```

### 問題：訓練很慢
```bash
# 如果有 NVIDIA GPU，安裝 CUDA 版本 PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 問題：生成質量差
- 需要更多訓練數據（建議 500+ 樣本）
- 增加訓練輪數
- 查看 `view_training_history.py` 確認訓練效果

---

## 配置建議

### 小數據集（< 100 樣本）
```python
epochs=30-50
batch_size=2-4
learning_rate=1e-4
```

### 中等數據集（100-500 樣本）
```python
epochs=10-20
batch_size=4-8
learning_rate=5e-5
```

### 大數據集（> 500 樣本）
```python
epochs=5-10
batch_size=8-16
learning_rate=1e-5
```

---

**開始使用**: `python use_model.py`  
**需要幫助**: 查看 [README.md](README.md) 或 [訓練指南](docs/知識蒸餾訓練指南.md)
