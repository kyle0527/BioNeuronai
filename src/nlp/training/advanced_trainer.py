"""
高級訓練腳本
===========
包含梯度累積、混合精度訓練、學習率調度等高級功能
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.cuda.amp import autocast, GradScaler
from pathlib import Path
import sys
import json
import time
from typing import Dict, cast
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent.parent))

from nlp.tiny_llm import TinyLLM, TinyLLMConfig


@dataclass
class TrainingConfig:
    """訓練配置"""
    # 基礎配置
    batch_size: int = 8
    gradient_accumulation_steps: int = 4  # 梯度累積步數
    max_epochs: int = 10
    learning_rate: float = 3e-4
    weight_decay: float = 0.01

    # 學習率調度
    warmup_steps: int = 500
    lr_scheduler_type: str = "cosine"  # "cosine", "linear", "constant"

    # 混合精度訓練
    use_amp: bool = True  # 自動混合精度

    # 梯度裁剪
    max_grad_norm: float = 1.0

    # 評估和保存
    eval_steps: int = 500
    save_steps: int = 1000
    logging_steps: int = 100

    # 設備
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

    # 輸出
    output_dir: str = "./output"

    # ── 多任務設定 ──────────────────────────────────────────────────────────────
    # 啟用後，每個 global_step 交替執行語言任務與訊號任務
    multitask: bool = False
    # 兩種 loss 的加權比例：total_loss = lm_loss + signal_loss_weight * signal_loss
    signal_loss_weight: float = 0.5
    # 序列長度（訊號任務：最近幾步 K 線特徵組成一個序列）
    signal_seq_len: int = 16

    def to_dict(self) -> Dict:
        """轉換為字典"""
        return asdict(self)


class Trainer:
    """高級訓練器（支援純語言模式與多任務模式）"""

    def __init__(
        self,
        model: TinyLLM,
        train_config: TrainingConfig,
        train_dataloader,
        eval_dataloader=None,
        signal_dataloader=None,       # 多任務模式：訊號任務的資料加載器
    ):
        self.model = model
        self.config = train_config
        self.train_dataloader = train_dataloader
        self.eval_dataloader = eval_dataloader
        self.signal_dataloader = signal_dataloader
        self._signal_iter = None      # 用於循環取 signal batch

        # 移動模型到設備
        self.device = torch.device(train_config.device)
        self.model = self.model.to(self.device)
        
        # 優化器
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=train_config.learning_rate,
            weight_decay=train_config.weight_decay
        )
        
        # 學習率調度器
        total_steps = len(train_dataloader) * train_config.max_epochs // train_config.gradient_accumulation_steps
        self.scheduler = self._create_scheduler(total_steps)
        
        # 混合精度訓練
        self.scaler = GradScaler() if train_config.use_amp else None
        
        # 訓練狀態
        self.global_step = 0
        self.current_epoch = 0
        self.best_loss = float('inf')
        
        # 訓練歷史
        self.train_history: Dict[str, list[float]] = {
            'train_loss': [],
            'lm_loss': [],
            'signal_loss': [],
            'eval_loss': [],
            'learning_rate': [],
            'epoch': [],
            'step': []
        }
        
        # 創建輸出目錄
        self.output_dir = Path(train_config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_scheduler(self, total_steps: int):
        """創建學習率調度器"""
        if self.config.lr_scheduler_type == "cosine":
            return optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=total_steps - self.config.warmup_steps,
                eta_min=1e-6
            )
        elif self.config.lr_scheduler_type == "linear":
            return optim.lr_scheduler.LinearLR(
                self.optimizer,
                start_factor=1.0,
                end_factor=0.1,
                total_iters=total_steps
            )
        else:  # constant
            return optim.lr_scheduler.ConstantLR(
                self.optimizer,
                factor=1.0
            )
    
    def _warmup_lr(self, step: int) -> float:
        """計算 warmup 學習率"""
        if step < self.config.warmup_steps:
            return self.config.learning_rate * (step / self.config.warmup_steps)
        return self.config.learning_rate
    
    def train(self):
        """訓練模型"""
        print("=" * 80)
        print("開始訓練")
        print("=" * 80)
        print(f"設備: {self.device}")
        print(f"批次大小: {self.config.batch_size}")
        print(f"梯度累積步數: {self.config.gradient_accumulation_steps}")
        print(f"有效批次大小: {self.config.batch_size * self.config.gradient_accumulation_steps}")
        print(f"最大 Epoch: {self.config.max_epochs}")
        print(f"學習率: {self.config.learning_rate}")
        print(f"使用混合精度: {self.config.use_amp}")
        print(f"總步數: {len(self.train_dataloader) * self.config.max_epochs // self.config.gradient_accumulation_steps}")
        print("=" * 80)
        
        start_time = time.time()
        
        for epoch in range(self.config.max_epochs):
            self.current_epoch = epoch
            self._train_epoch()
            
            # 評估
            if self.eval_dataloader is not None:
                eval_loss = self._evaluate()
                print(f"\nEpoch {epoch + 1} - 評估損失: {eval_loss:.4f}")
                
                # 保存最佳模型
                if eval_loss < self.best_loss:
                    self.best_loss = eval_loss
                    self._save_checkpoint("best_model")
                    print(f"✓ 保存最佳模型 (損失: {eval_loss:.4f})")
        
        total_time = time.time() - start_time
        print("\n" + "=" * 80)
        print("訓練完成!")
        print(f"總時間: {total_time:.2f} 秒 ({total_time/60:.2f} 分鐘)")
        print("=" * 80)
        
        # 保存最終模型和訓練歷史
        self._save_checkpoint("final_model")
        self._save_training_history()
    
    def _next_signal_batch(self):
        """從 signal_dataloader 循環取下一個 batch（無限迭代）"""
        if self._signal_iter is None:
            self._signal_iter = iter(self.signal_dataloader)
        try:
            return next(self._signal_iter)
        except StopIteration:
            self._signal_iter = iter(self.signal_dataloader)
            return next(self._signal_iter)

    def _compute_signal_loss(
        self, features: "torch.Tensor", signal_labels: "torch.Tensor"
    ) -> "torch.Tensor":
        """
        訊號任務 MSE Loss。
        features:      (B, T, 1024) — 時序特徵序列
        signal_labels: (B, 512)     — SignalInterpreter 輸出格式的標籤
        """
        signal_output = self.model.forward_signal(features)   # (B, 512)
        return nn.functional.mse_loss(signal_output, signal_labels)

    def _train_epoch(self):
        """訓練一個 epoch"""
        self.model.train()
        total_loss = 0.0
        total_lm_loss = 0.0
        total_signal_loss = 0.0
        num_batches = 0

        # sig_only 旗標由 unified_trainer 動態注入
        sig_only: bool = getattr(self, "_run_sig_only", False)
        multitask = self.config.multitask and self.signal_dataloader is not None

        self.optimizer.zero_grad()

        for batch_idx, batch in enumerate(self.train_dataloader):
            # ── sig_only 模式：batch 只含 feature_seq / signal_labels ──────────
            if sig_only:
                feat_seq = batch['feature_seq'].to(self.device)      # (B, T, 1024)
                sig_labels = batch['signal_labels'].to(self.device)  # (B, 512)
                if self.config.use_amp:
                    with autocast():
                        combined_loss = self._compute_signal_loss(feat_seq, sig_labels)
                else:
                    combined_loss = self._compute_signal_loss(feat_seq, sig_labels)
                total_signal_loss += combined_loss.item()
                lm_loss = combined_loss  # 供下方統一記錄
            else:
                # ── 語言任務 ─────────────────────────────────────────────────────
                input_ids = batch['input_ids'].to(self.device)
                labels = batch['labels'].to(self.device) if 'labels' in batch else input_ids

                if self.config.use_amp:
                    with autocast():
                        logits = self.model(input_ids)
                        lm_loss = self._compute_loss(logits, labels)
                else:
                    logits = self.model(input_ids)
                    lm_loss = self._compute_loss(logits, labels)

                # ── 訊號任務（多任務模式）──────────────────────────────────────
                signal_loss_val = 0.0
                if multitask:
                    sig_batch = self._next_signal_batch()
                    feat_seq = sig_batch['feature_seq'].to(self.device)    # (B, T, 1024)
                    sig_labels = sig_batch['signal_labels'].to(self.device) # (B, 512)
                    if self.config.use_amp:
                        with autocast():
                            sig_loss = self._compute_signal_loss(feat_seq, sig_labels)
                    else:
                        sig_loss = self._compute_signal_loss(feat_seq, sig_labels)
                    signal_loss_val = sig_loss.item()
                    combined_loss = (lm_loss + self.config.signal_loss_weight * sig_loss)
                else:
                    combined_loss = lm_loss
                total_signal_loss += signal_loss_val

            combined_loss = combined_loss / self.config.gradient_accumulation_steps

            if self.config.use_amp:
                assert self.scaler is not None
                self.scaler.scale(combined_loss).backward()
            else:
                combined_loss.backward()

            total_loss += combined_loss.item() * self.config.gradient_accumulation_steps
            total_lm_loss += lm_loss.item()
            num_batches += 1

            # ── 梯度累積 & 優化器步進 ──────────────────────────────────────────
            if (batch_idx + 1) % self.config.gradient_accumulation_steps == 0:
                if self.config.max_grad_norm > 0:
                    if self.config.use_amp:
                        assert self.scaler is not None
                        self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), self.config.max_grad_norm
                    )

                if self.config.use_amp:
                    assert self.scaler is not None
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    self.optimizer.step()

                if self.global_step < self.config.warmup_steps:
                    lr = self._warmup_lr(self.global_step)
                    for param_group in self.optimizer.param_groups:
                        param_group['lr'] = lr
                else:
                    self.scheduler.step()

                self.optimizer.zero_grad()
                self.global_step += 1

                # ── 記錄 ──────────────────────────────────────────────────────
                if self.global_step % self.config.logging_steps == 0:
                    avg_loss = total_loss / num_batches
                    avg_lm = total_lm_loss / num_batches
                    avg_sig = total_signal_loss / num_batches
                    current_lr = self.optimizer.param_groups[0]['lr']

                    if multitask:
                        print(
                            f"Epoch {self.current_epoch + 1} | Step {self.global_step} | "
                            f"Loss: {avg_loss:.4f} (LM: {avg_lm:.4f}, Sig: {avg_sig:.4f}) | "
                            f"LR: {current_lr:.2e}"
                        )
                    else:
                        print(
                            f"Epoch {self.current_epoch + 1} | Step {self.global_step} | "
                            f"Loss: {avg_loss:.4f} | LR: {current_lr:.2e}"
                        )

                    self.train_history['train_loss'].append(avg_loss)
                    self.train_history['lm_loss'].append(avg_lm)
                    self.train_history['signal_loss'].append(avg_sig)
                    self.train_history['learning_rate'].append(current_lr)
                    self.train_history['step'].append(self.global_step)
                    self.train_history['epoch'].append(self.current_epoch)

                    total_loss = total_lm_loss = total_signal_loss = 0.0
                    num_batches = 0

                if self.global_step % self.config.save_steps == 0:
                    self._save_checkpoint(f"checkpoint-{self.global_step}")
    
    def _evaluate(self) -> float:
        """評估模型"""
        if self.eval_dataloader is None:
            return float('inf')
        
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in self.eval_dataloader:
                input_ids = batch['input_ids'].to(self.device)
                labels = batch['labels'].to(self.device) if 'labels' in batch else input_ids
                
                if self.config.use_amp:
                    with autocast():
                        logits = self.model(input_ids)
                        loss = self._compute_loss(logits, labels)
                else:
                    logits = self.model(input_ids)
                    loss = self._compute_loss(logits, labels)
                
                total_loss += loss.item()
                num_batches += 1
        
        avg_loss = total_loss / num_batches
        self.train_history['eval_loss'].append(avg_loss)
        
        self.model.train()
        return avg_loss
    
    def _compute_loss(self, logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """計算損失"""
        # 語言模型損失: 預測下一個 token
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        
        loss_fct = nn.CrossEntropyLoss()
        loss = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1)
        )
        
        return cast(torch.Tensor, loss.contiguous())
    
    def _save_checkpoint(self, name: str):
        """保存檢查點"""
        checkpoint_dir = self.output_dir / name
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存模型
        torch.save(
            self.model.state_dict(),
            checkpoint_dir / "model.pth"
        )
        
        # 保存配置
        with open(checkpoint_dir / "config.json", 'w', encoding='utf-8') as f:
            json.dump(self.model.config.to_dict(), f, indent=2, ensure_ascii=False)
        
        # 保存訓練狀態
        torch.save({
            'epoch': self.current_epoch,
            'global_step': self.global_step,
            'optimizer_state': self.optimizer.state_dict(),
            'scheduler_state': self.scheduler.state_dict(),
            'best_loss': self.best_loss,
            'train_config': self.config.to_dict()
        }, checkpoint_dir / "training_state.pth")
    
    def _save_training_history(self):
        """保存訓練歷史"""
        history_path = self.output_dir / "training_history.json"
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(self.train_history, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 訓練歷史已保存至: {history_path}")


def create_real_dataloader(
    data_pairs: list,
    tokenizer,
    max_length: int = 128,
    batch_size: int = 8,
    shuffle: bool = True
):
    """創建真實的數據加載器
    
    Args:
        data_pairs: 包含 (input, output) 對的列表
        tokenizer: BilingualTokenizer 實例
        max_length: 最大序列長度
        batch_size: 批次大小
        shuffle: 是否打亂數據
    """
    from torch.utils.data import Dataset, DataLoader
    
    class TextPairDataset(Dataset):
        def __init__(self, data_pairs, tokenizer, max_length):
            self.data_pairs = data_pairs
            self.tokenizer = tokenizer
            self.max_length = max_length
        
        def __len__(self):
            return len(self.data_pairs)
        
        def __getitem__(self, idx):
            input_text, output_text = self.data_pairs[idx]
            
            # 組合為訓練格式
            text = f"{input_text} {output_text}"
            
            # 編碼
            ids = self.tokenizer.encode(text, add_special_tokens=False)
            
            # 截斷或填充
            if len(ids) > self.max_length:
                ids = ids[:self.max_length]
            else:
                ids = ids + [self.tokenizer.pad_token_id] * (self.max_length - len(ids))
            
            return torch.tensor(ids, dtype=torch.long)
    
    dataset = TextPairDataset(data_pairs, tokenizer, max_length)
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=0
    )
    
    # 包裝為字典格式（與 Trainer 兼容）
    class DataLoaderWrapper:
        def __init__(self, dataloader):
            self.dataloader = dataloader
        
        def __iter__(self):
            for batch in self.dataloader:
                yield {'input_ids': batch}
        
        def __len__(self):
            return len(self.dataloader)
    
    return DataLoaderWrapper(dataloader)


def main():
    """主函數 - 真實訓練示例"""
    import sys
    from pathlib import Path
    
    # 添加路徑
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from nlp.tiny_llm import TinyLLM
    from nlp.bilingual_tokenizer import BilingualTokenizer
    
    print("=" * 60)
    print("BioNeuronAI - 真實訓練示例")
    print("=" * 60)
    
    # 載入或創建 tokenizer
    tokenizer_path = Path("model/tokenizer/vocab.json")

    if tokenizer_path.exists():
        print(f"\n📖 載入 tokenizer: {tokenizer_path}")
        tokenizer = BilingualTokenizer.load(str(tokenizer_path))
    else:
        print("\n⚠️  未找到 tokenizer，請先執行 build_vocab.py：")
        print("   python -m nlp.training.build_vocab")
        return
    
    # 創建模型配置（與已訓練模型相同）
    model_config = TinyLLMConfig(
        vocab_size=tokenizer.vocab_size,
        max_seq_length=128,
        embed_dim=384,
        num_layers=6,
        num_heads=6,
        dropout=0.1
    )
    
    model = TinyLLM(model_config)
    print(f"\n🤖 模型參數: {model.count_parameters():,}")
    
    # 準備訓練數據（示例）
    train_data = [
        ("Hello", "Hi there! How can I help you?"),
        ("What is AI?", "AI is Artificial Intelligence."),
        ("你好", "你好！很高興見到你。"),
        ("什麼是機器學習？", "機器學習是讓電腦從數據中學習的技術。"),
        ("Thank you", "You're welcome!"),
        ("謝謝", "不客氣！"),
    ]
    
    eval_data = [
        ("Hi", "Hello! How are you?"),
        ("什麼是AI？", "AI是人工智慧。"),
    ]
    
    print(f"\n📊 訓練數據: {len(train_data)} 樣本")
    print(f"📊 評估數據: {len(eval_data)} 樣本")
    
    # 創建數據加載器
    train_dataloader = create_real_dataloader(
        data_pairs=train_data,
        tokenizer=tokenizer,
        max_length=model_config.max_seq_length,
        batch_size=2,
        shuffle=True
    )
    
    eval_dataloader = create_real_dataloader(
        data_pairs=eval_data,
        tokenizer=tokenizer,
        max_length=model_config.max_seq_length,
        batch_size=2,
        shuffle=False
    )
    
    # 訓練配置
    train_config = TrainingConfig(
        batch_size=2,
        gradient_accumulation_steps=2,
        max_epochs=3,
        learning_rate=3e-4,
        warmup_steps=10,
        eval_steps=3,
        save_steps=10,
        logging_steps=1,
        output_dir="./training_output_demo"
    )
    
    print("\n⚙️  訓練配置:")
    print(f"   批次大小: {train_config.batch_size}")
    print(f"   梯度累積: {train_config.gradient_accumulation_steps}")
    print(f"   訓練輪數: {train_config.max_epochs}")
    print(f"   學習率: {train_config.learning_rate}")
    
    # 創建訓練器
    trainer = Trainer(
        model=model,
        train_config=train_config,
        train_dataloader=train_dataloader,
        eval_dataloader=eval_dataloader
    )
    
    print("\n🚀 開始訓練...")
    print("=" * 60)
    
    # 開始訓練
    trainer.train()
    
    print("\n✅ 訓練完成！")
    print(f"   模型保存在: {train_config.output_dir}")
    print("\n💡 提示: 使用更多數據和更長訓練可以獲得更好的效果")
    print("   建議使用 training/train_with_ai_teacher.py 進行完整訓練")


if __name__ == "__main__":
    main()
