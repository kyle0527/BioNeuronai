"""
市場分析器 - Market Analyzer
分析當前市場環境，為交易計劃提供基礎數據
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class MarketCondition:
    """市場狀況數據結構"""
    timestamp: datetime
    overall_trend: str  # BULLISH, BEARISH, NEUTRAL, VOLATILE
    volatility_level: str  # LOW, MEDIUM, HIGH, EXTREME
    volatility_value: float
    market_phase: str  # ACCUMULATION, MARKUP, DISTRIBUTION, DECLINE
    sentiment_score: float  # -1.0 到 1.0
    fear_greed_index: int  # 0-100
    liquidity_condition: str  # EXCELLENT, GOOD, FAIR, POOR
    correlation_btc_eth: float
    external_factors: List[str]
    confidence_score: float  # 0-1

@dataclass
class TechnicalEnvironment:
    """技術環境分析"""
    timestamp: datetime
    dominant_timeframe: str  # 主導時間框架
    support_levels: List[float]
    resistance_levels: List[float]
    key_indicators: Dict[str, float]
    pattern_detected: List[str]
    breakout_probability: float
    reversal_signals: List[str]
    momentum_strength: float

@dataclass
class FundamentalEnvironment:
    """基本面環境分析"""
    timestamp: datetime
    macro_events: List[Dict]
    regulatory_climate: str  # POSITIVE, NEUTRAL, NEGATIVE
    adoption_trends: str  # INCREASING, STABLE, DECLINING
    institutional_flow: str  # INFLOW, NEUTRAL, OUTFLOW
    on_chain_metrics: Dict[str, float]
    news_sentiment: float
    social_sentiment: float

class MarketAnalyzer:
    """市場分析器 - 深度市場環境分析"""
    
    def __init__(self):
        self.analysis_history = []
        self.indicator_weights = {
            "trend_strength": 0.25,
            "volatility": 0.20,
            "sentiment": 0.20,
            "liquidity": 0.15,
            "fundamentals": 0.20
        }
    
    async def analyze_current_market_condition(self) -> MarketCondition:
        """分析當前市場狀況 - 核心功能"""
        logger.info("🔍 開始深度市場環境分析...")
        
        try:
            # 1. 趨勢分析
            trend_analysis = await self._analyze_market_trend()
            logger.info(f"   ✓ 趨勢分析: {trend_analysis['overall_trend']} (強度: {trend_analysis['strength']:.2f})")
            
            # 2. 波動性分析
            volatility_analysis = await self._analyze_volatility()
            logger.info(f"   ✓ 波動性: {volatility_analysis['level']} ({volatility_analysis['value']:.1f}%)")
            
            # 3. 市場階段識別
            phase_analysis = await self._identify_market_phase()
            logger.info(f"   ✓ 市場階段: {phase_analysis['phase']} (確信度: {phase_analysis['confidence']:.2f})")
            
            # 4. 情緒分析
            sentiment_analysis = await self._analyze_market_sentiment()
            logger.info(f"   ✓ 市場情緒: {sentiment_analysis['score']:.2f} | 恐懼貪婪指數: {sentiment_analysis['fear_greed']}")
            
            # 5. 流動性分析
            liquidity_analysis = await self._analyze_liquidity_condition()
            logger.info(f"   ✓ 流動性狀況: {liquidity_analysis['condition']} (深度: {liquidity_analysis['depth_score']:.2f})")
            
            # 6. 外部因素分析
            external_analysis = await self._analyze_external_factors()
            logger.info(f"   ✓ 外部因素: {len(external_analysis['factors'])} 個影響因子")
            
            # 7. 相關性分析
            correlation_analysis = await self._analyze_asset_correlations()
            logger.info(f"   ✓ BTC-ETH相關性: {correlation_analysis['btc_eth']:.3f}")
            
            # 8. 綜合評估
            overall_assessment = self._synthesize_market_analysis(
                trend_analysis, volatility_analysis, phase_analysis,
                sentiment_analysis, liquidity_analysis, external_analysis, correlation_analysis
            )
            
            condition = MarketCondition(
                timestamp=datetime.now(),
                overall_trend=overall_assessment['trend'],
                volatility_level=volatility_analysis['level'],
                volatility_value=volatility_analysis['value'],
                market_phase=phase_analysis['phase'],
                sentiment_score=sentiment_analysis['score'],
                fear_greed_index=sentiment_analysis['fear_greed'],
                liquidity_condition=liquidity_analysis['condition'],
                correlation_btc_eth=correlation_analysis['btc_eth'],
                external_factors=external_analysis['factors'],
                confidence_score=overall_assessment['confidence']
            )
            
            self.analysis_history.append(condition)
            return condition
            
        except Exception as e:
            logger.error(f"市場分析失敗: {e}")
            return self._get_default_market_condition()
    
    async def analyze_technical_environment(self, symbols: List[str]) -> TechnicalEnvironment:
        """技術環境分析"""
        logger.info("📊 分析技術環境...")
        
        try:
            # 多時間框架分析
            timeframe_analysis = await self._multi_timeframe_analysis(symbols)
            
            # 關鍵位分析
            levels_analysis = await self._analyze_key_levels(symbols)
            
            # 指標綜合分析
            indicators_analysis = await self._comprehensive_indicator_analysis(symbols)
            
            # 型態識別
            pattern_analysis = await self._detect_chart_patterns(symbols)
            
            # 動量分析
            momentum_analysis = await self._analyze_market_momentum(symbols)
            
            return TechnicalEnvironment(
                timestamp=datetime.now(),
                dominant_timeframe=timeframe_analysis['dominant'],
                support_levels=levels_analysis['support'],
                resistance_levels=levels_analysis['resistance'],
                key_indicators=indicators_analysis['values'],
                pattern_detected=pattern_analysis['patterns'],
                breakout_probability=pattern_analysis['breakout_prob'],
                reversal_signals=pattern_analysis['reversal_signals'],
                momentum_strength=momentum_analysis['strength']
            )
            
        except Exception as e:
            logger.error(f"技術環境分析失敗: {e}")
            return self._get_default_technical_environment()
    
    async def analyze_fundamental_environment(self) -> FundamentalEnvironment:
        """基本面環境分析"""
        logger.info("📰 分析基本面環境...")
        
        try:
            # 宏觀事件分析
            macro_analysis = await self._analyze_macro_events()
            
            # 監管環境分析
            regulatory_analysis = await self._analyze_regulatory_climate()
            
            # 採用趨勢分析
            adoption_analysis = await self._analyze_adoption_trends()
            
            # 機構資金流向
            institutional_analysis = await self._analyze_institutional_flows()
            
            # 鏈上數據分析
            onchain_analysis = await self._analyze_onchain_metrics()
            
            # 新聞情緒分析
            news_sentiment = await self._analyze_news_sentiment()
            
            # 社交媒體情緒
            social_sentiment = await self._analyze_social_sentiment()
            
            return FundamentalEnvironment(
                timestamp=datetime.now(),
                macro_events=macro_analysis['events'],
                regulatory_climate=regulatory_analysis['climate'],
                adoption_trends=adoption_analysis['trend'],
                institutional_flow=institutional_analysis['flow'],
                on_chain_metrics=onchain_analysis['metrics'],
                news_sentiment=news_sentiment['score'],
                social_sentiment=social_sentiment['score']
            )
            
        except Exception as e:
            logger.error(f"基本面環境分析失敗: {e}")
            return self._get_default_fundamental_environment()
    
    # ========== 私有方法 ==========
    
    async def _analyze_market_trend(self) -> Dict:
        """趨勢分析"""
        # 模擬多時間框架趨勢分析
        timeframes = ['15m', '1h', '4h', '1d', '1w']
        trends = {
            '15m': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL'], p=[0.4, 0.3, 0.3]),
            '1h': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL'], p=[0.35, 0.35, 0.3]),
            '4h': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL'], p=[0.4, 0.2, 0.4]),
            '1d': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL'], p=[0.5, 0.2, 0.3]),
            '1w': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL'], p=[0.6, 0.1, 0.3])
        }
        
        # 計算整體趨勢
        bullish_count = sum(1 for t in trends.values() if t == 'BULLISH')
        bearish_count = sum(1 for t in trends.values() if t == 'BEARISH')
        
        if bullish_count > bearish_count:
            overall = 'BULLISH'
        elif bearish_count > bullish_count:
            overall = 'BEARISH' 
        else:
            overall = 'NEUTRAL'
        
        strength = abs(bullish_count - bearish_count) / len(timeframes)
        
        return {
            'timeframe_trends': trends,
            'overall_trend': overall,
            'strength': strength
        }
    
    async def _analyze_volatility(self) -> Dict:
        """波動性分析"""
        # 模擬VIX風格的波動率指標
        vix_value = np.random.normal(25, 10)  # 平均25%，標準差10%
        vix_value = max(5, min(80, vix_value))  # 限制在5-80%範圍
        
        if vix_value < 15:
            level = "LOW"
        elif vix_value < 25:
            level = "MEDIUM"
        elif vix_value < 40:
            level = "HIGH"
        else:
            level = "EXTREME"
        
        return {
            'value': vix_value,
            'level': level,
            'percentile_30d': np.random.uniform(20, 80)  # 30天百分位
        }
    
    async def _identify_market_phase(self) -> Dict:
        """市場階段識別"""
        phases = ['ACCUMULATION', 'MARKUP', 'DISTRIBUTION', 'DECLINE']
        phase = np.random.choice(phases, p=[0.25, 0.35, 0.25, 0.15])
        confidence = np.random.uniform(0.6, 0.95)
        
        return {
            'phase': phase,
            'confidence': confidence,
            'duration_days': np.random.randint(5, 30)
        }
    
    async def _analyze_market_sentiment(self) -> Dict:
        """市場情緒分析"""
        sentiment_score = np.random.normal(0, 0.3)  # 正態分布，均值0
        sentiment_score = max(-1, min(1, sentiment_score))
        
        fear_greed = int(50 + sentiment_score * 40)  # 轉換到0-100範圍
        fear_greed = max(0, min(100, fear_greed))
        
        return {
            'score': sentiment_score,
            'fear_greed': fear_greed,
            'components': {
                'price_momentum': np.random.uniform(-1, 1),
                'volume': np.random.uniform(-1, 1),
                'social_media': np.random.uniform(-1, 1),
                'surveys': np.random.uniform(-1, 1)
            }
        }
    
    async def _analyze_liquidity_condition(self) -> Dict:
        """流動性分析"""
        depth_score = np.random.uniform(0.5, 1.0)
        spread_score = np.random.uniform(0.6, 1.0)
        
        overall_score = (depth_score + spread_score) / 2
        
        if overall_score > 0.8:
            condition = "EXCELLENT"
        elif overall_score > 0.6:
            condition = "GOOD"
        elif overall_score > 0.4:
            condition = "FAIR"
        else:
            condition = "POOR"
        
        return {
            'condition': condition,
            'depth_score': depth_score,
            'spread_score': spread_score,
            'overall_score': overall_score
        }
    
    async def _analyze_external_factors(self) -> Dict:
        """外部因素分析"""
        potential_factors = [
            "美聯儲利率決議",
            "通脹數據發布", 
            "監管政策變動",
            "機構投資動向",
            "地緣政治風險",
            "技術發展消息",
            "交易所事件",
            "季度財報季"
        ]
        
        # 隨機選擇當前活躍的因素
        active_factors = np.random.choice(
            potential_factors, 
            size=np.random.randint(1, 4), 
            replace=False
        ).tolist()
        
        return {
            'factors': active_factors,
            'impact_scores': {factor: np.random.uniform(0.3, 0.9) for factor in active_factors}
        }
    
    async def _analyze_asset_correlations(self) -> Dict:
        """資產相關性分析"""
        return {
            'btc_eth': np.random.uniform(0.7, 0.95),
            'btc_stocks': np.random.uniform(0.3, 0.7),
            'eth_alt': np.random.uniform(0.8, 0.95),
            'crypto_gold': np.random.uniform(-0.2, 0.3)
        }
    
    def _synthesize_market_analysis(self, *analyses) -> Dict:
        """綜合所有分析結果"""
        trend_analysis, volatility_analysis, phase_analysis, sentiment_analysis, liquidity_analysis, external_analysis, correlation_analysis = analyses
        
        # 計算綜合信心度
        confidence_factors = [
            phase_analysis['confidence'],
            1 - (volatility_analysis['value'] / 100),  # 低波動 = 高信心
            (liquidity_analysis['overall_score']),
            0.8 if len(external_analysis['factors']) <= 2 else 0.5  # 外部因素少 = 高信心
        ]
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return {
            'trend': trend_analysis['overall_trend'],
            'confidence': overall_confidence,
            'risk_level': self._calculate_risk_level(volatility_analysis, external_analysis)
        }
    
    def _calculate_risk_level(self, volatility_analysis, external_analysis) -> str:
        """計算風險級別"""
        risk_score = 0
        
        # 波動性風險
        if volatility_analysis['level'] == 'LOW':
            risk_score += 1
        elif volatility_analysis['level'] == 'MEDIUM':
            risk_score += 2
        elif volatility_analysis['level'] == 'HIGH':
            risk_score += 3
        else:  # EXTREME
            risk_score += 4
        
        # 外部因素風險
        risk_score += len(external_analysis['factors'])
        
        if risk_score <= 3:
            return "LOW"
        elif risk_score <= 5:
            return "MEDIUM"
        elif risk_score <= 7:
            return "HIGH"
        else:
            return "EXTREME"
    
    # ========== 技術分析相關方法 ==========
    
    async def _multi_timeframe_analysis(self, symbols: List[str]) -> Dict:
        """多時間框架分析"""
        timeframes = ['15m', '1h', '4h', '1d']
        analysis = {}
        
        for tf in timeframes:
            analysis[tf] = {
                'trend': np.random.choice(['UP', 'DOWN', 'SIDEWAYS']),
                'strength': np.random.uniform(0.3, 0.9)
            }
        
        # 確定主導時間框架
        dominant = max(timeframes, key=lambda tf: analysis[tf]['strength'])
        
        return {
            'analysis': analysis,
            'dominant': dominant
        }
    
    async def _analyze_key_levels(self, symbols: List[str]) -> Dict:
        """關鍵位分析"""
        # 模擬支撐阻力位
        base_price = 50000.0  # BTC基準價
        
        support_levels = [
            base_price * 0.98,  # 2%支撐
            base_price * 0.95,  # 5%支撐  
            base_price * 0.90   # 10%強支撐
        ]
        
        resistance_levels = [
            base_price * 1.02,  # 2%阻力
            base_price * 1.05,  # 5%阻力
            base_price * 1.10   # 10%強阻力
        ]
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    async def _comprehensive_indicator_analysis(self, symbols: List[str]) -> Dict:
        """綜合指標分析"""
        indicators = {
            'rsi_14': np.random.uniform(20, 80),
            'rsi_21': np.random.uniform(25, 75),
            'macd_signal': np.random.choice(['BULL', 'BEAR', 'NEUTRAL']),
            'bb_position': np.random.uniform(0.2, 0.8),  # 布林帶位置
            'stoch_k': np.random.uniform(10, 90),
            'stoch_d': np.random.uniform(15, 85),
            'cci': np.random.uniform(-200, 200),
            'williams_r': np.random.uniform(-100, 0)
        }
        
        return {'values': indicators}
    
    async def _detect_chart_patterns(self, symbols: List[str]) -> Dict:
        """圖表型態識別"""
        patterns = ['雙頂', '雙底', '頭肩頂', '頭肩底', '三角整理', '楔形', '旗型', '矩形整理']
        detected = np.random.choice(patterns, size=np.random.randint(0, 3), replace=False).tolist()
        
        return {
            'patterns': detected,
            'breakout_prob': np.random.uniform(0.3, 0.8),
            'reversal_signals': ['RSI背離', '量價背離'] if np.random.random() > 0.7 else []
        }
    
    async def _analyze_market_momentum(self, symbols: List[str]) -> Dict:
        """市場動量分析"""
        return {
            'strength': np.random.uniform(0.3, 0.9),
            'direction': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
            'acceleration': np.random.uniform(-0.5, 0.5)
        }
    
    # ========== 基本面分析相關方法 ==========
    
    async def _analyze_macro_events(self) -> Dict:
        """宏觀事件分析"""
        events = [
            {'event': 'FOMC會議', 'date': '2026-01-20', 'impact': 'HIGH'},
            {'event': 'CPI數據', 'date': '2026-01-25', 'impact': 'MEDIUM'},
            {'event': 'GDP數據', 'date': '2026-01-30', 'impact': 'MEDIUM'}
        ]
        
        return {'events': events}
    
    async def _analyze_regulatory_climate(self) -> Dict:
        """監管環境分析"""
        climates = ['POSITIVE', 'NEUTRAL', 'NEGATIVE']
        return {'climate': np.random.choice(climates)}
    
    async def _analyze_adoption_trends(self) -> Dict:
        """採用趨勢分析"""
        trends = ['INCREASING', 'STABLE', 'DECLINING']
        return {'trend': np.random.choice(trends, p=[0.5, 0.4, 0.1])}
    
    async def _analyze_institutional_flows(self) -> Dict:
        """機構資金流向"""
        flows = ['INFLOW', 'NEUTRAL', 'OUTFLOW']
        return {'flow': np.random.choice(flows, p=[0.4, 0.4, 0.2])}
    
    async def _analyze_onchain_metrics(self) -> Dict:
        """鏈上數據分析"""
        metrics = {
            'active_addresses': np.random.randint(800000, 1200000),
            'transaction_volume': np.random.uniform(10, 50),  # 億美元
            'exchange_inflow': np.random.uniform(-20, 20),    # %變化
            'whale_activity': np.random.choice(['HIGH', 'MEDIUM', 'LOW'])
        }
        
        return {'metrics': metrics}
    
    async def _analyze_news_sentiment(self) -> Dict:
        """新聞情緒分析"""
        return {'score': np.random.uniform(-0.3, 0.3)}
    
    async def _analyze_social_sentiment(self) -> Dict:
        """社交媒體情緒分析"""
        return {'score': np.random.uniform(-0.5, 0.5)}
    
    # ========== 預設值方法 ==========
    
    def _get_default_market_condition(self) -> MarketCondition:
        """預設市場狀況"""
        return MarketCondition(
            timestamp=datetime.now(),
            overall_trend="NEUTRAL",
            volatility_level="MEDIUM",
            volatility_value=25.0,
            market_phase="ACCUMULATION",
            sentiment_score=0.0,
            fear_greed_index=50,
            liquidity_condition="GOOD",
            correlation_btc_eth=0.8,
            external_factors=["正常市場狀況"],
            confidence_score=0.5
        )
    
    def _get_default_technical_environment(self) -> TechnicalEnvironment:
        """預設技術環境"""
        return TechnicalEnvironment(
            timestamp=datetime.now(),
            dominant_timeframe="1h",
            support_levels=[49000, 47500, 45000],
            resistance_levels=[51000, 52500, 55000],
            key_indicators={'rsi_14': 50.0, 'macd_signal_value': 0.0},  # 只使用數值
            pattern_detected=[],
            breakout_probability=0.5,
            reversal_signals=[],
            momentum_strength=0.5
        )
    
    def _get_default_fundamental_environment(self) -> FundamentalEnvironment:
        """預設基本面環境"""
        return FundamentalEnvironment(
            timestamp=datetime.now(),
            macro_events=[],
            regulatory_climate="NEUTRAL",
            adoption_trends="STABLE",
            institutional_flow="NEUTRAL",
            on_chain_metrics={},
            news_sentiment=0.0,
            social_sentiment=0.0
        )
    
    def get_analysis_summary(self) -> Dict:
        """獲取分析摘要"""
        if not self.analysis_history:
            return {"message": "尚無分析數據"}
        
        latest = self.analysis_history[-1]
        return {
            "latest_analysis": {
                "trend": latest.overall_trend,
                "volatility": latest.volatility_level,
                "sentiment": latest.sentiment_score,
                "confidence": latest.confidence_score
            },
            "analysis_count": len(self.analysis_history)
        }