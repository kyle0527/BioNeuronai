#!/usr/bin/env python3


"""
BioNeuronAI 基本使用範例
演示如何使用 BioNeuron 進行模式學習、新穎性檢測，以及保存/載入持久化狀態。

教學重點：
1. 建立神經元並啟用在線學習模式，透過滑動窗口避免災難性遺忘。
2. 使用 `save_state()` 與 `load_state()` 在磁碟間傳遞權重、記憶與閾值。
3. 將持久化流程整合至 `BioNet`，作為部署前快照範例。
"""



from pathlib import Path

import numpy as np


from bioneuronai import BioNet, BioNetConfig, BioNeuron, LayerConfig, NeuronConfig


def demo_programmatic_config() -> None:
    """展示如何以程式碼組裝異質網路配置."""

    print("\n=== 程式化定義網路拓樸 ===")
    config = BioNetConfig(
        input_dim=2,
        layers=[
            LayerConfig(
                neurons=[
                    NeuronConfig("BioNeuron", count=2, params={"threshold": 0.6}),
                    NeuronConfig("ImprovedBioNeuron", params={"adaptive_threshold": True}),
                ]
            ),
            LayerConfig(neurons=[NeuronConfig("BioNeuron", count=3)]),
        ],
    )
    net = BioNet(config)
    print(net.summary())

# matplotlib is optional and is imported locally in plot_learning_curve()
# to avoid import-time errors when matplotlib is not installed.

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from bioneuronai.core import BioNeuron, BioNet, NetworkBuilder


class ScalingNeuron(BioNeuron):
    """簡單的縮放型神經元，示範如何混合不同類型神經元"""

    def __init__(self, *, scale: float = 0.5, **kwargs):
        super().__init__(**kwargs)
        self.scale = scale

    def forward(self, inputs):  # type: ignore[override]
        base = super().forward(inputs)
        return min(1.0, base * self.scale)

from bioneuronai.core import BioNeuron, BioNet
from bioneuronai.visualization.stats import (
    InputRecord,
    SecurityScanStatus,
    collect_snapshot_from_bionet,
    default_stats_hub,
)


