"""特徵工程模組 (Feature Engineering Module)
================================================

提供進階市場數據處理與特徵提取功能，用於 AI 交易模型和技術分析。

主要功能：

1. 成交量分布分析 (Volume Profile)
   - 識別關鍵價格區間與成交量集中點 (POC)
   - 計算價值區域 (Value Area) 與支撐/阻力位
   - 支援多時間週期分析

2. 清算熱力圖 (Liquidation Heatmap)
   - 預測潛在清算集中區域
   - 識別高槓桿部位風險區
   - 提供多空力量對比分析

3. 市場數據處理器 (Market Data Processor)
   - 原始K線數據轉換為交易特徵
   - 技術指標批量計算
   - 數據標準化與特徵工程

4. 流動性地圖 (Liquidity Map)
   - 訂單簿深度分析
   - 支撐/阻力位識別
   - 大額訂單追蹤

應用場景：
- AI 模型輸入特徵生成
- LLM 市場分析數據準備
- 交易策略技術指標計算
- 風險管理參數優化

Author: BioNeuronai Team
Version: 1.0
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# 
# ============================================================================

class PriceLevel(Enum):
    """"""
    POC = "poc"                    #  (Point of Control)
    VALUE_AREA_HIGH = "vah"        # 
    VALUE_AREA_LOW = "val"         # 
    HIGH_VOLUME_NODE = "hvn"       # 
    LOW_VOLUME_NODE = "lvn"        # 
    LIQUIDATION_CLUSTER = "liq"   # 


@dataclass
class VolumeProfileLevel:
    """"""
    price: float
    volume: float
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    trade_count: int = 0
    
    @property
    def delta(self) -> float:
        """"""
        return self.buy_volume - self.sell_volume
    
    @property
    def delta_percentage(self) -> float:
        """"""
        if self.volume == 0:
            return 0.0
        return self.delta / self.volume * 100


@dataclass
class VolumeProfile:
    """"""
    symbol: str
    start_time: datetime
    end_time: datetime
    price_levels: List[VolumeProfileLevel]
    tick_size: float = 1.0
    
    # 
    poc_price: float = 0.0              # 
    poc_volume: float = 0.0             # 
    value_area_high: float = 0.0        # 
    value_area_low: float = 0.0         # 
    high_volume_nodes: List[float] = field(default_factory=list)
    low_volume_nodes: List[float] = field(default_factory=list)
    
    def to_prompt(self) -> str:
        """ LLM """
        return (
            f" {self.symbol}\n"
            f": {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}\n"
            f" (POC): {self.poc_price:.2f} ()\n"
            f": {self.value_area_low:.2f} - {self.value_area_high:.2f}\n"
            f" (): {', '.join([f'{p:.2f}' for p in self.high_volume_nodes[:3]])}\n"
            f" (): {', '.join([f'{p:.2f}' for p in self.low_volume_nodes[:3]])}"
        )


@dataclass
class LiquidationCluster:
    """"""
    price: float
    estimated_liquidation_value: float  #  (USDT)
    side: str  # 'long'  'short'
    leverage_range: Tuple[int, int] = (10, 50)  # 
    confidence: float = 0.5  # 
    
    def to_prompt(self) -> str:
        """ LLM """
        side_text = "" if self.side == "long" else ""
        return (
            f"{self.price:.2f}: {side_text} "
            f"( ${self.estimated_liquidation_value/1e6:.1f}M, "
            f" {self.leverage_range[0]}-{self.leverage_range[1]}x)"
        )


@dataclass
class LiquidationHeatmap:
    """"""
    symbol: str
    current_price: float
    long_clusters: List[LiquidationCluster]   #  ()
    short_clusters: List[LiquidationCluster]  #  ()
    
    # 
    total_long_liquidation_risk: float = 0.0
    total_short_liquidation_risk: float = 0.0
    nearest_long_cluster_distance: float = 0.0
    nearest_short_cluster_distance: float = 0.0
    
    def to_prompt(self) -> str:
        """ LLM """
        lines = [f" {self.symbol}", f": {self.current_price:.2f}"]
        
        if self.long_clusters:
            lines.append(f"\n  ():")
            for cluster in self.long_clusters[:3]:
                lines.append(f"  - {cluster.to_prompt()}")
        
        if self.short_clusters:
            lines.append(f"\n  ():")
            for cluster in self.short_clusters[:3]:
                lines.append(f"  - {cluster.to_prompt()}")
        
        lines.append(f"\n:")
        lines.append(f"  : ${self.total_long_liquidation_risk/1e6:.1f}M")
        lines.append(f"  : ${self.total_short_liquidation_risk/1e6:.1f}M")
        
        return "\n".join(lines)


@dataclass
class MarketMicrostructure:
    """"""
    symbol: str
    timestamp: datetime
    
    # 
    price: float
    price_change_1m: float = 0.0
    price_change_5m: float = 0.0
    price_change_15m: float = 0.0
    price_change_1h: float = 0.0
    
    # 
    volume_1m: float = 0.0
    volume_5m: float = 0.0
    volume_1h: float = 0.0
    volume_ratio: float = 1.0  # 
    
    # 
    bid_ask_spread: float = 0.0
    bid_depth: float = 0.0
    ask_depth: float = 0.0
    order_book_imbalance: float = 0.0
    
    # 
    long_liquidation_1h: float = 0.0
    short_liquidation_1h: float = 0.0
    net_liquidation: float = 0.0
    
    # 
    open_interest: float = 0.0
    oi_change_1h: float = 0.0
    oi_change_24h: float = 0.0
    
    # 
    funding_rate: float = 0.0
    predicted_funding_rate: float = 0.0
    hours_to_funding: float = 0.0
    
    # 
    long_short_ratio: float = 1.0
    taker_buy_sell_ratio: float = 1.0
    
    def to_prompt(self) -> str:
        """ LLM """
        # 
        funding_warning = ""
        if abs(self.funding_rate) > 0.01:
            side = "" if self.funding_rate > 0 else ""
            funding_warning = f"  ({self.funding_rate*100:.3f}%){side}"
        
        liq_warning = ""
        if self.net_liquidation > 1e6:
            liq_warning = f" 1 ${self.long_liquidation_1h/1e6:.1f}M"
        elif self.net_liquidation < -1e6:
            liq_warning = f" 1 ${self.short_liquidation_1h/1e6:.1f}M"
        
        oi_trend = ""
        if self.oi_change_1h > 5:
            oi_trend = "OI  ()"
        elif self.oi_change_1h < -5:
            oi_trend = "OI  ()"
        
        lines = [
            f" {self.symbol}",
            f": {self.price:.2f}",
            f": 1m {self.price_change_1m:+.2f}% | 5m {self.price_change_5m:+.2f}% | 1h {self.price_change_1h:+.2f}%",
            f": {self.volume_ratio:.2f}x ()",
            f": {self.bid_ask_spread:.4f}%",
            f": {self.order_book_imbalance:+.2f} ({'' if self.order_book_imbalance > 0 else ''})",
            f": {self.open_interest/1e6:.1f}M ({self.oi_change_1h:+.2f}% 1h) {oi_trend}",
            f": {self.funding_rate*100:.4f}% (: {self.predicted_funding_rate*100:.4f}%)",
            f": {self.long_short_ratio:.2f}",
        ]
        
        if funding_warning:
            lines.append(funding_warning)
        if liq_warning:
            lines.append(liq_warning)
        
        return "\n".join(lines)
    
    def to_feature_vector(self) -> List[float]:
        """ ( AI )"""
        return [
            self.price_change_1m / 10,  # 
            self.price_change_5m / 10,
            self.price_change_15m / 10,
            self.price_change_1h / 10,
            np.tanh(self.volume_ratio - 1),  # -1  1
            self.bid_ask_spread * 100,
            self.order_book_imbalance,
            np.tanh(self.oi_change_1h / 10),
            np.tanh(self.oi_change_24h / 20),
            self.funding_rate * 100,
            self.predicted_funding_rate * 100,
            np.tanh((self.long_liquidation_1h - self.short_liquidation_1h) / 1e7),
            np.tanh(self.long_short_ratio - 1),
            np.tanh(self.taker_buy_sell_ratio - 1),
        ]


# ============================================================================
#  (Volume Profile Calculator)
# ============================================================================

class VolumeProfileCalculator:
    """
    
     POC/
    """
    
    def __init__(self, tick_size: float = 10.0, value_area_percent: float = 0.70):
        """
        Args:
            tick_size: 
            value_area_percent:  ( 70%)
        """
        self.tick_size = tick_size
        self.value_area_percent = value_area_percent
    
    def calculate_from_klines(
        self, 
        klines: List[Any],  # List[KlineData]
        use_tpo: bool = False
    ) -> VolumeProfile:
        """K
        
        Args:
            klines: K
            use_tpo:  TPO (Time Price Opportunity) 
        """
        if not klines:
            return VolumeProfile(
                symbol="",
                start_time=datetime.now(),
                end_time=datetime.now(),
                price_levels=[]
            )
        
        symbol = klines[0].symbol
        start_time = datetime.fromtimestamp(klines[0].open_time / 1000)
        end_time = datetime.fromtimestamp(klines[-1].close_time / 1000)
        
        # 
        volume_by_price = defaultdict(lambda: {"volume": 0, "buy": 0, "sell": 0, "count": 0})
        
        for kline in klines:
            # K
            price_low = self._round_to_tick(kline.low)
            price_high = self._round_to_tick(kline.high)
            
            # 
            price_range = price_high - price_low
            if price_range == 0:
                price_range = self.tick_size
            
            current_price = price_low
            while current_price <= price_high:
                # 
                level_count = max(1, int(price_range / self.tick_size))
                level_volume = kline.volume / level_count
                level_buy = kline.taker_buy_volume / level_count
                level_sell = (kline.volume - kline.taker_buy_volume) / level_count
                
                volume_by_price[current_price]["volume"] += level_volume
                volume_by_price[current_price]["buy"] += level_buy
                volume_by_price[current_price]["sell"] += level_sell
                volume_by_price[current_price]["count"] += 1
                
                current_price += self.tick_size
        
        # 
        price_levels = []
        for price, data in sorted(volume_by_price.items()):
            price_levels.append(VolumeProfileLevel(
                price=price,
                volume=data["volume"],
                buy_volume=data["buy"],
                sell_volume=data["sell"],
                trade_count=data["count"]
            ))
        
        # 
        profile = VolumeProfile(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            price_levels=price_levels,
            tick_size=self.tick_size
        )
        
        self._calculate_poc_and_value_area(profile)
        self._identify_volume_nodes(profile)
        
        return profile
    
    def _round_to_tick(self, price: float) -> float:
        """ tick"""
        return round(price / self.tick_size) * self.tick_size
    
    def _calculate_poc_and_value_area(self, profile: VolumeProfile):
        """ POC """
        if not profile.price_levels:
            return
        
        #  POC ()
        poc_level = max(profile.price_levels, key=lambda x: x.volume)
        profile.poc_price = poc_level.price
        profile.poc_volume = poc_level.volume
        
        # 
        total_volume = sum(level.volume for level in profile.price_levels)
        target_volume = total_volume * self.value_area_percent
        
        #  POC 
        poc_index = next(
            i for i, level in enumerate(profile.price_levels) 
            if level.price == profile.poc_price
        )
        
        accumulated_volume = profile.poc_volume
        low_index = poc_index
        high_index = poc_index
        
        while accumulated_volume < target_volume:
            # 
            can_expand_down = low_index > 0
            can_expand_up = high_index < len(profile.price_levels) - 1
            
            if not can_expand_down and not can_expand_up:
                break
            
            down_volume = profile.price_levels[low_index - 1].volume if can_expand_down else 0
            up_volume = profile.price_levels[high_index + 1].volume if can_expand_up else 0
            
            if down_volume >= up_volume and can_expand_down:
                low_index -= 1
                accumulated_volume += profile.price_levels[low_index].volume
            elif can_expand_up:
                high_index += 1
                accumulated_volume += profile.price_levels[high_index].volume
            else:
                break
        
        profile.value_area_low = profile.price_levels[low_index].price
        profile.value_area_high = profile.price_levels[high_index].price
    
    def _identify_volume_nodes(self, profile: VolumeProfile, threshold: float = 1.5):
        """/
        
        Args:
            threshold:  ()
        """
        if len(profile.price_levels) < 5:
            return
        
        volumes = [level.volume for level in profile.price_levels]
        avg_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        high_threshold = avg_volume + threshold * std_volume
        low_threshold = avg_volume - 0.5 * std_volume
        
        profile.high_volume_nodes = [
            level.price for level in profile.price_levels 
            if level.volume > high_threshold
        ]
        
        profile.low_volume_nodes = [
            level.price for level in profile.price_levels 
            if level.volume < low_threshold and level.volume > 0
        ]


# ============================================================================
#  (Liquidation Heatmap Calculator)
# ============================================================================

class LiquidationHeatmapCalculator:
    """
    
    
    """
    
    def __init__(self):
        # 
        self.leverage_levels = [3, 5, 10, 20, 25, 50, 75, 100, 125]
        
        #  ()
        self.maintenance_margin_rates = {
            3: 0.01,
            5: 0.02,
            10: 0.04,
            20: 0.05,
            25: 0.05,
            50: 0.10,
            75: 0.125,
            100: 0.15,
            125: 0.20
        }
    
    def calculate_liquidation_price(
        self, 
        entry_price: float, 
        leverage: int, 
        side: str,
        margin_rate: Optional[float] = None
    ) -> float:
        """
        
        Args:
            entry_price: 
            leverage: 
            side: 'long'  'short'
            margin_rate: 
        """
        if margin_rate is None:
            margin_rate = self.maintenance_margin_rates.get(leverage, 0.05)
        
        if side == 'long':
            #  =  * (1 - 1/ + )
            liq_price = entry_price * (1 - 1/leverage + margin_rate)
        else:
            #  =  * (1 + 1/ - )
            liq_price = entry_price * (1 + 1/leverage - margin_rate)
        
        return liq_price
    
    def estimate_liquidation_heatmap(
        self,
        symbol: str,
        current_price: float,
        open_interest: float,
        price_range_percent: float = 0.10,
        num_levels: int = 20
    ) -> LiquidationHeatmap:
        """
        
        
        
        """
        long_clusters = []
        short_clusters = []
        
        # 
        price_step = current_price * price_range_percent / num_levels
        
        # 
        for i in range(1, num_levels + 1):
            #  ()
            lower_price = current_price - i * price_step
            long_liq_value = self._estimate_liquidation_at_price(
                current_price, lower_price, open_interest, 'long'
            )
            if long_liq_value > 0:
                leverage_range = self._estimate_leverage_range(current_price, lower_price, 'long')
                long_clusters.append(LiquidationCluster(
                    price=lower_price,
                    estimated_liquidation_value=long_liq_value,
                    side='long',
                    leverage_range=leverage_range,
                    confidence=max(0.3, 1 - i * 0.05)  # 
                ))
            
            #  ()
            upper_price = current_price + i * price_step
            short_liq_value = self._estimate_liquidation_at_price(
                current_price, upper_price, open_interest, 'short'
            )
            if short_liq_value > 0:
                leverage_range = self._estimate_leverage_range(current_price, upper_price, 'short')
                short_clusters.append(LiquidationCluster(
                    price=upper_price,
                    estimated_liquidation_value=short_liq_value,
                    side='short',
                    leverage_range=leverage_range,
                    confidence=max(0.3, 1 - i * 0.05)
                ))
        
        # 
        long_clusters.sort(key=lambda x: x.estimated_liquidation_value, reverse=True)
        short_clusters.sort(key=lambda x: x.estimated_liquidation_value, reverse=True)
        
        # 
        total_long_risk = sum(c.estimated_liquidation_value for c in long_clusters)
        total_short_risk = sum(c.estimated_liquidation_value for c in short_clusters)
        
        # 
        nearest_long = (current_price - long_clusters[0].price) / current_price * 100 if long_clusters else 0
        nearest_short = (short_clusters[0].price - current_price) / current_price * 100 if short_clusters else 0
        
        return LiquidationHeatmap(
            symbol=symbol,
            current_price=current_price,
            long_clusters=long_clusters,
            short_clusters=short_clusters,
            total_long_liquidation_risk=total_long_risk,
            total_short_liquidation_risk=total_short_risk,
            nearest_long_cluster_distance=nearest_long,
            nearest_short_cluster_distance=nearest_short
        )
    
    def _estimate_liquidation_at_price(
        self, 
        current_price: float, 
        target_price: float,
        open_interest: float,
        side: str
    ) -> float:
        """"""
        price_diff_pct = abs(target_price - current_price) / current_price
        
        # 
        liquidation_value = 0
        for leverage in self.leverage_levels:
            liq_price = self.calculate_liquidation_price(current_price, leverage, side)
            
            # 
            if side == 'long' and target_price <= liq_price:
                #  ()
                leverage_weight = 1 / leverage
                portion = open_interest * leverage_weight * 0.1  # 
                liquidation_value += portion
            elif side == 'short' and target_price >= liq_price:
                leverage_weight = 1 / leverage
                portion = open_interest * leverage_weight * 0.1
                liquidation_value += portion
        
        return liquidation_value
    
    def _estimate_leverage_range(
        self, 
        current_price: float, 
        target_price: float,
        side: str
    ) -> Tuple[int, int]:
        """"""
        min_leverage = None
        max_leverage = None
        
        for leverage in self.leverage_levels:
            liq_price = self.calculate_liquidation_price(current_price, leverage, side)
            
            if side == 'long' and target_price <= liq_price:
                if min_leverage is None:
                    min_leverage = leverage
                max_leverage = leverage
            elif side == 'short' and target_price >= liq_price:
                if min_leverage is None:
                    min_leverage = leverage
                max_leverage = leverage
        
        return (min_leverage or 10, max_leverage or 125)


# ============================================================================
#  (Market Data Processor)
# ============================================================================

class MarketDataProcessor:
    """
    
    
    """
    
    def __init__(self):
        self.volume_profile_calc = VolumeProfileCalculator()
        self.liquidation_calc = LiquidationHeatmapCalculator()
        
        # 
        self.price_history: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        self.volume_history: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        self.oi_history: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        self.liquidation_history: Dict[str, List[Tuple[int, float, str]]] = defaultdict(list)
        
        # 
        self.max_history_length = 1000
    
    def update_price(self, symbol: str, timestamp: int, price: float):
        """"""
        self.price_history[symbol].append((timestamp, price))
        if len(self.price_history[symbol]) > self.max_history_length:
            self.price_history[symbol].pop(0)
    
    def update_volume(self, symbol: str, timestamp: int, volume: float):
        """"""
        self.volume_history[symbol].append((timestamp, volume))
        if len(self.volume_history[symbol]) > self.max_history_length:
            self.volume_history[symbol].pop(0)
    
    def update_open_interest(self, symbol: str, timestamp: int, oi: float):
        """"""
        self.oi_history[symbol].append((timestamp, oi))
        if len(self.oi_history[symbol]) > self.max_history_length:
            self.oi_history[symbol].pop(0)
    
    def record_liquidation(
        self, 
        symbol: str, 
        timestamp: int, 
        value: float, 
        side: str
    ):
        """"""
        self.liquidation_history[symbol].append((timestamp, value, side))
        if len(self.liquidation_history[symbol]) > self.max_history_length:
            self.liquidation_history[symbol].pop(0)
    
    def get_price_change(self, symbol: str, minutes: int) -> float:
        """"""
        history = self.price_history.get(symbol, [])
        if len(history) < 2:
            return 0.0
        
        current_price = history[-1][1]
        cutoff_time = history[-1][0] - minutes * 60 * 1000
        
        # 
        for ts, price in reversed(history):
            if ts <= cutoff_time:
                return ((current_price - price) / price) * 100
        
        return 0.0
    
    def get_volume_ratio(self, symbol: str, window_minutes: int = 60) -> float:
        """"""
        history = self.volume_history.get(symbol, [])
        if len(history) < 10:
            return 1.0
        
        current_time = history[-1][0]
        cutoff_time = current_time - window_minutes * 60 * 1000
        
        recent_volume = sum(v for ts, v in history if ts > cutoff_time)
        
        # 
        all_volume = sum(v for _, v in history)
        avg_volume = all_volume / len(history) * (window_minutes / 5)  #  5 
        
        return recent_volume / avg_volume if avg_volume > 0 else 1.0
    
    def get_oi_change(self, symbol: str, hours: int) -> float:
        """"""
        history = self.oi_history.get(symbol, [])
        if len(history) < 2:
            return 0.0
        
        current_oi = history[-1][1]
        cutoff_time = history[-1][0] - hours * 3600 * 1000
        
        for ts, oi in reversed(history):
            if ts <= cutoff_time:
                return ((current_oi - oi) / oi) * 100 if oi > 0 else 0.0
        
        return 0.0
    
    def get_liquidation_stats(
        self, 
        symbol: str, 
        hours: int = 1
    ) -> Tuple[float, float]:
        """
        
        Returns:
            (, )
        """
        history = self.liquidation_history.get(symbol, [])
        if not history:
            return 0.0, 0.0
        
        current_time = history[-1][0]
        cutoff_time = current_time - hours * 3600 * 1000
        
        long_liq = 0.0
        short_liq = 0.0
        
        for ts, value, side in history:
            if ts > cutoff_time:
                if side == 'long':
                    long_liq += value
                else:
                    short_liq += value
        
        return long_liq, short_liq
    
    def build_market_microstructure(
        self,
        symbol: str,
        current_price: float,
        order_book: Optional[Any] = None,  # OrderBookSnapshot
        funding_data: Optional[Any] = None,  # FundingRateData
        oi_data: Optional[Any] = None,  # OpenInterestData
        long_short_ratio: float = 1.0,
        taker_ratio: float = 1.0
    ) -> MarketMicrostructure:
        """"""
        
        # 
        price_change_1m = self.get_price_change(symbol, 1)
        price_change_5m = self.get_price_change(symbol, 5)
        price_change_15m = self.get_price_change(symbol, 15)
        price_change_1h = self.get_price_change(symbol, 60)
        
        # 
        volume_ratio = self.get_volume_ratio(symbol, 60)
        
        # 
        bid_ask_spread = 0.0
        bid_depth = 0.0
        ask_depth = 0.0
        imbalance = 0.0
        if order_book:
            bid_ask_spread = order_book.spread_percentage
            bid_depth = order_book.get_bid_depth(20)
            ask_depth = order_book.get_ask_depth(20)
            imbalance = order_book.get_imbalance(20)
        
        # 
        long_liq, short_liq = self.get_liquidation_stats(symbol, 1)
        
        # 
        oi = oi_data.open_interest if oi_data else 0.0
        oi_change_1h = self.get_oi_change(symbol, 1)
        oi_change_24h = self.get_oi_change(symbol, 24)
        
        # 
        funding_rate = funding_data.funding_rate if funding_data else 0.0
        predicted_funding = funding_data.predicted_funding_rate if funding_data else 0.0
        hours_to_funding = funding_data.hours_until_funding if funding_data else 0.0
        
        return MarketMicrostructure(
            symbol=symbol,
            timestamp=datetime.now(),
            price=current_price,
            price_change_1m=price_change_1m,
            price_change_5m=price_change_5m,
            price_change_15m=price_change_15m,
            price_change_1h=price_change_1h,
            volume_ratio=volume_ratio,
            bid_ask_spread=bid_ask_spread,
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            order_book_imbalance=imbalance,
            long_liquidation_1h=long_liq,
            short_liquidation_1h=short_liq,
            net_liquidation=long_liq - short_liq,
            open_interest=oi,
            oi_change_1h=oi_change_1h,
            oi_change_24h=oi_change_24h,
            funding_rate=funding_rate,
            predicted_funding_rate=predicted_funding,
            hours_to_funding=hours_to_funding,
            long_short_ratio=long_short_ratio,
            taker_buy_sell_ratio=taker_ratio
        )
    
    def generate_market_summary_prompt(
        self,
        microstructure: MarketMicrostructure,
        volume_profile: Optional[VolumeProfile] = None,
        liquidation_heatmap: Optional[LiquidationHeatmap] = None
    ) -> str:
        """ Prompt ( LLM )"""
        parts = [microstructure.to_prompt()]
        
        if volume_profile:
            parts.append("")
            parts.append(volume_profile.to_prompt())
        
        if liquidation_heatmap:
            parts.append("")
            parts.append(liquidation_heatmap.to_prompt())
        
        return "\n".join(parts)
