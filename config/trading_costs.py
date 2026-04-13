"""
 USDT 
==================================




- Binance Futures Fee Structure (2024-2026)
- https://www.binance.com/en/fee/futureFee
- 2026119


1.  VIP BNB 
2. 
3. 800:00, 08:00, 16:00 UTC
"""

from typing import Any, Dict, Literal, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timezone

if TYPE_CHECKING:
    from src.bioneuronai.data.binance_futures import BinanceFuturesConnector


# ========================================
# Trading Fees
# ========================================

@dataclass
class TradingFees:
    """"""
    maker_fee: float  # Maker
    taker_fee: float  # Taker
    vip_level: int    # VIP 
    
    def calculate_fee(self, notional_value: float, is_maker: bool = False) -> float:
        """
        
        
        Args:
            notional_value:  × 
            is_maker: Maker
            
        Returns:
            float: USDT
        """
        fee_rate = self.maker_fee if is_maker else self.taker_fee
        return notional_value * fee_rate


# VIP 0
STANDARD_FEES = TradingFees(
    maker_fee=0.0002,   # 0.02% ()
    taker_fee=0.0005,   # 0.05% ()
    vip_level=0
)

# VIP 30BNB
VIP_FEES = {
    0: TradingFees(maker_fee=0.0200, taker_fee=0.0500, vip_level=0),  # < $250K
    1: TradingFees(maker_fee=0.0160, taker_fee=0.0400, vip_level=1),  # $250K - $2.5M
    2: TradingFees(maker_fee=0.0140, taker_fee=0.0350, vip_level=2),  # $2.5M - $10M
    3: TradingFees(maker_fee=0.0120, taker_fee=0.0320, vip_level=3),  # $10M - $50M
    4: TradingFees(maker_fee=0.0100, taker_fee=0.0300, vip_level=4),  # $50M - $250M
    5: TradingFees(maker_fee=0.0080, taker_fee=0.0270, vip_level=5),  # $250M - $1B
    6: TradingFees(maker_fee=0.0060, taker_fee=0.0250, vip_level=6),  # $1B - $5B
    7: TradingFees(maker_fee=0.0040, taker_fee=0.0220, vip_level=7),  # $5B - $10B
    8: TradingFees(maker_fee=0.0020, taker_fee=0.0200, vip_level=8),  # $10B - $50B
    9: TradingFees(maker_fee=0.0000, taker_fee=0.0170, vip_level=9),  # > $50B
}

#  10000 
# 0.0200 = 0.0200% = 0.0002 ()
for vip_level, fees in VIP_FEES.items():
    fees.maker_fee /= 10000
    fees.taker_fee /= 10000


# ========================================
# BNB BNB Discount
# ========================================

BNB_DISCOUNT = {
    "enabled": True,
    "discount_rate": 0.10,  # 10% 
    "description": " BNB  10% "
}


# ========================================
# Funding Rate
# ========================================

@dataclass
class FundingRateInfo:
    """"""
    settlement_interval_hours: int = 8  # 
    typical_range: tuple = (-0.01, 0.01)  # -0.01%  0.01%
    extreme_range: tuple = (-0.75, 0.75)  # -0.75%  0.75%
    cap_rate: float = 0.0075  # ±0.75%
    
    def estimate_daily_cost(self, position_value: float, avg_rate: float = 0.0001) -> float:
        """
        
        
        Args:
            position_value: USDT
            avg_rate:  0.01%
            
        Returns:
            float: USDT
        """
        daily_settlements = 24 / self.settlement_interval_hours  # 3/
        return position_value * avg_rate * daily_settlements


FUNDING_RATE = FundingRateInfo()

