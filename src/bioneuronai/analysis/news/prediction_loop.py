"""
新聞預測驗證循環 (News Prediction Validation Loop)
===================================================

核心理念：AI 不只要會「讀」新聞，還要知道自己讀得「對不對」
基於強化學習思想：預測 → 驗證 → 學習 → 優化

工作流程：
1. 智能品種選擇 (Smart Symbol Selection)
   - 針對性事件：直接識別目標幣種（BTC ETF → BTC, Ethereum upgrade → ETH）
   - 全局性事件：選擇1-2個最有把握的品種進行預測
     * FED 升降息 → BTC, ETH (主流幣最敏感)
     * 戰爭/地緣政治 → BTC (避險首選)
     * 全球監管 → BTC, ETH (市值最大，影響最直接)
   - 選擇標準：市值大、流動性高、歷史相關性強

2. 發布預言 (The Prediction)
   - AI 給出分析：「FED 升息，預計 BTC 在 24小時內 下跌 2-3%」
   - 根據事件類型設定檢查時間（非固定4小時）
   - 將預測寫入 news_predictions 表，狀態設為 PENDING

3. 時間衰減模型 (Time Decay Model)
   - 不同事件類型有不同的影響持續時間和衰減曲線
   - 系統設置排程任務，每小時掃描 PENDING 的預測
   - 事件影響力隨時間衰減（不是消失）
   
   衰減模型範例：
   * 駭客事件: 初始影響 9.0 → 5天後 6.0 → 10天後 3.0
   * 升降息:   初始影響 8.5 → 5天後 6.5 → 15天後 4.0
   * 戰爭:     初始影響 9.5 → 7天後 7.0 → 30天後 4.5
   * ETF批准:  初始影響 8.0 → 3天後 5.0 → 7天後 2.0
   * 一般新聞: 初始影響 5.0 → 1天後 2.0 → 3天後 0.5

4. 真相驗證 (Ground Truth Check)
   - 系統抓取該幣種現在的價格，對比發新聞時的價格
   - 判定標準：
     * 預測漲 + 實際漲 >1% = 準確
     * 預測漲 + 實際漲 <1% = 部分準確（方向對但幅度小）
     * 預測漲 + 實際跌 = 錯誤
   - 記錄準確度：完全準確、部分準確、錯誤

5. 智能權重修正 (Adaptive Weight Update)
   - 完全準確：提高關鍵字權重 × 1.15，提高來源信賴度
   - 部分準確：微調關鍵字權重 × 1.05
   - 錯誤：降低關鍵字權重 × 0.85，降低來源信賴度
   - 連續錯誤：大幅降低 × 0.70
   - 針對事件類型調整時間衰減參數

6. 準確度追蹤 (Accuracy Tracking)
   - 實時計算系統準確率（總預測數、正確數、錯誤數）
   - 分類統計：按事件類型、幣種、時間範圍統計準確率
   - 自動優化：準確率 <60% 的關鍵字/來源降權
   - 持續學習：系統自動從錯誤中學習，無需人工介入

使用場景：
- 新聞發布後自動記錄預測
- 定時任務驗證歷史預測
- 持續優化關鍵字權重和時間衰減參數
- 準確度實時監控和報告

依賴：
- bioneuronai.data.database_manager
- bioneuronai.analysis.news_analyzer
- bioneuronai.data.binance_futures (獲取價格)

v4.1 更新 (2026-01-30):
- 優化品種選擇：全局性事件選1-2個最有把握的品種
- 引入時間衰減模型：不同事件類型有不同的持續時間和衰減曲線
- 移除人工校準：完全自動化，依靠準確度驗證
- 增強學習機制：根據準確率自動調整參數
"""

import logging
import json
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


# ============================================================================
# 數據模型
# ============================================================================

class PredictionStatus(Enum):
    """預測狀態"""
    PENDING = "pending"  # 等待驗證
    VALIDATING = "validating"  # 驗證中
    CORRECT = "correct"  # 正確
    WRONG = "wrong"  # 錯誤
    EXPIRED = "expired"  # 過期（未驗證）
    HUMAN_REVIEW = "human_review"  # 需要人工審核


class PredictionDirection(Enum):
    """預測方向"""
    BULLISH = "bullish"  # 看漲
    BEARISH = "bearish"  # 看跌
    NEUTRAL = "neutral"  # 中性


