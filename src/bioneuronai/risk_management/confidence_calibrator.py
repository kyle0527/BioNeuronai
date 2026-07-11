"""
AI 信心校準與動態倉位系統 (Confidence Calibrator & Dynamic Sizing)
================================================================

核心理念 (參考 Marcos López de Prado, "Advances in Financial Machine Learning"):
  本模組將 AI 的「機率思維」轉化為實際的倉位大小。

三大功能：
  1. Temperature Scaling — 校準神經網路的信心輸出（防止過度自信）
  2. Fractional Kelly Criterion — 用校準後的機率計算最佳下注比例
  3. Macro-Micro Alignment — 連續的宏觀微觀對齊度函數（取代 if/else）

設計原則：
  - 所有輸出都是 [0, 1] 之間的連續值，不使用硬編碼閾值
  - 只擴展不破壞：現有架構完全不需修改即可使用本模組
  - 中/英雙語日誌與說明，方便 AI 自然語言理解與報告

使用範例:
    from bioneuronai.risk_management.confidence_calibrator import AIConfidenceCalibrator

    calibrator = AIConfidenceCalibrator()

    # 校準 AI 信心
    calibrated_p = calibrator.calibrate_confidence(raw_confidence=0.82)

    # AI 驅動的 Kelly 倉位比例
    kelly_frac = calibrator.fractional_kelly(
        calibrated_p=calibrated_p,
        net_odds=0.06,   # 預期盈利 6%
    )

    # 宏觀微觀對齊度 (連續值)
    alignment = calibrator.compute_alignment(
        macro_sentiment=-0.4,
        micro_direction="long",
        micro_confidence=0.75,
    )

    # 最終倉位乘數
    multiplier = calibrator.compute_position_multiplier(
        ai_confidence=calibrated_p,
        alignment_score=alignment,
        net_odds=0.06,
    )

Author: BioNeuronai Team
Date: 2026-06-09
"""

import json
import logging
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
# 資料結構
# ════════════════════════════════════════════════════════════════════

@dataclass
class CalibrationRecord:
    """單筆校準紀錄，用於後續 Temperature 重新 fit"""
    timestamp: datetime
    raw_confidence: float      # AI 原始信心 (0~1)
    calibrated_confidence: float  # 校準後信心 (0~1)
    alignment_score: float     # 宏觀微觀對齊度 (0~1)
    position_multiplier: float # 最終倉位乘數 (0~1)
    actual_outcome: Optional[float] = None  # 交易結果 (盈虧比例)，事後填入
    was_profitable: Optional[bool] = None   # 是否盈利，事後填入


@dataclass
class AlignmentReport:
    """
    宏觀微觀對齊分析報告

    可用於 AI 自然語言生成（中/英文），也可用於結構化日誌。
    """
    alignment_score: float          # 0.0 ~ 1.0
    macro_sentiment: float          # -1.0 ~ +1.0
    micro_direction: str            # "long" / "short"
    micro_confidence: float         # 0.0 ~ 1.0
    is_divergent: bool              # 宏觀與微觀方向是否背離
    position_multiplier: float      # 最終倉位乘數
    dynamic_threshold: float        # 動態進場門檻
    reasoning_zh: str = ""          # 中文推理說明
    reasoning_en: str = ""          # 英文推理說明


# ════════════════════════════════════════════════════════════════════
# 主類別
# ════════════════════════════════════════════════════════════════════

