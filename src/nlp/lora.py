"""
LoRA (Low-Rank Adaptation) 微調
==============================
高效的參數微調方法，只訓練很少的參數
"""

import torch
import torch.nn as nn
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import math


@dataclass
class LoRAConfig:
    """配置"""
    r: int = 8  # LoRA 秩
    lora_alpha: int = 16  # LoRA 縮放因子
    lora_dropout: float = 0.1  # Dropout
    target_modules: Optional[List[str]] = None  # 要應用 LoRA 的模塊名稱
    
    def __post_init__(self):
        if self.target_modules is None:
            # 默認應用到所有線性層
            self.target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "fc1", "fc2"]


class LoRALayer(nn.Module):
    """LoRA 層
    
    將權重矩陣 W 分解為: W' = W + BA
    其中 B 和 A 是低秩矩陣，秩為 r << min(in_features, out_features)
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1
    ):
        super().__init__()
        self.r = r
        self.lora_alpha = lora_alpha
        self.scaling = lora_alpha / r
        
        # LoRA 矩陣 A 和 B
        self.lora_A = nn.Parameter(torch.zeros(r, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        
        # Dropout
        self.lora_dropout = nn.Dropout(p=lora_dropout) if lora_dropout > 0 else nn.Identity()
        
        # 初始化
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """計算 LoRA 增量
        
        Args:
            x: (batch_size, ..., in_features)
        
        Returns:
            delta: (batch_size, ..., out_features)
        """
        # x @ A^T @ B^T
        # = (x @ A^T) @ B^T
        x_dropout = self.lora_dropout(x)
        result = x_dropout @ self.lora_A.t() @ self.lora_B.t()
        return result * self.scaling


class LoRALinear(nn.Module):
    """帶 LoRA 的線性層"""
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1,
        bias: bool = True
    ):
        super().__init__()
        
        # 原始線性層（凍結）
        self.linear = nn.Linear(in_features, out_features, bias=bias)
        self.linear.weight.requires_grad = False
        if bias:
            self.linear.bias.requires_grad = False
        
        # LoRA 層
        self.lora = LoRALayer(in_features, out_features, r, lora_alpha, lora_dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向傳播
        
        Args:
            x: (batch_size, ..., in_features)
        
        Returns:
            output: (batch_size, ..., out_features)
        """
        # 原始輸出 + LoRA 增量
        if self.lora is not None:
            return self.linear(x) + self.lora(x)
        return self.linear(x)
    
    @classmethod
    def from_linear(
        cls,
        linear: nn.Linear,
        r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.1
    ):
        """從普通線性層創建 LoRA 層
        
        Args:
            linear: 原始線性層
            r: LoRA 秩
            lora_alpha: 縮放因子
            lora_dropout: Dropout
        
        Returns:
            LoRA 線性層
        """
        lora_linear = cls(
            linear.in_features,
            linear.out_features,
            r=r,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            bias=linear.bias is not None
        )
        
        # 複製原始權重
        lora_linear.linear.weight.data = linear.weight.data.clone()
        if linear.bias is not None:
            lora_linear.linear.bias.data = linear.bias.data.clone()
        
        return lora_linear
    
    def merge_weights(self):
        """合併 LoRA 權重到原始權重"""
        if self.lora is not None:
            # W' = W + BA * scaling
            delta_weight = (self.lora.lora_B @ self.lora.lora_A) * self.lora.scaling
            self.linear.weight.data += delta_weight
            
            # 移除 LoRA 層
            self.lora = None
    
    def unmerge_weights(self, r: int = 8, lora_alpha: int = 16, lora_dropout: float = 0.1):
        """取消合併（重新創建 LoRA 層）"""
        if self.lora is None:
            self.lora = LoRALayer(
                self.linear.in_features,
                self.linear.out_features,
                r=r,
                lora_alpha=lora_alpha,
                lora_dropout=lora_dropout
            )


def apply_lora_to_model(
    model: nn.Module,
    config: LoRAConfig
) -> nn.Module:
    """為模型應用 LoRA
    
    Args:
        model: 原始模型
        config: LoRA 配置
    
    Returns:
        應用了 LoRA 的模型
    """
    print(f"應用 LoRA 到模型...")
    print(f"  秩 (r): {config.r}")
    print(f"  Alpha: {config.lora_alpha}")
    print(f"  Dropout: {config.lora_dropout}")
    print(f"  目標模塊: {config.target_modules}")
    
    replaced_count = 0
    
    def _replace_with_lora(module: nn.Module, name: str = ""):
        nonlocal replaced_count
        
        for child_name, child in module.named_children():
            full_name = f"{name}.{child_name}" if name else child_name
            
            # 檢查是否應該替換
            if isinstance(child, nn.Linear):
                # 檢查名稱是否匹配
                should_replace = False
                if config.target_modules is not None:
                    for target in config.target_modules:
                        if target in child_name or target in full_name:
                            should_replace = True
                            break
                
                if should_replace:
                    # 替換為 LoRA 層
                    lora_linear = LoRALinear.from_linear(
                        child,
                        r=config.r,
                        lora_alpha=config.lora_alpha,
                        lora_dropout=config.lora_dropout
                    )
                    setattr(module, child_name, lora_linear)
                    replaced_count += 1
                    print(f"  ✓ 替換: {full_name}")
            else:
                # 遞歸處理子模塊
                _replace_with_lora(child, full_name)
    
    _replace_with_lora(model)
    
    print(f"✓ LoRA 應用完成! 替換了 {replaced_count} 個模塊")
    
    # 凍結所有非 LoRA 參數
    freeze_non_lora_parameters(model)
    
    return model


