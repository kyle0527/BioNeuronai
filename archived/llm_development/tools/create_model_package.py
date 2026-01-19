"""
完整語言模型包創建工具
=====================
根據標準 HuggingFace 格式創建完整的模型包
"""

import json
import torch
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# 添加路徑
sys.path.insert(0, str(Path(__file__).parent / "src" / "bioneuronai"))

from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
from src.bioneuronai.bilingual_tokenizer import BilingualTokenizer, create_bilingual_tokenizer


def create_config_json(config: TinyLLMConfig, save_dir: Path) -> None:
    """創建 config.json"""
    config_dict = {
        "architectures": ["TinyLLM"],
        "model_type": "tiny_llm",
        "vocab_size": config.vocab_size,
        "max_position_embeddings": config.max_seq_length,
        "hidden_size": config.embed_dim,
        "num_attention_heads": config.num_heads,
        "num_hidden_layers": config.num_layers,
        "intermediate_size": config.ffn_dim,
        "hidden_act": "gelu",
        "hidden_dropout_prob": config.dropout,
        "attention_probs_dropout_prob": config.attention_dropout,
        "initializer_range": 0.02,
        "layer_norm_eps": 1e-5,
        "bos_token_id": 2,
        "eos_token_id": 3,
        "pad_token_id": 0,
        "torch_dtype": "float32",
        "transformers_version": "4.0.0",
    }
    
    config_path = save_dir / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已創建: {config_path}")


def create_tokenizer_config(tokenizer: BilingualTokenizer, save_dir: Path) -> None:
    """創建 tokenizer_config.json"""
    tokenizer_config = {
        "tokenizer_class": "BilingualTokenizer",
        "vocab_size": len(tokenizer.vocab),
        "model_max_length": 512,
        "padding_side": "right",
        "truncation_side": "right",
        "special_tokens": tokenizer.special_tokens,
        "bos_token": tokenizer.special_tokens["bos_token"],
        "eos_token": tokenizer.special_tokens["eos_token"],
        "unk_token": tokenizer.special_tokens["unk_token"],
        "sep_token": tokenizer.special_tokens["sep_token"],
        "pad_token": tokenizer.special_tokens["pad_token"],
        "cls_token": tokenizer.special_tokens["cls_token"],
        "mask_token": tokenizer.special_tokens["mask_token"],
    }
    
    config_path = save_dir / "tokenizer_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(tokenizer_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已創建: {config_path}")


