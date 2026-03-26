"""
模型導出工具
===========
支持導出為 ONNX、TorchScript 等格式
"""

import torch
import torch.nn as nn
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import json


class ModelExporter:
    """模型導出器"""
    
    def __init__(self, model: nn.Module, device: str = "cpu"):
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()
    
    def export_to_onnx(
        self,
        save_path: Union[str, Path],
        input_sample: Optional[torch.Tensor] = None,
        input_names: Optional[List[str]] = None,
        output_names: Optional[List[str]] = None,
        dynamic_axes: Optional[Dict[str, Dict[int, str]]] = None,
        opset_version: int = 14
    ):
        """導出為 ONNX 格式
        
        Args:
            save_path: 保存路徑
            input_sample: 示例輸入
            input_names: 輸入名稱列表
            output_names: 輸出名稱列表
            dynamic_axes: 動態軸配置
            opset_version: ONNX opset 版本
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 默認示例輸入
        if input_sample is None:
            input_sample = torch.randint(0, 1000, (1, 10)).to(self.device)
        
        # 默認名稱
        if input_names is None:
            input_names = ['input_ids']
        if output_names is None:
            output_names = ['logits']
        
        # 默認動態軸
        if dynamic_axes is None:
            dynamic_axes = {
                'input_ids': {0: 'batch_size', 1: 'sequence'},
                'logits': {0: 'batch_size', 1: 'sequence'}
            }
        
        print("導出 ONNX 模型...")
        print(f"  保存路徑: {save_path}")
        print(f"  Opset 版本: {opset_version}")
        
        # 導出
        torch.onnx.export(
            self.model,
            (input_sample,),
            str(save_path),
            input_names=input_names,
            output_names=output_names,
            dynamic_axes=dynamic_axes,
            opset_version=opset_version,
            do_constant_folding=True,
            export_params=True
        )
        
        print("✓ ONNX 模型已保存")
        
        # 驗證
        try:
            import onnx  # type: ignore
            onnx_model = onnx.load(str(save_path))
            onnx.checker.check_model(onnx_model)
            print("✓ ONNX 模型驗證通過")
        except ImportError:
            print("⚠️  未安裝 onnx，跳過驗證")
        except Exception as e:
            print(f"⚠️  ONNX 驗證失敗: {e}")
    
    def export_to_torchscript(
        self,
        save_path: Union[str, Path],
        method: str = "trace",
        input_sample: Optional[torch.Tensor] = None
    ):
        """導出為 TorchScript 格式
        
        Args:
            save_path: 保存路徑
            method: 導出方法 ("trace" or "script")
            input_sample: 示例輸入（trace 方法需要）
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        print("導出 TorchScript 模型...")
        print(f"  方法: {method}")
        print(f"  保存路徑: {save_path}")
        
        if method == "trace":
            if input_sample is None:
                input_sample = torch.randint(0, 1000, (1, 10)).to(self.device)
            
            # Trace 模型
            traced_model: torch.jit.ScriptModule = torch.jit.trace(self.model, input_sample)  # type: ignore
            traced_model.save(str(save_path))
            
        elif method == "script":
            # Script 模型
            scripted_model = torch.jit.script(self.model)
            scripted_model.save(str(save_path))
        
        else:
            raise ValueError(f"不支持的方法: {method}")
        
        print("✓ TorchScript 模型已保存")
    
    def export_to_safetensors(
        self,
        save_path: Union[str, Path],
        metadata: Optional[Dict[str, str]] = None
    ):
        """導出為 SafeTensors 格式
        
        Args:
            save_path: 保存路徑
            metadata: 元數據
        """
        try:
            from safetensors.torch import save_file
        except ImportError:
            raise ImportError("請安裝 safetensors: pip install safetensors")
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        print("導出 SafeTensors 格式...")
        print(f"  保存路徑: {save_path}")
        
        # 獲取狀態字典
        state_dict = self.model.state_dict()
        
        # 轉換為 CPU
        state_dict = {k: v.cpu() for k, v in state_dict.items()}
        
        # 保存
        save_file(state_dict, str(save_path), metadata=metadata)
        
        print("✓ SafeTensors 模型已保存")
    
    def export_config(
        self,
        save_path: Union[str, Path],
        additional_info: Optional[Dict[str, Any]] = None
    ):
        """導出模型配置
        
        Args:
            save_path: 保存路徑
            additional_info: 額外信息
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = {}
        
        # 嘗試獲取模型配置
        if hasattr(self.model, 'config'):
            model_config = getattr(self.model, 'config')
            if hasattr(model_config, 'to_dict'):
                config.update(model_config.to_dict())
            else:
                config.update(vars(model_config))
        
        # 添加額外信息
        if additional_info:
            config.update(additional_info)
        
        # 添加基本信息
        config['total_parameters'] = sum(p.numel() for p in self.model.parameters())
        config['trainable_parameters'] = sum(
            p.numel() for p in self.model.parameters() if p.requires_grad
        )
        
        # 保存
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 配置已保存至: {save_path}")


def export_model_package(
    model: nn.Module,
    save_dir: Union[str, Path],
    model_name: str = "model",
    export_formats: Optional[List[str]] = None,
    input_sample: Optional[torch.Tensor] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """導出完整模型包
    
    Args:
        model: 模型
        save_dir: 保存目錄
        model_name: 模型名稱
        export_formats: 導出格式列表 ["onnx", "torchscript", "safetensors", "pytorch"]
        input_sample: 示例輸入
        metadata: 元數據
    """
    if export_formats is None:
        export_formats = ["pytorch"]
    
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    exporter = ModelExporter(model)
    
    print("=" * 80)
    print(f"導出模型包: {model_name}")
    print("=" * 80)
    
    # PyTorch 格式
    if "pytorch" in export_formats:
        print("\n[1/4] 導出 PyTorch 格式...")
        torch.save(model.state_dict(), save_dir / f"{model_name}.pth")
        print(f"✓ 已保存: {model_name}.pth")
    
    # ONNX 格式
    if "onnx" in export_formats:
        print("\n[2/4] 導出 ONNX 格式...")
        try:
            exporter.export_to_onnx(
                save_dir / f"{model_name}.onnx",
                input_sample=input_sample
            )
        except Exception as e:
            print(f"⚠️  ONNX 導出失敗: {e}")
    
    # TorchScript 格式
    if "torchscript" in export_formats:
        print("\n[3/4] 導出 TorchScript 格式...")
        try:
            exporter.export_to_torchscript(
                save_dir / f"{model_name}.pt",
                method="trace",
                input_sample=input_sample
            )
        except Exception as e:
            print(f"⚠️  TorchScript 導出失敗: {e}")
    
    # SafeTensors 格式
    if "safetensors" in export_formats:
        print("\n[4/4] 導出 SafeTensors 格式...")
        try:
            exporter.export_to_safetensors(
                save_dir / f"{model_name}.safetensors",
                metadata=metadata
            )
        except Exception as e:
            print(f"⚠️  SafeTensors 導出失敗: {e}")
    
    # 導出配置
    print("\n導出配置文件...")
    exporter.export_config(
        save_dir / "config.json",
        additional_info=metadata
    )
    
    # 創建 README
    readme_content = f"""# {model_name}

