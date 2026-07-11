"""
Meta-Learner 訓練器
====================
使用真實的本地歷史 OHLCV 資料，透過回測標籤生成訓練集，
並訓練 MetaLearnerModel，訓練完成後儲存至 rl_models/ 目錄。

訓練流程：
1. 載入本地 ZIP 歷史資料 (backtest/data/binance_historical)
2. 滑動視窗：每 WINDOW 根 K 線計算一次特徵，並用「未來 N 根」的策略績效作為標籤
3. 標籤定義：對每個時間點模擬各策略的方向，乘上未來實際報酬，勝率最高者取得最高權重
4. 訓練神經網路 (CrossEntropy + 軟標籤)
5. 儲存模型

執行方式：
    python -m bioneuronai.strategies.meta_learner.trainer
    或
    python tools/train_meta_learner.py
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# 確保可以找到專案根模組
# trainer.py 位於: src/bioneuronai/strategies/meta_learner/trainer.py
# 所以往上 4 層才是專案根目錄
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from .feature_extractor import FeatureExtractor
    from .model import EVENT_FEATURE_DIM, MARKET_FEATURE_DIM, STRATEGY_NAMES, MetaLearnerModel
except ImportError:
    # 當以独立模組方式執行時
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_dir = _Path(__file__).resolve().parent
    if str(_pkg_dir) not in _sys.path:
        _sys.path.insert(0, str(_pkg_dir))
    from feature_extractor import FeatureExtractor  # type: ignore

    from model import (  # type: ignore
        EVENT_FEATURE_DIM,
        MARKET_FEATURE_DIM,
        STRATEGY_NAMES,
        MetaLearnerModel,
    )

logger = logging.getLogger(__name__)

# ── 超參數 ───────────────────────────────────────────────────────────
WINDOW_SIZE = 80          # 每個樣本使用過去 80 根 K 線計算特徵
FORWARD_BARS = 5          # 以未來 5 根 K 線的策略績效作為標籤依據
STEP_SIZE = 10            # 每隔 10 根取一個樣本 (避免樣本高度相關)
BATCH_SIZE = 64
EPOCHS = 100
LEARNING_RATE = 3e-4
WEIGHT_DECAY = 1e-4
PATIENCE = 15             # Early stopping 耐心值
MODEL_SAVE_DIR = _PROJECT_ROOT / "rl_models"
MODEL_FILENAME = "meta_learner.pth"
TRAINING_LOG_FILENAME = "meta_learner_training_log.json"


# ── 策略方向模擬 ─────────────────────────────────────────────────────
def _simulate_strategy_direction(
    ohlcv: np.ndarray,
    strategy_name: str,
) -> float:
    """
    用純技術指標快速模擬各策略在當前時間點的訊號方向。
    返回 +1 (做多), -1 (做空), 0 (中立)
    這不是完整的策略實作，而是用於標籤生成的輕量代理函數。
    """
    c = ohlcv[:, 3].astype(float)
    h = ohlcv[:, 2].astype(float)
    low = ohlcv[:, 1].astype(float)

    if len(c) < 26:
        return 0.0

    if strategy_name == "trend_following":
        sma20 = np.mean(c[-20:])
        sma50 = np.mean(c[-50:]) if len(c) >= 50 else np.mean(c)
        return 1.0 if sma20 > sma50 else -1.0

    elif strategy_name == "mean_reversion":
        sma20 = np.mean(c[-20:])
        std20 = np.std(c[-20:])
        if std20 == 0:
            return 0.0
        z_score = (c[-1] - sma20) / std20
        if z_score > 1.5:
            return -1.0   # 過高 → 做空 (均值回歸)
        elif z_score < -1.5:
            return 1.0    # 過低 → 做多 (均值回歸)
        return 0.0

    elif strategy_name == "breakout":
        high20 = np.max(h[-21:-1])
        low20 = np.min(low[-21:-1])
        if c[-1] > high20:
            return 1.0
        elif c[-1] < low20:
            return -1.0
        return 0.0

    elif strategy_name == "swing_trading":
        # 簡化的波段：用 RSI
        if len(c) < 15:
            return 0.0
        deltas = np.diff(c[-15:])
        gains = deltas[deltas > 0]
        losses = -deltas[deltas < 0]
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 1e-8
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))
        if rsi < 35:
            return 1.0
        elif rsi > 65:
            return -1.0
        return 0.0

    elif strategy_name == "direction_change":
        if len(c) < 5:
            return 0.0
        recent_trend = c[-1] - c[-5]
        prev_trend = c[-5] - c[-10] if len(c) >= 10 else 0
        # 偵測趨勢反轉
        if prev_trend > 0 and recent_trend < 0:
            return -1.0
        elif prev_trend < 0 and recent_trend > 0:
            return 1.0
        return 0.0

    return 0.0


def generate_labels(
    ohlcv: np.ndarray,
    window_start: int,
    window_end: int,
    forward_end: int,
) -> np.ndarray:
    """
    計算每個策略在 [window_start:window_end] 視窗末尾的預測方向，
    並用 [window_end:forward_end] 的實際報酬作為績效評分。
    返回 shape (NUM_STRATEGIES,) 的軟標籤，合計 = 1.0。
    """
    window = ohlcv[window_start:window_end]
    future_close = ohlcv[window_end:forward_end, 3].astype(float)

    if len(future_close) == 0:
        return np.ones(len(STRATEGY_NAMES)) / len(STRATEGY_NAMES)

    forward_return = (future_close[-1] - future_close[0]) / future_close[0]

    scores = []
    for name in STRATEGY_NAMES:
        direction = _simulate_strategy_direction(window, name)
        # 分數 = 策略方向 × 實際報酬 (方向正確且報酬大 → 高分)
        score = direction * forward_return
        scores.append(score)

    score_array = np.asarray(scores, dtype=np.float32)

    # 轉為軟標籤：用 Softmax 讓分數高的策略取得更高權重
    # 先做簡單的 Min-Max + Softmax
    scores_shifted = score_array - score_array.min() + 1e-8
    soft_labels = scores_shifted / scores_shifted.sum()
    return np.asarray(soft_labels, dtype=np.float32)


# ── Dataset ──────────────────────────────────────────────────────────
class StrategyLabelDataset(Dataset):
    """從歷史 OHLCV 建立 (特徵, 軟標籤) 訓練集"""

    def __init__(
        self,
        ohlcv: np.ndarray,
        extractor: FeatureExtractor,
        window_size: int = WINDOW_SIZE,
        forward_bars: int = FORWARD_BARS,
        step_size: int = STEP_SIZE,
    ):
        self.samples: List[Tuple[np.ndarray, np.ndarray, np.ndarray]] = []
        self._build(ohlcv, extractor, window_size, forward_bars, step_size)

    def _build(self, ohlcv, extractor, window_size, forward_bars, step_size):
        n = len(ohlcv)
        skipped = 0
        for i in range(window_size, n - forward_bars, step_size):
            window = ohlcv[i - window_size:i]
            market_feat = extractor.extract(window)
            if market_feat is None:
                skipped += 1
                continue
            # 預設事件特徵全為 neutral (無新聞資料時)
            event_feat = extractor.build_event_features()
            labels = generate_labels(ohlcv, i - window_size, i, i + forward_bars)
            self.samples.append((market_feat, event_feat, labels))

        logger.info(f"資料集建立完成: {len(self.samples)} 個樣本 (略過 {skipped} 個)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        mf, ef, lbl = self.samples[idx]
        return (
            torch.tensor(mf, dtype=torch.float32),
            torch.tensor(ef, dtype=torch.float32),
            torch.tensor(lbl, dtype=torch.float32),
        )


# ── Trainer ──────────────────────────────────────────────────────────
class MetaLearnerTrainer:
    """完整的訓練管線：資料載入 → 標籤生成 → 訓練 → 儲存"""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model_save_dir: Path = MODEL_SAVE_DIR,
    ):
        self.symbol = symbol
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.model_save_dir = model_save_dir
        self.model_save_dir.mkdir(parents=True, exist_ok=True)

        # 解析資料目錄
        if data_dir is None:
            data_dir = _PROJECT_ROOT / "backtest" / "data" / "binance_historical"
        self.data_dir = Path(data_dir)

        self.extractor = FeatureExtractor()
        self.model = MetaLearnerModel()
        self.log: dict = {"epochs": [], "best_val_loss": float("inf")}

    # ── 資料載入 ────────────────────────────────────────────────────
    def _load_ohlcv(self) -> np.ndarray:
        """從本地 ZIP 載入 OHLCV，返回 shape (N, 5) 的 float32 陣列"""
        import zipfile

        import pandas as pd

        data_path_candidates = [
            self.data_dir / "data" / "futures" / "um" / "daily" / "klines" / self.symbol / self.interval,
            self.data_dir / "futures" / "um" / "daily" / "klines" / self.symbol / self.interval,
            self.data_dir / self.symbol / self.interval,
        ]
        data_path = None
        for p in data_path_candidates:
            if p.exists():
                data_path = p
                break

        if data_path is None:
            # 嘗試遞迴搜尋
            found = list(self.data_dir.rglob(f"{self.symbol}/{self.interval}"))
            if found:
                data_path = found[0]
            else:
                raise FileNotFoundError(
                    f"找不到 {self.symbol}/{self.interval} 的歷史資料目錄。\n"
                    f"已搜尋: {self.data_dir}"
                )

        zip_files = sorted(
            p for p in data_path.rglob("*.zip") if "CHECKSUM" not in p.name
        )
        if not zip_files:
            raise FileNotFoundError(f"找不到任何 ZIP 資料檔: {data_path}")

        logger.info(f"找到 {len(zip_files)} 個 ZIP 資料檔，開始載入...")
        all_dfs = []
        columns = ["open_time", "open", "high", "low", "close", "volume",
                   "close_time", "quote_volume", "trades",
                   "taker_buy_base", "taker_buy_quote", "ignore"]

        for zf in zip_files:
            # 日期過濾
            parts = zf.stem.split("-")
            if len(parts) >= 4:
                date_str = "-".join(parts[-3:])
                try:
                    file_date = pd.to_datetime(date_str)
                    if self.start_date and file_date < pd.to_datetime(self.start_date):
                        continue
                    if self.end_date and file_date > pd.to_datetime(self.end_date):
                        continue
                except Exception:
                    pass
            try:
                with zipfile.ZipFile(zf) as z:
                    csvs = [n for n in z.namelist() if n.endswith(".csv")]
                    if not csvs:
                        continue
                    with z.open(csvs[0]) as f:
                        df = pd.read_csv(f, header=0, names=columns)
                all_dfs.append(df)
            except Exception as e:
                logger.warning(f"略過 {zf.name}: {e}")

        if not all_dfs:
            raise ValueError("指定日期範圍內沒有任何可用資料")

        df_all = pd.concat(all_dfs, ignore_index=True)
        df_all = df_all.sort_values("open_time").reset_index(drop=True)
        numeric_cols = ["open", "high", "low", "close", "volume"]
        ohlcv = df_all[numeric_cols].astype(float).values
        logger.info(f"載入完成: {len(ohlcv):,} 根 {self.interval} K 線")
        return ohlcv.astype(np.float32)

    # ── 訓練主程式 ──────────────────────────────────────────────────
    def train(
        self,
        epochs: int = EPOCHS,
        batch_size: int = BATCH_SIZE,
        lr: float = LEARNING_RATE,
        val_split: float = 0.15,
        verbose: bool = True,
    ) -> dict:
        """執行完整訓練流程，返回訓練日誌"""
        ohlcv = self._load_ohlcv()

        # 建立資料集
        logger.info("開始建立訓練資料集...")
        dataset = StrategyLabelDataset(ohlcv, self.extractor)
        if len(dataset) < 50:
            raise ValueError(f"樣本數太少 ({len(dataset)})，請擴大日期範圍或確認資料完整性")

        # 訓練 / 驗證分割
        val_size = max(1, int(len(dataset) * val_split))
        train_size = len(dataset) - val_size
        train_ds, val_ds = torch.utils.data.random_split(
            dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(42)
        )
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

        logger.info(f"訓練集: {train_size} 個樣本  驗證集: {val_size} 個樣本")
        logger.info(f"模型參數量: {self.model.total_parameters():,}")

        # 損失函數：軟標籤 KL 散度 (比 CrossEntropy 更適合軟標籤)
        criterion = nn.KLDivLoss(reduction="batchmean")
        optimizer = optim.AdamW(
            self.model.parameters(), lr=lr, weight_decay=WEIGHT_DECAY
        )
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        best_val_loss = float("inf")
        patience_count = 0
        best_state = None

        for epoch in range(1, epochs + 1):
            # ── 訓練 ──
            self.model.train()
            train_loss = 0.0
            for mf, ef, lbl in train_loader:
                optimizer.zero_grad()
                pred = self.model(mf, ef)          # (B, 5) Softmax 輸出
                log_pred = torch.log(pred + 1e-8)  # KLDivLoss 需要 log 機率
                loss = criterion(log_pred, lbl)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                train_loss += loss.item()
            train_loss /= len(train_loader)

            # ── 驗證 ──
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for mf, ef, lbl in val_loader:
                    pred = self.model(mf, ef)
                    log_pred = torch.log(pred + 1e-8)
                    val_loss += criterion(log_pred, lbl).item()
            val_loss /= len(val_loader)

            scheduler.step()

            self.log["epochs"].append({
                "epoch": epoch, "train_loss": train_loss, "val_loss": val_loss
            })

            if verbose and epoch % 10 == 0:
                logger.info(
                    f"Epoch {epoch:3d}/{epochs} | "
                    f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}"
                )

            # ── Early Stopping ──
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                patience_count = 0
            else:
                patience_count += 1
                if patience_count >= PATIENCE:
                    logger.info(f"Early stopping at epoch {epoch} (patience={PATIENCE})")
                    break

        # 還原最佳權重並儲存
        if best_state:
            self.model.load_state_dict(best_state)
        self.log["best_val_loss"] = best_val_loss
        self.log["total_samples"] = len(dataset)
        self.log["strategy_names"] = STRATEGY_NAMES
        self.log["trained_at"] = datetime.now().isoformat()

        self.save_model()
        logger.info(f"訓練完成。最佳驗證損失: {best_val_loss:.4f}")
        return self.log

    # ── 儲存 / 載入 ─────────────────────────────────────────────────
    def save_model(self):
        model_path = self.model_save_dir / MODEL_FILENAME
        self.model.save(model_path)

        log_path = self.model_save_dir / TRAINING_LOG_FILENAME
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.log, f, indent=2, ensure_ascii=False)

        logger.info(f"模型已儲存: {model_path}")
        logger.info(f"訓練紀錄已儲存: {log_path}")

    @classmethod
    def load_trained_model(cls) -> MetaLearnerModel:
        """載入已訓練的模型，供 strategy_fusion.py 使用"""
        model_path = MODEL_SAVE_DIR / MODEL_FILENAME
        if not model_path.exists():
            raise FileNotFoundError(
                f"找不到訓練好的模型: {model_path}\n"
                "請先執行訓練: python tools/train_meta_learner.py"
            )
        model = MetaLearnerModel()
        model.load(model_path)
        logger.info(f"Meta-Learner 模型已載入: {model_path}")
        return model


# ── CLI 入口 ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    trainer = MetaLearnerTrainer(
        symbol="BTCUSDT",
        interval="1h",
    )
    log = trainer.train(epochs=EPOCHS, verbose=True)
    print(f"\n訓練完成。最佳驗證損失: {log['best_val_loss']:.4f}")
    print(f"總樣本數: {log['total_samples']}")
    print(f"模型路徑: {MODEL_SAVE_DIR / MODEL_FILENAME}")
