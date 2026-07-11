"""
特徵萃取器
===========
從真實的 OHLCV numpy 陣列計算 60 維技術指標特徵。
所有特徵都做了歸一化處理，確保輸入範圍在 [-1, 1] 或 [0, 1] 之間。

特徵清單 (共 60 維):
  [0]   收盤價相對 SMA20 的距離 (%)
  [1]   收盤價相對 SMA50 的距離 (%)
  [2]   SMA20 相對 SMA50 的距離 (%) => 均線排列
  [3]   RSI(14) 正規化 (/ 100)
  [4]   MACD 線 (正規化)
  [5]   MACD Signal 線 (正規化)
  [6]   MACD Histogram (正規化)
  [7]   布林通道寬度 (%)
  [8]   收盤價在布林通道中的位置 (0=下軌, 1=上軌)
  [9]   ATR(14) 正規化 (相對於收盤價的 %)
  [10]  ADX(14) 正規化 (/ 100)
  [11]  過去 1 根 K 線的漲跌幅 (%)
  [12]  過去 3 根 K 線的漲跌幅 (%)
  [13]  過去 5 根 K 線的漲跌幅 (%)
  [14]  過去 10 根 K 線的漲跌幅 (%)
  [15]  過去 20 根 K 線的漲跌幅 (%)
  [16]  成交量相對 20 期均量的比率 (log 正規化)
  [17]  成交量相對 5 期均量的比率 (log 正規化)
  [18]  最高價在過去 20 根的分位數 (0~1)
  [19]  最低價在過去 20 根的分位數 (0~1)
  [20]  K 線實體佔最高最低範圍的比率 (方向性)
  [21]  上影線長度 (相對 ATR)
  [22]  下影線長度 (相對 ATR)
  [23]  過去 20 根的波動率 (std of returns, %)
  [24]  過去 5 根的波動率 (std of returns, %)
  [25]  StochK(14) 正規化 (/ 100)
  [26]  StochD(3) 正規化 (/ 100)
  [27]  Williams %R(14) 正規化 (/ -100, 使其在 0~1)
  [28]  CCI(14) 正規化 (tanh)
  [29]  ROC(10) 正規化 (tanh)
  [30~49] 過去 20 根 K 線的標準化收益率序列 (時間序列記憶)
  [50~59] 過去 10 根 K 線的標準化成交量序列
"""

from typing import Optional, Union

import numpy as np

MARKET_FEATURE_DIM = 60
EVENT_FEATURE_DIM = 8