# 
FUNDING_RATE_REFERENCE = {
    "BTCUSDT": {
        "avg_7d": 0.0001,      # 70.01%
        "avg_30d": 0.00008,    # 300.008%
        "description": "BTC  0.01% "
    },
    "ETHUSDT": {
        "avg_7d": 0.00012,
        "avg_30d": 0.0001,
        "description": "ETH  BTC"
    },
    "ALTCOINS": {
        "avg_7d": 0.0002,
        "avg_30d": 0.00015,
        "description": ""
    }
}


# ========================================
# Spread Cost
# ========================================

SPREAD_COSTS = {
    "BTCUSDT": {
        "typical_spread_bps": 1,  # 1  (0.01%)
        "min_spread_bps": 0.5,
        "max_spread_bps": 5,
        "description": "BTC "
    },
    "ETHUSDT": {
        "typical_spread_bps": 1.5,
        "min_spread_bps": 1,
        "max_spread_bps": 10,
        "description": "ETH "
    },
    "MAJOR_ALTS": {  # SOL, BNB, XRP, ADA
        "typical_spread_bps": 2,
        "min_spread_bps": 1,
        "max_spread_bps": 15,
        "description": ""
    },
    "MINOR_ALTS": {
        "typical_spread_bps": 5,
        "min_spread_bps": 2,
        "max_spread_bps": 50,
        "description": ""
    }
}


# ========================================
# Slippage
# ========================================