@dataclass
class DashboardStreamer:
    """Helper that pushes network updates to the visualization hub."""

    network: BioNet
    enable_security_scan: bool = True
    total_steps: int = 60
    _step_counter: int = 0

    _phases: tuple[str, ...] = (
        "初始化",
        "權重審核",
        "新穎性校正",
        "攻擊模擬",
        "最終審查",
    )

    def push(self, inputs: Sequence[float], outputs: Sequence[float], novelty: float, *, tag: Optional[str] = None) -> None:
        security_status: Optional[SecurityScanStatus] = None
        if self.enable_security_scan:
            progress = min(1.0, self._step_counter / max(1, self.total_steps))
            phase_index = min(len(self._phases) - 1, int(progress * len(self._phases)))
            security_status = SecurityScanStatus(
                progress=progress,
                current_phase=self._phases[phase_index],
                issues_found=max(0, self._step_counter // 15),
                notes="儀表板示範資料",
            )

        snapshot = collect_snapshot_from_bionet(self.network, security_status)
        default_stats_hub.update_snapshot(snapshot)
        default_stats_hub.log_input(
            InputRecord(values=inputs, outputs=outputs, novelty=novelty, tag=tag)
        )
        self._step_counter += 1


def demo_basic_neuron():
    """演示單一神經元的基本功能"""
    print("=== 基本神經元演示 ===")
    
    # 創建神經元
    neuron = BioNeuron(num_inputs=2, threshold=0.6, learning_rate=0.05, seed=42)
    
    # 訓練數據：簡單的 AND 邏輯
    training_data = [
        ([0.0, 0.0], 0.0),
        ([0.0, 1.0], 0.0),
        ([1.0, 0.0], 0.0),
        ([1.0, 1.0], 1.0),
    ]
    
    print("訓練前的權重:", neuron.weights)
    
    # 訓練過程
    for epoch in range(50):
        for inputs, target in training_data:
            output = neuron.forward(inputs)
            # 使用目標值進行學習
            neuron.hebbian_learn(inputs, target)
    
    print("訓練後的權重:", neuron.weights)
    
    # 測試
    print("\n測試結果:")
    for inputs, expected in training_data:
        output = neuron.forward(inputs)
        print(f"輸入 {inputs} -> 輸出 {output:.3f} (期望 {expected})")

    # 展示在線學習模式：啟用滑動窗口與穩定化
    neuron.configure_online_learning(window_size=5, stability_coefficient=0.1)
    for inputs, _ in training_data:
        neuron.online_learn(inputs)
    print("在線模式啟用後的權重:", neuron.weights)


def demo_novelty_detection():
    """演示新穎性檢測功能"""
    print("\n=== 新穎性檢測演示 ===")
    
    neuron = BioNeuron(num_inputs=2, memory_len=10, seed=42)
    
    # 規律性數據
    print("輸入規律性數據:")
    for i in range(5):
        inputs = [0.5, 0.5]  # 相同輸入
        output = neuron.forward(inputs)
        novelty = neuron.novelty_score()
        print(f"步驟 {i+1}: 輸入 {inputs} -> 新穎性 {novelty:.3f}")
    
    # 變化數據
    print("\n輸入變化數據:")
    varied_inputs = [[0.1, 0.9], [0.8, 0.2], [0.3, 0.7], [0.9, 0.1]]
    for i, inputs in enumerate(varied_inputs):
        output = neuron.forward(inputs)
        novelty = neuron.novelty_score()
        print(f"步驟 {i+6}: 輸入 {inputs} -> 新穎性 {novelty:.3f}")



def demo_network_adaptation() -> None:
    """演示如何以 JSON 組態宣告異質拓樸並進行學習."""

    print("\n=== 網路適應性學習 (JSON 組態) ===")

    config_payload = {
        "input_dim": 2,
        "layers": [
            {
                "neurons": [
                    {"type": "BioNeuron", "count": 2, "params": {"threshold": 0.7}},
                    {
                        "type": "ImprovedBioNeuron",
                        "params": {"adaptive_threshold": True, "learning_rate": 0.02},
                    },
                ]
            },
            {"neurons": [{"type": "BioNeuron", "count": 2}]},
        ],
    }

    print("宣告 JSON 組態:\n" + json.dumps(config_payload, indent=2, ensure_ascii=False))
    config = BioNetConfig.from_dict(config_payload)
    net = BioNet(config)
    print(net.summary())

    rng = np.random.default_rng(42)
    test_patterns: List[List[float]] = rng.random((5, config.input_dim)).round(2).tolist()

    for epoch in range(2):
        print(f"\n第 {epoch + 1} 輪學習:")
        for pattern in test_patterns:
            activations = net.forward(pattern)
            final_outputs = activations[-1]
            print(f"  輸入 {pattern} -> 最終輸出 {final_outputs}")
            net.learn(pattern, activations)

    print("\n最終層大小:", net.layer_sizes)
=======
def demo_network_adaptation(net: BioNet, streamer: Optional[DashboardStreamer] = None) -> None:
    """演示網路適應性學習，可選擇串流資料到儀表板。"""

    print("\n=== 網路適應性學習演示 ===")


    builder = NetworkBuilder({"ScalingNeuron": ScalingNeuron})
    custom_config = {
        "input_dim": 2,
        "layers": [
            {"size": 3, "neuron_type": "ScalingNeuron", "params": {"scale": 0.7}},
            {"size": 4},
            {"size": 2, "neuron_type": "ScalingNeuron", "params": {"scale": 1.2}},
        ],
    }
    net = BioNet(config=custom_config, builder=builder)



    # 生成一些測試數據
    np.random.seed(42)
    test_patterns = [
        [0.2, 0.8],
        [0.7, 0.3],
        [0.9, 0.1],
        [0.1, 0.9],
        [0.5, 0.5],
    ]

    print("網路學習過程:")
    for epoch in range(3):
        print(f"\n第 {epoch + 1} 輪:")
        for i, pattern in enumerate(test_patterns):

            l2_out, l1_out = net.forward(pattern)
            novelty = net.layer1.neurons[0].novelty_score()

            print(f"  模式 {i+1} {pattern}: 輸出={l2_out[0]:.3f}, 新穎性={novelty:.3f}")

            if streamer is not None:
                streamer.push(pattern, l2_out, novelty, tag=f"epoch-{epoch + 1}")

            # 學習
            net.learn(pattern)

    # 保存並重新載入網路狀態
    snapshot = Path("basic_net_state.npz")
    net.configure_online_learning(window_size=5, stability_coefficient=0.05)
    net.save_state(snapshot)
    restored = BioNet.load_state(snapshot)
    restored.configure_online_learning(window_size=5, stability_coefficient=0.05)
    l2_out_restored, _ = restored.forward(test_patterns[-1])
    print(f"\n重新載入後的輸出: {l2_out_restored[0]:.3f} (狀態保存於 {snapshot})")


def demo_loading_from_json(tmp_dir: Path | None = None):
    """演示如何從 JSON 設定建構網路"""
    print("\n=== JSON 設定載入示例 ===")

    config = {
        "input_dim": 3,
        "layers": [
            {"size": 2, "params": {"threshold": 0.4}},
            {"size": 2},
        ],
    }
    tmp_dir = tmp_dir or Path.cwd()
    json_path = tmp_dir / "demo_network.json"
    json_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"設定檔已寫入：{json_path}")

    net = BioNet(config=json_path)
    final_out, layer_outputs = net.forward([0.1, 0.5, 0.9])
    print(f"最終輸出：{final_out} | 各層輸出：{layer_outputs}")

    try:
        json_path.unlink()
    except OSError:
        pass