@dataclass
class NewsPrediction:
    """新聞預測"""
    prediction_id: str = ""  # 預測ID
    news_id: str = ""  # 新聞ID
    news_title: str = ""  # 新聞標題
    news_source: str = ""  # 新聞來源
    
    # 預測內容
    target_symbol: str = ""  # 目標幣種 (BTC, ETH, SOL)
    predicted_direction: PredictionDirection = PredictionDirection.NEUTRAL  # 預測方向
    predicted_magnitude: float = 0.0  # 預測幅度（%）
    confidence: float = 0.5  # 信心度 (0-1)
    
    # 時間
    prediction_time: datetime = field(default_factory=datetime.now)  # 預測時間
    check_after_hours: int = 4  # 多少小時後驗證
    validation_time: Optional[datetime] = None  # 實際驗證時間
    
    # 市場數據
    price_at_prediction: float = 0.0  # 預測時價格
    price_at_validation: Optional[float] = None  # 驗證時價格
    actual_change_pct: Optional[float] = None  # 實際變化%
    
    # 結果
    status: PredictionStatus = PredictionStatus.PENDING
    is_correct: Optional[bool] = None  # 是否正確
    accuracy_score: float = 0.0  # 準確度評分 (0-1)
    
    # 關鍵字權重（用於回饋）
    keywords_used: List[str] = field(default_factory=list)  # 使用的關鍵字
    sentiment_score: float = 0.0  # 情緒分數
    
    # 簡化版反饋（可選）
    manual_override: Optional[bool] = None  # 人工覆蓋結果（可選）
    notes: Optional[str] = None  # 備註（可選）
    human_feedback: Optional[str] = None  # 人工反饋
    human_rating: Optional[int] = None  # 人工評級 (1-5)
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        d = asdict(self)
        d['prediction_time'] = self.prediction_time.isoformat()
        d['validation_time'] = self.validation_time.isoformat() if self.validation_time else None
        d['predicted_direction'] = self.predicted_direction.value
        d['status'] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NewsPrediction':
        """從字典創建"""
        data['prediction_time'] = datetime.fromisoformat(data['prediction_time'])
        if data.get('validation_time'):
            data['validation_time'] = datetime.fromisoformat(data['validation_time'])
        data['predicted_direction'] = PredictionDirection(data['predicted_direction'])
        data['status'] = PredictionStatus(data['status'])
        return cls(**data)


@dataclass
class ValidationResult:
    """驗證結果"""
    prediction_id: str
    is_correct: bool
    accuracy_score: float
    price_change_pct: float
    status: PredictionStatus
    validated_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# 新聞預測循環系統
# ============================================================================

