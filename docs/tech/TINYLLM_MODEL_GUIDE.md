# TinyLLM 模型技術指南

**版本**: v2.2  
**更新日期**: 2026-04-06  
**適用對象**: 開發者、訓練工程師、系統整合者

---

## 📑 目錄

1. 模型定位
2. 架構總覽
3. 參數量計算
4. 雙模態設計說明
5. 推論路徑與資料流
6. 與系統各模組的整合方式
7. 訓練策略
8. 目前狀態與待完成事項

---

## 1. 模型定位

TinyLLM 是 BioNeuronai 的**核心 AI 模型**，設計目標是「一份權重，服務兩個任務」：

| 任務 | 輸入 | 輸出 | 對應系統模組 |
|------|------|------|------------|
| **交易訊號預測** | 最近 16 根 K 線的 1024 維特徵序列 | 512 維訊號向量 | `InferenceEngine` → `SignalInterpreter` |
| **自然語言對話** | 文字 token IDs | 下一個 token 的機率分布 | `ChatEngine` → CLI `chat` / API `/api/v1/chat` |

這兩個任務**共用同一個 Transformer backbone**（12 層）。不同的是輸入路徑：數值特徵經 `numeric_proj` 投影後進入 Transformer；文字 token 經 `token_embedding` 進入。

---

## 2. 架構總覽

```
┌─────────────────────────────────────────────────────────────────┐
│                         TinyLLM                                 │
│                                                                  │
│  ┌──────────────────┐          ┌───────────────────────────┐   │
│  │  文字路徑         │          │  數值路徑（交易訊號）       │   │
│  │                  │          │  use_numeric_mode=True     │   │
│  │  token_ids       │          │  features (B, T, 1024)     │   │
│  │      ↓           │          │      ↓                     │   │
│  │  token_embedding │          │  numeric_proj (2-layer)    │   │
│  │  (vocab×768)     │          │  L(1024→1536)+GELU+LN      │   │
│  │      ↓           │          │  →L(1536→768)+LN           │   │
│  │  + pos_embedding │          │      ↓                     │   │
│  └────────┬─────────┘          │  + pos_embedding(0..T-1)  │   │
│           │                    └───────────┬────────────────┘   │
│           └─────────────┬─────────────────┘                     │
│                         ↓                                        │
│          ┌──────────────────────────────┐                        │
│          │   Transformer Backbone       │                        │
│          │   12 × TransformerBlock      │                        │
│          │                              │                        │
│          │   每個 Block：                │                        │
│          │   ├ LayerNorm                │                        │
│          │   ├ MultiHeadAttention       │                        │
│          │   │  (12 heads, 64d/head)    │                        │
│          │   ├ LayerNorm                │                        │
│          │   └ FeedForward (768→3072→768)│                       │
│          └──────────────┬───────────────┘                        │
│                         ↓                                        │
│                    LayerNorm (ln_f)                              │
│                         ↓                                        │
│           ┌─────────────┴──────────────┐                        │
│           ↓                            ↓                        │
│  ┌────────────────┐         ┌─────────────────────┐             │
│  │  lm_head       │         │  signal_head        │             │
│  │  Linear(768    │         │  Linear(768→512)    │             │
│  │  →vocab_size)  │         │                     │             │
│  │  (共享 token   │         │  取 T=-1 最後時間步  │             │
│  │   embedding 權重│         │  的輸出             │             │
│  └────────────────┘         └─────────────────────┘             │
│       ↓                              ↓                           │
│  next token logits            signal output (512d)               │
│  (用於語言生成)                (傳入 SignalInterpreter)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 參數量計算

### 預設配置（`vocab_size=30000, use_numeric_mode=True`）

| 模組 | 計算 | 參數量 |
|------|------|--------|
| `token_embedding` | 30,000 × 768 | 23,040,000 |
| `position_embedding` | 512 × 768 | 393,216 |
| `blocks` × 12 | 見下表 | 84,934,656 |
| `ln_f` | 768 × 2 | 1,536 |
| `lm_head` | 共享 token_embedding 權重 | **0（額外）** |
| `numeric_proj` | L(1024→1536)+GELU+LN + L(1536→768)+LN | 2,759,424 |
| `signal_head` | Linear(768→512) + bias | 393,728 |
| **合計** | | **~111.6M** |

### 每個 TransformerBlock（×12）

| 子模組 | 計算 | 參數量 |
|------|------|--------|
| `ln1` | 768 × 2 | 1,536 |
| `attn.qkv_proj` | 768 × (3×768) | 1,769,472 |
| `attn.out_proj` | 768 × 768 | 589,824 |
| `ln2` | 768 × 2 | 1,536 |
| `ffn.fc1` | 768 × 3072 | 2,359,296 |
| `ffn.fc2` | 3072 × 768 | 2,359,296 |
| **每層合計** | | **7,080,960** |
| **12 層合計** | | **84,971,520** |

### 記憶體佔用估算

| 精度 | 記憶體 | 適用場景 |
|------|--------|---------|
| float32（訓練用） | ~440 MB | 訓練、首次驗證 |
| float16 / bfloat16 | ~220 MB | GPU 推論加速 |
| int8 量化（可選） | ~110 MB | 低資源部署 |

### 推論延遲估算（`forward_signal`，T=16，batch=1）

| 硬體 | 預估延遲 | 備注 |
|------|---------|------|
| CPU（現代 i7/Ryzen 5） | 50–120 ms | 可接受，目前系統設計允許 |
| GPU RTX 3060+ | 5–15 ms | warmup 後穩定 |
| GPU 加上 bfloat16 | 3–8 ms | 推薦部署精度 |

---

## 4. 雙模態設計說明

### 為什麼要共用 Transformer？

過去兩個任務各自獨立：
- `HundredMillionModel`：純 MLP，只看當前 1 步特徵
- `TinyLLM`：GPT，只用於語言，從未訓練

問題：維護兩套模型、兩套訓練流程、兩份權重檔案，且 MLP 完全無法利用時序上下文。

現在共用 backbone 的好處：
1. **時序建模**：Transformer Attention 學習「前 N 根 K 線如何影響當前判斷」
2. **語言–市場知識遷移**：語言訓練讓模型理解市場描述（如新聞語義）；訊號訓練讓模型理解市場數值型態，兩者在 backbone 中互相強化
3. **維護成本減半**：一個模型檔案、一套訓練系統、一套部署流程

### 數值特徵如何進入 Transformer

```
FeaturePipeline.build_features()
    → 1024 維 numpy array（每個時間步）
    → InferenceEngine._feature_buffer 累積最近 16 步
    → np.stack → (16, 1024) ndarray
    → Predictor.predict() → torch tensor (1, 16, 1024)
    → TinyLLM.forward_signal()
        → numeric_proj: L(1024→1536)+GELU+LN → L(1536→768)+LN
        → + position_embedding(0..15)
        → Transformer backbone（12 層 Attention）
        → ln_f
        → signal_head: Linear(768→512)
        → (1, 512) tensor
    → SignalInterpreter.interpret()
        → TradingSignal（方向、信心、槓桿建議、停損停利）
