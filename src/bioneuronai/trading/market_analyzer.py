"""
 - Market Analyzer

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
    """"""
    timestamp: datetime
    overall_trend: str  # BULLISH, BEARISH, NEUTRAL, VOLATILE
    volatility_level: str  # LOW, MEDIUM, HIGH, EXTREME
    volatility_value: float
    market_phase: str  # ACCUMULATION, MARKUP, DISTRIBUTION, DECLINE
    sentiment_score: float  # -1.0  1.0
    fear_greed_index: int  # 0-100
    liquidity_condition: str  # EXCELLENT, GOOD, FAIR, POOR
    correlation_btc_eth: float
    external_factors: List[str]
    confidence_score: float  # 0-1

@dataclass
class TechnicalEnvironment:
    """"""
    timestamp: datetime
    dominant_timeframe: str  # 
    support_levels: List[float]
    resistance_levels: List[float]
    key_indicators: Dict[str, float]
    pattern_detected: List[str]
    breakout_probability: float
    reversal_signals: List[str]
    momentum_strength: float

@dataclass
class FundamentalEnvironment:
    """"""
    timestamp: datetime
    macro_events: List[Dict]
    regulatory_climate: str  # POSITIVE, NEUTRAL, NEGATIVE
    adoption_trends: str  # INCREASING, STABLE, DECLINING
    institutional_flow: str  # INFLOW, NEUTRAL, OUTFLOW
    on_chain_metrics: Dict[str, float]
    news_sentiment: float
    social_sentiment: float

class MarketAnalyzer:
    """ - """
    
    def __init__(self):
        self.analysis_history = []
        self.indicator_weights = {
            "trend_strength": 0.25,
            "volatility": 0.20,
            "sentiment": 0.20,
            "liquidity": 0.15,
            "fundamentals": 0.20
        }
    
    async def analyze_current_market_condition(self, klines: Optional[List[Dict]] = None) -> MarketCondition:
        """ - 基於 K線數據 """
        logger.info("正在分析市場條件 ...")
        
        try:
            # 1. 趨勢分析
            trend_analysis = await self._analyze_market_trend(klines)
            logger.info(f"  ✓ 趨勢分析: {trend_analysis['overall_trend']} (強度: {trend_analysis['strength']:.2f})")
            
            # 2. 波動率分析
            volatility_analysis = await self._analyze_volatility(klines)
            logger.info(f"  ✓ 波動率: {volatility_analysis['level']} ({volatility_analysis['value']:.1f}%)")
            
            # 3. 市場階段
            phase_analysis = await self._identify_market_phase(klines)
            logger.info(f"  ✓ 市場階段: {phase_analysis['phase']} (信心: {phase_analysis['confidence']:.2f})")
            
            # 4. 情緒分析
            sentiment_analysis = await self._analyze_market_sentiment(klines)
            logger.info(f"  ✓ 市場情緒: {sentiment_analysis['score']:.2f} | 恐慌貪婪: {sentiment_analysis['fear_greed']}")
            
            # 5. 流動性分析
            liquidity_analysis = await self._analyze_liquidity_condition(klines)
            logger.info(f"  ✓ 流動性: {liquidity_analysis['condition']} (分數: {liquidity_analysis['depth_score']:.2f})")
            
            # 6. 外部因素
            external_analysis = await self._analyze_external_factors(klines)
            logger.info(f"  ✓ 外部因素: {len(external_analysis['factors'])} 個警示")
            
            # 7. 相關性分析
            correlation_analysis = await self._analyze_asset_correlations(klines)
            logger.info(f"  ✓ 資產相關性 BTC-ETH: {correlation_analysis['btc_eth']:.3f}")
            
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
            logger.error(f": {e}")
            return self._get_default_market_condition()
    
    async def analyze_technical_environment(self, symbols: List[str]) -> TechnicalEnvironment:
        """"""
        logger.info(" ...")
        
        try:
            # 
            timeframe_analysis = await self._multi_timeframe_analysis(symbols)
            
            # 
            levels_analysis = await self._analyze_key_levels(symbols)
            
            # 
            indicators_analysis = await self._comprehensive_indicator_analysis(symbols)
            
            # 
            pattern_analysis = await self._detect_chart_patterns(symbols)
            
            # 
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
            logger.error(f": {e}")
            return self._get_default_technical_environment()
    
    async def analyze_fundamental_environment(self) -> FundamentalEnvironment:
        """"""
        logger.info(" ...")
        
        try:
            # 
            macro_analysis = await self._analyze_macro_events()
            
            # 
            regulatory_analysis = await self._analyze_regulatory_climate()
            
            # 
            adoption_analysis = await self._analyze_adoption_trends()
            
            # 
            institutional_analysis = await self._analyze_institutional_flows()
            
            # 
            onchain_analysis = await self._analyze_onchain_metrics()
            
            # 
            news_sentiment = await self._analyze_news_sentiment()
            
            # 
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
            logger.error(f": {e}")
            return self._get_default_fundamental_environment()
    
    # ==========  ==========
    
    async def _analyze_market_trend(self, klines: Optional[List[Dict]] = None) -> Dict:
        """基於真實 K線數據分析趨勢"""
        if not klines or len(klines) < 50:
            logger.warning("K線數據不足，使用保守評估")
            return {
                'timeframe_trends': {},
                'overall_trend': 'NEUTRAL',
                'strength': 0.3
            }
        
        # 計算多個週期的 EMA
        closes = np.array([float(k.get('close', k.get('c', 0))) for k in klines])
        
        # 短期 vs 長期趨勢
        ema_fast = self._calculate_ema(closes, 12)
        ema_slow = self._calculate_ema(closes, 26)
        ema_long = self._calculate_ema(closes, 50) if len(closes) >= 50 else ema_slow
        
        # 判斷趨勢方向
        trend_score = 0
        if ema_fast > ema_slow:
            trend_score += 1
        else:
            trend_score -= 1
            
        if ema_slow > ema_long:
            trend_score += 1
        else:
            trend_score -= 1
        
        # 價格相對於 EMA 的位置
        current_price = closes[-1]
        if current_price > ema_fast:
            trend_score += 1
        else:
            trend_score -= 1
        
        # 判斷總體趨勢
        if trend_score >= 2:
            overall = 'BULLISH'
        elif trend_score <= -2:
            overall = 'BEARISH'
        else:
            overall = 'NEUTRAL'
        
        # 趨勢強度（0-1）
        strength = abs(trend_score) / 3.0
        
        return {
            'timeframe_trends': {
                'ema_12': ema_fast,
                'ema_26': ema_slow,
                'ema_50': ema_long
            },
            'overall_trend': overall,
            'strength': strength
        }
    
    async def _analyze_volatility(self, klines: Optional[List[Dict]] = None) -> Dict:
        """基於真實數據計算波動率"""
        if not klines or len(klines) < 20:
            return {
                'value': 20.0,
                'level': 'MEDIUM',
                'percentile_30d': 50.0
            }
        
        # 計算歷史波動率（年化）
        closes = np.array([float(k.get('close', k.get('c', 0))) for k in klines])
        returns = np.diff(closes) / closes[:-1]
        
        # 標準差 * sqrt(365) 年化
        volatility = np.std(returns) * np.sqrt(365) * 100  # 轉為百分比
        
        # ATR 作為補充
        highs = np.array([float(k.get('high', k.get('h', 0))) for k in klines])
        lows = np.array([float(k.get('low', k.get('l', 0))) for k in klines])
        atr = self._calculate_atr(highs, lows, closes, period=14)
        atr_pct = (atr / closes[-1]) * 100 if closes[-1] > 0 else 0
        
        # 綜合評估
        vix_value = (volatility + atr_pct * 10) / 2  # 混合指標
        
        if vix_value < 15:
            level = "LOW"
        elif vix_value < 30:
            level = "MEDIUM"
        elif vix_value < 50:
            level = "HIGH"
        else:
            level = "EXTREME"
        
        return {
            'value': float(vix_value),
            'level': level,
            'atr_pct': float(atr_pct),
            'percentile_30d': 50.0  # 需要更多歷史數據才能計算
        }
    
    async def _identify_market_phase(self, klines: Optional[List[Dict]] = None) -> Dict:
        """基於成交量和價格關係判斷市場階段"""
        if not klines or len(klines) < 30:
            return {
                'phase': 'NEUTRAL',
                'confidence': 0.5,
                'duration_days': 0
            }
        
        closes = np.array([float(k.get('close', k.get('c', 0))) for k in klines[-30:]])
        volumes = np.array([float(k.get('volume', k.get('v', 0))) for k in klines[-30:]])
        
        # 價格趨勢
        price_change = (closes[-1] - closes[0]) / closes[0]
        
        # 成交量趨勢
        vol_recent = np.mean(volumes[-10:])
        vol_before = np.mean(volumes[-30:-10])
        vol_change = (vol_recent - vol_before) / vol_before if vol_before > 0 else 0
        
        # Wyckoff 分析
        if price_change < 0.01 and price_change > -0.01:  # 橫盤
            if vol_change < -0.1:  # 量縮
                phase = 'ACCUMULATION'
                confidence = 0.7
            elif vol_change > 0.1:  # 量增
                phase = 'DISTRIBUTION'
                confidence = 0.7
            else:
                phase = 'NEUTRAL'
                confidence = 0.6
        elif price_change > 0.05:  # 上漲
            if vol_change > 0:
                phase = 'MARKUP'
                confidence = 0.8
            else:
                phase = 'DISTRIBUTION'  # 價漲量縮，可能見頂
                confidence = 0.65
        else:  # 下跌
            phase = 'DECLINE'
            confidence = 0.75
        
        return {
            'phase': phase,
            'confidence': confidence,
            'price_change_pct': price_change * 100,
            'volume_change_pct': vol_change * 100
        }
    
    async def _analyze_market_sentiment(self, klines: Optional[List[Dict]] = None) -> Dict:
        """基於價格和成交量動能評估市場情緒"""
        if not klines or len(klines) < 14:
            return {
                'score': 0.0,
                'fear_greed': 50,
                'components': {}
            }
        
        closes = np.array([float(k.get('close', k.get('c', 0))) for k in klines])
        volumes = np.array([float(k.get('volume', k.get('v', 0))) for k in klines])
        
        # 計算 RSI（超買超賣指標）
        rsi = self._calculate_rsi(closes, 14)
        rsi_sentiment = (rsi - 50) / 50  # 轉為 -1 到 1
        
        # 價格動能
        price_momentum = (closes[-1] - closes[-7]) / closes[-7] if len(closes) >= 7 else 0
        momentum_sentiment = np.tanh(price_momentum * 10)  # 壓縮到 -1 到 1
        
        # 成交量趨勢
        vol_avg = np.mean(volumes)
        vol_recent = volumes[-1]
        volume_sentiment = np.tanh((vol_recent - vol_avg) / vol_avg) if vol_avg > 0 else 0
        
        # 綜合情緒分數
        sentiment_score = (rsi_sentiment * 0.4 + momentum_sentiment * 0.4 + volume_sentiment * 0.2)
        sentiment_score = max(-1, min(1, sentiment_score))
        
        # 轉為恐慌貪婪指數 (0-100)
        fear_greed = int(50 + sentiment_score * 50)
        fear_greed = max(0, min(100, fear_greed))
        
        return {
            'score': float(sentiment_score),
            'fear_greed': fear_greed,
            'components': {
                'rsi': float(rsi),
                'price_momentum': float(momentum_sentiment),
                'volume': float(volume_sentiment)
            }
        }
    
    async def _analyze_liquidity_condition(self, klines: Optional[List[Dict]] = None) -> Dict:
        """基於成交量評估流動性"""
        if not klines or len(klines) < 10:
            return {
                'condition': 'FAIR',
                'depth_score': 0.6,
                'spread_score': 0.6,
                'overall_score': 0.6
            }
        
        volumes = np.array([float(k.get('volume', k.get('v', 0))) for k in klines[-30:]])
        
        # 成交量穩定性（變異係數）
        vol_mean = np.mean(volumes)
        vol_std = np.std(volumes)
        cv = vol_std / vol_mean if vol_mean > 0 else 1.0
        
        # 變異係數越小越好（0-1，反轉）
        depth_score = max(0, min(1, 1 - cv))
        
        # 近期成交量相對水平
        recent_vol = np.mean(volumes[-5:])
        volume_ratio = recent_vol / vol_mean if vol_mean > 0 else 1.0
        spread_score = min(1.0, volume_ratio)  # 越高越好，但上限1
        
        overall_score = (depth_score * 0.6 + spread_score * 0.4)
        
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
            'depth_score': float(depth_score),
            'spread_score': float(spread_score),
            'overall_score': float(overall_score)
        }
    
    async def _analyze_external_factors(self, klines: Optional[List[Dict]] = None) -> Dict:
        """基於波動率判斷可能存在的外部因素"""
        if not klines or len(klines) < 20:
            return {
                'factors': [],
                'impact_scores': {}
            }
        
        closes = np.array([float(k.get('close', k.get('c', 0))) for k in klines])
        returns = np.diff(closes) / closes[:-1]
        
        # 檢測異常波動
        recent_volatility = np.std(returns[-10:])
        normal_volatility = np.std(returns[:-10]) if len(returns) > 10 else recent_volatility
        
        factors = []
        impact_scores = {}
        
        # 波動率突然增加 > 50%
        if recent_volatility > normal_volatility * 1.5:
            factors.append("市場波動加劇")
            impact_scores["市場波動加劇"] = 0.7
        
        # 檢測大幅單日變動
        max_return = np.max(np.abs(returns[-5:])) if len(returns) >= 5 else 0
        if max_return > 0.05:  # 5% 以上單日變動
            factors.append("重大價格變動")
            impact_scores["重大價格變動"] = 0.8
        
        return {
            'factors': factors,
            'impact_scores': impact_scores
        }
    
    async def _analyze_asset_correlations(self, klines: Optional[List[Dict]] = None) -> Dict:
        """暫時返回默認相關性，需要多幣種數據才能計算"""
        # TODO: 當有多個交易對的數據時，計算真實相關性
        return {
            'btc_eth': 0.85,  # 加密貨幣間通常高度相關
            'btc_stocks': 0.5,  # 中等相關
            'eth_alt': 0.9,  # 山寨幣與 ETH 高度相關
            'crypto_gold': 0.0  # 低相關或負相關
        }
    
    def _synthesize_market_analysis(self, *analyses) -> Dict:
        """"""
        trend_analysis, volatility_analysis, phase_analysis, sentiment_analysis, liquidity_analysis, external_analysis, correlation_analysis = analyses
        
        # 
        confidence_factors = [
            phase_analysis['confidence'],
            1 - (volatility_analysis['value'] / 100),  #  = 
            (liquidity_analysis['overall_score']),
            0.8 if len(external_analysis['factors']) <= 2 else 0.5  #  = 
        ]
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        
        return {
            'trend': trend_analysis['overall_trend'],
            'confidence': overall_confidence,
            'risk_level': self._calculate_risk_level(volatility_analysis, external_analysis)
        }
    
    def _calculate_risk_level(self, volatility_analysis, external_analysis) -> str:
        """"""
        risk_score = 0
        
        # 
        if volatility_analysis['level'] == 'LOW':
            risk_score += 1
        elif volatility_analysis['level'] == 'MEDIUM':
            risk_score += 2
        elif volatility_analysis['level'] == 'HIGH':
            risk_score += 3
        else:  # EXTREME
            risk_score += 4
        
        # 
        risk_score += len(external_analysis['factors'])
        
        if risk_score <= 3:
            return "LOW"
        elif risk_score <= 5:
            return "MEDIUM"
        elif risk_score <= 7:
            return "HIGH"
        else:
            return "EXTREME"
    
    # ==========  ==========
    
    async def _multi_timeframe_analysis(self, symbols: List[str]) -> Dict:
        """"""
        timeframes = ['15m', '1h', '4h', '1d']
        analysis = {}
        
        for tf in timeframes:
            analysis[tf] = {
                'trend': np.random.choice(['UP', 'DOWN', 'SIDEWAYS']),
                'strength': np.random.uniform(0.3, 0.9)
            }
        
        # 
        dominant = max(timeframes, key=lambda tf: analysis[tf]['strength'])
        
        return {
            'analysis': analysis,
            'dominant': dominant
        }
    
    async def _analyze_key_levels(self, symbols: List[str]) -> Dict:
        """"""
        # 
        base_price = 50000.0  # BTC
        
        support_levels = [
            base_price * 0.98,  # 2%
            base_price * 0.95,  # 5%  
            base_price * 0.90   # 10%
        ]
        
        resistance_levels = [
            base_price * 1.02,  # 2%
            base_price * 1.05,  # 5%
            base_price * 1.10   # 10%
        ]
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    async def _comprehensive_indicator_analysis(self, symbols: List[str]) -> Dict:
        """"""
        indicators = {
            'rsi_14': np.random.uniform(20, 80),
            'rsi_21': np.random.uniform(25, 75),
            'macd_signal': np.random.choice(['BULL', 'BEAR', 'NEUTRAL']),
            'bb_position': np.random.uniform(0.2, 0.8),  # 
            'stoch_k': np.random.uniform(10, 90),
            'stoch_d': np.random.uniform(15, 85),
            'cci': np.random.uniform(-200, 200),
            'williams_r': np.random.uniform(-100, 0)
        }
        
        return {'values': indicators}
    
    async def _detect_chart_patterns(self, symbols: List[str]) -> Dict:
        """"""
        patterns = ['', '', '', '', '', '', '', '']
        detected = np.random.choice(patterns, size=np.random.randint(0, 3), replace=False).tolist()
        
        return {
            'patterns': detected,
            'breakout_prob': np.random.uniform(0.3, 0.8),
            'reversal_signals': ['RSI', ''] if np.random.random() > 0.7 else []
        }
    
    async def _analyze_market_momentum(self, symbols: List[str]) -> Dict:
        """"""
        return {
            'strength': np.random.uniform(0.3, 0.9),
            'direction': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
            'acceleration': np.random.uniform(-0.5, 0.5)
        }
    
    # ==========  ==========
    
    async def _analyze_macro_events(self) -> Dict:
        """"""
        events = [
            {'event': 'FOMC', 'date': '2026-01-20', 'impact': 'HIGH'},
            {'event': 'CPI', 'date': '2026-01-25', 'impact': 'MEDIUM'},
            {'event': 'GDP', 'date': '2026-01-30', 'impact': 'MEDIUM'}
        ]
        
        return {'events': events}
    
    async def _analyze_regulatory_climate(self) -> Dict:
        """"""
        climates = ['POSITIVE', 'NEUTRAL', 'NEGATIVE']
        return {'climate': np.random.choice(climates)}
    
    async def _analyze_adoption_trends(self) -> Dict:
        """"""
        trends = ['INCREASING', 'STABLE', 'DECLINING']
        return {'trend': np.random.choice(trends, p=[0.5, 0.4, 0.1])}
    
    async def _analyze_institutional_flows(self) -> Dict:
        """"""
        flows = ['INFLOW', 'NEUTRAL', 'OUTFLOW']
        return {'flow': np.random.choice(flows, p=[0.4, 0.4, 0.2])}
    
    async def _analyze_onchain_metrics(self) -> Dict:
        """"""
        metrics = {
            'active_addresses': np.random.randint(800000, 1200000),
            'transaction_volume': np.random.uniform(10, 50),  # 
            'exchange_inflow': np.random.uniform(-20, 20),    # %
            'whale_activity': np.random.choice(['HIGH', 'MEDIUM', 'LOW'])
        }
        
        return {'metrics': metrics}
    
    async def _analyze_news_sentiment(self) -> Dict:
        """"""
        return {'score': np.random.uniform(-0.3, 0.3)}
    
    async def _analyze_social_sentiment(self) -> Dict:
        """"""
        return {'score': np.random.uniform(-0.5, 0.5)}
    
    # ==========  ==========
    
    def _get_default_market_condition(self) -> MarketCondition:
        """"""
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
            external_factors=[""],
            confidence_score=0.5
        )
    
    def _get_default_technical_environment(self) -> TechnicalEnvironment:
        """"""
        return TechnicalEnvironment(
            timestamp=datetime.now(),
            dominant_timeframe="1h",
            support_levels=[49000, 47500, 45000],
            resistance_levels=[51000, 52500, 55000],
            key_indicators={'rsi_14': 50.0, 'macd_signal_value': 0.0},  # 
            pattern_detected=[],
            breakout_probability=0.5,
            reversal_signals=[],
            momentum_strength=0.5
        )
    
    def _get_default_fundamental_environment(self) -> FundamentalEnvironment:
        """"""
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
        """"""
        if not self.analysis_history:
            return {"message": ""}
        
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
    
    # ========== 技術指標計算方法 ==========
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """計算 RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """計算 EMA"""
        if len(prices) < period:
            return prices[-1] if len(prices) > 0 else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[-period]
        
        for price in prices[-period+1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def _calculate_atr(
        self, 
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int = 14
    ) -> float:
        """計算 ATR"""
        if len(highs) < period + 1:
            return 0.0
        
        tr_list = []
        for i in range(-period, 0):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_list.append(tr)
        
        return float(np.mean(tr_list))