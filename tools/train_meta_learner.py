"""
Meta-Learner 訓練腳本
執行方式：在專案根目錄下執行
    python tools/train_meta_learner.py
"""
import sys
import logging
from pathlib import Path

# 直接加入 meta_learner 的父目錄，避免觸發 bioneuronai/__init__.py 的全量載入
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

# 直接匯入 trainer 模組 (繞過 bioneuronai.__init__)
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "trainer",
    _ROOT / "src" / "bioneuronai" / "strategies" / "meta_learner" / "trainer.py"
)
_mod = _ilu.module_from_spec(_spec)  # type: ignore
_spec.loader.exec_module(_mod)       # type: ignore
MetaLearnerTrainer = _mod.MetaLearnerTrainer
EPOCHS = _mod.EPOCHS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    print("=" * 60)
    print("BioNeuronAI Meta-Learner 訓練器")
    print("=" * 60)
    print(f"資料來源: backtest/data/binance_historical (BTCUSDT 1H)")
    print(f"訓練週期: 最多 {EPOCHS} epochs (含 Early Stopping)")
    print("=" * 60)

    trainer = MetaLearnerTrainer(
        symbol="BTCUSDT",
        interval="1h",
    )

    log = trainer.train(epochs=EPOCHS, verbose=True)

    print("\n" + "=" * 60)
    print("訓練結果摘要")
    print("=" * 60)
    print(f"  總樣本數:     {log['total_samples']}")
    print(f"  最佳驗證損失: {log['best_val_loss']:.4f}")
    print(f"  模型儲存至:   rl_models/meta_learner.pth")
    print(f"  策略對應:     {log['strategy_names']}")
    print("=" * 60)