```

### 文字如何進入 Transformer

```
ChatEngine.chat(user_message)
    → ConversationHistory.build_prompt()
    → BilingualTokenizer.encode() → token IDs
    → TinyLLM.forward(input_ids)
        → token_embedding + position_embedding
        → Transformer backbone（同一組 12 層）
        → ln_f
        → lm_head（共享 token_embedding 權重）
        → logits (seq_len, vocab_size)
    → top-k/top-p 採樣 → 生成回應文字
```

---

## 5. 推論路徑與資料流

### 5.1 交易訊號推論流程

```
即時行情 (WebSocket)
    ↓
BinanceFuturesConnector
    ↓
TradingEngine._handle_market_update()
    ↓
InferenceEngine.predict(symbol, price, klines, ...)
    ├── FeaturePipeline.build_features() → 1024d 當步特徵
    ├── _feature_buffer.append()         → deque(maxlen=16) 滾動視窗
    ├── np.stack(buffer) → (16, 1024)
    └── Predictor.predict((16, 1024))
            ↓
        TinyLLM.forward_signal(tensor(1, 16, 1024))
            ↓
        (1, 512) 輸出
            ↓
        SignalInterpreter.interpret() → TradingSignal
    ↓
TradingEngine._fuse_signals()       ← 與策略層訊號融合
    ↓
RiskManagement → 倉位計算
    ↓
