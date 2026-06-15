"""
AI 反思與自我學習系統 (AI Reflection Loop)
=======================================

核心功能：
  1. 定期（每日/每週）從 EpisodicMemory 提取交易經驗記錄（特別是虧損交易）。
  2. 分析市場特徵（波動率、資金費率、對齊度、信心度）與盈虧的關聯。
  3. 生成結構化的 `learning_report.json` 分析報告。
  4. 回饋並呼叫 `confidence_calibrator` 的 `refit_temperature` 重新擬合信心校準參數 (T)。

設計原則：
  - 遵循 CODE_FIX_GUIDE.md 規範：清晰的類型標註、完整的錯誤處理、可直接運行驗證。
  - 與現有 `EpisodicMemory` 和 `AIConfidenceCalibrator` 無縫整合。
  - 中英文雙語日誌輸出，便於系統可觀測性。
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# 導入現有依賴
from bioneuronai.memory.episodic_memory import EpisodicMemory, ExperienceRecord
from bioneuronai.risk_management.confidence_calibrator import get_confidence_calibrator

logger = logging.getLogger(__name__)


@dataclass
class ReflectionResult:
    """反思循環執行結果"""
    timestamp: datetime
    total_trades_analyzed: int
    losing_trades_count: int
    average_loss_pct: float
    recommended_temperature: Optional[float]
    learning_report_path: str
    feature_insights: Dict[str, Any] = field(default_factory=dict)
    status: str = "SUCCESS"


class AIReflectionLoop:
    """
    AI 反思循環器 (System 2 / 反思大腦)

    負責從交易歷史中提煉教訓，調整 System 1 的核心風控與校準參數。
    """

    def __init__(
        self,
        memory_instance: Optional[EpisodicMemory] = None,
        report_dir: Optional[str] = None,
    ) -> None:
        """
        Args:
            memory_instance: 傳入的 EpisodicMemory 實例。若為 None 則使用預設路徑載入。
            report_dir: 學習報告的保存目錄。
        """
        project_root = Path(__file__).resolve().parents[3]
        
        # 延遲初始化 EpisodicMemory，避免冷啟動問題
        self.memory = memory_instance
        if self.memory is None:
            memory_dir = project_root / "data" / "bioneuronai" / "memory"
            try:
                self.memory = EpisodicMemory(data_dir=memory_dir)
            except Exception as e:
                logger.warning(f"⚠️ 無法初始化 EpisodicMemory 實例: {e}")

        # 報告保存路徑
        self.report_dir = Path(report_dir) if report_dir else project_root / "data" / "bioneuronai" / "planning" / "reflection"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ AIReflectionLoop 初始化成功 | 報告目錄: {self.report_dir}")

    def run_reflection_cycle(self, k: int = 50) -> ReflectionResult:
        """
        執行一次反思與自我學習循環

        Args:
            k: 抽樣分析的歷史記錄筆數。

        Returns:
            ReflectionResult 分析結果
        """
        start_time = datetime.now()
        logger.info(f"🧠 [反思大腦] 開始執行自我優化反思循環... (抽樣數 k={k})")

        if self.memory is None:
            logger.error("[反思大腦] 記憶層 EpisodicMemory 不可用，中止反思流程。")
            return ReflectionResult(
                timestamp=start_time,
                total_trades_analyzed=0,
                losing_trades_count=0,
                average_loss_pct=0.0,
                recommended_temperature=None,
                learning_report_path="",
                status="ERROR_MEMORY_UNAVAILABLE"
            )

        # 1. 採樣熱回放緩衝
        records: List[ExperienceRecord] = self.memory.sample_hot(k)
        if not records:
            # 如果熱緩衝為空，嘗試載入冷庫中的記錄做備用
            logger.warning("[反思大腦] 熱記憶庫為空，無可用交易數據進行反思。")
            return ReflectionResult(
                timestamp=start_time,
                total_trades_analyzed=0,
                losing_trades_count=0,
                average_loss_pct=0.0,
                recommended_temperature=None,
                learning_report_path="",
                status="NO_DATA"
            )

        # 2. 篩選與分析虧損交易
        losing_trades = [r for r in records if r.pnl_pct < 0]
        total_count = len(records)
        loss_count = len(losing_trades)
        
        avg_loss = 0.0
        if loss_count > 0:
            avg_loss = float(np.mean([r.pnl_pct for r in losing_trades]))

        logger.info(
            f"📊 [反思大腦] 樣本分析: 共 {total_count} 筆交易，其中 {loss_count} 筆虧損，"
            f"平均虧損幅度: {avg_loss:.2%}"
        )

        # 3. 提煉特徵關聯性 (Feature Correlation Insights)
        insights = self._analyze_loss_factors(records, losing_trades)

        # 4. 重新擬合信心校準溫度參數 T (Temperature Fitting)
        calibrator = get_confidence_calibrator()
        new_temp = None
        try:
            # 傳遞當前記憶庫有結果的總數進行擬合
            new_temp = calibrator.refit_temperature(min_samples=20)
        except Exception as e:
            logger.error(f"[反思大腦] 信心校準器重新擬合失敗: {e}")

        # 5. 保存報告為 JSON 格式
        report_data = {
            "timestamp": start_time.isoformat(),
            "sample_size": total_count,
            "loss_ratio": loss_count / total_count if total_count > 0 else 0,
            "average_loss_pct": avg_loss,
            "new_fitted_temperature": new_temp,
            "current_temperature": calibrator.temperature,
            "insights": insights,
        }

        report_file = self.report_dir / f"learning_report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 [反思大腦] 自我學習報告已寫入: {report_file}")
        except Exception as e:
            logger.error(f"[反思大腦] 寫入報告檔案失敗: {e}")

        return ReflectionResult(
            timestamp=start_time,
            total_trades_analyzed=total_count,
            losing_trades_count=loss_count,
            average_loss_pct=avg_loss,
            recommended_temperature=new_temp,
            learning_report_path=str(report_file),
            feature_insights=insights,
            status="SUCCESS"
        )

    def _analyze_loss_factors(
        self, 
        all_records: List[ExperienceRecord], 
        losing_records: List[ExperienceRecord]
    ) -> Dict[str, Any]:
        """
        分析在虧損交易中，哪些市場特徵有異常高或低的分佈。
        例如：是否大部份虧損都集中在 High Volatility 或是新聞逆風期。
        """
        if not losing_records:
            return {"message": "無虧損交易，表現優異。"}

        # 波動率分析
        avg_vol_all = float(np.mean([r.volatility_1h for r in all_records]))
        avg_vol_loss = float(np.mean([r.volatility_1h for r in losing_records]))

        # 對齊度分析 (如果有)
        avg_p_all = float(np.mean([r.decoded_confidence for r in all_records]))
        avg_p_loss = float(np.mean([r.decoded_confidence for r in losing_records]))

        # 事件分析
        regimes: Dict[str, int] = {}
        for r in losing_records:
            regimes[r.market_regime] = regimes.get(r.market_regime, 0) + 1

        # 判斷是否因高波動性導致虧損
        vol_sensitivity = "NORMAL"
        if avg_vol_loss > avg_vol_all * 1.25:
            vol_sensitivity = "HIGH"
            logger.warning("⚠️ [反思警告] 虧損交易的平均波動率顯著高於平均值！建議調低高波動環境的倉位。")

        # 判斷是否過度自信 (High confidence, yet losing)
        overconfidence_risk = "LOW"
        high_conf_losses = [r for r in losing_records if r.decoded_confidence > 0.75]
        if len(high_conf_losses) > len(losing_records) * 0.4:
            overconfidence_risk = "HIGH"
            logger.warning("⚠️ [反思警告] 高信心卻虧損的交易佔比過高！信心校準溫度參數亟需調高 (更保守)。")

        return {
            "volatility": {
                "average_volatility_all": round(avg_vol_all, 5),
                "average_volatility_loss": round(avg_vol_loss, 5),
                "sensitivity_level": vol_sensitivity
            },
            "confidence": {
                "average_confidence_all": round(avg_p_all, 3),
                "average_confidence_loss": round(avg_p_loss, 3),
                "overconfidence_risk": overconfidence_risk
            },
            "top_loss_regimes": sorted(regimes.items(), key=lambda x: x[1], reverse=True)
        }


# ════════════════════════════════════════════════════════════════════
# 🚀 程式可運行與直接驗證原則 (CODE_FIX_GUIDE.md)
# ════════════════════════════════════════════════════════════════════