def create_vocab_json(tokenizer: BilingualTokenizer, save_dir: Path) -> None:
    """創建 vocab.json"""
    vocab_path = save_dir / "vocab.json"
    with open(vocab_path, 'w', encoding='utf-8') as f:
        json.dump(tokenizer.vocab, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已創建: {vocab_path}")


def create_model_card(save_dir: Path) -> None:
    """創建 README.md (模型卡片)"""
    readme_content = """# 英中雙語小型語言模型 (Tiny LLM)

## 模型描述

這是一個專為英文和中文設計的小型語言模型，基於 GPT 架構。

### 模型規格

- **參數量**: 124M (1.24億)
- **架構**: GPT-like Transformer
- **層數**: 12
- **注意力頭數**: 12
- **嵌入維度**: 768
- **FFN 維度**: 3072
- **詞彙表大小**: 30,000
- **最大序列長度**: 512
- **支持語言**: 英文、中文

## 使用方法

### 載入模型

```python
import torch
from bioneuronai import load_llm

# 載入模型
model, checkpoint = load_llm("path/to/model/pytorch_model.bin")

# 生成文本
prompt = torch.tensor([[1, 2, 3, 4, 5]])  # 需要 tokenizer 編碼
output = model.generate(prompt, max_new_tokens=50)
```

### 使用 Tokenizer

```python
from bilingual_tokenizer import BilingualTokenizer

# 載入 tokenizer
tokenizer = BilingualTokenizer.load("path/to/tokenizer/tokenizer.pkl")

# 編碼
text = "Hello 你好"
ids = tokenizer.encode(text)

# 解碼
decoded_text = tokenizer.decode(ids)
```

## 訓練數據

模型使用英文和中文文本數據訓練（當前為隨機初始化，需要實際訓練）。

## 限制

- 當前模型為隨機初始化，需要在實際數據上訓練才能使用
- 僅支持英文和中文，其他語言未經優化
- 最大序列長度為 512 tokens

## 技術細節

### 架構

- **嵌入層**: Token Embedding + Position Embedding
- **Transformer 層**: 12 層，每層包含:
  - Multi-Head Self-Attention (12 heads)
  - Feed Forward Network (768 → 3072 → 768)
  - Layer Normalization
  - Residual Connections
- **輸出層**: Language Model Head (權重與 Token Embedding 共享)

### 訓練配置

建議配置:
- Learning Rate: 1e-4 ~ 5e-4
- Batch Size: 8-32
- Sequence Length: 256-512
- Warmup Steps: 1000-5000
- Optimizer: AdamW

## 檔案結構

```
model_directory/
├── config.json              # 模型配置
├── pytorch_model.bin        # 模型權重
├── tokenizer_config.json    # Tokenizer 配置
├── tokenizer.pkl            # Tokenizer 檔案
├── vocab.json               # 詞彙表
├── special_tokens_map.json  # 特殊 tokens 映射
└── README.md               # 本檔案
```

## 授權

MIT License

## 引用

如果你使用這個模型，請引用:

```bibtex
@software{tiny_llm_bilingual,
  author = {BioNeuronai Team},
  title = {Tiny LLM: 英中雙語小型語言模型},
  year = {2026},
  url = {https://github.com/yourusername/bioneuronai}
}
```

## 聯繫

如有問題，請提交 Issue。

---

**版本**: 1.0.0  
**創建日期**: 2026-01-19  
**模型類型**: Causal Language Model  
**語言**: 英文 (en), 中文 (zh)
"""
    
    readme_path = save_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ 已創建: {readme_path}")


def create_special_tokens_map(tokenizer: BilingualTokenizer, save_dir: Path) -> None:
    """創建 special_tokens_map.json"""
    special_tokens_map = {
        "bos_token": tokenizer.special_tokens["bos_token"],
        "eos_token": tokenizer.special_tokens["eos_token"],
        "unk_token": tokenizer.special_tokens["unk_token"],
        "sep_token": tokenizer.special_tokens["sep_token"],
        "pad_token": tokenizer.special_tokens["pad_token"],
        "cls_token": tokenizer.special_tokens["cls_token"],
        "mask_token": tokenizer.special_tokens["mask_token"],
    }
    
    map_path = save_dir / "special_tokens_map.json"
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(special_tokens_map, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 已創建: {map_path}")


def create_complete_model_package(
    model_dir: str = "models/tiny_llm_en_zh",
    from_checkpoint: Optional[str] = None
) -> None:
    """創建完整的模型包
    
    包含:
    1. config.json - 模型配置
    2. pytorch_model.bin - 模型權重
    3. tokenizer_config.json - Tokenizer 配置
    4. tokenizer.pkl - Tokenizer 檔案
    5. vocab.json - 詞彙表
    6. special_tokens_map.json - 特殊 tokens
    7. README.md - 模型卡片
    """
    
    print("=" * 70)
    print("📦 創建完整語言模型包")
    print("=" * 70)
    
    model_dir_path = Path(model_dir)
    model_dir_path.mkdir(parents=True, exist_ok=True)
    
    # 1. 創建/載入模型
    print("\n1️⃣ 準備模型...")
    if from_checkpoint:
        checkpoint = torch.load(from_checkpoint, map_location='cpu', weights_only=False)
        config = TinyLLMConfig.from_dict(checkpoint["config"])
        model = TinyLLM(config)
        model.load_state_dict(checkpoint["state_dict"])
        print(f"   已從檢查點載入: {from_checkpoint}")
    else:
        # 創建新模型（針對英中雙語）
        config = TinyLLMConfig(
            vocab_size=30000,  # 英中雙語詞彙表
            max_seq_length=512,
            embed_dim=768,
            num_heads=12,
            num_layers=12,
            ffn_dim=3072,
            dropout=0.1,
            attention_dropout=0.1,
        )
        model = TinyLLM(config)
        print(f"   已創建新模型 (隨機初始化)")
    
    # 2. 創建 config.json
    print("\n2️⃣ 創建模型配置...")
    create_config_json(config, model_dir_path)
    
    # 3. 保存模型權重
    print("\n3️⃣ 保存模型權重...")
    model_path = model_dir_path / "pytorch_model.bin"
    torch.save(model.state_dict(), model_path)
    file_size = model_path.stat().st_size / 1024 / 1024
    print(f"✅ 已保存: {model_path} ({file_size:.2f} MB)")
    
    # 4. 創建 Tokenizer
    print("\n4️⃣ 創建 Tokenizer...")
    tokenizer = create_bilingual_tokenizer(vocab_size=config.vocab_size)
    
    # 5. 保存 Tokenizer
    print("\n5️⃣ 保存 Tokenizer...")
    tokenizer_path = model_dir_path / "tokenizer.pkl"
    tokenizer.save(str(tokenizer_path))
    
    # 6. 創建 tokenizer_config.json
    print("\n6️⃣ 創建 Tokenizer 配置...")
    create_tokenizer_config(tokenizer, model_dir_path)
    
    # 7. 創建 vocab.json
    print("\n7️⃣ 創建詞彙表...")
    create_vocab_json(tokenizer, model_dir_path)
    
    # 8. 創建 special_tokens_map.json
    print("\n8️⃣ 創建特殊 tokens 映射...")
    create_special_tokens_map(tokenizer, model_dir_path)
    
    # 9. 創建 README.md
    print("\n9️⃣ 創建模型卡片...")
    create_model_card(model_dir_path)
    
    # 10. 創建元數據
    print("\n🔟 創庺元數據...")
    metadata = {
        "model_name": "tiny_llm_en_zh",
        "version": "1.0.0",
        "created_at": "2026-01-19",
        "description": "英中雙語小型語言模型",
        "languages": ["en", "zh"],
        "parameters": sum(p.numel() for p in model.parameters()),
        "architecture": "GPT-like Transformer",
        "license": "MIT",
    }
    
    metadata_path = model_dir_path / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ 已創建: {metadata_path}")
    
    # 總結
    print("\n" + "=" * 70)
    print("✅ 模型包創建完成!")
    print("=" * 70)
    print(f"\n📂 模型目錄: {model_dir}")
    print(f"📊 模型參數: {sum(p.numel() for p in model.parameters()):,}")
    print(f"📝 詞彙表大小: {len(tokenizer.vocab)}")
    print(f"🌏 支持語言: 英文 (en), 中文 (zh)")
    
    print("\n📦 檔案列表:")
    for file in sorted(model_dir_path.glob("*")):
        size = file.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / 1024 / 1024:.2f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.2f} KB"
        else:
            size_str = f"{size} bytes"
        print(f"  ✓ {file.name:30s} {size_str:>15s}")
    
    print("\n💡 下一步:")
    print("1. 準備英文和中文訓練數據")
    print("2. 訓練模型")
    print("3. 評估模型性能")
    print("4. 開始使用!")


if __name__ == "__main__":
    # 創建完整模型包
    create_complete_model_package(
        model_dir="models/tiny_llm_en_zh",
        from_checkpoint="weights/tiny_llm_100m.pth"  # 使用現有權重
    )