BinanceFuturesConnector.place_order()
```

### 5.2 對話推論流程

```
使用者輸入（CLI / API）
    ↓
ChatEngine.chat(user_message, market_ctx)
    ├── detect_language() → zh / en
    ├── MarketContext.to_context_str() → 附加市場資訊（可選）
    ├── ConversationHistory.add() + build_prompt()
    └── TinyLLM.generate(input_ids)   ← 文字生成模式
            ↓
        next token 逐步採樣
            ↓
        BilingualTokenizer.decode()
            ↓
        ChatResponse（含信心度、語言、延遲）
    ↓
輸出至 CLI / REST API
```

---

## 6. 與系統各模組的整合方式

### 6.1 整合地圖

```
src/bioneuronai/core/inference_engine.py
    ModelLoader.load_model()
    └── 使用 TinyLLMConfig(use_numeric_mode=True)
    └── 載入 model/my_100m_model.pth
    └── Predictor.predict() 呼叫 model.forward_signal()

src/nlp/chat_engine.py
    create_chat_engine()
    └── 使用相同 TinyLLMConfig(use_numeric_mode=True)
    └── 載入同一個 model/my_100m_model.pth
    └── ChatEngine.chat() 呼叫 model.generate()
```

**重點：兩處載入的是同一個檔案 `model/my_100m_model.pth`**

### 6.2 各模組調用規則

| 調用者 | 使用方法 | 注意事項 |
|--------|---------|---------|
| `InferenceEngine` | `model.forward_signal(tensor)` | 需要 `use_numeric_mode=True` |
| `ChatEngine` | `model.generate(input_ids)` | 不需要 `use_numeric_mode`，但加了也無妨 |
| `Predictor` | 透過 `InferenceEngine` | 不直接呼叫 TinyLLM |
| `BacktestEngine` | 透過 `TradingEngine` → `InferenceEngine` | 換 episode 前需呼叫 `reset_buffer()` |
| 訓練腳本 | 直接操作 `TinyLLM` | 見第 7 節 |

### 6.3 回測中的特殊處理

回測每個 episode 開始時，必須清空滾動視窗，否則上一個 episode 的特徵會污染當前推論：

```python
# backtest/backtest_engine.py 在每個 episode 開始時：
engine.inference_engine.reset_buffer()
```

### 6.4 模型檔案規範

```
model/
├── my_100m_model.pth     ← 正式模型權重（InferenceEngine + ChatEngine 共用）
├── tokenizer/
│   └── vocab.json        ← BilingualTokenizer 詞彙（由 build_vocab.py 產生）
└── checkpoints/          ← 訓練過程中的檢查點（不直接用於推論）
    ├── checkpoint-1000/
    │   ├── model.pth
    │   └── config.json
    └── best_model/
        ├── model.pth
        └── config.json
```

---

## 7. 訓練策略

### 7.1 訓練任務對照

| 任務 | 訓練資料來源 | Loss 函數 | 輸入 | 標籤 |
|------|------------|---------|------|------|
| 語言任務 | `trading_dialogue_data.py` QA 對 | CrossEntropyLoss（next-token） | token IDs | 位移一位的 token IDs |
| 訊號任務 | 回測歷史 JSONL | MSELoss | `(B, 16, 1024)` 特徵序列 | `(B, 512)` SignalInterpreter 格式 |

### 7.2 多任務合併 Loss

```
total_loss = lm_loss + signal_loss_weight × signal_loss
           = lm_loss + 0.5 × signal_loss   （預設）
```

`signal_loss_weight` 可以調整：
- 提高（→1.0）：更重視訊號準確度，可能犧牲語言流暢度
- 降低（→0.1）：語言優先，訊號任務輔助

### 7.3 建議訓練順序

```
階段一（語言預熱）：
    python -m nlp.training.unified_trainer --lm-only --epochs 20
    → 先讓 backbone 學習語言結構，穩定 embedding 空間

階段二（訊號對齊）：
    python -m nlp.training.unified_trainer --sig-only \
        --signal-data data/signal_history.jsonl --epochs 10
    → 用真實回測資料校準數值路徑

階段三（多任務精調）：
    python -m nlp.training.unified_trainer \
        --signal-data data/signal_history.jsonl --epochs 10
    → 兩個任務共同精調，讓 backbone 真正融合兩種知識