def freeze_non_lora_parameters(model: nn.Module):
    """凍結所有非 LoRA 參數"""
    frozen_params = 0
    trainable_params = 0
    
    for name, param in model.named_parameters():
        if 'lora' in name:
            param.requires_grad = True
            trainable_params += param.numel()
        else:
            param.requires_grad = False
            frozen_params += param.numel()
    
    print(f"\n參數統計:")
    print(f"  凍結參數: {frozen_params:,} ({frozen_params/(frozen_params+trainable_params)*100:.2f}%)")
    print(f"  可訓練參數: {trainable_params:,} ({trainable_params/(frozen_params+trainable_params)*100:.2f}%)")
    print(f"  總參數: {frozen_params+trainable_params:,}")


def get_lora_parameters(model: nn.Module) -> List[nn.Parameter]:
    """獲取所有 LoRA 參數
    
    Args:
        model: 模型
    
    Returns:
        LoRA 參數列表
    """
    lora_params = []
    for name, param in model.named_parameters():
        if 'lora' in name and param.requires_grad:
            lora_params.append(param)
    return lora_params


def merge_lora_weights(model: nn.Module) -> nn.Module:
    """合併所有 LoRA 權重
    
    將 LoRA 增量合併到原始權重中，移除 LoRA 層
    
    Args:
        model: 帶 LoRA 的模型
    
    Returns:
        合併後的模型
    """
    print("合併 LoRA 權重...")
    merged_count = 0
    
    for module in model.modules():
        if isinstance(module, LoRALinear):
            module.merge_weights()
            merged_count += 1
    
    print(f"✓ 合併完成! 合併了 {merged_count} 個 LoRA 層")
    return model


def save_lora_weights(
    model: nn.Module,
    save_path: str,
    config: Optional[LoRAConfig] = None
):
    """只保存 LoRA 權重
    
    Args:
        model: 帶 LoRA 的模型
        save_path: 保存路徑
        config: LoRA 配置
    """
    from pathlib import Path
    import json
    
    save_dir = Path(save_path)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 只保存 LoRA 參數
    lora_state_dict = {}
    for name, param in model.named_parameters():
        if 'lora' in name:
            lora_state_dict[name] = param.data
    
    torch.save(lora_state_dict, save_dir / 'lora_weights.pth')
    
    # 保存配置
    if config:
        config_dict = {
            'r': config.r,
            'lora_alpha': config.lora_alpha,
            'lora_dropout': config.lora_dropout,
            'target_modules': config.target_modules
        }
        with open(save_dir / 'lora_config.json', 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    # 計算大小
    total_size = sum(p.numel() * p.element_size() for p in lora_state_dict.values())
    size_mb = total_size / (1024 * 1024)
    
    print(f"✓ LoRA 權重已保存至: {save_dir}")
    print(f"  參數數量: {sum(p.numel() for p in lora_state_dict.values()):,}")
    print(f"  文件大小: {size_mb:.2f} MB")


def load_lora_weights(
    model: nn.Module,
    load_path: str,
    strict: bool = False
) -> nn.Module:
    """加載 LoRA 權重
    
    Args:
        model: 模型（應該已經應用了 LoRA）
        load_path: 加載路徑
        strict: 是否嚴格匹配
    
    Returns:
        加載了 LoRA 權重的模型
    """
    from pathlib import Path
    import json
    
    load_dir = Path(load_path)
    
    # 加載 LoRA 權重
    lora_state_dict = torch.load(load_dir / 'lora_weights.pth', map_location='cpu')
    
    # 加載到模型
    missing_keys, unexpected_keys = model.load_state_dict(lora_state_dict, strict=False)
    
    if not strict:
        # 過濾掉非 LoRA 的 missing keys
        missing_lora = [k for k in missing_keys if 'lora' in k]
        if missing_lora:
            print(f"⚠️  缺少 LoRA 鍵: {missing_lora}")
    
    print(f"✓ LoRA 權重已從 {load_dir} 加載")
    print(f"  加載參數: {len(lora_state_dict)}")
    
    return model


class LoRATrainer:
    """LoRA 訓練器輔助類"""
    
    @staticmethod
    def prepare_model_for_lora(
        model: nn.Module,
        config: LoRAConfig
    ) -> nn.Module:
        """準備模型進行 LoRA 訓練"""
        model = apply_lora_to_model(model, config)
        return model
    
    @staticmethod
    def get_trainable_parameters(model: nn.Module) -> Dict[str, Any]:
        """獲取可訓練參數統計"""
        total = 0
        trainable = 0
        
        for param in model.parameters():
            total += param.numel()
            if param.requires_grad:
                trainable += param.numel()
        
        return {
            'total': total,
            'trainable': trainable,
            'frozen': total - trainable,
            'trainable_percent': trainable / total * 100 if total > 0 else 0
        }
    
    @staticmethod
    def print_trainable_parameters(model: nn.Module):
        """打印可訓練參數統計"""
        stats = LoRATrainer.get_trainable_parameters(model)
        
        print("\n" + "=" * 60)
        print("參數統計")
        print("=" * 60)
        print(f"總參數:       {stats['total']:>15,}")
        print(f"可訓練參數:   {stats['trainable']:>15,}  ({stats['trainable_percent']:.2f}%)")
        print(f"凍結參數:     {stats['frozen']:>15,}  ({100-stats['trainable_percent']:.2f}%)")
        print("=" * 60 + "\n")
