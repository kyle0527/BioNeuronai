"""
自動進化訓練腳本
================
自動使用進化數據進行微調

使用方式：
python auto_evolve.py
"""

import torch
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.bioneuronai.tiny_llm import TinyLLM, TinyLLMConfig
from src.bioneuronai.bilingual_tokenizer import BilingualTokenizer
from torch.utils.data import Dataset, DataLoader
import torch.optim as optim
from tqdm import tqdm


class EvolutionDataset(Dataset):
    """進化訓練數據集"""
    
    def __init__(self, evolution_data_file: str, tokenizer: BilingualTokenizer, max_length: int = 128):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.data = []
        
        # 載入進化數據
        with open(evolution_data_file, 'r', encoding='utf-8') as f:
            samples = json.load(f)
        
        for sample in samples:
            if sample.get("quality") in ["high", "medium", "corrected"]:
                text = f"{sample['input']} {sample['output']}"
                self.data.append(text)
        
        print(f"📚 載入了 {len(self.data)} 個進化訓練樣本")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        text = self.data[idx]
        tokens = self.tokenizer.encode(text)
        
        # 截斷或填充
        if len(tokens) > self.max_length:
            tokens = tokens[:self.max_length]
        else:
            tokens = tokens + [self.tokenizer.pad_token_id] * (self.max_length - len(tokens))
        
        input_ids = torch.tensor(tokens[:-1])
        labels = torch.tensor(tokens[1:])
        
        return input_ids, labels


def auto_evolve_training(
    model_path: str = "./models/tiny_llm_en_zh_trained",
    evolution_data_file: str = "./evolution_data/new_training_data.json",
    output_path: str = "./models/tiny_llm_evolved",
    num_epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 1e-5
):
    """
    自動進化訓練
    
    Args:
        model_path: 基礎模型路徑
        evolution_data_file: 進化數據文件
        output_path: 輸出路徑
        num_epochs: 訓練輪數
        batch_size: 批次大小
        learning_rate: 學習率（較小，防止過擬合）
    """
    
    print("=" * 80)
    print("🧬 AI 自動進化訓練")
    print("=" * 80)
    
    # 檢查進化數據
    evolution_file = Path(evolution_data_file)
    if not evolution_file.exists():
        print(f"\n❌ 未找到進化數據: {evolution_file}")
        print("   請先使用 use_model_evolving.py 收集反饋數據\n")
        return
    
    # 載入基礎模型
    print("\n📦 載入基礎模型...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    with open(Path(model_path) / "config.json", 'r') as f:
        config_dict = json.load(f)
    
    config = TinyLLMConfig(**config_dict)
    model = TinyLLM(config).to(device)
    
    # 載入權重
    weights_file = Path(model_path) / "pytorch_model.bin"
    if weights_file.exists():
        model.load_state_dict(torch.load(weights_file, map_location=device))
        print("   ✅ 已載入基礎權重")
    
    # 載入分詞器
    vocab_file = Path(model_path) / "vocab.json"
    if vocab_file.exists():
        tokenizer = BilingualTokenizer.load(str(model_path))
    else:
        tokenizer = BilingualTokenizer()
    
    # 準備進化數據
    print("\n📚 準備進化訓練數據...")
    dataset = EvolutionDataset(evolution_data_file, tokenizer)
    
    if len(dataset) < 10:
        print(f"\n⚠️  警告：進化數據太少 ({len(dataset)} 個樣本)")
        print("   建議收集至少 50-100 個高質量樣本再進化\n")
        response = input("是否繼續？(y/N): ").strip().lower()
        if response != 'y':
            print("已取消")
            return
    
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # 優化器（使用較小學習率）
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    
    # 訓練
    print(f"\n🚀 開始進化訓練...")
    print(f"   輪數: {num_epochs}")
    print(f"   批次: {batch_size}")
    print(f"   學習率: {learning_rate}")
    print(f"   設備: {device}\n")
    
    model.train()
    avg_loss = 0.0  # 初始化以避免未綁定錯誤
    
    for epoch in range(num_epochs):
        total_loss = 0
        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch+1}/{num_epochs}")
        
        for batch_idx, (input_ids, labels) in enumerate(progress_bar):
            input_ids = input_ids.to(device)
            labels = labels.to(device)
            
            # 前向傳播
            outputs = model(input_ids)
            logits = outputs.logits
            
            # 計算損失
            loss = torch.nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
                ignore_index=tokenizer.pad_token_id
            )
            
            # 反向傳播
            optimizer.zero_grad()
            loss.backward()
            
            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            
            optimizer.step()
            
            total_loss += loss.item()
            progress_bar.set_postfix({"loss": loss.item()})
        
        avg_loss = total_loss / len(dataloader)
        print(f"   Epoch {epoch+1} - 平均損失: {avg_loss:.4f}")
    
    # 保存進化後的模型
    print(f"\n💾 保存進化模型到: {output_path}")
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存權重
    torch.save(model.state_dict(), output_dir / "pytorch_model.bin")
    
    # 保存配置
    with open(output_dir / "config.json", 'w') as f:
        json.dump(config_dict, f, indent=2)
    
    # 複製分詞器
    if vocab_file.exists():
        import shutil
        shutil.copy(vocab_file, output_dir / "vocab.json")
    
    print("   ✅ 模型已保存")
    
    # 統計信息
    print("\n" + "=" * 80)
    print("✅ 進化訓練完成！")
    print("=" * 80)
    print(f"   訓練樣本: {len(dataset)}")
    print(f"   訓練輪數: {num_epochs}")
    if 'avg_loss' in locals() and avg_loss is not None:
        print(f"   最終損失: {avg_loss:.4f}")
    else:
        print(f"   最終損失: N/A")
    print(f"   模型版本: V2 (進化版)")
    print("\n💡 測試進化模型:")
    print(f"   python use_model.py --model {output_path}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI 自動進化訓練")
    parser.add_argument("--model", default="./models/tiny_llm_en_zh_trained", help="基礎模型路徑")
    parser.add_argument("--data", default="./evolution_data/new_training_data.json", help="進化數據路徑")
    parser.add_argument("--output", default="./models/tiny_llm_evolved", help="輸出路徑")
    parser.add_argument("--epochs", type=int, default=3, help="訓練輪數")
    parser.add_argument("--batch-size", type=int, default=4, help="批次大小")
    parser.add_argument("--lr", type=float, default=1e-5, help="學習率")
    
    args = parser.parse_args()
    
    auto_evolve_training(
        model_path=args.model,
        evolution_data_file=args.data,
        output_path=args.output,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
