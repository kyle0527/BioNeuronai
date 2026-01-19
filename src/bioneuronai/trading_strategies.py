"""
三大經過驗證的加密貨幣交易策略
基於網路研究和技術分析最佳實踐
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import numpy as np
from collections import deque


@dataclass
class MarketData:
    """市場數據"""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    high: float
    low: float
    open: float
    close: float
    bid: float
    ask: float
    funding_rate: float = 0.0
    open_interest: float = 0.0


@dataclass
class TradingSignal:
    """交易信號"""
    action: str  # BUY, SELL, HOLD
    symbol: str
    confidence: float  # 0.0-1.0
    reason: str
    strategy_name: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: Optional[datetime] = None


class AITradingStrategy:
    """AI交易策略基類"""
    
    def __init__(self):
        self.name = "AI_Trading_Strategy"
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """分析市場並返回交易信號"""
        # 基礎實現，子類可以覆蓋
        return TradingSignal(
            action="HOLD",
            symbol=market_data.symbol,
            confidence=0.5,
            reason="默認AI策略分析",
            strategy_name=self.name
        )
    
    def get_strategy_report(self) -> Dict:
        """獲取策略報告"""
        return {
            "strategy_name": self.name,
            "status": "Active",
            "total_trades": 0
        }


class Strategy1_RSI_Divergence:
    """
    策略一：RSI 背離策略
    
    基於 Relative Strength Index (RSI) 指標的背離交易
    當價格創新高但 RSI 未能創新高時(熊背離),產生賣出信號
    當價格創新低但 RSI 未能創新低時(牛背離),產生買入信號
    
    優勢：
    - 捕捉趨勢反轉點
    - RSI 超買(>70)超賣(<30)區域有明確定義
    - 背離信號通常領先價格變化
    
    參數：
    - RSI 週期：14 (標準)
    - 超買線：70
    - 超賣線：30
    - 背離確認期：3-5 根 K 線
    """
    
    def __init__(self, rsi_period: int = 14, overbought: int = 70, oversold: int = 30):
        self.rsi_period = rsi_period
        self.overbought = overbought
        self.oversold = oversold
        self.price_history = deque(maxlen=100)
        self.rsi_history = deque(maxlen=100)
        
    def calculate_rsi(self, prices: List[float]) -> float:
        """
        計算 RSI 指標
        
        RSI = 100 - (100 / (1 + RS))
        RS = 平均上漲幅度 / 平均下跌幅度
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
        """
        檢測價格與 RSI 的背離
        
        返回: (信號類型, 置信度)
        """
        if len(self.price_history) < 20 or len(self.rsi_history) < 20:
            return "HOLD", 0.0
        
        prices = list(self.price_history)[-20:]
        rsi_values = list(self.rsi_history)[-20:]
        
        # 檢測牛背離 (Bullish Divergence)
        # 價格創新低,但 RSI 未創新低
        price_low_indices = []
        for i in range(2, len(prices) - 2):
            if prices[i] < prices[i-1] and prices[i] < prices[i-2] and \
               prices[i] < prices[i+1] and prices[i] < prices[i+2]:
                price_low_indices.append(i)
        
        if len(price_low_indices) >= 2:
            latest_price_low_idx = price_low_indices[-1]
            prev_price_low_idx = price_low_indices[-2]
            
            if prices[latest_price_low_idx] < prices[prev_price_low_idx]:  # 價格新低
                if rsi_values[latest_price_low_idx] > rsi_values[prev_price_low_idx]:  # RSI 未新低
                    # 牛背離確認
                    confidence = min(
                        (rsi_values[latest_price_low_idx] - rsi_values[prev_price_low_idx]) / 10,
                        0.95
                    )
                    if rsi_values[latest_price_low_idx] < self.oversold:
                        confidence += 0.1  # RSI 在超賣區加分
                    return "BUY", max(0.6, min(confidence, 1.0))
        
        # 檢測熊背離 (Bearish Divergence)
        # 價格創新高,但 RSI 未創新高
        price_high_indices = []
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i-2] and \
               prices[i] > prices[i+1] and prices[i] > prices[i+2]:
                price_high_indices.append(i)
        
        if len(price_high_indices) >= 2:
            latest_price_high_idx = price_high_indices[-1]
            prev_price_high_idx = price_high_indices[-2]
            
            if prices[latest_price_high_idx] > prices[prev_price_high_idx]:  # 價格新高
                if rsi_values[latest_price_high_idx] < rsi_values[prev_price_high_idx]:  # RSI 未新高
                    # 熊背離確認
                    confidence = min(
                        (rsi_values[prev_price_high_idx] - rsi_values[latest_price_high_idx]) / 10,
                        0.95
                    )
                    if rsi_values[latest_price_high_idx] > self.overbought:
                        confidence += 0.1  # RSI 在超買區加分
                    return "SELL", max(0.6, min(confidence, 1.0))
        
        return "HOLD", 0.0
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """分析市場並生成信號"""
        self.price_history.append(market_data.close)
        
        # 計算當前 RSI
        current_rsi = self.calculate_rsi(list(self.price_history))
        self.rsi_history.append(current_rsi)
        
        # 檢測背離
        signal_type, confidence = self.detect_divergence()
        
        # 基本 RSI 信號
        if signal_type == "HOLD":
            if current_rsi < self.oversold:
                signal_type = "BUY"
                confidence = 0.5 + (self.oversold - current_rsi) / 100
                reason = f"RSI 超賣 ({current_rsi:.2f})"
            elif current_rsi > self.overbought:
                signal_type = "SELL"
                confidence = 0.5 + (current_rsi - self.overbought) / 100
                reason = f"RSI 超買 ({current_rsi:.2f})"
            else:
                reason = f"RSI 中性 ({current_rsi:.2f})"
        else:
            if signal_type == "BUY":
                reason = f"牛背離 - RSI={current_rsi:.2f}"
            else:
                reason = f"熊背離 - RSI={current_rsi:.2f}"
        
        # 計算止損和止盈
        if signal_type == "BUY":
            stop_loss = market_data.close * 0.98  # 2% 止損
            take_profit = market_data.close * 1.04  # 4% 止盈
        elif signal_type == "SELL":
            stop_loss = market_data.close * 1.02
            take_profit = market_data.close * 0.96
        else:
            stop_loss = None
            take_profit = None
        
        return TradingSignal(
            action=signal_type,
            symbol=market_data.symbol,
            confidence=confidence,
            reason=f"[RSI背離策略] {reason}",
            strategy_name="RSI_Divergence",
            target_price=market_data.close,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now()
        )


