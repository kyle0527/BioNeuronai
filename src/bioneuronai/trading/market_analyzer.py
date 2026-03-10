"""
BioNeuronai - Market Analyzer

職責：市場分析（整合外部數據源）
更新：2026-02-15 - 添加 WebDataFetcher 整合
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

# 從 schemas 導入數據模型（遵循單一數據來源原則）
from schemas.external_data import ExternalDataSnapshot, MarketSentiment

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
    """
    市場分析器 - 整合外部數據源
    
    新增功能 (2026-02-15):
    - 整合 WebDataFetcher 抓取外部數據
    - 綜合市場情緒計算（恐慌貪婪指數 + 技術指標）
    - 宏觀市場掃描（全球市值、DeFi TVL、穩定幣供應）
    """
    
    def __init__(self):
        self.analysis_history = []
        self.indicator_weights = {
            "trend_strength": 0.25,
            "volatility": 0.20,
            "sentiment": 0.20,
            "liquidity": 0.15,
            "fundamentals": 0.20
        }
        
        # 外部數據緩存（避免過度調用 API）
        self.external_data_cache: Optional[ExternalDataSnapshot] = None
        self.cache_timestamp: Optional[datetime] = None
        self.cache_ttl_minutes = 15  # 快取 15 分鐘
    
    async def analyze_current_market_condition(self, klines: Optional[List[Dict]] = None) -> MarketCondition:
        """ - 基於 K線數據 """
        logger.info("正在分析市場條件 ...")
        
        # 異步讓步點（允許其他協程執行）
        await asyncio.sleep(0)
        
        try:
            # 1. 趨勢分析
            trend_analysis = self._analyze_market_trend(klines)
            logger.info(f"  ✓ 趨勢分析: {trend_analysis['overall_trend']} (強度: {trend_analysis['strength']:.2f})")
            
            # 2. 波動率分析
            volatility_analysis = self._analyze_volatility(klines)
            logger.info(f"  ✓ 波動率: {volatility_analysis['level']} ({volatility_analysis['value']:.1f}%)")
            
            # 3. 市場階段
            phase_analysis = self._identify_market_phase(klines)
            logger.info(f"  ✓ 市場階段: {phase_analysis['phase']} (信心: {phase_analysis['confidence']:.2f})")
            
            # 4. 情緒分析
            sentiment_analysis = self._analyze_market_sentiment(klines)
            logger.info(f"  ✓ 市場情緒: {sentiment_analysis['score']:.2f} | 恐慌貪婪: {sentiment_analysis['fear_greed']}")
            
            # 5. 流動性分析
            liquidity_analysis = self._analyze_liquidity_condition(klines)
            logger.info(f"  ✓ 流動性: {liquidity_analysis['condition']} (分數: {liquidity_analysis['depth_score']:.2f})")
            
            # 6. 外部因素
            external_analysis = self._analyze_external_factors(klines)
            logger.info(f"  ✓ 外部因素: {len(external_analysis['factors'])} 個警示")
            
            # 7. 相關性分析
            correlation_analysis = self._analyze_asset_correlations()
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
        _ = symbols  # 預留參數，未來用於多幣種分析
        logger.info(" ...")
        
        # 異步讓步點（允許其他協程執行）
        await asyncio.sleep(0)
        
        try:
            # 
            timeframe_analysis = self._multi_timeframe_analysis()
            
            # 
            levels_analysis = self._analyze_key_levels()
            
            # 
            indicators_analysis = self._comprehensive_indicator_analysis()
            
            # 
            pattern_analysis = self._detect_chart_patterns()
            
            #
            momentum_analysis = self._analyze_market_momentum()
            
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
        
        # 異步讓步點（允許其他協程執行）
        await asyncio.sleep(0)
        
        try:
            #
            macro_analysis = self._analyze_macro_events()
            
            # 
            regulatory_analysis = self._analyze_regulatory_climate()
            
            # 
            adoption_analysis = self._analyze_adoption_trends()
            
            #
            institutional_analysis = self._analyze_institutional_flows()
            
            # 
            onchain_analysis = self._analyze_onchain_metrics()
            
            # 
            news_sentiment = self._analyze_news_sentiment()
            
            # 
            social_sentiment = self._analyze_social_sentiment()
            
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
    
    def _analyze_market_trend(self, klines: Optional[List[Dict]] = None) -> Dict:
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
    
    def _analyze_volatility(self, klines: Optional[List[Dict]] = None) -> Dict:
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
    
    def _identify_market_phase(self, klines: Optional[List[Dict]] = None) -> Dict:
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
    
    def _analyze_market_sentiment(self, klines: Optional[List[Dict]] = None) -> Dict:
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
    
    def _analyze_liquidity_condition(self, klines: Optional[List[Dict]] = None) -> Dict:
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
    
    def _analyze_external_factors(self, klines: Optional[List[Dict]] = None) -> Dict:
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
    
    def _analyze_asset_correlations(self) -> Dict:
        """
        資產相關性分析
        
        返回預設相關性係數，未來可擴展為多幣種實時計算
        """
        # 預設相關性係數（基於歷史經驗值）
        return {
            'btc_eth': 0.85,  # 加密貨幣間通常高度相關
            'btc_stocks': 0.5,  # 中等相關
            'eth_alt': 0.9,  # 山寨幣與 ETH 高度相關
            'crypto_gold': 0.0  # 低相關或負相關
        }
    
    def _synthesize_market_analysis(self, *analyses) -> Dict:
        """"""
        trend_analysis, volatility_analysis, phase_analysis, _, liquidity_analysis, external_analysis, _ = analyses
        
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
    
    def _multi_timeframe_analysis(self) -> Dict:
        """多時間週期分析（保守中性預設值）"""
        timeframes = ['15m', '1h', '4h', '1d']
        analysis = {tf: {'trend': 'SIDEWAYS', 'strength': 0.5} for tf in timeframes}
        return {
            'analysis': analysis,
            'dominant': '1h'
        }
    
    def _analyze_key_levels(self) -> Dict:
        """關鍵價位分析（基於固定比例）"""
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
    
    def _comprehensive_indicator_analysis(self) -> Dict:
        """綜合指標分析（保守中性預設值）"""
        indicators = {
            'rsi_14': 50.0,
            'rsi_21': 50.0,
            'macd_signal': 'NEUTRAL',
            'bb_position': 0.5,
            'stoch_k': 50.0,
            'stoch_d': 50.0,
            'cci': 0.0,
            'williams_r': -50.0
        }
        return {'values': indicators}
    
    def _detect_chart_patterns(self) -> Dict:
        """圖表型態偵測（真實數據不足時回傳空結果）"""
        return {
            'patterns': [],
            'breakout_prob': 0.5,
            'reversal_signals': []
        }
    
    def _analyze_market_momentum(self) -> Dict:
        """市場動能分析（保守中性預設值）"""
        return {
            'strength': 0.5,
            'direction': 'NEUTRAL',
            'acceleration': 0.0
        }
    
    # ==========  ==========
    
    def _analyze_macro_events(self) -> Dict:
        """宏觀事件分析"""
        events = [
            {'event': 'FOMC', 'date': '2026-01-20', 'impact': 'HIGH'},
            {'event': 'CPI', 'date': '2026-01-25', 'impact': 'MEDIUM'},
            {'event': 'GDP', 'date': '2026-01-30', 'impact': 'MEDIUM'}
        ]
        
        return {'events': events}
    
    def _analyze_regulatory_climate(self) -> Dict:
        """監管環境分析（保守中性預設值）"""
        return {'climate': 'NEUTRAL'}
    
    def _analyze_adoption_trends(self) -> Dict:
        """採用趨勢分析（保守中性預設值）"""
        return {'trend': 'STABLE'}
    
    def _analyze_institutional_flows(self) -> Dict:
        """機構資金流分析（保守中性預設值）"""
        return {'flow': 'NEUTRAL'}
    
    def _analyze_onchain_metrics(self) -> Dict:
        """鏈上指標分析（保守中性預設值）"""
        metrics = {
            'active_addresses': 0,
            'transaction_volume': 0.0,
            'exchange_inflow': 0.0,
            'whale_activity': 'MEDIUM'
        }
        return {'metrics': metrics}
    
    def _analyze_news_sentiment(self) -> Dict:
        """新聞情緒分析（保守中性預設值）"""
        return {'score': 0.0}
    
    def _analyze_social_sentiment(self) -> Dict:
        """社交情緒分析（保守中性預設值）"""
        return {'score': 0.0}
    
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
    
    # ========== 外部數據整合（新增 2026-02-15）==========
    
    async def fetch_external_data(self, force_refresh: bool = False) -> Optional[ExternalDataSnapshot]:
        """
        抓取外部市場數據（帶緩存機制）
        
        Args:
            force_refresh: 強制刷新緩存
            
        Returns:
            ExternalDataSnapshot 或 None
        """
        # 檢查緩存
        if not force_refresh and self.external_data_cache and self.cache_timestamp:
            age_minutes = (datetime.now() - self.cache_timestamp).total_seconds() / 60
            if age_minutes < self.cache_ttl_minutes:
                logger.info(f"💾 使用緩存的外部數據（{age_minutes:.1f} 分鐘前）")
                return self.external_data_cache
        
        # 抓取新數據
        try:
            from bioneuronai.data.web_data_fetcher import WebDataFetcher
            
            async with WebDataFetcher() as fetcher:
                snapshot = await fetcher.fetch_all()
                
                # 更新緩存
                self.external_data_cache = snapshot
                self.cache_timestamp = datetime.now()
                
                return snapshot
        
        except Exception as e:
            logger.error(f"❌ 抓取外部數據失敗: {e}", exc_info=True)
            return self.external_data_cache  # 返回舊緩存（如果有）
    
    async def calculate_comprehensive_sentiment(
        self,
        klines: Optional[List[Dict]] = None,
        external_data: Optional[ExternalDataSnapshot] = None
    ) -> MarketSentiment:
        """
        計算綜合市場情緒（整合多個數據源）
        
        組成：
        1. 恐慌貪婪指數（Alternative.me）- 30%
        2. 技術指標情緒（RSI, 動能）- 30%
        3. 市場動量（成交量, 市值變化）- 25%
        4. 新聞情緒（如果有 RAG 數據）- 15%
        
        Args:
            klines: K線數據
            external_data: 外部數據快照
            
        Returns:
            MarketSentiment 對象
        """
        logger.info("🧠 計算綜合市場情緒...")
        
        # 異步讓步點（允許其他協程執行）
        await asyncio.sleep(0)
        
        components = {}
        sentiment_scores = []
        weights = []
        
        # 1. 恐慌貪婪指數 (如果有外部數據)
        if external_data and external_data.fear_greed:
            # 轉換 0-100 到 -1 到 +1
            fg_value = external_data.fear_greed.value
            fg_score = (fg_value - 50) / 50  # 標準化到 -1 到 1
            sentiment_scores.append(fg_score)
            weights.append(0.30)
            components["fear_greed_index"] = fg_value
            logger.info(f"  ✓ 恐慌貪婪: {fg_value} → {fg_score:+.3f}")
        
        # 2. 技術指標情緒
        if klines and len(klines) >= 14:
            tech_sentiment = self._analyze_market_sentiment(klines)
            sentiment_scores.append(tech_sentiment["score"])
            weights.append(0.30)
            components["rsi"] = tech_sentiment["components"]["rsi"]
            components["price_momentum"] = tech_sentiment["components"]["price_momentum"]
            logger.info(f"  ✓ 技術指標: {tech_sentiment['score']:+.3f}")
        
        # 3. 市場動量
        if external_data and external_data.global_market:
            gm = external_data.global_market
            
            # 市值變化 (-10% 到 +10% 映射到 -1 到 +1)
            mc_change = gm.market_cap_change_24h / 10  # 除以 10 進行壓縮
            mc_score = np.tanh(mc_change)  # 壓縮到 -1 到 1
            
            sentiment_scores.append(mc_score)
            weights.append(0.25)
            components["market_cap_change_24h"] = gm.market_cap_change_24h
            logger.info(f"  ✓ 市場動量: {gm.market_cap_change_24h:+.2f}% → {mc_score:+.3f}")
        
        # 4. 新聞情緒（預留介面，待 RAG 系統整合）
        # 未來可透過 bioneuronai.analysis.news.analyzer 提供新聞情緒分析
        
        # 計算加權平均
        if not sentiment_scores:
            logger.warning("⚠️ 無可用數據計算情緒，使用中性值")
            overall_sentiment = 0.0
            confidence = 0.1
        else:
            # 標準化權重
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            
            # 加權平均
            overall_sentiment = sum(s * w for s, w in zip(sentiment_scores, normalized_weights))
            confidence = min(total_weight / 0.85, 1.0)  # 最大權重總和為 0.85
            
            logger.info(f"  ✓ 綜合情緒: {overall_sentiment:+.3f} (信心: {confidence:.2f})")
        
        # 創建 MarketSentiment 對象
        market_sentiment = MarketSentiment(
            overall_sentiment=float(overall_sentiment),
            fear_greed_score=(sentiment_scores[0] if sentiment_scores else 0.0),
            news_sentiment=0.0,  # 待實現
            social_sentiment=None,
            market_momentum=(sentiment_scores[2] if len(sentiment_scores) > 2 else 0.0),
            confidence_level=float(confidence),
            timestamp=datetime.now(),
            components=components
        )
        
        return market_sentiment
    
    async def scan_macro_market(
        self,
        check_mode: str = "daily"
    ) -> Dict[str, Any]:
        """
        宏觀市場掃描（步驟 2 - 實現）
        
        數據來源：
        - Alternative.me (恐慌貪婪指數)
        - CoinGecko (全球市場數據)
        - DefiLlama (DeFi TVL)
        - CoinGecko (穩定幣供應)
        
        Args:
            check_mode: "daily" (每日) 或 "quick" (快速)
            
        Returns:
            包含所有宏觀指標的字典
        """
        logger.info("=" * 70)
        logger.info("🌍 步驟 2: 宏觀市場掃描")
        logger.info("=" * 70)
        
        # 抓取外部數據
        external_data = await self.fetch_external_data()
        
        if not external_data:
            logger.error("❌ 無法獲取外部數據")
            return {
                "status": "FAILED",
                "error": "無法連接到外部數據源"
            }
        
        result = {
            "status": "SUCCESS",
            "check_mode": check_mode,
            "timestamp": external_data.timestamp.isoformat(),
            "data_sources": [ds.value for ds in external_data.data_sources],
            "fetch_duration_ms": external_data.fetch_duration_ms
        }
        
        # 1. 恐慌貪婪指數
        if external_data.fear_greed:
            fg = external_data.fear_greed
            result["fear_greed_index"] = {
                "value": fg.value,
                "classification": fg.value_classification,
                "interpretation": self._interpret_fear_greed(fg.value)
            }
            logger.info(f"  ✓ 恐慌貪婪指數: {fg.value} ({fg.value_classification})")
        
        # 2. 全球市場數據
        if external_data.global_market:
            gm = external_data.global_market
            result["global_market"] = {
                "total_market_cap_usd": gm.total_market_cap,
                "total_volume_24h_usd": gm.total_volume_24h,
                "btc_dominance_pct": gm.btc_dominance,
                "eth_dominance_pct": gm.eth_dominance,
                "market_cap_change_24h_pct": gm.market_cap_change_24h
            }
            logger.info(f"  ✓ 全球市值: ${gm.total_market_cap/1e12:.2f}T ({gm.market_cap_change_24h:+.2f}%)")
            logger.info(f"  ✓ BTC 占比: {gm.btc_dominance:.1f}%")
        
        # 3. DeFi TVL
        if external_data.defi_metrics:
            defi = external_data.defi_metrics
            result["defi_tvl"] = {
                "total_tvl_usd": defi.total_tvl,
                "top_chains": defi.chains
            }
            logger.info(f"  ✓ DeFi TVL: ${defi.total_tvl/1e9:.1f}B")
        
        # 4. 穩定幣供應
        if external_data.stablecoin_metrics:
            sc = external_data.stablecoin_metrics
            result["stablecoin_supply"] = {
                "total_supply_usd": sc.total_supply,
                "by_token": sc.supply_by_token
            }
            logger.info(f"  ✓ 穩定幣供應: ${sc.total_supply/1e9:.1f}B")
        
        # 5. 市場狀態評估
        if external_data.fear_greed and external_data.global_market:
            market_state = self._assess_market_state(
                external_data.fear_greed.value,
                external_data.global_market.market_cap_change_24h,
                external_data.global_market.btc_dominance
            )
            result["market_state"] = market_state
            logger.info(f"  ✓ 市場狀態: {market_state['condition']} ({market_state['recommendation']})")
        
        # 6. 錯誤報告
        if external_data.errors:
            result["errors"] = external_data.errors
            logger.warning(f"  ⚠️ 部分數據源失敗: {len(external_data.errors)} 個")
        
        logger.info("=" * 70)
        return result
    
    def _interpret_fear_greed(self, value: int) -> str:
        """解釋恐慌貪婪指數"""
        if value <= 25:
            return "極度恐慌 - 可能是買入機會"
        elif value <= 45:
            return "恐慌 - 市場謹慎"
        elif value <= 55:
            return "中性 - 市場平衡"
        elif value <= 75:
            return "貪婪 - 注意風險"
        else:
            return "極度貪婪 - 考慮獲利了結"
    
    def _assess_market_state(
        self,
        fear_greed: int,
        market_cap_change: float,
        btc_dominance: float
    ) -> Dict[str, str]:
        """評估市場狀態"""
        # 綜合評估
        if fear_greed <= 30 and market_cap_change < -3:
            condition = "EXTREME_FEAR"
            recommendation = "強烈買入信號"
        elif fear_greed >= 75 and market_cap_change > 5:
            condition = "EXTREME_GREED"
            recommendation = "考慮減倉"
        elif 45 <= fear_greed <= 55:
            condition = "NEUTRAL"
            recommendation = "觀望或按計劃執行"
        elif market_cap_change > 3:
            condition = "BULLISH"
            recommendation = "趨勢跟隨策略"
        elif market_cap_change < -3:
            condition = "BEARISH"
            recommendation = "保守防守"
        else:
            condition = "MIXED"
            recommendation = "綜合策略"
        
        # BTC 占比分析
        if btc_dominance > 60:
            btc_note = "BTC 主導，山寨幣可能表現不佳"
        elif btc_dominance < 40:
            btc_note = "山寨季可能來臨"
        else:
            btc_note = "市場相對平衡"
        
        return {
            "condition": condition,
            "recommendation": recommendation,
            "btc_dominance_note": btc_note
        }