def plot_learning_curve():
    """繪製學習曲線（需要 matplotlib）"""
    try:
        import matplotlib.pyplot as plt
        
        print("\n=== 學習曲線分析 ===")
        
        neuron = BioNeuron(num_inputs=2, learning_rate=0.1, seed=42)
        
        # 固定目標模式
        target_pattern = [0.8, 0.6]
        target_output = 1.0
        
        outputs = []
        novelties = []
        
        # 收集學習數據
        for i in range(100):
            # 添加噪音
            noisy_input = [
                target_pattern[0] + np.random.normal(0, 0.1),
                target_pattern[1] + np.random.normal(0, 0.1)
            ]
            
            output = neuron.forward(noisy_input)
            novelty = neuron.novelty_score()
            
            outputs.append(output)
            novelties.append(novelty)
            
            # 學習
            neuron.hebbian_learn(noisy_input, target_output)
        
        # 繪圖
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        ax1.plot(outputs)
        ax1.set_title('神經元輸出隨時間變化')
        ax1.set_ylabel('輸出值')
        ax1.grid(True)
        
        ax2.plot(novelties)
        ax2.set_title('新穎性評分隨時間變化')
        ax2.set_xlabel('時間步')
        ax2.set_ylabel('新穎性評分')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('learning_curve.png', dpi=150)
        print("學習曲線已保存為 learning_curve.png")
        
    except ImportError:
        print("matplotlib 未安裝，跳過繪圖演示")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BioNeuronAI basic demo with dashboard streaming support")
    parser.add_argument(
        "--stream-dashboard",
        action="store_true",
        help="即時將網路狀態與輸入資料串流到 FastAPI 儀表板",
    )
    parser.add_argument(
        "--disable-security-scan",
        action="store_true",
        help="停用安全掃描進度模擬",
    )
    return parser.parse_args()


def main() -> None:
    """主函數"""

    args = parse_args()

    print("BioNeuronAI 使用範例")
    print("=" * 50)

    demo_basic_neuron()
    demo_novelty_detection()



    shared_net = BioNet()
    streamer: Optional[DashboardStreamer] = None
    if args.stream_dashboard:
        streamer = DashboardStreamer(
            shared_net, enable_security_scan=not args.disable_security_scan
        )
        # 初始化一次快照讓儀表板在第一筆資料前就有狀態
        default_stats_hub.update_snapshot(collect_snapshot_from_bionet(shared_net))
        print("\n[儀表板] 已啟用串流，請啟動 `uvicorn bioneuronai.visualization.api:app --reload` 或使用 docker-compose 觀察儀表板。")

    demo_network_adaptation(shared_net, streamer)

    plot_learning_curve()


    print("\n演示完成！")


if __name__ == "__main__":
    main()