class Strategy2_Bollinger_Bands_Breakout:
    """
    策略二：布林帶突破策略
    
    布林帶 (Bollinger Bands) 基於標準差構建上下軌道
    當價格突破上軌時,可能是強勢突破或超買反轉
    當價格跌破下軌時,可能是弱勢突破或超賣反轉
    
    優勢：
    - 自動適應市場波動性
    - 明確的超買/超賣區域
    - 結合成交量確認可提高準確度
    
    參數：
    - 中軌：20 期 SMA
    - 上軌：中軌 + 2倍標準差
    - 下軌：中軌 - 2倍標準差
    - 突破確認：收盤價突破且成交量放大
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
        self.price_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=100)
        
    def calculate_bollinger_bands(self, prices: List[float]) -> Tuple[float, float, float]:
        """
        計算布林帶
        
        返回: (上軌, 中軌, 下軌)
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
        """計算帶寬百分比"""
        if middle == 0:
            return 0
        return ((upper - lower) / middle) * 100
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """分析市場並生成信號"""
        self.price_history.append(market_data.close)
        self.volume_history.append(market_data.volume)
        
        if len(self.price_history) < self.period:
            return TradingSignal(
                action="HOLD",
                symbol=market_data.symbol,
                confidence=0.0,
                reason="[布林帶策略] 數據不足",
                strategy_name="Bollinger_Bands_Breakout",
                timestamp=datetime.now()
            )
        
        # 計算布林帶
        upper, middle, lower = self.calculate_bollinger_bands(list(self.price_history))
        bandwidth = self.calculate_bandwidth(upper, lower, middle)
        
        current_price = market_data.close
        prev_price = list(self.price_history)[-2] if len(self.price_history) >= 2 else current_price
        
        # 計算平均成交量
        avg_volume = np.mean(list(self.volume_history)[-10:]) if len(self.volume_history) >= 10 else market_data.volume
        volume_ratio = market_data.volume / avg_volume if avg_volume > 0 else 1.0
        
        signal_type = "HOLD"
        confidence = 0.0
        reason = ""
        
        # 價格位置百分比 (0=下軌, 50=中軌, 100=上軌)
        if upper != lower:
            price_position = ((current_price - lower) / (upper - lower)) * 100
        else:
            price_position = 50
        
        # 突破上軌 (可能做空或追多)
        if current_price > upper and prev_price <= upper:
            if volume_ratio > 1.5:  # 成交量確認
                # 強勢突破,追多
                signal_type = "BUY"
                confidence = min(0.65 + (volume_ratio - 1.5) * 0.1, 0.9)
                reason = f"突破上軌,成交量放大 {volume_ratio:.1f}x (帶寬={bandwidth:.2f}%)"
            else:
                # 可能超買,等待回調或做空
                signal_type = "SELL"
                confidence = 0.55
                reason = f"觸及上軌但成交量不足,可能回調 (帶寬={bandwidth:.2f}%)"
        
        # 突破下軌 (可能做多或追空)
        elif current_price < lower and prev_price >= lower:
            if volume_ratio > 1.5:  # 成交量確認
                # 恐慌性拋售,可能反彈
                signal_type = "BUY"
                confidence = min(0.65 + (volume_ratio - 1.5) * 0.1, 0.9)
                reason = f"跌破下軌,成交量放大 {volume_ratio:.1f}x,超賣反彈 (帶寬={bandwidth:.2f}%)"
            else:
                # 弱勢下跌
                signal_type = "SELL"
                confidence = 0.55
                reason = f"跌破下軌,可能繼續下跌 (帶寬={bandwidth:.2f}%)"
        
        # 布林帶收縮 (Squeeze) - 通常預示大行情
        elif bandwidth < 10:  # 帶寬小於 10%
            if price_position > 60:
                signal_type = "BUY"
                confidence = 0.6
                reason = f"布林帶收縮,價格偏上,可能向上突破 (帶寬={bandwidth:.2f}%)"
            elif price_position < 40:
                signal_type = "SELL"
                confidence = 0.6
                reason = f"布林帶收縮,價格偏下,可能向下突破 (帶寬={bandwidth:.2f}%)"
            else:
                reason = f"布林帶極度收縮,等待方向 (帶寬={bandwidth:.2f}%)"
        
        # 回歸中軌策略
        elif abs(price_position - 50) > 30:  # 偏離中軌超過 30%
            if price_position > 80:
                signal_type = "SELL"
                confidence = 0.55
                reason = f"遠離中軌,回歸交易 (位置={price_position:.1f}%)"
            elif price_position < 20:
                signal_type = "BUY"
                confidence = 0.55
                reason = f"遠離中軌,回歸交易 (位置={price_position:.1f}%)"
        
        if not reason:
            reason = f"價格在帶內 (位置={price_position:.1f}%, 帶寬={bandwidth:.2f}%)"
        
        # 計算止損和止盈
        if signal_type == "BUY":
            stop_loss = lower * 0.99  # 下軌下方 1%
            take_profit = upper * 1.01  # 上軌上方 1%
        elif signal_type == "SELL":
            stop_loss = upper * 1.01
            take_profit = lower * 0.99
        else:
            stop_loss = None
            take_profit = None
        
        return TradingSignal(
            action=signal_type,
            symbol=market_data.symbol,
            confidence=float(confidence),
            reason=f"[布林帶策略] {reason}",
            strategy_name="Bollinger_Bands_Breakout",
            target_price=market_data.close,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now()
        )