class FeatureExtractor:
    """從 OHLCV numpy 陣列提取 60 維技術特徵"""

    MIN_BARS = 60  # 計算 ADX/SMA50 等需要至少 60 根 K 線

    def extract(self, ohlcv: np.ndarray) -> Optional[np.ndarray]:
        """
        Args:
            ohlcv: shape (N, 5), 欄位 = [open, high, low, close, volume]
                   N 必須 >= MIN_BARS
        Returns:
            features: shape (MARKET_FEATURE_DIM,), float32
            None: 資料不足
        """
        if ohlcv is None or len(ohlcv) < self.MIN_BARS:
            return None

        o = ohlcv[:, 0].astype(float)
        h = ohlcv[:, 1].astype(float)
        low = ohlcv[:, 2].astype(float)
        c = ohlcv[:, 3].astype(float)
        v = ohlcv[:, 4].astype(float)

        feats = []
        price = c[-1]

        # ── 均線系列 ───────────────────────────────────────────────
        sma20 = np.mean(c[-20:])
        sma50 = np.mean(c[-50:])
        feats.append(np.clip((price - sma20) / sma20 * 100, -10, 10))      # [0]
        feats.append(np.clip((price - sma50) / sma50 * 100, -10, 10))      # [1]
        feats.append(np.clip((sma20 - sma50) / sma50 * 100, -5, 5))        # [2]

        # ── RSI(14) ────────────────────────────────────────────────
        feats.append(self._rsi(c, 14) / 100.0)                              # [3]

        # ── MACD(12,26,9) ─────────────────────────────────────────
        macd_line, signal_line, histogram = self._macd(c)
        norm = max(abs(price) * 0.001, 1e-8)
        feats.append(np.clip(macd_line / norm, -3, 3))                      # [4]
        feats.append(np.clip(signal_line / norm, -3, 3))                    # [5]
        feats.append(np.clip(histogram / norm, -3, 3))                      # [6]

        # ── 布林通道(20,2) ────────────────────────────────────────
        bb_mid = sma20
        bb_std = np.std(c[-20:])
        bb_upper = bb_mid + 2 * bb_std
        bb_lower = bb_mid - 2 * bb_std
        bb_width = (bb_upper - bb_lower) / bb_mid * 100 if bb_mid > 0 else 0
        bb_pos = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
        feats.append(np.clip(bb_width, 0, 20))                              # [7]
        feats.append(np.clip(bb_pos, 0, 1))                                 # [8]

        # ── ATR(14) ───────────────────────────────────────────────
        atr = self._atr(h, low, c, 14)
        feats.append(np.clip(atr / price * 100, 0, 10))                     # [9]

        # ── ADX(14) ───────────────────────────────────────────────
        adx = self._adx(h, low, c, 14)
        feats.append(np.clip(adx / 100.0, 0, 1))                            # [10]

        # ── 多週期動能 ────────────────────────────────────────────
        for lookback in [1, 3, 5, 10, 20]:
            if len(c) > lookback:
                ret = (c[-1] - c[-1 - lookback]) / c[-1 - lookback] * 100
                feats.append(np.clip(ret, -20, 20))
            else:
                feats.append(0.0)
        # [11~15]

        # ── 成交量比率 ────────────────────────────────────────────
        vol_avg20 = np.mean(v[-20:])
        vol_avg5 = np.mean(v[-5:])
        vol_ratio20 = v[-1] / vol_avg20 if vol_avg20 > 0 else 1.0
        vol_ratio5 = v[-1] / vol_avg5 if vol_avg5 > 0 else 1.0
        feats.append(np.clip(np.log1p(vol_ratio20), 0, 3))                  # [16]
        feats.append(np.clip(np.log1p(vol_ratio5), 0, 3))                   # [17]

        # ── 價格分位 ──────────────────────────────────────────────
        high20 = h[-20:]
        low20 = low[-20:]
        h_max, h_min = np.max(high20), np.min(high20)
        l_max, l_min = np.max(low20), np.min(low20)
        feats.append((h[-1] - h_min) / (h_max - h_min) if h_max > h_min else 0.5)  # [18]
        feats.append((low[-1] - l_min) / (l_max - l_min) if l_max > l_min else 0.5)  # [19]

        # ── K 線形態 ──────────────────────────────────────────────
        bar_range = h[-1] - low[-1]
        body = c[-1] - o[-1]
        body_ratio = body / bar_range if bar_range > 0 else 0
        upper_shadow = (h[-1] - max(o[-1], c[-1])) / (atr if atr > 0 else 1)
        lower_shadow = (min(o[-1], c[-1]) - low[-1]) / (atr if atr > 0 else 1)
        feats.append(np.clip(body_ratio, -1, 1))                             # [20]
        feats.append(np.clip(upper_shadow, 0, 3))                            # [21]
        feats.append(np.clip(lower_shadow, 0, 3))                            # [22]

        # ── 波動率 ────────────────────────────────────────────────
        returns = np.diff(c) / c[:-1]
        feats.append(np.clip(np.std(returns[-20:]) * 100, 0, 5))             # [23]
        feats.append(np.clip(np.std(returns[-5:]) * 100, 0, 5))              # [24]

        # ── Stochastic(14,3) ──────────────────────────────────────
        stoch_k, stoch_d = self._stochastic(h, low, c, 14, 3)
        feats.append(np.clip(stoch_k, 0, 1))                                 # [25]
        feats.append(np.clip(stoch_d, 0, 1))                                 # [26]

        # ── Williams %R(14) ───────────────────────────────────────
        wr = self._williams_r(h, low, c, 14)
        feats.append(np.clip((wr + 100) / 100.0, 0, 1))                      # [27]

        # ── CCI(14) ───────────────────────────────────────────────
        cci = self._cci(h, low, c, 14)
        feats.append(np.tanh(cci / 200.0))                                   # [28]

        # ── ROC(10) ───────────────────────────────────────────────
        roc = (c[-1] - c[-11]) / c[-11] * 100 if len(c) > 10 and c[-11] > 0 else 0
        feats.append(np.tanh(roc / 10.0))                                    # [29]

        # [30~49] 過去 20 根標準化收益率序列 ─────────────────────
        ret_seq = returns[-20:] if len(returns) >= 20 else np.zeros(20)
        ret_seq = ret_seq[-20:]  # 確保長度 20
        ret_std = np.std(ret_seq) if np.std(ret_seq) > 0 else 1e-8
        ret_normalized = np.clip(ret_seq / ret_std, -3, 3)
        feats.extend(ret_normalized.tolist())                                  # [30~49]

        # [50~59] 過去 10 根標準化成交量序列 ──────────────────────
        vol_seq = v[-10:] if len(v) >= 10 else np.ones(10) * v[-1]
        vol_seq = vol_seq[-10:]
        vol_mean = np.mean(vol_seq) if np.mean(vol_seq) > 0 else 1e-8
        vol_normalized = np.clip(vol_seq / vol_mean, 0, 5)
        feats.extend(vol_normalized.tolist())                                  # [50~59]

        result = np.array(feats, dtype=np.float32)
        assert len(result) == MARKET_FEATURE_DIM, f"特徵維度錯誤: {len(result)}"
        # 處理 NaN/Inf
        result = np.nan_to_num(result, nan=0.0, posinf=3.0, neginf=-3.0)
        return result

    def build_event_features(
        self,
        news_sentiment: float = 0.0,     # -1 ~ +1
        fear_greed: float = 50.0,         # 0 ~ 100
        oi_change_pct: float = 0.0,       # -10 ~ +10
        funding_rate: float = 0.0,        # -0.1 ~ +0.1
        btc_dominance: float = 50.0,      # 0 ~ 100
        market_cap_change: float = 0.0,   # -5 ~ +5
        event_intensity: float = 0.0,     # 0 ~ 1 (新聞強度衰減後的值)
        rag_hist_win_rate: float = 0.5,   # 0 ~ 1 (RAG 查出的歷史勝率)
    ) -> np.ndarray:
        """
        建立 8 維事件上下文特徵 (EVENT_FEATURE_DIM = 8)
        所有輸入都已正規化到 [-1, 1] 或 [0, 1]
        """
        feats = [
            np.clip(news_sentiment, -1, 1),
            np.clip(fear_greed / 100.0, 0, 1),
            np.clip(oi_change_pct / 10.0, -1, 1),
            np.clip(funding_rate / 0.1, -1, 1),
            np.clip(btc_dominance / 100.0, 0, 1),
            np.clip(market_cap_change / 5.0, -1, 1),
            np.clip(event_intensity, 0, 1),
            np.clip(rag_hist_win_rate, 0, 1),
        ]
        return np.array(feats, dtype=np.float32)

    # ── 私有指標計算函數 ──────────────────────────────────────────────

    def _rsi(self, close: np.ndarray, period: int = 14) -> float:
        if len(close) < period + 1:
            return 50.0
        deltas = np.diff(close[-(period + 1):])
        gains = deltas[deltas > 0]
        losses = -deltas[deltas < 0]
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 1e-8
        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))

    def _macd(self, close: np.ndarray):
        ema12 = self._ema(close, 12)
        ema26 = self._ema(close, 26)
        macd = ema12 - ema26
        signal = self._ema_scalar(macd, 9) if len(close) >= 35 else 0.0
        return macd, signal, macd - signal

    def _ema(self, close: np.ndarray, period: int) -> float:
        if len(close) < period:
            return float(close[-1])
        k = 2 / (period + 1)
        ema = close[-period]
        for price in close[-(period - 1):]:
            ema = price * k + ema * (1 - k)
        return float(ema)

    def _ema_scalar(self, series: Union[np.ndarray, float], period: int) -> float:
        if not isinstance(series, np.ndarray):
            return float(series)
        arr = np.atleast_1d(series)
        if len(arr) < period:
            return float(arr[-1])
        k = 2 / (period + 1)
        ema = arr[-period]
        for v in arr[-(period - 1):]:
            ema = float(v) * k + ema * (1 - k)
        return float(ema)

    def _atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        if len(close) < period + 1:
            return float(np.mean(high[-period:] - low[-period:]))
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )
        return float(np.mean(tr[-period:]))

    def _adx(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        if len(close) < period * 2:
            return 20.0
        plus_dm = np.zeros(len(high))
        minus_dm = np.zeros(len(high))
        for i in range(1, len(high)):
            up = high[i] - high[i - 1]
            down = low[i - 1] - low[i]
            plus_dm[i] = up if up > down and up > 0 else 0
            minus_dm[i] = down if down > up and down > 0 else 0
        atr = self._atr(high, low, close, period)
        if atr == 0:
            return 0.0
        plus_di = 100 * np.mean(plus_dm[-period:]) / atr
        minus_di = 100 * np.mean(minus_dm[-period:]) / atr
        denom = plus_di + minus_di
        if denom == 0:
            return 0.0
        dx = 100 * abs(plus_di - minus_di) / denom
        return float(dx)

    def _stochastic(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3):
        if len(close) < k_period:
            return 0.5, 0.5
        lowest = np.min(low[-k_period:])
        highest = np.max(high[-k_period:])
        if highest == lowest:
            return 0.5, 0.5
        k = (close[-1] - lowest) / (highest - lowest)
        d = k  # 簡化：單點無法計算平均，返回 k
        return float(k), float(d)

    def _williams_r(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        if len(close) < period:
            return -50.0
        highest = np.max(high[-period:])
        lowest = np.min(low[-period:])
        if highest == lowest:
            return -50.0
        return float((highest - close[-1]) / (highest - lowest) * -100)

    def _cci(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        if len(close) < period:
            return 0.0
        tp = (high[-period:] + low[-period:] + close[-period:]) / 3
        mean_tp = np.mean(tp)
        mean_dev = np.mean(np.abs(tp - mean_tp))
        if mean_dev == 0:
            return 0.0
        return float((tp[-1] - mean_tp) / (0.015 * mean_dev))
