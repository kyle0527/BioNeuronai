"""


"""


from typing import List, Dict, Tuple, Optional
from datetime import datetime
import numpy as np
from collections import deque

# 遵循 CODE_FIX_GUIDE：schemas 為單一數據來源，此處僅 re-export 以維持向後兼容
from schemas.market import MarketData   # noqa: F401
from schemas.trading import TradingSignal  # noqa: F401
from schemas.enums import SignalType


class AITradingStrategy:
    """AI"""
    
    def __init__(self):
        self.name = "AI_Trading_Strategy"
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """"""
        # 
        return TradingSignal(
            signal_type=SignalType.HOLD,
            symbol=market_data.symbol,
            confidence=0.5,
            reason="AI",
            strategy_name=self.name
        )
    
    def get_strategy_report(self) -> Dict:
        """"""
        return {
            "strategy_name": self.name,
            "status": "Active",
            "total_trades": 0
        }


class Strategy1_RSI_Divergence:
    """
    RSI 
    
     Relative Strength Index (RSI) 
     RSI (),
     RSI (),
    
    
    - 
    - RSI (>70)(<30)
    - 
    
    
    - RSI 14 ()
    - 70
    - 30
    - 3-5  K 
    """
    
    def __init__(self, rsi_period: int = 14, overbought: int = 70, oversold: int = 30):
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.price_history = deque(maxlen=100)
        self.rsi_history = deque(maxlen=100)
        
    def calculate_rsi(self, prices: List[float]) -> float:
        """
         RSI 
        
        RSI = 100 - (100 / (1 + RS))
        RS =  / 
        """
        if len(prices) < self.rsi_period + 1:
            return 50.0
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-self.rsi_period:])
        avg_loss = np.mean(losses[-self.rsi_period:])
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    def detect_divergence(self) -> Tuple[str, float]:
        """檢測 RSI 背離信號 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離背離檢測邏輯
        """
        if len(self.price_history) < 20 or len(self.rsi_history) < 20:
            return "HOLD", 0.0
        
        prices = list(self.price_history)[-20:]
        rsi_values = list(self.rsi_history)[-20:]
        
        # 檢查看漲背離
        bullish_signal = self._check_bullish_divergence(prices, rsi_values)
        if bullish_signal[0] != "HOLD":
            return bullish_signal
        
        # 檢查看跌背離
        bearish_signal = self._check_bearish_divergence(prices, rsi_values)
        if bearish_signal[0] != "HOLD":
            return bearish_signal
        
        return "HOLD", 0.0
    
    def _check_bullish_divergence(self, prices: List[float], rsi_values: List[float]) -> Tuple[str, float]:
        """檢查看漲背離（價格下跌，RSI 上升）"""
        price_low_indices = self._find_price_lows(prices)
        
        if len(price_low_indices) < 2:
            return "HOLD", 0.0
        
        latest_idx = price_low_indices[-1]
        prev_idx = price_low_indices[-2]
        
        # 價格創新低，RSI 不創新低
        if (prices[latest_idx] < prices[prev_idx] and 
            rsi_values[latest_idx] > rsi_values[prev_idx]):
            
            confidence = self._calculate_bullish_confidence(
                rsi_values, latest_idx, prev_idx
            )
            return "BUY", confidence
        
        return "HOLD", 0.0
    
    def _check_bearish_divergence(self, prices: List[float], rsi_values: List[float]) -> Tuple[str, float]:
        """檢查看跌背離（價格上漲，RSI 下跌）"""
        price_high_indices = self._find_price_highs(prices)
        
        if len(price_high_indices) < 2:
            return "HOLD", 0.0
        
        latest_idx = price_high_indices[-1]
        prev_idx = price_high_indices[-2]
        
        # 價格創新高，RSI 不創新高
        if (prices[latest_idx] > prices[prev_idx] and
            rsi_values[latest_idx] < rsi_values[prev_idx]):
            
            confidence = self._calculate_bearish_confidence(
                rsi_values, latest_idx, prev_idx
            )
            return "SELL", confidence
        
        return "HOLD", 0.0
    
    def _find_price_lows(self, prices: List[float]) -> List[int]:
        """尋找價格低點索引"""
        indices = []
        for i in range(2, len(prices) - 2):
            if (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
                prices[i] < prices[i+1] and prices[i] < prices[i+2]):
                indices.append(i)
        return indices
    
    def _find_price_highs(self, prices: List[float]) -> List[int]:
        """尋找價格高點索引"""
        indices = []
        for i in range(2, len(prices) - 2):
            if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
                prices[i] > prices[i+1] and prices[i] > prices[i+2]):
                indices.append(i)
        return indices
    
    def _calculate_bullish_confidence(self, rsi_values: List[float], latest_idx: int, prev_idx: int) -> float:
        """計算看漲信號信心度"""
        confidence = min(
            (rsi_values[latest_idx] - rsi_values[prev_idx]) / 10,
            0.95
        )
        if rsi_values[latest_idx] < self.oversold:
            confidence += 0.1  # RSI 超賣加分
        return max(0.6, min(confidence, 1.0))
    
    def _calculate_bearish_confidence(self, rsi_values: List[float], latest_idx: int, prev_idx: int) -> float:
        """計算看跌信號信心度"""
        confidence = min(
            (rsi_values[prev_idx] - rsi_values[latest_idx]) / 10,
            0.95
        )
        if rsi_values[latest_idx] > self.overbought:
            confidence += 0.1  # RSI 超買加分
        return max(0.6, min(confidence, 1.0))
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """"""
        self.price_history.append(market_data.close)
        
        #  RSI
        current_rsi = self.calculate_rsi(list(self.price_history))
        self.rsi_history.append(current_rsi)
        
        # 
        signal_type, confidence = self.detect_divergence()
        
        #  RSI 
        if signal_type == "HOLD":
            if current_rsi < self.oversold:
                signal_type = "BUY"
                confidence = 0.5 + (self.oversold - current_rsi) / 100
                reason = f"RSI  ({current_rsi:.2f})"
            elif current_rsi > self.overbought:
                signal_type = "SELL"
                confidence = 0.5 + (current_rsi - self.overbought) / 100
                reason = f"RSI  ({current_rsi:.2f})"
            else:
                reason = f"RSI  ({current_rsi:.2f})"
        else:
            if signal_type == "BUY":
                reason = f" - RSI={current_rsi:.2f}"
            else:
                reason = f" - RSI={current_rsi:.2f}"
        
        # 
        if signal_type == "BUY":
            stop_loss = market_data.close * 0.98  # 2% 
            take_profit = market_data.close * 1.04  # 4% 
        elif signal_type == "SELL":
            stop_loss = market_data.close * 1.02
            take_profit = market_data.close * 0.96
        else:
            stop_loss = None
            take_profit = None
        
        return TradingSignal(
            signal_type=SignalType(signal_type.lower()),
            symbol=market_data.symbol,
            confidence=confidence,
            reason=f"[RSI] {reason}",
            strategy_name="RSI_Divergence",
            target_price=market_data.close,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now()
        )