class Strategy3_MACD_Trend_Following:
    """
    策略三：MACD 趨勢跟隨策略
    
    MACD (Moving Average Convergence Divergence) 是趨勢跟隨指標
    由快線(12 EMA)、慢線(26 EMA)和信號線(9 EMA)組成
    
    優勢：
    - 同時捕捉趨勢和動量
    - 金叉/死叉信號明確
    - 柱狀圖顯示動量強弱
    
    信號：
    - 金叉 (MACD 上穿信號線) = 買入
    - 死叉 (MACD 下穿信號線) = 賣出
    - 零軸上方/下方 = 多頭/空頭市場
    - 柱狀圖擴張/收縮 = 動量增強/減弱
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.price_history = deque(maxlen=100)
        self.macd_history = deque(maxlen=50)
        self.signal_history = deque(maxlen=50)
        
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """計算指數移動平均線"""
        if len(prices) < period:
            return float(np.mean(prices))
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return float(ema)
    
    def calculate_macd(self, prices: List[float]) -> Tuple[float, float, float]:
        """
        計算 MACD 指標
        
        返回: (MACD 線, 信號線, 柱狀圖)
        """
        if len(prices) < self.slow_period:
            return 0, 0, 0
        
        fast_ema = self.calculate_ema(prices[-self.fast_period:], self.fast_period)
        slow_ema = self.calculate_ema(prices[-self.slow_period:], self.slow_period)
        
        macd_line = fast_ema - slow_ema
        
        # 計算信號線 (MACD 的 9 期 EMA)
        self.macd_history.append(macd_line)
        signal_line = self.calculate_ema(list(self.macd_history), self.signal_period)
        
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """分析市場並生成信號"""
        self.price_history.append(market_data.close)
        
        if len(self.price_history) < self.slow_period:
            return TradingSignal(
                action="HOLD",
                symbol=market_data.symbol,
                confidence=0.0,
                reason="[MACD策略] 數據不足",
                strategy_name="MACD_Trend_Following",
                timestamp=datetime.now()
            )
        
        # 計算 MACD
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
        
        signal_type = "HOLD"
        confidence = 0.0
        reason = ""
        
        # 檢測金叉 (買入信號)
        if macd_line > signal_line and prev_macd <= prev_signal:
            signal_type = "BUY"
            # 置信度取決於：
            # 1. 是否在零軸上方 (趨勢強)
            # 2. 柱狀圖是否擴張
            confidence = 0.65
            if macd_line > 0:
                confidence += 0.15  # 多頭市場加分
            if histogram > prev_histogram:
                confidence += 0.1  # 動量增強加分
            reason = f"金叉 - MACD 上穿信號線 (MACD={macd_line:.4f}, 信號={signal_line:.4f})"
        
        # 檢測死叉 (賣出信號)
        elif macd_line < signal_line and prev_macd >= prev_signal:
            signal_type = "SELL"
            confidence = 0.65
            if macd_line < 0:
                confidence += 0.15  # 空頭市場加分
            if histogram < prev_histogram:
                confidence += 0.1  # 動量增強加分
            reason = f"死叉 - MACD 下穿信號線 (MACD={macd_line:.4f}, 信號={signal_line:.4f})"
        
        # 動量加速/減速
        elif abs(histogram) > abs(prev_histogram) * 1.5:  # 柱狀圖快速擴張
            if histogram > 0:
                signal_type = "BUY"
                confidence = 0.6
                reason = f"多頭動量加速 (柱狀圖={histogram:.4f})"
            else:
                signal_type = "SELL"
                confidence = 0.6
                reason = f"空頭動量加速 (柱狀圖={histogram:.4f})"
        
        # 背離檢測
        elif histogram > 0 and histogram < prev_histogram * 0.5:  # 動量快速衰減
            signal_type = "SELL"
            confidence = 0.55
            reason = f"多頭動量衰減,可能反轉 (柱狀圖={histogram:.4f})"
        elif histogram < 0 and histogram > prev_histogram * 0.5:
            signal_type = "BUY"
            confidence = 0.55
            reason = f"空頭動量衰減,可能反轉 (柱狀圖={histogram:.4f})"
        
        if not reason:
            trend = "多頭" if macd_line > 0 else "空頭"
            momentum = "增強" if abs(histogram) > abs(prev_histogram) else "減弱"
            reason = f"{trend}趨勢,動量{momentum} (MACD={macd_line:.4f})"
        
        # 計算止損和止盈
        if signal_type == "BUY":
            stop_loss = market_data.close * 0.97  # 3% 止損
            take_profit = market_data.close * 1.06  # 6% 止盈 (2:1 風險回報)
        elif signal_type == "SELL":
            stop_loss = market_data.close * 1.03
            take_profit = market_data.close * 0.94
        else:
            stop_loss = None
            take_profit = None
        
        return TradingSignal(
            action=signal_type,
            symbol=market_data.symbol,
            confidence=confidence,
            reason=f"[MACD趨勢策略] {reason}",
            strategy_name="MACD_Trend_Following",
            target_price=market_data.close,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timestamp=datetime.now()
        )


class StrategyFusion:
    """
    策略融合系統
    
    AI 自主學習和融合多種策略,發展出自己的交易方式
    
    融合方法：
    1. 多數投票 (Majority Voting)
    2. 加權平均 (Weighted Average) - 根據歷史表現
    3. 動態權重調整 - 根據市場狀態
    4. 信號強度篩選 - 只採用高置信度信號
    """
    
    def __init__(self):
        self.strategy1 = Strategy1_RSI_Divergence()
        self.strategy2 = Strategy2_Bollinger_Bands_Breakout()
        self.strategy3 = Strategy3_MACD_Trend_Following()
        
        # 策略權重 (初始均等,會根據表現動態調整)
        self.weights = {
            "RSI_Divergence": 1.0,
            "Bollinger_Bands_Breakout": 1.0,
            "MACD_Trend_Following": 1.0
        }
        
        # 策略表現追蹤
        self.performance_history = {
            "RSI_Divergence": [],
            "Bollinger_Bands_Breakout": [],
            "MACD_Trend_Following": []
        }
        
        self.signal_history = []
    
    def update_strategy_performance(self, strategy_name: str, profit_loss: float):
        """
        更新策略表現
        
        Args:
            strategy_name: 策略名稱
            profit_loss: 盈虧百分比 (如 0.05 表示 5% 盈利)
        """
        self.performance_history[strategy_name].append(profit_loss)
        
        # 保留最近 100 筆記錄
        if len(self.performance_history[strategy_name]) > 100:
            self.performance_history[strategy_name].pop(0)
        
        # 動態調整權重
        self._adjust_weights()
    
    def _adjust_weights(self):
        """根據歷史表現動態調整策略權重"""
        for strategy_name in self.weights.keys():
            history = self.performance_history[strategy_name]
            
            if len(history) >= 10:  # 至少 10 筆交易才調整
                # 計算平均收益率
                avg_return = np.mean(history)
                # 計算勝率
                win_rate = sum(1 for x in history if x > 0) / len(history)
                # 計算夏普比率 (簡化版)
                returns_std = np.std(history) if np.std(history) > 0 else 0.01
                sharpe = avg_return / returns_std
                
                # 綜合評分
                score = (avg_return * 0.4) + (win_rate * 0.3) + (sharpe * 0.3)
                
                # 更新權重 (使用指數移動平均,避免劇烈變化)
                self.weights[strategy_name] = float((self.weights[strategy_name] * 0.7) + (max(score, 0.1) * 0.3))
        
        # 歸一化權重
        total_weight = sum(self.weights.values())
        if total_weight > 0:
            for key in self.weights:
                self.weights[key] = float(self.weights[key] / total_weight)
    
    def analyze(self, market_data: MarketData) -> TradingSignal:
        """
        融合多個策略的分析結果
        
        採用加權投票和置信度篩選
        """
        # 獲取三個策略的信號
        signal1 = self.strategy1.analyze(market_data)
        signal2 = self.strategy2.analyze(market_data)
        signal3 = self.strategy3.analyze(market_data)
        
        signals = [signal1, signal2, signal3]
        
        # 計算加權信號
        buy_score = 0.0
        sell_score = 0.0
        
        reasons = []
        
        for signal in signals:
            weight = self.weights[signal.strategy_name]
            weighted_confidence = signal.confidence * weight
            
            if signal.action == "BUY":
                buy_score += weighted_confidence
                reasons.append(f"✓ {signal.strategy_name}: 買入 ({signal.confidence:.2f})")
            elif signal.action == "SELL":
                sell_score += weighted_confidence
                reasons.append(f"✗ {signal.strategy_name}: 賣出 ({signal.confidence:.2f})")
            else:
                reasons.append(f"○ {signal.strategy_name}: 觀望")
        
        # 決策邏輯
        if buy_score > sell_score and buy_score > 0.5:
            final_action = "BUY"
            final_confidence = min(buy_score, 1.0)
        elif sell_score > buy_score and sell_score > 0.5:
            final_action = "SELL"
            final_confidence = min(sell_score, 1.0)
        else:
            final_action = "HOLD"
            final_confidence = 0.0
        
        # 計算融合後的止損止盈 (取平均)
        if final_action == "BUY":
            stop_losses = [s.stop_loss for s in signals if s.stop_loss and s.action == "BUY"]
            take_profits = [s.take_profit for s in signals if s.take_profit and s.action == "BUY"]
            stop_loss = np.mean(stop_losses) if stop_losses else market_data.close * 0.97
            take_profit = np.mean(take_profits) if take_profits else market_data.close * 1.06
        elif final_action == "SELL":
            stop_losses = [s.stop_loss for s in signals if s.stop_loss and s.action == "SELL"]
            take_profits = [s.take_profit for s in signals if s.take_profit and s.action == "SELL"]
            stop_loss = np.mean(stop_losses) if stop_losses else market_data.close * 1.03
            take_profit = np.mean(take_profits) if take_profits else market_data.close * 0.94
        else:
            stop_loss = None
            take_profit = None
        
        # 策略權重信息
        weight_info = " | ".join([f"{k.split('_')[0]}:{v:.2f}" for k, v in self.weights.items()])
        
        fusion_reason = f"[融合策略] 買入分數={buy_score:.2f}, 賣出分數={sell_score:.2f}\n"
        fusion_reason += f"策略權重: {weight_info}\n"
        fusion_reason += "\n".join(reasons)
        
        fused_signal = TradingSignal(
            action=final_action,
            symbol=market_data.symbol,
            confidence=final_confidence,
            reason=fusion_reason,
            strategy_name="AI_Strategy_Fusion",
            target_price=market_data.close,
            stop_loss=float(stop_loss) if stop_loss is not None else None,
            take_profit=float(take_profit) if take_profit is not None else None,
            timestamp=datetime.now()
        )
        
        self.signal_history.append({
            'signal': fused_signal,
            'individual_signals': signals,
            'weights': self.weights.copy()
        })
        
        return fused_signal
    
    def analyze_market(self, market_data: MarketData) -> TradingSignal:
        """分析市場 - analyze 方法的別名"""
        return self.analyze(market_data)
    
    def get_strategy_report(self) -> Dict:
        """獲取策略表現報告"""
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
