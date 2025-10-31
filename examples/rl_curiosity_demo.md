# RL 好奇心示例

本示例展示如何使用 `CuriositDrivenNet` 在 OpenAI Gym / Gymnasium 環境中計算內在獎勵（好奇心水位），並將其整合至強化學習回合。

## 依賴安裝

請先安裝核心套件：

```bash
pip install -e .
```

接著安裝示例所需的額外依賴：

```bash
pip install gymnasium==0.29.1  # 或 `pip install gym`（舊版 OpenAI Gym）
pip install matplotlib          # 選用，用於繪製探索曲線
```

> **提示**：若使用 `gym` 舊版 API，腳本會自動適配。

## 啟動示例

在專案根目錄執行：

```bash
python examples/rl_curiosity_demo.py --env CartPole-v1 --episodes 5
```

### 常用參數

- `--env`: 指定環境 ID，預設為 `CartPole-v1`
- `--episodes`: 演示回合數
- `--max-steps`: 每回合最多步數
- `--intrinsic-scale`: 內在獎勵與外在獎勵的加權係數
- `--threshold`: 觸發神經元 Hebbian 學習的好奇心水位門檻
- `--no-plot`: 禁用好奇心探索曲線輸出

### 輸出內容

- 終端會顯示平均回報、平均內在獎勵與最大好奇心水位。
- 若安裝 `matplotlib` 且未使用 `--no-plot`，會在 `examples/rl_curiosity_demo_curve.png` 生成探索曲線。

## 以自訂環境測試

範例函式 `run_curiosity_demo` 支援傳入 `env_factory` 參數，可提供自訂或模擬環境，例如：

```python
from examples.rl_curiosity_demo import run_curiosity_demo

class TinyEnv:
    observation_space = ...
    action_space = ...

metrics = run_curiosity_demo(env_factory=lambda: TinyEnv(), episodes=2, plot=False)
```

此模式適合單元測試或在無法安裝完整 Gym 套件時做快速驗證。