class Strategy2_Bollinger_Bands_Breakout:
    """
    
    
     (Bollinger Bands) 
    ,
    ,
    
    
    - 
    - /
    - 
    
    
    - 20  SMA
    -  + 2
    -  - 2
    - 
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
        self.price_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=100)
        
    def calculate_bollinger_bands(self, prices: List[float]) -> Tuple[float, float, float]:
        """
        
        
        : (, , )
        """
        if len(prices) < self.period:
            return 0, 0, 0
        
        recent_prices = prices[-self.period:]
        middle_band = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        upper_band = middle_band + (self.std_dev * std)
        lower_band = middle_band - (self.std_dev * std)
        
        return float(upper_band), float(middle_band), float(lower_band)
    
    def calculate_bandwidth(self, upper: float, lower: float, middle: float) -> float:
        """"""
        if middle == 0:
            return 0
        return ((upper - lower) / middle) * 100
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """分析布林通道突破信號 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離信號分析邏輯
        """
        self.price_history.append(market_data.close)
        self.volume_history.append(market_data.volume)
        
        if len(self.price_history) < self.period:
            return self._create_hold_signal(market_data, "數據不足，等待更多數據")
        
        # 計算布林通道
        upper, middle, lower = self.calculate_bollinger_bands(list(self.price_history))
        bandwidth = self.calculate_bandwidth(upper, lower, middle)
        
        # 準備分析數據
        analysis_data = self._prepare_analysis_data(market_data, upper, middle, lower, bandwidth)
        
        # 分析信號
        signal_type, confidence, reason = self._analyze_bollinger_signals(analysis_data)
        
        # 計算停損止盈
        stop_loss, take_profit = self._calculate_risk_levels(
            signal_type, upper, lower
        )
        
        return TradingSignal(
            signal_type=SignalType(signal_type.lower()),
            symbol=market_data.symbol,
            confidence=float(confidence),
            reason=f"[布林通道] {reason}",
            strategy_name="Bollinger_Bands_Breakout",
            target_price=market_data.close,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now()
        )
    
    def _create_hold_signal(self, market_data: MarketData, reason: str) -> TradingSignal:
        """創建持有信號"""
        return TradingSignal(
            signal_type=SignalType.HOLD,
            symbol=market_data.symbol,
            confidence=0.0,
            reason=reason,
            strategy_name="Bollinger_Bands_Breakout",
            timestamp=datetime.now()
        )
    
    def _prepare_analysis_data(self, market_data: MarketData, upper: float, 
                              middle: float, lower: float, bandwidth: float) -> Dict:
        """準備分析所需數據"""
        current_price = market_data.close
        prev_price = list(self.price_history)[-2] if len(self.price_history) >= 2 else current_price
        
        # 計算價格相對位置
        if upper != lower:
            price_position = ((current_price - lower) / (upper - lower)) * 100
        else:
            price_position = 50
        
        # 計算成交量比率
        avg_volume = np.mean(list(self.volume_history)[-10:]) if len(self.volume_history) >= 10 else market_data.volume
        volume_ratio = market_data.volume / avg_volume if avg_volume > 0 else 1.0
        
        return {
            'current_price': current_price,
            'prev_price': prev_price,
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': bandwidth,
            'price_position': price_position,
            'volume_ratio': volume_ratio
        }
    
    def _analyze_bollinger_signals(self, data: Dict) -> Tuple[str, float, str]:
        """分析布林通道信號"""
        # 檢查上軌突破
        upper_breakout = self._check_upper_breakout(data)
        if upper_breakout[0] != "HOLD":
            return upper_breakout
        
        # 檢查下軌突破
        lower_breakout = self._check_lower_breakout(data)
        if lower_breakout[0] != "HOLD":
            return lower_breakout
        
        # 檢查壓縮狀態
        squeeze_signal = self._check_squeeze_state(data)
        if squeeze_signal[0] != "HOLD":
            return squeeze_signal
        
        # 檢查極端位置
        extreme_position = self._check_extreme_positions(data)
        if extreme_position[0] != "HOLD":
            return extreme_position
        
        # 默認持有
        return "HOLD", 0.0, f"中性狀態 (位置={data['price_position']:.1f}%, 帶寬={data['bandwidth']:.2f}%)"
    
    def _check_upper_breakout(self, data: Dict) -> Tuple[str, float, str]:
        """檢查上軌突破"""
        if data['current_price'] > data['upper'] and data['prev_price'] <= data['upper']:
            if data['volume_ratio'] > 1.5:
                confidence = min(0.65 + (data['volume_ratio'] - 1.5) * 0.1, 0.9)
                reason = f"上軌突破確認, 成交量放大{data['volume_ratio']:.1f}x (帶寬={data['bandwidth']:.2f}%)"
                return "BUY", confidence, reason
            else:
                reason = f"上軌假突破, 成交量不足 (帶寬={data['bandwidth']:.2f}%)"
                return "SELL", 0.55, reason
        return "HOLD", 0.0, ""
    
    def _check_lower_breakout(self, data: Dict) -> Tuple[str, float, str]:
        """檢查下軌突破"""
        if data['current_price'] < data['lower'] and data['prev_price'] >= data['lower']:
            if data['volume_ratio'] > 1.5:
                confidence = min(0.65 + (data['volume_ratio'] - 1.5) * 0.1, 0.9)
                reason = f"下軌突破確認, 成交量放大{data['volume_ratio']:.1f}x, 反彈信號 (帶寬={data['bandwidth']:.2f}%)"
                return "BUY", confidence, reason
            else:
                reason = f"下軌假突破, 成交量不足 (帶寬={data['bandwidth']:.2f}%)"
                return "SELL", 0.55, reason
        return "HOLD", 0.0, ""
    
    def _check_squeeze_state(self, data: Dict) -> Tuple[str, float, str]:
        """檢查壓縮狀態"""
        if data['bandwidth'] < 10:  # 帶寬小於10%
            if data['price_position'] > 60:
                reason = f"壓縮狀態,價格偏高, 準備突破 (帶寬={data['bandwidth']:.2f}%)"
                return "BUY", 0.6, reason
            elif data['price_position'] < 40:
                reason = f"壓縮狀態,價格偏低, 準備突破 (帶寬={data['bandwidth']:.2f}%)"
                return "SELL", 0.6, reason
            else:
                reason = f"壓縮狀態, 等待方向 (帶寬={data['bandwidth']:.2f}%)"
                return "HOLD", 0.0, reason
        return "HOLD", 0.0, ""
    
    def _check_extreme_positions(self, data: Dict) -> Tuple[str, float, str]:
        """檢查極端位置"""
        if abs(data['price_position'] - 50) > 30:  # 偏離中軸超過30%
            if data['price_position'] > 80:
                reason = f"價格過高, 回歸預期 (位置={data['price_position']:.1f}%)"
                return "SELL", 0.55, reason
            elif data['price_position'] < 20:
                reason = f"價格過低, 反彈預期 (位置={data['price_position']:.1f}%)"
                return "BUY", 0.55, reason
        return "HOLD", 0.0, ""
    
    def _calculate_risk_levels(self, signal_type: str, upper: float, lower: float) -> Tuple[Optional[float], Optional[float]]:
        """計算風險水準"""
        if signal_type == "BUY":
            stop_loss = lower * 0.99  # 下軌減1%
            take_profit = upper * 1.01  # 上軌加1%
        elif signal_type == "SELL":
            stop_loss = upper * 1.01
            take_profit = lower * 0.99
        else:
            stop_loss = None
            take_profit = None
        
        return stop_loss, take_profit


class Strategy3_MACD_Trend_Following:
    """
    MACD 
    
    MACD (Moving Average Convergence Divergence) 
    (12 EMA)(26 EMA)(9 EMA)
    
    
    - 
    - /
    - 
    
    
    -  (MACD ) = 
    -  (MACD ) = 
    - / = /
    - / = /
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.price_history = deque(maxlen=100)
        self.macd_history = deque(maxlen=50)
        self.signal_history = deque(maxlen=50)
        
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """"""
        if len(prices) < period:
            return float(np.mean(prices))
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return float(ema)
    
    def calculate_macd(self, prices: List[float]) -> Tuple[float, float, float]:
        """
         MACD 
        
        : (MACD , , )
        """
        if len(prices) < self.slow_period:
            return 0, 0, 0
        
        fast_ema = self.calculate_ema(prices[-self.fast_period:], self.fast_period)
        slow_ema = self.calculate_ema(prices[-self.slow_period:], self.slow_period)
        
        macd_line = fast_ema - slow_ema
        
        #  (MACD  9  EMA)
        self.macd_history.append(macd_line)
        signal_line = self.calculate_ema(list(self.macd_history), self.signal_period)
        
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """分析MACD趨勢跟隨信號 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離信號分析邏輯
        """
        self.price_history.append(market_data.close)
        
        if len(self.price_history) < self.slow_period:
            return self._create_hold_signal_macd(market_data, "數據不足，等待更多數據")
        
        # 計算MACD指標
        macd_data = self._calculate_macd_indicators()
        
        # 分析信號
        signal_type, confidence, reason = self._analyze_macd_signals(macd_data)
        
        # 計算風險水準
        stop_loss, take_profit = self._calculate_macd_risk_levels(
            market_data.close, signal_type
        )
        
        return TradingSignal(
            signal_type=SignalType(signal_type.lower()),
            symbol=market_data.symbol,
            confidence=confidence,
            reason=f"[MACD趨勢] {reason}",
            strategy_name="MACD_Trend_Following",
            target_price=market_data.close,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now()
        )
    
    def _create_hold_signal_macd(self, market_data: MarketData, reason: str) -> TradingSignal:
        """創建MACD持有信號"""
        return TradingSignal(
            signal_type=SignalType.HOLD,
            symbol=market_data.symbol,
            confidence=0.0,
            reason=f"[MACD趨勢] {reason}",
            strategy_name="MACD_Trend_Following",
            timestamp=datetime.now()
        )
    
    def _calculate_macd_indicators(self) -> Dict:
        """計算MACD指標數據"""
        macd_line, signal_line, histogram = self.calculate_macd(list(self.price_history))
        self.signal_history.append(signal_line)
        
        # 獲取前一期數據
        if len(self.macd_history) >= 2 and len(self.signal_history) >= 2:
            prev_macd = list(self.macd_history)[-2]
            prev_signal = list(self.signal_history)[-2]
            prev_histogram = prev_macd - prev_signal
        else:
            prev_macd = macd_line
            prev_signal = signal_line
            prev_histogram = histogram
        
        return {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram,
            'prev_macd': prev_macd,
            'prev_signal': prev_signal,
            'prev_histogram': prev_histogram
        }
    
    def _analyze_macd_signals(self, data: Dict) -> Tuple[str, float, str]:
        """分析MACD信號"""
        # 檢查黃金交叉
        golden_cross = self._check_golden_cross(data)
        if golden_cross[0] != "HOLD":
            return golden_cross
        
        # 檢查死亡交叉
        death_cross = self._check_death_cross(data)
        if death_cross[0] != "HOLD":
            return death_cross
        
        # 檢查柱狀圖動量
        histogram_momentum = self._check_histogram_momentum(data)
        if histogram_momentum[0] != "HOLD":
            return histogram_momentum
        
        # 檢查動量衰竭
        momentum_exhaustion = self._check_momentum_exhaustion(data)
        if momentum_exhaustion[0] != "HOLD":
            return momentum_exhaustion
        
        # 默認信號
        return self._get_default_macd_signal(data)
    
    def _check_golden_cross(self, data: Dict) -> Tuple[str, float, str]:
        """檢查黃金交叉（看漲）"""
        if (data['macd_line'] > data['signal_line'] and 
            data['prev_macd'] <= data['prev_signal']):
            
            confidence = 0.65
            if data['macd_line'] > 0:
                confidence += 0.15  # 零軸上方
            if data['histogram'] > data['prev_histogram']:
                confidence += 0.1  # 柱狀圖擴大
            
            reason = f"黃金交叉 - MACD線上穿信號線 (MACD={data['macd_line']:.4f}, 信號={data['signal_line']:.4f})"
            return "BUY", confidence, reason
        
        return "HOLD", 0.0, ""
    
    def _check_death_cross(self, data: Dict) -> Tuple[str, float, str]:
        """檢查死亡交叉（看跌）"""
        if (data['macd_line'] < data['signal_line'] and 
            data['prev_macd'] >= data['prev_signal']):
            
            confidence = 0.65
            if data['macd_line'] < 0:
                confidence += 0.15  # 零軸下方
            if data['histogram'] < data['prev_histogram']:
                confidence += 0.1  # 柱狀圖擴大
            
            reason = f"死亡交叉 - MACD線下穿信號線 (MACD={data['macd_line']:.4f}, 信號={data['signal_line']:.4f})"
            return "SELL", confidence, reason
        
        return "HOLD", 0.0, ""
    
    def _check_histogram_momentum(self, data: Dict) -> Tuple[str, float, str]:
        """檢查柱狀圖動量加速"""
        if abs(data['histogram']) > abs(data['prev_histogram']) * 1.5:  # 動量加速
            if data['histogram'] > 0:
                reason = f"多頭動量加速 (柱狀圖={data['histogram']:.4f})"
                return "BUY", 0.6, reason
            else:
                reason = f"空頭動量加速 (柱狀圖={data['histogram']:.4f})"
                return "SELL", 0.6, reason
        
        return "HOLD", 0.0, ""
    
    def _check_momentum_exhaustion(self, data: Dict) -> Tuple[str, float, str]:
        """檢查動量衰竭信號"""
        if data['histogram'] > 0 and data['histogram'] < data['prev_histogram'] * 0.5:  # 多頭衰竭
            reason = f"多頭動量衰竭, 反轉信號 (柱狀圖={data['histogram']:.4f})"
            return "SELL", 0.55, reason
        elif data['histogram'] < 0 and data['histogram'] > data['prev_histogram'] * 0.5:  # 空頭衰竭
            reason = f"空頭動量衰竭, 反轉信號 (柱狀圖={data['histogram']:.4f})"
            return "BUY", 0.55, reason
        
        return "HOLD", 0.0, ""
    
    def _get_default_macd_signal(self, data: Dict) -> Tuple[str, float, str]:
        """獲取默認MACD信號"""
        trend = "多頭趨勢" if data['macd_line'] > 0 else "空頭趨勢"
        momentum = "動量增強" if abs(data['histogram']) > abs(data['prev_histogram']) else "動量減弱"
        reason = f"{trend},{momentum} (MACD={data['macd_line']:.4f})"
        return "HOLD", 0.0, reason
    
    def _calculate_macd_risk_levels(self, current_price: float, signal_type: str) -> Tuple[Optional[float], Optional[float]]:
        """計算MACD策略風險水準"""
        if signal_type == "BUY":
            stop_loss = current_price * 0.97  # 3% 停損
            take_profit = current_price * 1.06  # 6% 止盈 (2:1 風報比)
        elif signal_type == "SELL":
            stop_loss = current_price * 1.03
            take_profit = current_price * 0.94
        else:
            stop_loss = None
            take_profit = None
        
        return stop_loss, take_profit