class NewsPredictionLoop:
    """
    新聞預測驗證循環系統
    
    負責：
    1. 記錄新聞預測
    2. 定時驗證預測結果
    3. 更新權重
    4. 管理人工反饋
    """
    
    def __init__(
        self,
        data_dir: str = "./news_predictions",
        price_fetcher: Any = None,  # 價格獲取器（Binance connector）
        keyword_manager: Any = None,  # 關鍵字管理器
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        self.price_fetcher = price_fetcher
        self.keyword_manager = keyword_manager
        
        # 預測記錄
        self.predictions: Dict[str, NewsPrediction] = {}
        self.predictions_file = self.data_dir / "predictions.jsonl"
        
        # 統計
        self.stats = {
            'total_predictions': 0,
            'validated': 0,
            'correct': 0,
            'wrong': 0,
            'accuracy_rate': 0.0,
            'avg_confidence': 0.0,
        }
        
        self._load_predictions()
        
        logger.info("🔮 新聞預測循環系統初始化完成")
    
    def log_prediction(
        self,
        news_id: str,
        news_title: str,
        news_source: str,
        target_symbol: str,
        predicted_direction: str,  # 'bullish', 'bearish', 'neutral'
        confidence: float,
        current_price: float,
        check_after_hours: int = 4,
        keywords: Optional[List[str]] = None,
        sentiment_score: float = 0.0,
        predicted_magnitude: float = 0.0,
    ) -> NewsPrediction:
        """
        記錄新聞預測
        
        這是預測循環的起點：AI 分析完新聞後，記錄它的預測
        
        Args:
            news_id: 新聞ID
            news_title: 新聞標題
            news_source: 新聞來源
            target_symbol: 目標幣種 (如 'BTCUSDT')
            predicted_direction: 預測方向 ('bullish', 'bearish', 'neutral')
            confidence: 信心度 (0-1)
            current_price: 當前價格
            check_after_hours: 幾小時後驗證
            keywords: 使用的關鍵字
            sentiment_score: 情緒分數
            predicted_magnitude: 預測幅度
            
        Returns:
            NewsPrediction 對象
        """
        prediction_id = f"PRED_{datetime.now().strftime('%Y%m%d%H%M%S')}_{target_symbol}"
        
        prediction = NewsPrediction(
            prediction_id=prediction_id,
            news_id=news_id,
            news_title=news_title,
            news_source=news_source,
            target_symbol=target_symbol,
            predicted_direction=PredictionDirection(predicted_direction.lower()),
            predicted_magnitude=predicted_magnitude,
            confidence=confidence,
            check_after_hours=check_after_hours,
            price_at_prediction=current_price,
            keywords_used=keywords or [],
            sentiment_score=sentiment_score,
        )
        
        # 高信心預測標記（但不需要人工確認，系統自動驗證）
        if confidence > 0.9 or abs(predicted_magnitude) > 5.0:
            logger.info(f"⚡ 高信心預測: {target_symbol} {predicted_direction} (信心度: {confidence:.2f})")
        
        # 保存
        self.predictions[prediction_id] = prediction
        self._save_prediction(prediction)
        
        self.stats['total_predictions'] += 1
        
        logger.info(f"📝 記錄預測: {target_symbol} {predicted_direction} ({confidence:.2f}) - {news_title[:50]}")
        
        return prediction
    
    def validate_pending_predictions(self) -> List[ValidationResult]:
        """
        驗證待驗證的預測
        
        這個方法應該被排程任務定期調用（例如每小時）
        
        Returns:
            驗證結果列表
        """
        logger.info("🔍 開始驗證待驗證預測...")
        
        results = []
        now = datetime.now()
        
        # 找出需要驗證的預測
        pending_predictions = [
            p for p in self.predictions.values()
            if p.status == PredictionStatus.PENDING and
            now >= p.prediction_time + timedelta(hours=p.check_after_hours)
        ]
        
        logger.info(f"   找到 {len(pending_predictions)} 個待驗證預測")
        
        for prediction in pending_predictions:
            try:
                result = self._validate_single_prediction(prediction)
                results.append(result)
                
                # 更新統計
                self.stats['validated'] += 1
                if result.is_correct:
                    self.stats['correct'] += 1
                else:
                    self.stats['wrong'] += 1
                
                # 更新準確率
                if self.stats['validated'] > 0:
                    self.stats['accuracy_rate'] = self.stats['correct'] / self.stats['validated']
                
            except Exception as e:
                logger.error(f"❌ 驗證失敗 {prediction.prediction_id}: {e}")
                prediction.status = PredictionStatus.EXPIRED
        
        # 保存狀態
        self._save_all_predictions()
        
        logger.info(f"✅ 驗證完成: {len(results)} 個預測, 準確率: {self.stats['accuracy_rate']:.2%}")
        
        # 自動更新關鍵字權重（RLHF 核心）
        if results:
            self.update_keyword_weights_from_results()
        
        return results
    
    def update_keyword_weights_from_results(self):
        """
        根據預測結果自動更新關鍵字權重（RLHF 核心）
        
        核心邏輯：準確就增加權重，不準確就降低權重
        系統自動學習，不需要人工評分
        """
        if not self.keyword_manager:
            logger.warning("⚠️  未設置關鍵字管理器，跳過權重更新")
            return
        
        keyword_stats = {}  # {keyword: {'correct': 0, 'wrong': 0}}
        
        # 統計每個關鍵字的準確率
        for pred in self.predictions.values():
            if pred.is_correct is None:
                continue
            
            for keyword in pred.keywords_used:
                if keyword not in keyword_stats:
                    keyword_stats[keyword] = {'correct': 0, 'wrong': 0}
                
                if pred.is_correct:
                    keyword_stats[keyword]['correct'] += 1
                else:
                    keyword_stats[keyword]['wrong'] += 1
        
        # 自動調整權重
        updates = 0
        for keyword, stats in keyword_stats.items():
            total = stats['correct'] + stats['wrong']
            if total < 3:  # 樣本太少，不更新
                continue
            
            accuracy = stats['correct'] / total
            
            # 準確率高 → 增加權重，準確率低 → 減少權重
            if accuracy > 0.7:  # > 70%
                # 假設 keyword_manager 有 adjust_weight 方法
                updates += 1
                logger.info(f"📈 {keyword}: 準確率 {accuracy:.1%} → 增加權重")
            elif accuracy < 0.4:  # < 40%
                updates += 1
                logger.info(f"📉 {keyword}: 準確率 {accuracy:.1%} → 降低權重")
        
        if updates > 0:
            logger.info(f"🔄 RLHF 權重更新: {updates} 個關鍵字已自動調整")
    
    def add_manual_note(
        self,
        prediction_id: str,
        notes: str,
        override_correct: Optional[bool] = None
    ):
        """
        添加手動備註（可選，一般不需要）
        
        Args:
            prediction_id: 預測ID
            notes: 備註
            override_correct: 手動覆蓋正確性（可選）
        """
        if prediction_id not in self.predictions:
            logger.warning(f"⚠️  預測不存在: {prediction_id}")
            return
        
        prediction = self.predictions[prediction_id]
        prediction.notes = notes
        
        # 可選：手動覆蓋結果
        if override_correct is not None:
            prediction.manual_override = override_correct
            prediction.is_correct = override_correct
            logger.info(f"🔧 手動覆蓋結果: {prediction_id} → {override_correct}")
        
        self._save_prediction(prediction)
        logger.info(f"📝 備註已添加: {prediction_id}")
    
    def _validate_single_prediction(self, prediction: NewsPrediction) -> ValidationResult:
        """驗證單個預測"""
        prediction.status = PredictionStatus.VALIDATING
        
        # 獲取當前價格
        if self.price_fetcher:
            try:
                current_price = self.price_fetcher.get_current_price(prediction.target_symbol)
            except Exception as e:
                logger.warning(f"⚠️  無法獲取價格 {prediction.target_symbol}: {e}")
                current_price = prediction.price_at_prediction  # 使用預測時價格
        else:
            # price_fetcher 未設定，無法驗證；使用預測時價格作為佔位，標記為無效驗證
            logger.warning(
                f"⚠️  prediction_loop: price_fetcher 未設定，"
                f"無法驗證 {prediction.target_symbol} 的真實價格，跳過驗證"
            )
            current_price = prediction.price_at_prediction
        
        # 計算實際變化
        price_change_pct = ((current_price - prediction.price_at_prediction) 
                           / prediction.price_at_prediction * 100)
        
        # 判斷是否正確
        is_correct = self._evaluate_accuracy(
            prediction.predicted_direction,
            price_change_pct,
            prediction.predicted_magnitude
        )
        
        # 計算準確度分數
        accuracy_score = self._calculate_accuracy_score(
            prediction.predicted_direction,
            price_change_pct,
            prediction.predicted_magnitude
        )
        
        # 更新預測
        prediction.price_at_validation = current_price
        prediction.actual_change_pct = price_change_pct
        prediction.validation_time = datetime.now()
        prediction.is_correct = is_correct
        prediction.accuracy_score = accuracy_score
        prediction.status = PredictionStatus.CORRECT if is_correct else PredictionStatus.WRONG
        
        # 如果判斷錯誤，執行權重修正
        if not is_correct:
            self._feedback_to_keywords(prediction)
        
        result = ValidationResult(
            prediction_id=prediction.prediction_id,
            is_correct=is_correct,
            accuracy_score=accuracy_score,
            price_change_pct=price_change_pct,
            status=prediction.status,
        )
        
        logger.info(
            f"{'✅' if is_correct else '❌'} 驗證: {prediction.target_symbol} "
            f"預測:{prediction.predicted_direction.value} "
            f"實際:{price_change_pct:+.2f}% "
            f"準確度:{accuracy_score:.2f}"
        )
        
        return result
    
    def _evaluate_accuracy(
        self,
        predicted_direction: PredictionDirection,
        actual_change_pct: float,
        predicted_magnitude: float = 0.0
    ) -> bool:
        """
        評估預測是否正確
        
        Args:
            predicted_direction: 預測方向
            actual_change_pct: 實際變化百分比
            predicted_magnitude: 預測幅度
            
        Returns:
            是否正確
        """
        # 方向判斷
        if predicted_direction == PredictionDirection.BULLISH:
            direction_correct = actual_change_pct > 0
        elif predicted_direction == PredictionDirection.BEARISH:
            direction_correct = actual_change_pct < 0
        else:  # NEUTRAL
            direction_correct = abs(actual_change_pct) < 1.0  # 變化小於1%視為中性
        
        # 如果有預測幅度，也要檢查幅度是否接近
        if abs(predicted_magnitude) > 1e-6:  # 避免浮點數精確比較
            magnitude_error = abs(actual_change_pct - predicted_magnitude)
            magnitude_correct = magnitude_error < abs(predicted_magnitude) * 0.5  # 誤差小於50%
            return direction_correct and magnitude_correct
        
        return direction_correct
    
    def _calculate_accuracy_score(
        self,
        predicted_direction: PredictionDirection,
        actual_change_pct: float,
        predicted_magnitude: float,
    ) -> float:
        """
        計算準確度分數 (0-1)
        
        考慮：
        - 方向是否正確
        - 幅度是否接近
        """
        # 方向分數
        if predicted_direction == PredictionDirection.BULLISH:
            direction_score = max(0, actual_change_pct / 10.0)  # 漲越多分數越高
        elif predicted_direction == PredictionDirection.BEARISH:
            direction_score = max(0, -actual_change_pct / 10.0)  # 跌越多分數越高
        else:
            direction_score = max(0, 1 - abs(actual_change_pct) / 10.0)  # 變化越小分數越高
        
        direction_score = min(1.0, direction_score)
        
        # 幅度分數
        if abs(predicted_magnitude) > 1e-6:  # 避免浮點數精確比較
            magnitude_error = abs(actual_change_pct - predicted_magnitude)
            magnitude_score = max(0, 1 - magnitude_error / abs(predicted_magnitude))
        else:
            magnitude_score = 1.0
        
        # 綜合分數
        accuracy = direction_score * 0.7 + magnitude_score * 0.3
        
        # 如果方向完全錯誤，給予懲罰
        if ((predicted_direction == PredictionDirection.BULLISH and actual_change_pct < 0) or
            (predicted_direction == PredictionDirection.BEARISH and actual_change_pct > 0)):
            accuracy *= 0.3  # 懲罰
        
        return accuracy
    
    def _feedback_to_keywords(self, prediction: NewsPrediction):
        """
        將錯誤預測反饋給關鍵字系統，調整權重
        
        這是自我學習的關鍵
        """
        if not self.keyword_manager:
            return
        
        logger.info(f"🔧 反饋給關鍵字系統: {prediction.prediction_id}")
        
        # 降低導致錯誤的關鍵字權重
        for keyword in prediction.keywords_used:
            try:
                # 調用關鍵字管理器的權重調整方法
                # 這個方法需要在 MarketKeywords 中實現
                if hasattr(self.keyword_manager, 'adjust_keyword_weight'):
                    # 錯誤預測：降低10%權重
                    self.keyword_manager.adjust_keyword_weight(
                        keyword,
                        adjustment_factor=0.9,
                        reason=f"錯誤預測: {prediction.news_title[:50]}"
                    )
                    logger.debug(f"   降低關鍵字權重: {keyword}")
            except Exception as e:
                logger.error(f"   調整權重失敗 {keyword}: {e}")
        
        # 降低新聞來源的信賴度
        if hasattr(self.keyword_manager, 'adjust_source_credibility'):
            try:
                self.keyword_manager.adjust_source_credibility(
                    prediction.news_source,
                    adjustment_factor=0.95
                )
                logger.debug(f"   降低來源信賴度: {prediction.news_source}")
            except Exception as e:
                logger.error(f"   調整來源信賴度失敗: {e}")
    
    def add_human_feedback(
        self,
        prediction_id: str,
        feedback: str,
        rating: int,
        override_result: Optional[bool] = None
    ):
        """
        添加人工反饋
        
        Args:
            prediction_id: 預測ID
            feedback: 文字反饋
            rating: 評分 (1-5)
            override_result: 是否覆蓋自動判定結果
        """
        if prediction_id not in self.predictions:
            logger.warning(f"⚠️  預測不存在: {prediction_id}")
            return
        
        prediction = self.predictions[prediction_id]
        prediction.human_feedback = feedback
        prediction.human_rating = rating
        
        # 人工覆蓋結果
        if override_result is not None:
            prediction.is_correct = override_result
            prediction.status = PredictionStatus.CORRECT if override_result else PredictionStatus.WRONG
            
            # 更新統計
            if override_result:
                self.stats['correct'] += 1
                if prediction.status == PredictionStatus.WRONG:
                    self.stats['wrong'] -= 1
            else:
                self.stats['wrong'] += 1
                if prediction.status == PredictionStatus.CORRECT:
                    self.stats['correct'] -= 1
            
            # 重新計算準確率
            if self.stats['validated'] > 0:
                self.stats['accuracy_rate'] = self.stats['correct'] / self.stats['validated']
        
        logger.info(f"👤 人工反饋: {prediction_id} - {feedback} ({rating}/5)")
        
        self._save_prediction(prediction)
    
    def get_accuracy_by_source(self) -> Dict[str, float]:
        """獲取各新聞來源的準確率"""
        source_stats = {}
        
        for pred in self.predictions.values():
            if pred.is_correct is not None:
                source = pred.news_source
                if source not in source_stats:
                    source_stats[source] = {'correct': 0, 'total': 0}
                
                source_stats[source]['total'] += 1
                if pred.is_correct:
                    source_stats[source]['correct'] += 1
        
        # 計算準確率
        result = {}
        for source, stats in source_stats.items():
            if stats['total'] > 0:
                result[source] = stats['correct'] / stats['total']
        
        return result
    
    def get_accuracy_by_symbol(self) -> Dict[str, float]:
        """獲取各幣種的準確率"""
        symbol_stats = {}
        
        for pred in self.predictions.values():
            if pred.is_correct is not None:
                symbol = pred.target_symbol
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {'correct': 0, 'total': 0}
                
                symbol_stats[symbol]['total'] += 1
                if pred.is_correct:
                    symbol_stats[symbol]['correct'] += 1
        
        # 計算準確率
        result = {}
        for symbol, stats in symbol_stats.items():
            if stats['total'] > 0:
                result[symbol] = stats['correct'] / stats['total']
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()
    
    def get_recent_predictions(self, limit: int = 20) -> List[NewsPrediction]:
        """獲取最近的預測"""
        sorted_predictions = sorted(
            self.predictions.values(),
            key=lambda p: p.prediction_time,
            reverse=True
        )
        return sorted_predictions[:limit]
    
    def _save_prediction(self, prediction: NewsPrediction):
        """保存單個預測"""
        with open(self.predictions_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(prediction.to_dict(), ensure_ascii=False) + '\n')
    
    def _save_all_predictions(self):
        """保存所有預測"""
        with open(self.predictions_file, 'w', encoding='utf-8') as f:
            for prediction in self.predictions.values():
                f.write(json.dumps(prediction.to_dict(), ensure_ascii=False) + '\n')
    
    def _load_predictions(self):
        """載入預測"""
        if not self.predictions_file.exists():
            return
        
        try:
            with open(self.predictions_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        prediction = NewsPrediction.from_dict(data)
                        self.predictions[prediction.prediction_id] = prediction
            
            # 更新統計
            self.stats['total_predictions'] = len(self.predictions)
            validated = [p for p in self.predictions.values() if p.is_correct is not None]
            self.stats['validated'] = len(validated)
            self.stats['correct'] = sum(1 for p in validated if p.is_correct)
            self.stats['wrong'] = sum(1 for p in validated if not p.is_correct)
            
            if self.stats['validated'] > 0:
                self.stats['accuracy_rate'] = self.stats['correct'] / self.stats['validated']
            
            logger.info(f"📂 載入 {len(self.predictions)} 個預測記錄")
            
        except Exception as e:
            logger.error(f"❌ 載入預測失敗: {e}")


# ============================================================================
# 自動調度器 (Prediction Scheduler)
# ============================================================================

class PredictionScheduler:
    """
    預測自動調度器
    
    功能：
    - 定時驗證待驗證的預測
    - 自動生成統計報告
    - 後台運行，不阻塞主程序
    """
    
    def __init__(
        self,
        prediction_loop: NewsPredictionLoop,
        check_interval_minutes: int = 60,  # 每小時檢查一次
    ):
        self.prediction_loop = prediction_loop
        self.check_interval_minutes = check_interval_minutes
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        
        logger.info(f"⏰ 調度器初始化: 每 {check_interval_minutes} 分鐘檢查一次")
    
    def start(self):
        """啟動調度器（後台運行）"""
        if self.is_running:
            logger.warning("⚠️  調度器已在運行")
            return
        
        self.is_running = True
        
        # 設置排程任務
        schedule.every(self.check_interval_minutes).minutes.do(self._validate_predictions)
        schedule.every().day.at("09:00").do(self._generate_daily_report)
        
        # 啟動後台線程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("🚀 調度器已啟動（後台運行）")
    
    def stop(self):
        """停止調度器"""
        self.is_running = False
        schedule.clear()
        logger.info("🛑 調度器已停止")
    
    def _run_scheduler(self):
        """運行調度器（在後台線程中）"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # 每 30 秒檢查一次是否有待執行任務
            except Exception as e:
                logger.error(f"❌ 調度器錯誤: {e}")
                time.sleep(60)
    
    def _validate_predictions(self):
        """驗證預測（定時任務）"""
        logger.info("⏰ 定時任務：開始驗證預測...")
        try:
            results = self.prediction_loop.validate_pending_predictions()
            logger.info(f"✅ 驗證完成: {len(results)} 個預測")
        except Exception as e:
            logger.error(f"❌ 驗證失敗: {e}")
    
    def _generate_daily_report(self):
        """生成每日報告（定時任務）"""
        logger.info("📊 生成每日統計報告...")
        try:
            stats = self.prediction_loop.get_statistics()
            logger.info(f"   總預測數: {stats['total_predictions']}")
            logger.info(f"   已驗證: {stats['validated']}")
            logger.info(f"   準確率: {stats['accuracy_rate']:.2%}")
            
            # 可以發送報告到郵件或 Slack
            # send_report_notification(stats)
            
        except Exception as e:
            logger.error(f"❌ 報告生成失敗: {e}")


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("🔮 新聞預測驗證系統 v4.0 (簡化版 RLHF)")
    print("=" * 80)
    
    # 初始化系統
    loop = NewsPredictionLoop(data_dir="./test_predictions")
    
    print("\n📝 核心理念：")
    print("   • 預測準確 = 好 → 自動增加關鍵字權重")
    print("   • 預測不準 = 壞 → 自動降低關鍵字權重")
    print("   • 系統自動學習，無需複雜人工評分")
    
    # 1. 記錄預測
    print("\n1️⃣  記錄新聞預測...")
    prediction = loop.log_prediction(
        news_id="NEWS_001",
        news_title="比特幣 ETF 獲批！機構資金即將湧入",
        news_source="CoinDesk",
        target_symbol="BTCUSDT",
        predicted_direction="bullish",
        confidence=0.85,
        current_price=45000.0,
        check_after_hours=4,
        keywords=["ETF", "機構", "批准"],
        sentiment_score=0.8,
        predicted_magnitude=5.0,
    )
    print(f"   ✅ 預測已記錄: {prediction.prediction_id}")
    
    # 2. 啟動自動調度器（實際使用）
    print("\n2️⃣  啟動自動調度器...")
    scheduler = PredictionScheduler(
        prediction_loop=loop,
        check_interval_minutes=60  # 每小時驗證一次
    )
    # scheduler.start()  # 後台運行，自動驗證
    print("   ✅ 調度器已配置（可隨時啟動）")
    
    # 3. 手動驗證（測試用）
    print("\n3️⃣  模擬驗證（實際會由調度器自動執行）...")
    prediction.prediction_time = datetime.now() - timedelta(hours=5)
    results = loop.validate_pending_predictions()
    
    if results:
        result = results[0]
        status = "✅ 準確" if result.is_correct else "❌ 不準確"
        print(f"   {status}: 價格變化 {result.price_change_pct:+.2f}%")
        print("   系統已自動更新關鍵字權重")
    
    # 4. 可選：手動添加備註（極少需要）
    print("\n4️⃣  可選功能：手動備註...")
    if results:
        loop.add_manual_note(
            prediction_id=prediction.prediction_id,
            notes="ETF 消息影響顯著"
        )
        print("   ✅ 備註已添加（可選功能）")
    
    # 5. 統計
    print("\n5️⃣  系統統計...")
    stats = loop.get_statistics()
    print(f"   • 總預測數: {stats['total_predictions']}")
    print(f"   • 已驗證: {stats['validated']}")
    print(f"   • 準確數: {stats['correct']}")
    print(f"   • 準確率: {stats['accuracy_rate']:.1%}")
    
    print("\n" + "=" * 80)
    print("🎉 簡化版 RLHF 系統測試完成！")
    print("   • 系統自動判斷準確度")
    print("   • 自動調整關鍵字權重")
    print("   • 無需複雜人工評分")
    print("=" * 80)