class AIConfidenceCalibrator:
    """
    AI 信心校準器 — 將 AI 的機率輸出轉化為倉位決策

    整合角色：作為「AI 中央統帥」，同時接收戰術層 (Strategy Fusion) 與
    戰略層 (News/Macro Analysis) 的報告，計算出一個統一的「信心與對齊度」，
    用以控制倉位大小與進場門檻。
    """

    # 預設參數（可由 System 2 反思 Loop 覆寫）
    DEFAULT_TEMPERATURE = 1.5        # Temperature Scaling 參數
    DEFAULT_KELLY_FRACTION = 0.25    # 1/4 Kelly (冷啟動安全倍率)
    DEFAULT_ALIGNMENT_TEMP = 2.0     # 對齊度 Sigmoid 溫度
    MIN_POSITION_MULTIPLIER = 0.05   # 最低倉位乘數（永遠不會是零）
    BASE_ENTRY_THRESHOLD = 6.0       # 基礎進場信號強度門檻

    def __init__(
        self,
        temperature: Optional[float] = None,
        kelly_fraction: Optional[float] = None,
        alignment_temperature: Optional[float] = None,
        calibration_data_path: Optional[str] = None,
    ):
        """
        Args:
            temperature: Temperature Scaling 參數。> 1.0 = 降低信心（更保守），
                         < 1.0 = 提高信心（更激進）。
            kelly_fraction: Kelly 公式的安全倍率 (0~1)。0.25 = 1/4 Kelly。
            alignment_temperature: 對齊度 Sigmoid 的溫度參數。越高越陡峭。
            calibration_data_path: 校準紀錄的持久化路徑。
        """
        self.temperature = temperature or self.DEFAULT_TEMPERATURE
        self.kelly_fraction = kelly_fraction or self.DEFAULT_KELLY_FRACTION
        self.alignment_temperature = alignment_temperature or self.DEFAULT_ALIGNMENT_TEMP
        self.min_multiplier = self.MIN_POSITION_MULTIPLIER

        # 校準紀錄（用於自我學習）
        self._records: List[CalibrationRecord] = []
        self._data_path = Path(calibration_data_path) if calibration_data_path else None

        # 統計指標
        self._total_calibrations = 0
        self._total_outcomes_recorded = 0

        if self._data_path:
            self._load_records()

        logger.info(
            "✅ AIConfidenceCalibrator 初始化完成 | "
            f"T={self.temperature:.2f}, Kelly={self.kelly_fraction:.0%}, "
            f"AlignT={self.alignment_temperature:.1f}"
        )

    # ════════════════════════════════════════════════════════════════
    # 1. Temperature Scaling — 校準信心
    # ════════════════════════════════════════════════════════════════

    def calibrate_confidence(self, raw_confidence: float) -> float:
        """
        校準 AI 的信心輸出 (Temperature Scaling)

        神經網路天生「過度自信」。例如，模型說有 90% 信心，但實際勝率只有 60%。
        Temperature Scaling 通過一個學習參數 T 來壓制這種過度自信：

            calibrated = sigmoid(logit(raw) / T)

        當 T > 1 時，信心被壓低（更保守）。
        當 T < 1 時，信心被放大（更激進）。

        Args:
            raw_confidence: AI 原始信心值 (0.0 ~ 1.0)

        Returns:
            校準後的信心值 (0.0 ~ 1.0)
        """
        # 確保輸入在合法範圍
        raw = max(0.01, min(0.99, raw_confidence))

        # logit 變換: log(p / (1-p))
        logit = math.log(raw / (1.0 - raw))

        # Temperature Scaling
        scaled_logit = logit / self.temperature

        # Sigmoid 反變換
        calibrated = 1.0 / (1.0 + math.exp(-scaled_logit))

        self._total_calibrations += 1

        logger.debug(
            f"[校準] raw={raw_confidence:.3f} → logit={logit:.3f} "
            f"→ /T={scaled_logit:.3f} → calibrated={calibrated:.3f}"
        )

        return calibrated

    # ════════════════════════════════════════════════════════════════
    # 2. Fractional Kelly Criterion — AI 驅動的倉位比例
    # ════════════════════════════════════════════════════════════════

    def fractional_kelly(
        self,
        calibrated_p: float,
        net_odds: float,
        max_fraction: float = 0.30,
    ) -> float:
        """
        Fractional Kelly Criterion — 用校準後的 AI 信心計算最佳下注比例

        Kelly 公式: f* = (b*p - q) / b
          - p: 校準後的勝率（AI 信心）
          - q: 1 - p（敗率）
          - b: 淨賠率（預期盈利 / 預期虧損）

        我們用 Fractional Kelly (k * f*) 來降低方差：
          - k = 0.25 → 1/4 Kelly，方差降低 93.75%，成長率僅降低 25%

        Args:
            calibrated_p: 校準後的勝率 (0.0 ~ 1.0)
            net_odds: 淨賠率 = 預期盈利 / 預期虧損（已扣除手續費）
            max_fraction: 最大允許的 Kelly 比例

        Returns:
            倉位比例 (0.0 ~ max_fraction)
        """
        if net_odds <= 0 or calibrated_p <= 0:
            return 0.0

        q = 1.0 - calibrated_p

        # Kelly 公式
        kelly_full = (net_odds * calibrated_p - q) / net_odds

        # 如果 AI 認為沒有正期望（edge <= 0），不下注
        if kelly_full <= 0:
            logger.debug(
                f"[Kelly] 無正期望值: p={calibrated_p:.3f}, odds={net_odds:.3f}, "
                f"kelly={kelly_full:.4f} → 不下注"
            )
            return 0.0

        # Fractional Kelly
        fractional = kelly_full * self.kelly_fraction

        # 安全上限
        result = min(fractional, max_fraction)

        logger.debug(
            f"[Kelly] p={calibrated_p:.3f}, odds={net_odds:.3f} → "
            f"full_kelly={kelly_full:.4f}, frac={fractional:.4f}, "
            f"capped={result:.4f}"
        )

        return result

    # ════════════════════════════════════════════════════════════════
    # 3. Macro-Micro Alignment — 宏觀微觀對齊度（連續函數）
    # ════════════════════════════════════════════════════════════════

    def compute_alignment(
        self,
        macro_sentiment: float,
        micro_direction: str,
        micro_confidence: float,
    ) -> float:
        """
        計算宏觀（戰略）與微觀（戰術）的對齊度

        這是整個系統的核心 AI 函數。不使用任何 if/else 硬編碼。
        而是用 Sigmoid 函數將兩個 AI 信號的「內積」映射到 [0, 1]。

        對齊度的語義：
          - 1.0: 完全順風（新聞看多 + 戰術做多）
          - 0.5: 中性（新聞沒有明確方向）
          - 0.0: 完全逆風（新聞看空但戰術做多）

        Args:
            macro_sentiment: 宏觀情緒分數 (-1.0 ~ +1.0)，來自 NewsAdapter
            micro_direction: 微觀方向 ("long" 或 "short")，來自 StrategyFusion
            micro_confidence: 微觀信心 (0.0 ~ 1.0)，來自 FusionSignal

        Returns:
            alignment_score (0.0 ~ 1.0)
        """
        # 方向符號
        direction_sign = 1.0 if micro_direction == "long" else -1.0

        # 核心：兩個 AI 信號的「方向性內積」
        raw_alignment = macro_sentiment * direction_sign

        # Sigmoid 映射到 [0, 1]
        alignment = 1.0 / (1.0 + math.exp(-raw_alignment * self.alignment_temperature))

        # 微觀信心越高時，逆風的「過度自信懲罰」越大
        # 這模擬了「越自信的錯誤越危險」的直覺
        if alignment < 0.5:
            overconfidence_penalty = (1.0 - alignment) * micro_confidence * 0.3
            alignment = max(self.min_multiplier, alignment - overconfidence_penalty)

        return round(alignment, 4)

    def compute_alignment_report(
        self,
        macro_sentiment: float,
        micro_direction: str,
        micro_confidence: float,
    ) -> AlignmentReport:
        """
        生成完整的宏觀微觀對齊報告（含中英文推理說明）

        此函數供 AI 的自然語言模組使用，可直接用於生成
        交易前報告或交易日誌。

        Args:
            macro_sentiment: 宏觀情緒分數 (-1.0 ~ +1.0)
            micro_direction: 微觀方向 ("long" / "short")
            micro_confidence: 微觀信心 (0.0 ~ 1.0)

        Returns:
            AlignmentReport 完整報告
        """
        alignment = self.compute_alignment(
            macro_sentiment, micro_direction, micro_confidence
        )

        direction_sign = 1.0 if micro_direction == "long" else -1.0
        is_divergent = (macro_sentiment * direction_sign) < -0.1

        multiplier = self._alignment_to_multiplier(alignment)
        threshold = self._alignment_to_threshold(alignment)

        # ── 中文推理 ──
        macro_desc_zh = self._describe_sentiment_zh(macro_sentiment)
        micro_desc_zh = "做多" if micro_direction == "long" else "做空"
        conf_desc_zh = self._describe_confidence_zh(micro_confidence)

        if is_divergent:
            reasoning_zh = (
                f"⚠️ 宏觀微觀背離：新聞面{macro_desc_zh}（{macro_sentiment:+.2f}），"
                f"但戰術建議{micro_desc_zh}（信心{conf_desc_zh} {micro_confidence:.0%}）。"
                f"AI 對齊度 {alignment:.2f}，倉位乘數自動縮減至 {multiplier:.0%}，"
                f"進場門檻提高至 {threshold:.1f}。"
            )
        else:
            reasoning_zh = (
                f"✅ 宏觀微觀一致：新聞面{macro_desc_zh}（{macro_sentiment:+.2f}），"
                f"戰術建議{micro_desc_zh}（信心{conf_desc_zh} {micro_confidence:.0%}）。"
                f"AI 對齊度 {alignment:.2f}，倉位維持 {multiplier:.0%}。"
            )

        # ── 英文推理 ──
        macro_desc_en = self._describe_sentiment_en(macro_sentiment)
        micro_desc_en = "LONG" if micro_direction == "long" else "SHORT"
        conf_desc_en = self._describe_confidence_en(micro_confidence)

        if is_divergent:
            reasoning_en = (
                f"⚠️ Macro-Micro Divergence: News is {macro_desc_en} ({macro_sentiment:+.2f}), "
                f"but tactics suggest {micro_desc_en} ({conf_desc_en} confidence {micro_confidence:.0%}). "
                f"AI alignment {alignment:.2f}, position reduced to {multiplier:.0%}, "
                f"entry threshold raised to {threshold:.1f}."
            )
        else:
            reasoning_en = (
                f"✅ Macro-Micro Aligned: News is {macro_desc_en} ({macro_sentiment:+.2f}), "
                f"tactics suggest {micro_desc_en} ({conf_desc_en} confidence {micro_confidence:.0%}). "
                f"AI alignment {alignment:.2f}, position at {multiplier:.0%}."
            )

        return AlignmentReport(
            alignment_score=alignment,
            macro_sentiment=macro_sentiment,
            micro_direction=micro_direction,
            micro_confidence=micro_confidence,
            is_divergent=is_divergent,
            position_multiplier=multiplier,
            dynamic_threshold=threshold,
            reasoning_zh=reasoning_zh,
            reasoning_en=reasoning_en,
        )

    # ════════════════════════════════════════════════════════════════
    # 4. 統合函數 — 最終倉位乘數
    # ════════════════════════════════════════════════════════════════

    def compute_position_multiplier(
        self,
        ai_confidence: float,
        alignment_score: float,
        net_odds: float,
    ) -> float:
        """
        統合所有 AI 信號，計算最終倉位乘數

        這是「AI 中央統帥」的最終決策函數。它綜合考慮：
          1. AI 信心（校準後）→ Kelly 最佳比例
          2. 宏觀微觀對齊度 → 順/逆風調整

        輸出的乘數直接乘以 `pretrade_automation._calculate_risk()` 中的
        `position_size`，無需修改原有的 1% 風險規則。

        Args:
            ai_confidence: 校準後的 AI 信心 (0.0 ~ 1.0)
            alignment_score: 宏觀微觀對齊度 (0.0 ~ 1.0)
            net_odds: 淨賠率

        Returns:
            position_multiplier (MIN_POSITION_MULTIPLIER ~ 1.0)
        """
        # 1. Kelly 比例 (基於 AI 信心)
        kelly = self.fractional_kelly(ai_confidence, net_odds)

        # 2. 將 Kelly 比例映射到 [0, 1] 的乘數
        #    kelly_fraction=0.25 且 net_odds 合理時，kelly 通常在 0~0.15
        #    我們將其映射到 0.3 ~ 1.0 的範圍
        kelly_multiplier = min(1.0, 0.3 + kelly * 4.0)

        # 3. 結合對齊度
        #    兩者取幾何平均（而非算術平均），讓任一方極低都能拉下倉位
        combined = math.sqrt(kelly_multiplier * alignment_score)

        # 4. 安全底線
        result = max(self.min_multiplier, min(1.0, combined))

        logger.info(
            f"[AI 統帥] 倉位乘數: {result:.2f} | "
            f"Kelly={kelly:.4f} → KellyMul={kelly_multiplier:.2f}, "
            f"Align={alignment_score:.2f}, Combined={combined:.2f}"
        )

        return round(result, 4)

    def compute_dynamic_threshold(
        self,
        alignment_score: float,
        base_threshold: Optional[float] = None,
    ) -> float:
        """
        計算動態進場信號強度門檻

        當宏觀微觀背離時，AI 自動提高進場門檻，減少交易頻率。
        這取代了人工設定的「逆風時信號數量 >= N」的硬規則。

        公式: dynamic_threshold = base / alignment_score
        - 順風 (alignment=0.95): threshold ≈ 6.3 → 幾乎不影響
        - 嚴重逆風 (alignment=0.3): threshold ≈ 20.0 → 極難通過

        Args:
            alignment_score: 宏觀微觀對齊度 (0.0 ~ 1.0)
            base_threshold: 基礎門檻，預設 6.0

        Returns:
            動態門檻值
        """
        return self._alignment_to_threshold(alignment_score, base_threshold)

    # ════════════════════════════════════════════════════════════════
    # 5. 學習紀錄 — 用於 System 2 反思 Loop
    # ════════════════════════════════════════════════════════════════

    def record_decision(
        self,
        raw_confidence: float,
        calibrated_confidence: float,
        alignment_score: float,
        position_multiplier: float,
    ) -> CalibrationRecord:
        """紀錄一次 AI 決策，用於後續校準"""
        record = CalibrationRecord(
            timestamp=datetime.now(),
            raw_confidence=raw_confidence,
            calibrated_confidence=calibrated_confidence,
            alignment_score=alignment_score,
            position_multiplier=position_multiplier,
        )
        self._records.append(record)
        return record

    def record_outcome(self, record: CalibrationRecord, pnl_pct: float) -> None:
        """交易結束後，回填實際結果"""
        record.actual_outcome = pnl_pct
        record.was_profitable = pnl_pct > 0
        self._total_outcomes_recorded += 1
        try:
            self._save_records()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[校準] 儲存 outcome 紀錄失敗: %s", exc)

    def record_outcome_by_index(self, index: int, pnl_pct: float) -> bool:
        """依 pretrade 寫入的 calibration_record_index 回填結果。"""
        if index < 0 or index >= len(self._records):
            return False
        self.record_outcome(self._records[index], pnl_pct)
        return True

    def refit_temperature(self, min_samples: int = 50) -> Optional[float]:
        """
        用歷史紀錄重新 fit Temperature 參數

        採用 grid search 最小化 Brier Score:
            BS = (1/N) * Σ (calibrated_p_i - actual_outcome_i)²

        Args:
            min_samples: 最少需要多少筆有結果的紀錄才啟動 refit

        Returns:
            新的 Temperature 值，或 None（樣本不足）
        """
        completed = [r for r in self._records if r.was_profitable is not None]
        if len(completed) < min_samples:
            logger.info(
                f"[校準] 樣本不足 ({len(completed)}/{min_samples})，保持 T={self.temperature:.2f}"
            )
            return None

        best_t = self.temperature
        best_brier = float("inf")

        for t_candidate in np.arange(0.5, 4.0, 0.1):
            brier = 0.0
            for r in completed:
                # 用候選 T 重新校準
                raw = max(0.01, min(0.99, r.raw_confidence))
                logit_val = math.log(raw / (1.0 - raw))
                p_cal = 1.0 / (1.0 + math.exp(-logit_val / t_candidate))
                actual = 1.0 if r.was_profitable else 0.0
                brier += (p_cal - actual) ** 2
            brier /= len(completed)

            if brier < best_brier:
                best_brier = brier
                best_t = float(t_candidate)

        old_t = self.temperature
        self.temperature = best_t

        logger.info(
            f"[校準] Temperature refit: {old_t:.2f} → {best_t:.2f} "
            f"(Brier Score: {best_brier:.4f}, samples: {len(completed)})"
        )

        if self._data_path:
            self._save_records()

        return best_t

    def get_calibration_stats(self) -> Dict:
        """取得校準統計資訊"""
        completed = [r for r in self._records if r.was_profitable is not None]
        if not completed:
            return {
                "total_decisions": self._total_calibrations,
                "total_outcomes": 0,
                "current_temperature": self.temperature,
                "brier_score": None,
            }

        # 計算當前 Brier Score
        brier = 0.0
        for r in completed:
            actual = 1.0 if r.was_profitable else 0.0
            brier += (r.calibrated_confidence - actual) ** 2
        brier /= len(completed)

        # Expected Calibration Error (ECE) — 10 個 bin
        bins: List[List[float]] = [[] for _ in range(10)]
        for r in completed:
            idx = min(9, int(r.calibrated_confidence * 10))
            bins[idx].append(1.0 if r.was_profitable else 0.0)

        ece = 0.0
        for i, bin_data in enumerate(bins):
            if bin_data:
                bin_confidence = (i + 0.5) / 10.0
                bin_accuracy = sum(bin_data) / len(bin_data)
                ece += abs(bin_accuracy - bin_confidence) * len(bin_data)
        ece /= len(completed) if completed else 1

        return {
            "total_decisions": self._total_calibrations,
            "total_outcomes": len(completed),
            "current_temperature": round(self.temperature, 3),
            "kelly_fraction": self.kelly_fraction,
            "brier_score": round(brier, 4),
            "expected_calibration_error": round(ece, 4),
            "win_rate": round(sum(1 for r in completed if r.was_profitable) / len(completed), 3),
        }

    # ════════════════════════════════════════════════════════════════
    # 私有方法
    # ════════════════════════════════════════════════════════════════

    def _alignment_to_multiplier(self, alignment: float) -> float:
        """將對齊度轉為倉位乘數"""
        return max(self.min_multiplier, min(1.0, alignment))

    def _alignment_to_threshold(
        self,
        alignment: float,
        base: Optional[float] = None,
    ) -> float:
        """將對齊度轉為動態門檻"""
        base = base or self.BASE_ENTRY_THRESHOLD
        safe_alignment = max(0.15, alignment)  # 防止除以太小的數
        threshold = base / safe_alignment
        return min(threshold, 40.0)  # 安全上限

    # ── 自然語言描述 ──

    @staticmethod
    def _describe_sentiment_zh(score: float) -> str:
        if score > 0.5:
            return "強烈看多"
        elif score > 0.15:
            return "偏多"
        elif score > -0.15:
            return "中性"
        elif score > -0.5:
            return "偏空"
        else:
            return "強烈看空"

    @staticmethod
    def _describe_sentiment_en(score: float) -> str:
        if score > 0.5:
            return "strongly bullish"
        elif score > 0.15:
            return "moderately bullish"
        elif score > -0.15:
            return "neutral"
        elif score > -0.5:
            return "moderately bearish"
        else:
            return "strongly bearish"

    @staticmethod
    def _describe_confidence_zh(conf: float) -> str:
        if conf >= 0.8:
            return "極高"
        elif conf >= 0.6:
            return "高"
        elif conf >= 0.4:
            return "中等"
        else:
            return "低"

    @staticmethod
    def _describe_confidence_en(conf: float) -> str:
        if conf >= 0.8:
            return "very high"
        elif conf >= 0.6:
            return "high"
        elif conf >= 0.4:
            return "moderate"
        else:
            return "low"

    # ── 持久化 ──

    def _save_records(self) -> None:
        if not self._data_path:
            return
        try:
            self._data_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "temperature": self.temperature,
                "kelly_fraction": self.kelly_fraction,
                "alignment_temperature": self.alignment_temperature,
                "records": [
                    {
                        "timestamp": r.timestamp.isoformat(),
                        "raw_confidence": r.raw_confidence,
                        "calibrated_confidence": r.calibrated_confidence,
                        "alignment_score": r.alignment_score,
                        "position_multiplier": r.position_multiplier,
                        "actual_outcome": r.actual_outcome,
                        "was_profitable": r.was_profitable,
                    }
                    for r in self._records[-500:]  # 保留最近 500 筆
                ],
                "saved_at": datetime.now().isoformat(),
            }
            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"[校準] 紀錄已保存: {self._data_path}")
        except Exception as e:
            logger.warning(f"[校準] 保存紀錄失敗: {e}")

    def _load_records(self) -> None:
        if not self._data_path or not self._data_path.exists():
            return
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.temperature = data.get("temperature", self.temperature)
            self.kelly_fraction = data.get("kelly_fraction", self.kelly_fraction)
            self.alignment_temperature = data.get(
                "alignment_temperature", self.alignment_temperature
            )
            for r_data in data.get("records", []):
                record = CalibrationRecord(
                    timestamp=datetime.fromisoformat(r_data["timestamp"]),
                    raw_confidence=r_data["raw_confidence"],
                    calibrated_confidence=r_data["calibrated_confidence"],
                    alignment_score=r_data["alignment_score"],
                    position_multiplier=r_data["position_multiplier"],
                    actual_outcome=r_data.get("actual_outcome"),
                    was_profitable=r_data.get("was_profitable"),
                )
                self._records.append(record)
            logger.info(
                f"[校準] 載入 {len(self._records)} 筆歷史紀錄 | T={self.temperature:.2f}"
            )
        except Exception as e:
            logger.warning(f"[校準] 載入紀錄失敗: {e}")


# ════════════════════════════════════════════════════════════════════
# 模組級單例
# ════════════════════════════════════════════════════════════════════

_calibrator_instance: Optional[AIConfidenceCalibrator] = None


def get_confidence_calibrator(
    calibration_data_path: Optional[str] = None,
) -> AIConfidenceCalibrator:
    """取得 AIConfidenceCalibrator 單例"""
    global _calibrator_instance
    if _calibrator_instance is None:
        if calibration_data_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            calibration_data_path = str(
                project_root / "data" / "bioneuronai" / "risk" / "calibration_records.json"
            )
        _calibrator_instance = AIConfidenceCalibrator(
            calibration_data_path=calibration_data_path,
        )
    return _calibrator_instance


__all__ = [
    "AIConfidenceCalibrator",
    "AlignmentReport",
    "CalibrationRecord",
    "get_confidence_calibrator",
]


# ════════════════════════════════════════════════════════════════════
# 🚀 程式可運行與直接驗證原則 (CODE_FIX_GUIDE.md)
# ════════════════════════════════════════════════════════════════════