def estimate_slippage(
    order_size_usd: float,
    symbol: str,
    market_condition: Literal["normal", "volatile", "extreme"] = "normal"
) -> float:
    """
    
    
    Args:
        order_size_usd: USDT
        symbol: 
        market_condition: 
        
    Returns:
        float: 
    """
    base_slippage = {
        "BTCUSDT": 0.0001,   # 0.01%
        "ETHUSDT": 0.0002,   # 0.02%
        "MAJOR_ALTS": 0.0005,  # 0.05%
        "MINOR_ALTS": 0.001,   # 0.1%
    }
    
    # 
    size_multiplier = 1.0
    if order_size_usd > 100000:  # > $100K
        size_multiplier = 1.5
    elif order_size_usd > 500000:  # > $500K
        size_multiplier = 2.0
    elif order_size_usd > 1000000:  # > $1M
        size_multiplier = 3.0
    
    # 
    volatility_multiplier = {
        "normal": 1.0,
        "volatile": 2.0,
        "extreme": 5.0
    }[market_condition]
    
    # 
    if symbol in ["BTCUSDT"]:
        category = "BTCUSDT"
    elif symbol in ["ETHUSDT"]:
        category = "ETHUSDT"
    elif symbol in ["SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]:
        category = "MAJOR_ALTS"
    else:
        category = "MINOR_ALTS"
    
    return base_slippage[category] * size_multiplier * volatility_multiplier


# ========================================
# USDT
# ========================================

MARGIN_INTEREST = {
    "usdt_perpetual": 0.0,  # USDT 
    "description": " USDT "
}


# ========================================
# 
# ========================================

class TradingCostCalculator:
    """
    
    
    
    """
    
    def __init__(self, vip_level: int = 0, use_bnb: bool = False, default_leverage: int = 10):
        """
        Args:
            vip_level: VIP 0-9
            use_bnb: 使用 BNB 支付手續費
            default_leverage: 預設槓桿倍數 1-125
        """
        self.fees = VIP_FEES.get(vip_level, STANDARD_FEES)
        self.use_bnb = use_bnb
        self.bnb_discount: float = float(BNB_DISCOUNT["discount_rate"]) if use_bnb else 0.0  # type: ignore[arg-type]
        self.default_leverage = default_leverage
    
    def calculate_entry_exit_costs(
        self,
        position_size_usd: float,
        entry_price: float,
        exit_price: float,
        symbol: str = "BTCUSDT",
        is_maker_entry: bool = False,
        is_maker_exit: bool = False,
        holding_hours: float = 24.0,
        market_condition: Literal["normal", "volatile", "extreme"] = "normal",
        leverage: Optional[int] = None,
        funding_rate: Optional[float] = None,
        funding_interval_hours: float = 8.0,
        spread_bps: Optional[float] = None,
        position_side: Literal["long", "short"] = "long",
    ) -> Dict:
        """
        Args:
            funding_rate: 當下資金費率（可正可負）。正值=多單付費，負值=多單收入。
                          由呼叫方從已收集的 MarketMicrostructure 傳入；None 時用靜態預設。
            funding_interval_hours: 實際結算間隔小時數（Binance 可能非固定 8h）。
            spread_bps: 當下買賣價差基點。由呼叫方從 order_book 計算後傳入；None 時用靜態預設。
        """
        lev = leverage if leverage is not None else self.default_leverage
        required_margin = position_size_usd / lev
        maintenance_margin_rate = 0.004 if symbol == "BTCUSDT" else 0.01
        liquidation_distance = (1 / lev) - maintenance_margin_rate
        if position_side == "short":
            liquidation_price = entry_price * (1 + liquidation_distance)
        else:
            liquidation_price = entry_price * (1 - liquidation_distance)

        # 1. 開倉手續費
        entry_fee = self.fees.calculate_fee(position_size_usd, is_maker_entry)
        if self.use_bnb:
            entry_fee *= (1 - float(self.bnb_discount))

        # 2. 平倉手續費
        exit_value = position_size_usd * (exit_price / entry_price)
        exit_fee = self.fees.calculate_fee(exit_value, is_maker_exit)
        if self.use_bnb:
            exit_fee *= (1 - float(self.bnb_discount))

        # 3. 資金費率（由呼叫方傳入已收集的即時值；可正可負）
        actual_funding_rate = funding_rate if funding_rate is not None else float(
            FUNDING_RATE_REFERENCE.get(symbol, FUNDING_RATE_REFERENCE["ALTCOINS"])["avg_7d"]  # type: ignore[arg-type]
        )
        funding_settlements = holding_hours / funding_interval_hours
        funding_cost = position_size_usd * actual_funding_rate * funding_settlements

        # 4. 買賣價差（由呼叫方傳入即時值；否則用靜態預設）
        actual_spread_bps = spread_bps if spread_bps is not None else float(
            SPREAD_COSTS.get(symbol, SPREAD_COSTS["MINOR_ALTS"])["typical_spread_bps"]  # type: ignore[index]
        )
        spread_cost = position_size_usd * (actual_spread_bps / 10000) * 2
        
        # 5. 
        slippage_rate = estimate_slippage(position_size_usd, symbol, market_condition)
        slippage_cost = position_size_usd * slippage_rate * 2  # 
        
        # 
        total_cost = entry_fee + exit_fee + funding_cost + spread_cost + slippage_cost
        
        # 
        cost_percentage_on_margin = (total_cost / required_margin) * 100
        
        # 
        cost_percentage_on_notional = (total_cost / position_size_usd) * 100
        
        # 
        breakeven_price = entry_price * (1 + total_cost / position_size_usd)
        
        # 
        if exit_price != entry_price:
            gross_pnl = (exit_price - entry_price) / entry_price * position_size_usd
            net_pnl = gross_pnl - total_cost
            # ROI 
            roi_on_margin = (net_pnl / required_margin) * 100
            #  ROI 
            roi_on_notional = (net_pnl / position_size_usd) * 100
        else:
            roi_on_margin = 0
            roi_on_notional = 0
        
        return {
            # 
            "entry_fee": round(entry_fee, 4),
            "exit_fee": round(exit_fee, 4),
            "funding_cost": round(funding_cost, 4),
            "spread_cost": round(spread_cost, 4),
            "slippage_cost": round(slippage_cost, 4),
            "total_cost": round(total_cost, 4),
            
            # 
            "cost_percentage": round(cost_percentage_on_notional, 4),  # 
            "cost_percentage_on_margin": round(cost_percentage_on_margin, 4),  # 
            
            # 
            "leverage": lev,
            "position_size_usd": position_size_usd,
            "required_margin": round(required_margin, 2),
            "liquidation_price": round(liquidation_price, 2),
            "breakeven_price": round(breakeven_price, 2),
            "roi_on_margin": round(roi_on_margin, 2) if exit_price != entry_price else 0.0,
            "roi_on_notional": round(roi_on_notional, 2) if exit_price != entry_price else 0.0,
            "details": {
                "vip_level": self.fees.vip_level,
                "bnb_discount": self.bnb_discount,
                "holding_hours": holding_hours,
                "funding_rate": actual_funding_rate,
                "funding_rate_is_negative": actual_funding_rate < 0,
                "funding_interval_hours": funding_interval_hours,
                "funding_settlements": round(funding_settlements, 2),
                "maintenance_margin_rate": maintenance_margin_rate,
            }
        }
    
    def get_minimum_profit_target(
        self,
        position_size_usd: float,
        symbol: str = "BTCUSDT",
        desired_profit_margin: float = 0.01,
        leverage: Optional[int] = None,
        based_on: Literal["margin", "notional"] = "notional",
        funding_rate: Optional[float] = None,
        spread_bps: Optional[float] = None,
        position_side: Literal["long", "short"] = "long",
    ) -> float:
        """
        
        Args:
            position_size_usd: USDT
            symbol: 
            desired_profit_margin: 0.01 = 1%
            leverage: None
            based_on:  - "notional" "margin"
            
        Returns:
            float: %
        """
        if leverage is None:
            leverage = self.default_leverage
        
        # 24market order 
        costs = self.calculate_entry_exit_costs(
            position_size_usd=position_size_usd,
            entry_price=50000,
            exit_price=50000,
            symbol=symbol,
            is_maker_entry=False,
            is_maker_exit=False,
            holding_hours=24.0,
            leverage=leverage,
            funding_rate=funding_rate,
            spread_bps=spread_bps,
            position_side=position_side,
        )
        
        if based_on == "margin":
            # 
            # 10x  10%  = 1% 
            required_margin = position_size_usd / leverage
            desired_profit_usd = required_margin * desired_profit_margin
            total_required_pnl = desired_profit_usd + costs["total_cost"]
            minimum_price_move_pct = (total_required_pnl / position_size_usd)
        else:
            # 
            total_cost_pct = costs["cost_percentage"] / 100
            minimum_price_move_pct = total_cost_pct + desired_profit_margin
        
        return float(round(minimum_price_move_pct * 100, 2))  # 


# ========================================
# 
# ========================================

QUICK_REFERENCE = {
    "standard_user": {
        "maker_fee": "0.02%",
        "taker_fee": "0.05%",
        "bnb_discount": "10% (if enabled)",
        "funding_rate": "~0.01% per 8h (varies)",
        "min_profit_target": "0.15% - 0.25% (24h hold)"
    },
    "typical_trade_costs": {
        "btc_1000usd_24h": {
            "entry_fee": 0.50,      # $0.50 (taker)
            "exit_fee": 0.50,       # $0.50 (taker)
            "funding_3x": 0.30,     # $0.30 (0.01% × 3)
            "spread": 0.20,         # $0.20 (2 bps × 2)
            "slippage": 0.20,       # $0.20 (2 bps × 2)
            "total": 1.70,          # $1.70
            "percentage": "0.17%"
        },
        "eth_5000usd_24h": {
            "total": 9.50,
            "percentage": "0.19%"
        }
    },
    "notes": [
        "8UTC 00:00, 08:00, 16:00",
        "",
        "maker 60% ",
        "BNB "
    ]
}


# ========================================
# 
# ========================================

if __name__ == "__main__":
    print("="*80)
    print("  USDT ")
    print("="*80)
    
    # 1: 5x
    print("\n1BTC 5x")
    print("-"*80)
    calc_5x = TradingCostCalculator(vip_level=0, use_bnb=True, default_leverage=5)
    costs_5x = calc_5x.calculate_entry_exit_costs(
        position_size_usd=1000,
        entry_price=50000,
        exit_price=51000,
        symbol="BTCUSDT",
        holding_hours=24,
        leverage=5
    )
    
    print(f": ${costs_5x['position_size_usd']:,.0f}")
    print(f": {costs_5x['leverage']}x")
    print(f": ${costs_5x['required_margin']:.2f}")
    print(f": ${costs_5x['liquidation_price']:,.2f}")
    print("\n: $50,000")
    print(": $51,000 (+2.00%)")
    print("\n:")
    print(f"  : ${costs_5x['entry_fee']:.2f}")
    print(f"  : ${costs_5x['exit_fee']:.2f}")
    print(f"  :   ${costs_5x['funding_cost']:.2f}")
    print(f"  +:  ${costs_5x['spread_cost'] + costs_5x['slippage_cost']:.2f}")
    print("  ")
    print(f"  :     ${costs_5x['total_cost']:.2f}")
    print("\n:")
    print(f"  : {costs_5x['cost_percentage']:.2f}%")
    print(f"  :   {costs_5x['cost_percentage_on_margin']:.2f}% ")
    print("\n:")
    print(f"  : ${costs_5x['breakeven_price']:,.2f}")
    print(f"  : {costs_5x['roi_on_margin']:.2f}% ")
    print(f"  :   {costs_5x['roi_on_notional']:.2f}%")
    
    # 2: 20x
    print("\n" + "="*80)
    print("2BTC 20x- ")
    print("-"*80)
    calc_20x = TradingCostCalculator(vip_level=0, use_bnb=True, default_leverage=20)
    costs_20x = calc_20x.calculate_entry_exit_costs(
        position_size_usd=1000,
        entry_price=50000,
        exit_price=51000,
        symbol="BTCUSDT",
        holding_hours=24,
        leverage=20
    )
    
    print(f": ${costs_20x['position_size_usd']:,.0f}")
    print(f": {costs_20x['leverage']}x")
    print(f": ${costs_20x['required_margin']:.2f} ")
    print(f": ${costs_20x['liquidation_price']:,.2f}  ")
    print("\n:")
    print(f"  : ${costs_20x['total_cost']:.2f}")
    print(f"  : {costs_20x['cost_percentage_on_margin']:.2f}% ")
    print("\n:")
    print(f"  : {costs_20x['roi_on_margin']:.2f}% ")
    print(f"  ( {costs_20x['leverage']}x)")
    
    # 
    print("\n" + "="*80)
    print(" $1000 +2% ")
    print("-"*80)
    print("               5x     20x     ")
    print("-"*80)
    print(f"         ${costs_5x['required_margin']:>7.2f}   ${costs_20x['required_margin']:>8.2f}   4x ")
    print(f"           ${costs_5x['liquidation_price']:>7,.0f}   ${costs_20x['liquidation_price']:>8,.0f}    ")
    print(f"       {costs_5x['cost_percentage_on_margin']:>6.2f}%   {costs_20x['cost_percentage_on_margin']:>7.2f}%   {costs_20x['cost_percentage_on_margin']/costs_5x['cost_percentage_on_margin']:.1f}x")
    print(f"       {costs_5x['roi_on_margin']:>6.2f}%   {costs_20x['roi_on_margin']:>7.2f}%   {costs_20x['roi_on_margin']/costs_5x['roi_on_margin']:.1f}x")
    
    # 
    print("\n" + "="*80)
    print(" 10% ")
    print("-"*80)
    min_5x = calc_5x.get_minimum_profit_target(1000, "BTCUSDT", 0.10, 5, "margin")
    min_20x = calc_20x.get_minimum_profit_target(1000, "BTCUSDT", 0.10, 20, "margin")
    print(f"5x :   {min_5x}%")
    print(f"20x :  {min_20x}%")
    print("\n : ")
    print("="*80)