```

### 7.4 訊號標籤如何生成

訊號標籤來自回測系統的歷史輸出，格式為 JSONL，每行一筆：

```json
{
    "features": [[f1...f1024], [f1...f1024], ...(共 16 行)],
    "signal":   [s1, s2, ..., s512]
}
```

生成方式（已實作於 `backtest/service.py::collect_signal_training_data()`）：

```bash
# 執行回測並輸出 JSONL
python -m bioneuronai.cli.main collect-signal-data \
    --symbol BTCUSDT --interval 1h \
    --start-date 2024-01-01 --end-date 2024-12-31
# 輸出：data/signal_history.jsonl（預設）
```

1. 回測 replay 每根 K 線後，`FeaturePipeline` 提取 1024 維特徵
2. `deque(maxlen=16)` 維護滾動視窗，累積至 16 步後輸出一筆
3. 若 `InferenceEngine` 已載入，`signal` 欄位為模型推論值；否則填零向量
4. 寫入 `data/signal_history.jsonl`，可直接作為 `unified_trainer --signal-data` 的輸入

---

## 8. 目前狀態與待完成事項

### 8.1 已完成

| 項目 | 狀態 |
|------|------|
| TinyLLM 雙模態架構（`forward_signal` + `generate`） | ✅ 已完成 |
| `numeric_proj` 加深為 2 層（GELU 非線性，1024→1536→768） | ✅ 已完成 |
| `InferenceEngine` 整合（16步滾動視窗 + `reset_buffer()`） | ✅ 已完成 |
| `BacktestEngine` 換 episode 時自動呼叫 `reset_buffer()` | ✅ 已完成 |
| `ChatEngine` 整合（語言生成路徑） | ✅ 已完成 |
| `BilingualTokenizer.encode()` 支援 `max_length`/`truncation` | ✅ 已完成 |
| Tokenizer 路徑標準化（`model/tokenizer/vocab.json`） | ✅ 已完成 |
| `build_vocab.py` 詞彙建立腳本 | ✅ 已完成 |
| `unified_trainer.py` 無詞彙時自動從訓練語料建立 | ✅ 已完成 |
| `collect_signal_training_data()` 回測產生 JSONL 訓練資料 | ✅ 已完成 |
| `advanced_trainer.py` 多任務訓練支援 | ✅ 已完成 |
| `unified_trainer.py` 訓練入口腳本 | ✅ 已完成 |
| 語言訓練資料（`trading_dialogue_data.py`） | ✅ 31 組 QA（基礎） |

### 8.2 待完成（訓練前必做）

| 項目 | 優先度 | 說明 |
|------|--------|------|
| 擴充語言訓練資料至 500+ 組 | 高 | 31 組不足以訓練語言能力 |
| 執行 `build_vocab.py` 建立詞彙檔案 | 高 | 首次訓練前必做 |
| 執行回測產生 `signal_history.jsonl` | 高 | 目前訊號任務只有合成資料 |
| 首次完整訓練（階段一：語言預熱） | 高 | 模型目前為隨機初始化 |

### 8.3 目前推論能力評估

```
交易訊號路徑：可以跑，但輸出是隨機的（未訓練）
語言對話路徑：可以跑，但輸出是亂碼（未訓練）
CLI chat 指令：已降級為關鍵字匹配模式（不需要模型）
```

### 8.4 與舊 HundredMillionModel 的相容性

舊模型（`HundredMillionModel`）的 state_dict key 結構與 TinyLLM 完全不同，**無法直接遷移權重**。

```
舊格式 key：fc_layers.0.weight, fc_layers.2.weight, ...
新格式 key：blocks.0.attn.qkv_proj.weight, numeric_proj.0.weight, ...
```

結論：需要從頭訓練。舊的 `.pth` 檔案若存在，`load_state_dict(strict=False)` 會忽略所有不匹配的 key，效果等同隨機初始化。

---

> 相關文件：
> - 訓練指南：[NLP_TRAINING_GUIDE.md](../NLP_TRAINING_GUIDE.md)
> - 系統架構：[../ARCHITECTURE_OVERVIEW.md](../ARCHITECTURE_OVERVIEW.md)
> - 接手地圖：[../PROJECT_HANDOVER_MAP.md](../PROJECT_HANDOVER_MAP.md)
