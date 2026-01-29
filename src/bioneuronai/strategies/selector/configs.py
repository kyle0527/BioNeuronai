"""
策略配置庫 - Strategy Configurations

包含 10 種預定義策略的詳細配置 (來自 v1)。

每個策略配置包含:
- 入場條件
- 出場條件
- 風險參數
- 預期績效
- 適合的市場環境

Created: 2026-01-25
"""

from typing import Dict

from .types import (
    StrategyConfigTemplate,
    StrategyType,
    MarketRegime,
    Complexity,
)


def get_default_strategy_configs() -> Dict[str, StrategyConfigTemplate]:
    """
    獲取所有預設策略配置
    
    Returns:
        策略名稱 -> StrategyConfigTemplate 的字典
    """
    configs = {}
    
    # 1. MA 交叉趨勢策略
    configs["MA_Crossover_Trend"] = StrategyConfigTemplate(
        strategy_type=StrategyType.TREND_FOLLOWING,
        name="MA 交叉趨勢",
        description="使用移動平均線交叉識別趨勢方向",
        entry_conditions={
            "fast_ma_period": 21,
            "slow_ma_period": 50,
            "signal": "fast_ma > slow_ma",
            "volume_confirmation": True,
            "trend_strength_min": 0.6
        },
        exit_conditions={
            "stop_loss": 0.02,
            "take_profit": 0.06,
            "trailing_stop": True,
            "ma_cross_reverse": True
        },
        risk_parameters={
            "position_size": 0.05,
            "max_positions": 3,
            "risk_per_trade": 0.01
        },
        timeframe="1h",
        min_capital=1000.0,
        expected_return=0.15,
        max_drawdown=0.08,
        win_rate=0.55,
        profit_factor=1.4,
        sharpe_ratio=1.2,
        suitable_markets=[MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
        complexity=Complexity.SIMPLE
    )
    
    # 2. RSI 均值回歸策略
    configs["RSI_Mean_Reversion"] = StrategyConfigTemplate(
        strategy_type=StrategyType.MEAN_REVERSION,
        name="RSI 均值回歸",
        description="RSI 超買超賣反轉交易",
        entry_conditions={
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "bollinger_bands_confirm": True,
            "volume_spike": False
        },
        exit_conditions={
            "rsi_neutral": 50,
            "profit_target": 0.03,
            "stop_loss": 0.015,
            "time_exit": "2h"
        },
        risk_parameters={
            "position_size": 0.03,
            "max_positions": 5,
            "risk_per_trade": 0.008
        },
        timeframe="15m",
        min_capital=500.0,
        expected_return=0.12,
        max_drawdown=0.06,
        win_rate=0.65,
        profit_factor=1.3,
        sharpe_ratio=1.1,
        suitable_markets=[MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL],
        complexity=Complexity.MEDIUM
    )
    
    # 3. 動量突破策略
    configs["Momentum_Breakout"] = StrategyConfigTemplate(
        strategy_type=StrategyType.MOMENTUM,
        name="動量突破",
        description="捕捉價格動量突破機會",
        entry_conditions={
            "momentum_period": 20,
            "momentum_threshold": 0.02,
            "volume_multiplier": 1.5,
            "price_breakout": True,
            "macd_confirmation": True
        },
        exit_conditions={
            "momentum_loss": 0.5,
            "profit_target": 0.08,
            "stop_loss": 0.025,
            "volume_decline": True
        },
        risk_parameters={
            "position_size": 0.04,
            "max_positions": 3,
            "risk_per_trade": 0.012
        },
        timeframe="30m",
        min_capital=1500.0,
        expected_return=0.20,
        max_drawdown=0.12,
        win_rate=0.50,
        profit_factor=1.6,
        sharpe_ratio=1.3,
        suitable_markets=[MarketRegime.TRENDING_BULL, MarketRegime.VOLATILE_UNCERTAIN],
        complexity=Complexity.MEDIUM
    )
    
    # 4. 高頻剝頭皮策略
    configs["High_Frequency_Scalp"] = StrategyConfigTemplate(
        strategy_type=StrategyType.SCALPING,
        name="高頻剝頭皮",
        description="利用小幅價差進行快速交易",
        entry_conditions={
            "spread_threshold": 0.001,
            "order_book_imbalance": 0.3,
            "micro_trend": True,
            "liquidity_min": 1000000
        },
        exit_conditions={
            "profit_target": 0.005,
            "stop_loss": 0.003,
            "time_exit": "5m",
            "spread_widen": 0.002
        },
        risk_parameters={
            "position_size": 0.02,
            "max_positions": 10,
            "risk_per_trade": 0.003
        },
        timeframe="1m",
        min_capital=5000.0,
        expected_return=0.25,
        max_drawdown=0.04,
        win_rate=0.75,
        profit_factor=1.2,
        sharpe_ratio=2.1,
        suitable_markets=[MarketRegime.SIDEWAYS_LOW_VOL],
        complexity=Complexity.COMPLEX
    )
    
    # 5. 網格交易策略
    configs["Grid_Trading"] = StrategyConfigTemplate(
        strategy_type=StrategyType.GRID_TRADING,
        name="網格交易",
        description="在價格區間內設置多層買賣網格",
        entry_conditions={
            "grid_levels": 10,
            "grid_spacing": 0.01,
            "range_detection": True,
            "volatility_adjustment": True
        },
        exit_conditions={
            "range_break": 0.05,
            "profit_accumulation": 0.10,
            "max_grid_age": "24h"
        },
        risk_parameters={
            "total_grid_allocation": 0.30,
            "max_grid_levels": 20,
            "risk_per_level": 0.015
        },
        timeframe="1h",
        min_capital=2000.0,
        expected_return=0.18,
        max_drawdown=0.15,
        win_rate=0.70,
        profit_factor=1.5,
        sharpe_ratio=1.4,
        suitable_markets=[MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL],
        complexity=Complexity.COMPLEX
    )
    
    # 6. 波動率交易策略
    configs["Volatility_Trading"] = StrategyConfigTemplate(
        strategy_type=StrategyType.VOLATILITY_TRADING,
        name="波動率交易",
        description="利用隱含波動率與歷史波動率差異獲利",
        entry_conditions={
            "iv_hv_ratio": 1.2,
            "volatility_spike": 0.3,
            "vix_divergence": True,
            "option_skew": 0.1
        },
        exit_conditions={
            "volatility_normalize": 0.8,
            "time_decay": 0.5,
            "profit_target": 0.15,
            "delta_neutral": True
        },
        risk_parameters={
            "volatility_allocation": 0.10,
            "max_vega_exposure": 1000,
            "delta_hedge_threshold": 0.1
        },
        timeframe="4h",
        min_capital=10000.0,
        expected_return=0.22,
        max_drawdown=0.18,
        win_rate=0.48,
        profit_factor=1.8,
        sharpe_ratio=1.6,
        suitable_markets=[MarketRegime.VOLATILE_UNCERTAIN, MarketRegime.SIDEWAYS_HIGH_VOL],
        complexity=Complexity.COMPLEX
    )
    
    # 7. 新聞驅動策略
    configs["News_Trading"] = StrategyConfigTemplate(
        strategy_type=StrategyType.NEWS_TRADING,
        name="新聞驅動交易",
        description="基於新聞情緒分析進行交易決策",
        entry_conditions={
            "sentiment_threshold": 0.7,
            "news_freshness": "1h",
            "source_reliability": 0.8,
            "volume_surge": 2.0
        },
        exit_conditions={
            "sentiment_reversal": True,
            "profit_target": 0.05,
            "stop_loss": 0.02,
            "time_decay": "4h"
        },
        risk_parameters={
            "position_size": 0.03,
            "max_positions": 2,
            "risk_per_trade": 0.01
        },
        timeframe="15m",
        min_capital=3000.0,
        expected_return=0.25,
        max_drawdown=0.10,
        win_rate=0.55,
        profit_factor=1.7,
        sharpe_ratio=1.5,
        suitable_markets=[MarketRegime.VOLATILE_UNCERTAIN, MarketRegime.TRENDING_BULL],
        complexity=Complexity.MEDIUM
    )
    
    # 8. 突破交易策略
    configs["Breakout_Trading"] = StrategyConfigTemplate(
        strategy_type=StrategyType.BREAKOUT,
        name="區間突破",
        description="識別並交易價格區間突破",
        entry_conditions={
            "consolidation_period": 20,
            "breakout_threshold": 0.02,
            "volume_confirmation": 1.5,
            "false_breakout_filter": True
        },
        exit_conditions={
            "profit_target": 0.06,
            "stop_loss": 0.015,
            "breakout_failure": True,
            "time_exit": "6h"
        },
        risk_parameters={
            "position_size": 0.04,
            "max_positions": 3,
            "risk_per_trade": 0.01
        },
        timeframe="1h",
        min_capital=1500.0,
        expected_return=0.18,
        max_drawdown=0.08,
        win_rate=0.52,
        profit_factor=1.5,
        sharpe_ratio=1.3,
        suitable_markets=[MarketRegime.BREAKOUT_POTENTIAL, MarketRegime.SIDEWAYS_LOW_VOL],
        complexity=Complexity.MEDIUM
    )
    
    # 9. 波段交易策略
    configs["Swing_Trading"] = StrategyConfigTemplate(
        strategy_type=StrategyType.SWING_TRADING,
        name="波段交易",
        description="捕捉中期價格波動",
        entry_conditions={
            "swing_detection": True,
            "support_resistance": True,
            "trend_alignment": True,
            "fibonacci_levels": [0.382, 0.5, 0.618]
        },
        exit_conditions={
            "swing_target": 0.08,
            "stop_loss": 0.03,
            "trailing_stop": 0.02,
            "time_exit": "48h"
        },
        risk_parameters={
            "position_size": 0.05,
            "max_positions": 3,
            "risk_per_trade": 0.015
        },
        timeframe="4h",
        min_capital=2000.0,
        expected_return=0.20,
        max_drawdown=0.10,
        win_rate=0.58,
        profit_factor=1.6,
        sharpe_ratio=1.4,
        suitable_markets=[MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
        complexity=Complexity.MEDIUM
    )
    
    # 10. 套利策略
    configs["Arbitrage_Trading"] = StrategyConfigTemplate(
        strategy_type=StrategyType.ARBITRAGE,
        name="套利交易",
        description="利用市場間價差進行無風險套利",
        entry_conditions={
            "spread_threshold": 0.002,
            "execution_latency_max": 100,  # ms
            "liquidity_both_sides": True,
            "correlation_check": 0.95
        },
        exit_conditions={
            "spread_close": 0.0005,
            "max_hold_time": "5m",
            "slippage_exceeded": True
        },
        risk_parameters={
            "position_size": 0.10,
            "max_exposure": 0.20,
            "risk_per_trade": 0.002
        },
        timeframe="1m",
        min_capital=20000.0,
        expected_return=0.10,
        max_drawdown=0.02,
        win_rate=0.90,
        profit_factor=3.0,
        sharpe_ratio=3.5,
        suitable_markets=[MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL],
        complexity=Complexity.COMPLEX
    )
    
    return configs


# 策略別名映射 (便於查找)
STRATEGY_ALIASES: Dict[StrategyType, str] = {
    StrategyType.TREND_FOLLOWING: "MA_Crossover_Trend",
    StrategyType.MEAN_REVERSION: "RSI_Mean_Reversion",
    StrategyType.MOMENTUM: "Momentum_Breakout",
    StrategyType.SCALPING: "High_Frequency_Scalp",
    StrategyType.GRID_TRADING: "Grid_Trading",
    StrategyType.VOLATILITY_TRADING: "Volatility_Trading",
    StrategyType.NEWS_TRADING: "News_Trading",
    StrategyType.BREAKOUT: "Breakout_Trading",
    StrategyType.SWING_TRADING: "Swing_Trading",
    StrategyType.ARBITRAGE: "Arbitrage_Trading",
}


def get_strategy_by_type(strategy_type: StrategyType) -> StrategyConfigTemplate:
    """根據策略類型獲取配置"""
    configs = get_default_strategy_configs()
    alias = STRATEGY_ALIASES.get(strategy_type)
    if alias and alias in configs:
        return configs[alias]
    raise ValueError(f"Unknown strategy type: {strategy_type}")
