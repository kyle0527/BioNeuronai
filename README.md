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
- 🧬 **多樣神經元**: 內建 Hebb、LIF 及反 Hebb 神經元實作

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
from bioneuronai.core import BioNeuron, BioNet

# 創建單一神經元
neuron = BioNeuron(num_inputs=2, threshold=0.6, learning_rate=0.05)

# 前向傳播
output = neuron.forward([0.8, 0.6])
print(f"輸出: {output}")

# Hebbian 學習
neuron.hebbian_learn([0.8, 0.6], target_output=1.0)

# 新穎性檢測
novelty = neuron.novelty_score()
print(f"新穎性評分: {novelty}")

# 使用多層網路
net = BioNet()
l2_out, l1_out = net.forward([0.5, 0.8])
net.learn([0.5, 0.8])
```

### NetworkBuilder：透過設定構建網路

```python
from bioneuronai import NetworkBuilder

builder = NetworkBuilder()
config = {
    "input_dim": 2,
    "layers": [
        {"type": "lif", "count": 2, "params": {"threshold": 0.4}},
        {"type": "anti_hebb", "count": 1},
    ],
}
network = builder.build_from_config(config)
output, activations = network.forward([1.0, 0.5])
# 若有監督目標，可提供各層對應的 targets（可省略則使用神經元自身輸出）
network.learn([1.0, 0.5], targets=[[0.8, 0.2], [0.1]])
```

### 命令行界面

```bash
# 啟動互動式 CLI
bioneuron-cli
```

## 📖 範例

查看 `examples/` 目錄中的詳細範例：

```bash
python examples/basic_demo.py
```

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

### 神經元類型比較

| 類型 | 激活行為 | 學習規則 | 新穎性評分 |
| --- | --- | --- | --- |
| `BioNeuron` | 線性疊加並套用閾值 | 經典 Hebbian 增強高相關輸入 | 以輸入差異為主 | 
| `LIFNeuron` | 漏電積分後觸發尖峰，含不應期 | 尖峰時強化權重、未觸發時緩慢衰減 | 追蹤輸入變化並保留尖峰歷史 |
| `AntiHebbNeuron` | 平滑抑制輸出，偏好不相關訊號 | 相關輸入時抑制權重，藉 decorrelation 回復平衡 | 綜合輸入差異與權重變化 |

如需擴充自訂神經元類型，可繼承 `BaseBioNeuron` 並透過 `NetworkBuilder.register_neuron_type()` 註冊，即可在設定中使用自訂名稱載入。

## 🛠️ 開發

### 項目結構

```
BioNeuronai/
├── src/bioneuronai/     # 核心代碼
│   ├── __init__.py
│   └── core.py          # 主要實現
├── tests/               # 測試套件
│   └── test_core.py
├── examples/            # 使用範例
│   └── basic_demo.py
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
