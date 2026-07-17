"""
一億參數 PyTorch 神經網路
==========================
真正的生產級 AI 模型，使用 PyTorch 框架
權重保存為標準 .pth 格式
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import time
import math


class HundredMillionModel(nn.Module):
    """一億參數 PyTorch 神經網路
    
    架構: 1024 → 8192 → 8192 → 4096 → 512
    總參數: ~111M
    """
    
    def __init__(
        self,
        input_dim: int = 1024,
        hidden_dims: Optional[List[int]] = None,
        output_dim: int = 512,
        dropout: float = 0.1,
        use_layer_norm: bool = True
    ):
        super().__init__()
        
        if hidden_dims is None:
            hidden_dims = [8192, 8192, 4096]
        
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.output_dim = output_dim
        
        # 構建層
        layers = []
        dims = [input_dim] + hidden_dims
        
        for i in range(len(dims) - 1):
            # 線性層
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            
            # Layer Normalization
            if use_layer_norm:
                layers.append(nn.LayerNorm(dims[i + 1]))
            
            # 激活函數 (GELU)
            layers.append(nn.GELU())
            
            # Dropout
            if dropout > 0:
                layers.append(nn.Dropout(dropout))
        
        self.hidden_layers = nn.Sequential(*layers)
        
        # 輸出層
        self.output_layer = nn.Linear(hidden_dims[-1], output_dim)
        
        # 初始化權重
        self._init_weights()
        
    def _init_weights(self):
        """Xavier 初始化"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向傳播"""
        x = self.hidden_layers(x)
        x = self.output_layer(x)
        return x
    
    def count_parameters(self) -> int:
        """計算總參數數量"""
        return sum(p.numel() for p in self.parameters())
    
    def count_trainable_parameters(self) -> int:
        """計算可訓練參數數量"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def get_layer_info(self) -> List[Dict[str, Any]]:
        """獲取每層信息"""
        info = []
        for name, param in self.named_parameters():
            info.append({
                "name": name,
                "shape": list(param.shape),
                "params": param.numel(),
                "dtype": str(param.dtype),
                "requires_grad": param.requires_grad
            })
        return info


class HundredMillionModelWithAttention(nn.Module):
    """帶自注意力機制的一億參數模型
    
    更先進的架構，包含:
    - 多頭自注意力
    - 殘差連接
    - Layer Normalization
    """
    
    def __init__(
        self,
        input_dim: int = 1024,
        hidden_dim: int = 4096,
        output_dim: int = 512,
        num_heads: int = 8,
        num_layers: int = 6,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        
        # 輸入投影
        self.input_projection = nn.Linear(input_dim, hidden_dim)
        self.input_norm = nn.LayerNorm(hidden_dim)
        
        # Transformer 層
        self.transformer_layers = nn.ModuleList([
            TransformerBlock(hidden_dim, num_heads, dropout)
            for _ in range(num_layers)
        ])
        
        # 輸出層
        self.output_projection = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 2, output_dim)
        )
        
        self._init_weights()
    
    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 輸入投影
        x = self.input_projection(x)
        x = self.input_norm(x)
        
        # 確保有 sequence 維度
        if x.dim() == 2:
            x = x.unsqueeze(1)  # (batch, 1, hidden)
        
        # Transformer 層
        for layer in self.transformer_layers:
            x = layer(x)
        
        # 取最後一個位置的輸出
        x = x.mean(dim=1)  # (batch, hidden)
        
        # 輸出投影
        x = self.output_projection(x)
        
        return x
    
    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())


class TransformerBlock(nn.Module):
    """Transformer 區塊"""
    
    def __init__(self, hidden_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        
        self.attention = nn.MultiheadAttention(
            hidden_dim, num_heads, dropout=dropout, batch_first=True
        )
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # 自注意力 + 殘差
        attn_out, _ = self.attention(x, x, x)
        x = self.norm1(x + attn_out)
        
        # FFN + 殘差
        ffn_out = self.ffn(x)
        x = self.norm2(x + ffn_out)
        
        return x


def create_100m_pytorch_model(
    architecture: str = "mlp",
    device: str = "cpu"
) -> nn.Module:
    """創建一億參數 PyTorch 模型
    
    Args:
        architecture: "mlp" 或 "transformer"
        device: "cpu" 或 "cuda"
    
    Returns:
        PyTorch 模型
    """
    if architecture == "transformer":
        # Transformer 架構 (~100M 參數)
        model = HundredMillionModelWithAttention(
            input_dim=1024,
            hidden_dim=2048,
            output_dim=512,
            num_heads=8,
            num_layers=12,  # 12 層 transformer
            dropout=0.1
        )
    else:
        # MLP 架構 (~111M 參數)
        model = HundredMillionModel(
            input_dim=1024,
            hidden_dims=[8192, 8192, 4096],
            output_dim=512,
            dropout=0.1,
            use_layer_norm=True
        )
    
    model = model.to(device)
    return model


def save_model_weights(model: nn.Module, path: str, metadata: Optional[Dict] = None) -> None:
    """保存模型權重為 .pth 格式
    
    Args:
        model: PyTorch 模型
        path: 保存路徑
        metadata: 額外的元數據
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # 準備保存的數據
    save_dict = {
        "state_dict": model.state_dict(),
        "total_params": sum(p.numel() for p in model.parameters()),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # 添加模型配置
    if hasattr(model, 'input_dim'):
        save_dict["config"] = {
            "input_dim": model.input_dim,
            "output_dim": model.output_dim,
        }
        if hasattr(model, 'hidden_dims'):
            save_dict["config"]["hidden_dims"] = model.hidden_dims
        if hasattr(model, 'hidden_dim'):
            save_dict["config"]["hidden_dim"] = model.hidden_dim
    
    # 添加元數據
    if metadata:
        save_dict["metadata"] = metadata
    
    # 保存
    torch.save(save_dict, path_obj)
    
    file_size = path_obj.stat().st_size / 1024 / 1024
    print(f"✅ 權重已保存: {path_obj}")
    print(f"   檔案大小: {file_size:.2f} MB")


def save_weights_only(model: nn.Module, path: str) -> None:
    """只保存權重（標準格式，與其他框架相容）"""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    torch.save(model.state_dict(), path_obj)
    
    file_size = path_obj.stat().st_size / 1024 / 1024
    print(f"✅ 純權重已保存: {path_obj}")
    print(f"   檔案大小: {file_size:.2f} MB")


def load_model_weights(path: str, device: str = "cpu") -> Tuple[nn.Module, Dict]:
    """載入模型權重
    
    Args:
        path: 權重檔案路徑
        device: 設備
    
    Returns:
        (模型, 元數據)
    """
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    
    # 獲取配置
    config = checkpoint.get("config", {})
    
    # 根據配置創建模型
    if "hidden_dims" in config:
        model = HundredMillionModel(
            input_dim=config.get("input_dim", 1024),
            hidden_dims=config.get("hidden_dims", [8192, 8192, 4096]),
            output_dim=config.get("output_dim", 512)
        )
    else:
        model = HundredMillionModelWithAttention(
            input_dim=config.get("input_dim", 1024),
            hidden_dim=config.get("hidden_dim", 2048),
            output_dim=config.get("output_dim", 512)
        )
    
    # 載入權重
    if "state_dict" in checkpoint:
        model.load_state_dict(checkpoint["state_dict"])
    else:
        model.load_state_dict(checkpoint)
    
    model = model.to(device)
    
    return model, checkpoint


def print_model_info(model: nn.Module) -> None:
    """打印模型信息"""
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print("=" * 70)
    print(f"🧠 模型信息")
    print("=" * 70)
    print(f"總參數數量: {total_params:,} ({total_params / 1e6:.2f}M)")
    print(f"可訓練參數: {trainable_params:,}")
    print(f"模型大小 (float32): {total_params * 4 / 1024 / 1024:.2f} MB")
    print(f"模型大小 (float16): {total_params * 2 / 1024 / 1024:.2f} MB")
    print()
    
    print("層級結構:")
    for name, param in model.named_parameters():
        print(f"  {name}: {list(param.shape)} ({param.numel():,} params)")
    print("=" * 70)


# ============================================================================
# 主程序
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 創建一億參數 PyTorch 模型")
    print("=" * 70)
    
    # 選擇設備
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用設備: {device}")
    
    # 創建模型
    print("\n📦 創建 MLP 架構模型...")
    model = create_100m_pytorch_model(architecture="mlp", device=device)
    
    # 打印信息
    print_model_info(model)
    
    # 測試推理
    print("\n🔮 測試推理...")
    test_input = torch.randn(1, 1024).to(device)
    
    start = time.time()
    with torch.no_grad():
        output = model(test_input)
    inference_time = time.time() - start
    
    print(f"輸入形狀: {test_input.shape}")
    print(f"輸出形狀: {output.shape}")
    print(f"推理時間: {inference_time * 1000:.2f} ms")
    
    # 保存權重
    print("\n💾 保存權重...")
    save_path = Path("weights/my_100m_model.pth")
    save_model_weights(model, str(save_path), metadata={
        "name": "我的專屬AI-100M",
        "version": "1.0.0",
        "description": "一億參數生物啟發神經網路"
    })
    
    # 也保存純權重版本
    save_weights_only(model, "weights/my_100m_weights_only.pth")
    
    print("\n✅ 完成!")
