# BioNeuronAI

**生物啟發的新穎性檢測神經網路**

BioNeuronAI 是一個實現了 Hebbian 學習機制的生物啟發神經元模型，具有短期輸入記憶和新穎性評分功能。本項目為 AI 助手提供了新穎性門控機制，可整合強化學習循環、檢索增強生成(RAG)管道和工具門控。

## ✨ 特性

- 🧠 **Hebbian 學習**: 實現生物啟發的突觸可塑性
- 🔄 **短期記憶**: 神經元具有可配置的輸入記憶長度
- 📊 **新穎性檢測**: 自動計算輸入模式的新穎性評分
- 🔗 **層級架構**: 支援多層神經網路構建
- 🧪 **易於測試**: 完整的測試套件覆蓋
- 📦 **模組化設計**: 清晰的 API 和可擴展架構
- 🧾 **檢索門控**: 內建新穎性驅動的檢索控制器支援 RAG 流程

## 🚀 快速開始

### 安裝

```bash
# 克隆倉庫
git clone https://github.com/kyle0527/BioNeuronai.git
cd BioNeuronai

# 安裝（開發模式）
pip install -e .

# 安裝開發依賴
pip install -r requirements-dev.txt
```

### 基本使用

```python
from pathlib import Path

from bioneuronai.core import BioNeuron, BioNet

# 創建單一神經元並啟用在線學習保護
neuron = BioNeuron(num_inputs=2, threshold=0.6, learning_rate=0.05)
neuron.configure_online_learning(window_size=5, stability_coefficient=0.1)

# 前向傳播 + 在線學習
output = neuron.online_learn([0.8, 0.6])
print(f"輸出: {output}")

# 新穎性檢測
novelty = neuron.novelty_score()
print(f"新穎性評分: {novelty}")

# 保存並重新載入神經元狀態
state_path = Path("neuron_state.npz")
neuron.save_state(state_path)
reloaded = BioNeuron.load_state(state_path)

# 使用多層網路並持久化
net = BioNet()
net.configure_online_learning(window_size=5, stability_coefficient=0.05)
l2_out, l1_out = net.forward([0.5, 0.8])
net.learn([0.5, 0.8])
net.save_state("network_state.npz")
```

> 💡 小技巧：保存的 `.npz` 檔案可直接部署於長期服務中。
> 重啟時呼叫 `BioNeuron.load_state()` 或 `BioNet.load_state()` 便能回復先前的記憶與權重。

### 命令行界面

```bash
# 啟動互動式 CLI，啟用在線學習並指定持久化檔案
bioneuron-cli --online-window 8 --stability 0.08 --save ./network_state.npz

# 從既有檔案載入
bioneuron-cli --load ./network_state.npz
```

在 CLI 中可於運行期間輸入 `save <path>` 或 `load <path>` 動態切換持久化檔案。

## 💾 模型持久化與部署

BioNeuronAI 內建序列化 API，支援使用 `numpy.savez` 生成自包含的 `.npz` 檔案。推薦的部署流程：

1. 使用 `BioNeuron` 或 `BioNet` 訓練模型並調整在線學習參數（滑動窗口 + 穩定性係數）。
2. 呼叫 `save_state()` 將權重、記憶與閾值寫入檔案。
3. 在服務啟動時透過 `load_state()` 還原模型；若需要持續學習，可再次呼叫 `configure_online_learning()`。
4. 週期性地在 CLI 或應用程式內呼叫 `save_state()`，確保即時學習成果被保存。

範例：

```python
model_path = Path("./persistent/net_state.npz")
net.save_state(model_path)

# 部署時
net = BioNet.load_state(model_path)
net.configure_online_learning(window_size=10, stability_coefficient=0.05)
```

## 🔍 新穎性驅動的檢索門控

利用 `bioneuronai.agents.retrieval_controller` 模組即可在聊天或助理應用中導入新穎性門控邏輯。當最新輸入與既有上下文差異夠大時，系統會自動呼叫檢索器擷取相關背景，適合整合檢索增強生成 (RAG)。對話內容可以是單純的字串列表，也能直接使用 OpenAI/Anthropic 風格的訊息字典（需包含 `content` 欄位）。

```python
from bioneuronai.agents.retrieval_controller import (
    InMemoryVectorRetriever,
    RetrievalController,
)

retriever = InMemoryVectorRetriever({
    "intro": "RAG enriches answers with retrieved documents.",
    "vectors": "Vector search compares embedding similarity.",
})
controller = RetrievalController(retriever, novelty_threshold=0.5)

conversation = [
    {"role": "system", "content": "You are a research assistant."},
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "let's keep chatting about neural models"},
    {"role": "user", "content": "what is retrieval augmented generation?"},
]

decision = controller.maybe_retrieve(conversation)
if decision.triggered:
    print(decision.results)  # ['intro']
```

更多完整範例請參考 `examples/rag_chatbot.py`。

## 📖 範例

查看 `examples/` 目錄中的詳細範例：

```bash
python examples/basic_demo.py
python examples/rag_chatbot.py
```

## 🌐 官方網站與資源

- [GitHub Pages 官方網站](docs/index.md)：最新版本公告、發展路線圖與使用者故事。
- [案例研究與量化成效報告](docs/case-study.md)：新穎性閘門與安全模組的實務成效。
- [社群活動規劃](docs/community-engagement.md)：黑客松、工作坊資訊與贊助方案。
- [產業/學術 PoC 流程](docs/poc-process.md)：合作流程、部署需求與支援範圍。

## 🧪 測試

```bash
# 執行所有測試
pytest tests/ -v

# 測試涵蓋率
pytest tests/ --cov=bioneuronai
```

## 📚 API 文檔

### BioNeuron

```python
BioNeuron(
    num_inputs: int,           # 輸入維度
    threshold: float = 0.8,    # 激活閾值
    learning_rate: float = 0.01, # 學習率
    memory_len: int = 5,       # 記憶長度
    seed: int | None = None    # 隨機種子
)
```

**主要方法:**
- `forward(inputs)`: 前向傳播
- `hebbian_learn(inputs, output)`: Hebbian 學習更新
- `novelty_score()`: 計算新穎性評分

### BioLayer & BioNet

- `BioLayer`: 多神經元層級抽象
- `BioNet`: 預定義的雙層網路架構

## 🛠️ 開發

### 項目結構

```
BioNeuronai/
├── src/bioneuronai/     # 核心代碼
│   ├── __init__.py
│   ├── core.py          # 主要實現
│   └── agents/          # 新穎性檢索控制器等代理工具
├── tests/               # 測試套件
│   ├── test_core.py
│   └── test_retrieval_controller.py
├── examples/            # 使用範例
│   ├── basic_demo.py
│   └── rag_chatbot.py
├── pyproject.toml       # 項目配置
└── README.md
```

### 貢獻指南

1. Fork 此倉庫
2. 創建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送到分支: `git push origin feature/amazing-feature`
5. 提交 Pull Request

## 📄 授權

本項目採用 MIT 授權 - 查看 [LICENSE](LICENSE) 文件了解詳情。

## 🔮 未來發展

- [ ] 集成強化學習模組
- [ ] RAG 管道整合
- [ ] 可視化工具
- [ ] 性能優化
- [ ] 更多神經元類型
