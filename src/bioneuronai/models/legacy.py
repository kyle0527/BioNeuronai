"""
bioneuronai.models.legacy
=========================
舊版 MLP 交易模型定義，用於向下相容載入 my_100m_model.pth 等舊格式 checkpoint。

此模組是 archived/pytorch_100m_model.py 中 HundredMillionModel 的正式遷移位置。
inference_engine.ModelLoader 偵測到舊版 MLP checkpoint 時（key 以 hidden_layers. 開頭）
會自動使用此類別進行載入，無需修改舊版 .pth 檔案。

注意：此類別僅用於 checkpoint 載入相容性，不用於新模型訓練。
新模型請使用 src/nlp/tiny_llm.py 中的 TinyLLM。
"""

from typing import Dict, List, Optional, Any

import torch
import torch.nn as nn


class HundredMillionModel(nn.Module):
    """一億參數 MLP 交易模型 — 舊版 checkpoint 相容層

    架構: 1024 → 8192 → 8192 → 4096 → 512
    識別特徵: state_dict key 以 ``hidden_layers.`` 開頭

    此類別從 archived/pytorch_100m_model.py 遷移至此，
    以確保舊版 .pth checkpoint 仍可正確載入，不再依賴 archived/ 路徑。
    """

    def __init__(
        self,
        input_dim: int = 1024,
        hidden_dims: Optional[List[int]] = None,
        output_dim: int = 512,
        dropout: float = 0.1,
        use_layer_norm: bool = True,
    ):
        super().__init__()

        if hidden_dims is None:
            hidden_dims = [8192, 8192, 4096]

        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.output_dim = output_dim

        layers: List[nn.Module] = []
        dims = [input_dim] + hidden_dims

        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            if use_layer_norm:
                layers.append(nn.LayerNorm(dims[i + 1]))
            layers.append(nn.GELU())
            if dropout > 0:
                layers.append(nn.Dropout(dropout))

        self.hidden_layers = nn.Sequential(*layers)
        self.output_layer = nn.Linear(hidden_dims[-1], output_dim)
        self._init_weights()

    def _init_weights(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.hidden_layers(x)
        x = self.output_layer(x)
        return x

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def get_layer_info(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "shape": list(param.shape),
                "params": param.numel(),
                "requires_grad": param.requires_grad,
            }
            for name, param in self.named_parameters()
        ]