## 模型信息

- 總參數: {sum(p.numel() for p in model.parameters()):,}
- 可訓練參數: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}

## 文件列表

"""
    
    for fmt in export_formats:
        if fmt == "pytorch":
            readme_content += f"- `{model_name}.pth` - PyTorch 權重文件\n"
        elif fmt == "onnx":
            readme_content += f"- `{model_name}.onnx` - ONNX 模型\n"
        elif fmt == "torchscript":
            readme_content += f"- `{model_name}.pt` - TorchScript 模型\n"
        elif fmt == "safetensors":
            readme_content += f"- `{model_name}.safetensors` - SafeTensors 權重\n"
    
    readme_content += "- `config.json` - 模型配置\n"
    
    readme_content += """
## 使用方法

### PyTorch
```python
import torch
from your_model import YourModel

model = YourModel.from_pretrained('.')
```

### ONNX
```python
import onnxruntime

session = onnxruntime.InferenceSession('{model_name}.onnx')
```

### TorchScript
```python
import torch

model = torch.jit.load('{model_name}.pt')
```
"""
    
    with open(save_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("\n✓ README 已創建")
    
    print("\n" + "=" * 80)
    print("模型包導出完成!")
    print(f"保存目錄: {save_dir.absolute()}")
    print("=" * 80)


def convert_pytorch_to_onnx(
    pytorch_model_path: str,
    onnx_save_path: str,
    model_class,
    input_sample: Optional[torch.Tensor] = None,
    **model_kwargs
):
    """將 PyTorch 模型轉換為 ONNX
    
    Args:
        pytorch_model_path: PyTorch 模型路徑
        onnx_save_path: ONNX 保存路徑
        model_class: 模型類
        input_sample: 示例輸入
        **model_kwargs: 模型初始化參數
    """
    print(f"加載 PyTorch 模型: {pytorch_model_path}")
    
    # 創建模型
    model = model_class(**model_kwargs)
    
    # 加載權重
    state_dict = torch.load(pytorch_model_path, map_location='cpu')
    model.load_state_dict(state_dict)
    model.eval()
    
    # 導出
    exporter = ModelExporter(model)
    exporter.export_to_onnx(onnx_save_path, input_sample=input_sample)
    
    print(f"✓ 轉換完成: {onnx_save_path}")