class StrategyFusion:
    """
    
    
    AI ,
    
    
    1.  (Majority Voting)
    2.  (Weighted Average) - 
    3.  - 
    4.  - 
    """
    
    def __init__(self):
        self.strategy1 = Strategy1_RSI_Divergence()
        self.strategy2 = Strategy2_Bollinger_Bands_Breakout()
        self.strategy3 = Strategy3_MACD_Trend_Following()
        
        #  (,)
        self.weights = {
            "RSI_Divergence": 1.0,
            "Bollinger_Bands_Breakout": 1.0,
            "MACD_Trend_Following": 1.0
        }
        
        # 
        self.performance_history = {
            "RSI_Divergence": [],
            "Bollinger_Bands_Breakout": [],
            "MACD_Trend_Following": []
        }
        
        self.signal_history = []
    
    def update_strategy_performance(self, strategy_name: str, profit_loss: float):
        """
        
        
        Args:
            strategy_name: 
            profit_loss:  ( 0.05  5% )
        """
        self.performance_history[strategy_name].append(profit_loss)
        
        #  100 
        if len(self.performance_history[strategy_name]) > 100:
            self.performance_history[strategy_name].pop(0)
        
        # 
        self._adjust_weights()
    
    def _adjust_weights(self):
        """"""
        for strategy_name in self.weights.keys():
            history = self.performance_history[strategy_name]
            
            if len(history) >= 10:  #  10 
                # 
                avg_return = np.mean(history)
                # 
                win_rate = sum(1 for x in history if x > 0) / len(history)
                #  ()
                returns_std = np.std(history) if np.std(history) > 0 else 0.01
                sharpe = avg_return / returns_std
                
                # 
                score = (avg_return * 0.4) + (win_rate * 0.3) + (sharpe * 0.3)
                
                #  (,)
                self.weights[strategy_name] = float((self.weights[strategy_name] * 0.7) + (max(score, 0.1) * 0.3))
        
        # 
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for key in self.weights:
                self.weights[key] = float(self.weights[key] / total_weight)
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """策略融合分析 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離各分析階段
        
        主要功能：
        1. 收集各策略信號
        2. 加權評分計算
        3. 最終決策生成
        4. 風險參數設定
        """
        # 收集個別策略信號 (Extract Method)
        individual_signals = self._collect_individual_signals(market_data)
        
        # 計算加權評分 (Extract Method)
        buy_score, sell_score, reasons = self._calculate_weighted_scores(individual_signals)
        
        # 生成最終決策 (Extract Method)
        final_action, final_confidence = self._determine_final_action(buy_score, sell_score)
        
        # 計算風險參數 (Extract Method)
        stop_loss, take_profit = self._calculate_risk_parameters(
            final_action, individual_signals, market_data
        )
        
        # 構建融合信號 (Extract Method)
        return self._build_fused_signal(
            final_action, final_confidence, stop_loss, take_profit,
            buy_score, sell_score, reasons, market_data, individual_signals
        )
    
    def _collect_individual_signals(self, market_data: MarketData) -> List[TradingSignal]:
        """收集個別策略信號"""
        return [
            self.strategy1.analyze(market_data),
            self.strategy2.analyze(market_data),
            self.strategy3.analyze(market_data)
        ]
    
    def _calculate_weighted_scores(self, signals: List[TradingSignal]) -> Tuple[float, float, List[str]]:
        """計算加權評分"""
        buy_score = 0.0
        sell_score = 0.0
        reasons = []
        
        for signal in signals:
            weight = self.weights[signal.strategy_name]
            weighted_confidence = signal.confidence * weight
            
            if signal.action == "BUY":
                buy_score += weighted_confidence
                reasons.append(f" {signal.strategy_name}:  ({signal.confidence:.2f})")
            elif signal.action == "SELL":
                sell_score += weighted_confidence
                reasons.append(f" {signal.strategy_name}:  ({signal.confidence:.2f})")
            else:
                reasons.append(f" {signal.strategy_name}: ")
        
        return buy_score, sell_score, reasons
    
    def _determine_final_action(self, buy_score: float, sell_score: float) -> Tuple[str, float]:
        """確定最終行動和置信度"""
        if buy_score > sell_score and buy_score > 0.5:
            return "BUY", min(buy_score, 1.0)
        elif sell_score > buy_score and sell_score > 0.5:
            return "SELL", min(sell_score, 1.0)
        else:
            return "HOLD", 0.0
    
    def _calculate_risk_parameters(
        self, 
        action: str, 
        signals: List[TradingSignal], 
        market_data: MarketData
    ) -> Tuple[Optional[float], Optional[float]]:
        """計算風險參數"""
        if action == "BUY":
            return self._calculate_buy_risk_params(signals, market_data)
        elif action == "SELL":
            return self._calculate_sell_risk_params(signals, market_data)
        else:
            return None, None
    
    def _calculate_buy_risk_params(
        self, signals: List[TradingSignal], market_data: MarketData
    ) -> Tuple[float, float]:
        """計算買入風險參數"""
        stop_losses = [s.stop_loss for s in signals if s.stop_loss and s.action == "BUY"]
        take_profits = [s.take_profit for s in signals if s.take_profit and s.action == "BUY"]
        
        stop_loss = float(np.mean(stop_losses)) if stop_losses else market_data.close * 0.97
        take_profit = float(np.mean(take_profits)) if take_profits else market_data.close * 1.06
        
        return stop_loss, take_profit
    
    def _calculate_sell_risk_params(
        self, signals: List[TradingSignal], market_data: MarketData
    ) -> Tuple[float, float]:
        """計算賣出風險參數"""
        stop_losses = [s.stop_loss for s in signals if s.stop_loss and s.action == "SELL"]
        take_profits = [s.take_profit for s in signals if s.take_profit and s.action == "SELL"]
        
        stop_loss = float(np.mean(stop_losses)) if stop_losses else market_data.close * 1.03
        take_profit = float(np.mean(take_profits)) if take_profits else market_data.close * 0.94
        
        return stop_loss, take_profit
    
    def _build_fused_signal(
        self,
        final_action: str,
        final_confidence: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        buy_score: float,
        sell_score: float,
        reasons: List[str],
        market_data: MarketData,
        individual_signals: List[TradingSignal]
    ) -> TradingSignal:
        """構建融合信號"""
        # 權重信息
        weight_info = " | ".join([f"{k.split('_')[0]}:{v:.2f}" for k, v in self.weights.items()])
        
        # 融合原因
        fusion_reason = f"[] ={buy_score:.2f}, ={sell_score:.2f}\n"
        fusion_reason += f": {weight_info}\n"
        fusion_reason += "\n".join(reasons)
        
        # 創建融合信號
        fused_signal = TradingSignal(
            signal_type=SignalType(final_action.lower()),
            symbol=market_data.symbol,
            confidence=final_confidence,
            reason=fusion_reason,
            strategy_name="AI_Strategy_Fusion",
            target_price=market_data.close,
            stop_loss=float(stop_loss) if stop_loss is not None else None,
            take_profit=float(take_profit) if take_profit is not None else None,
            timestamp=datetime.now()
        )
        
        # 記錄歷史
        self.signal_history.append({
            'signal': fused_signal,
            'individual_signals': individual_signals,
            'weights': self.weights.copy()
        })
        
        return fused_signal
    
    def analyze_market(self, market_data: MarketData) -> TradingSignal:
        """ - analyze """
        return self.analyze(market_data)
    
    def get_strategy_report(self) -> Dict:
        """"""
        report = {}
        
        for strategy_name, history in self.performance_history.items():
            if len(history) > 0:
                total_return = sum(history)
                avg_return = np.mean(history)
                win_rate = sum(1 for x in history if x > 0) / len(history) * 100
                best_trade = max(history)
                worst_trade = min(history)
                
                report[strategy_name] = {
                    'total_trades': len(history),
                    'total_return': f"{total_return:.2%}",
                    'avg_return': f"{avg_return:.2%}",
                    'win_rate': f"{win_rate:.1f}%",
                    'best_trade': f"{best_trade:.2%}",
                    'worst_trade': f"{worst_trade:.2%}",
                    'current_weight': f"{self.weights[strategy_name]:.3f}"
                }
            else:
                report[strategy_name] = {
                    'total_trades': 0,
                    'status': 'No trades yet',
                    'current_weight': f"{self.weights[strategy_name]:.3f}"
                }
        
        return report
