"""
Walk-Forward 測試系統

實現滾動窗口回測，用於驗證策略的時間穩定性並避免過擬合。

核心概念：
    1. 滾動窗口：將歷史數據分為多個訓練期和測試期
    2. 參數優化：在訓練期優化參數
    3. 樣本外驗證：在測試期驗證性能
    4. 過擬合檢測：比較訓練期和測試期的性能差異

作者：BioNeuronai 開發團隊
創建日期：2026-02-15
版本：v4.0.0
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from schemas.backtesting import BacktestConfig, BacktestResult
from .historical_backtest import HistoricalBacktest, HistoricalDataLoader

logger = logging.getLogger(__name__)


@dataclass
class WalkForwardWindow:
    """滾動窗口定義"""
    
    window_id: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    
    @property
    def train_days(self) -> int:
        """訓練期天數"""
        return (self.train_end - self.train_start).days
    
    @property
    def test_days(self) -> int:
        """測試期天數"""
        return (self.test_end - self.test_start).days
    
    def __str__(self) -> str:
        return (f"Window {self.window_id}: "
                f"Train[{self.train_start.date()} to {self.train_end.date()}] "
                f"Test[{self.test_start.date()} to {self.test_end.date()}]")


@dataclass
class WindowResult:
    """單個窗口的回測結果"""
    
    window: WalkForwardWindow
    train_result: BacktestResult
    test_result: BacktestResult
    optimal_params: Dict[str, Any]
    
    @property
    def train_sharpe(self) -> float:
        """訓練期夏普比率"""
        return float(self.train_result.sharpe_ratio or 0)
    
    @property
    def test_sharpe(self) -> float:
        """測試期夏普比率"""
        return float(self.test_result.sharpe_ratio or 0)
    
    @property
    def sharpe_degradation(self) -> float:
        """夏普比率衰減（%）"""
        if self.train_sharpe == 0:
            return 0.0
        return (1 - self.test_sharpe / self.train_sharpe) * 100
    
    @property
    def is_overfitting(self) -> bool:
        """是否過擬合（測試期表現明顯差於訓練期）"""
        return self.sharpe_degradation > 30  # 夏普衰減超過 30%


class WalkForwardConfig(BaseModel):
    """Walk-Forward 測試配置"""
    
    # 基本配置
    name: str = Field(..., description="測試名稱")
    symbol: str = Field(..., description="交易對")
    start_date: datetime = Field(..., description="總體開始日期")
    end_date: datetime = Field(..., description="總體結束日期")
    
    # 窗口配置
    train_window_days: int = Field(default=90, ge=30, description="訓練窗口天數")
    test_window_days: int = Field(default=30, ge=7, description="測試窗口天數")
    step_days: int = Field(default=30, ge=1, description="滾動步長（天）")
    
    # 回測配置
    initial_capital: Decimal = Field(default=Decimal("10000"), gt=0, description="初始資金")
    interval: str = Field(default="1h", description="K 線週期")
    
    # 參數優化配置
    param_grid: Dict[str, List[Any]] = Field(
        default_factory=dict,
        description="參數網格（用於訓練期優化）"
    )
    optimization_metric: str = Field(
        default="sharpe_ratio",
        description="優化目標指標"
    )
    
    # 風險管理
    max_drawdown_pct: float = Field(default=20.0, gt=0, description="最大回撤限制（%）")
    
    # 其他
    use_testnet: bool = Field(default=False, description="使用測試網")
    
    class Config:
        arbitrary_types_allowed = True


class WalkForwardResult(BaseModel):
    """Walk-Forward 測試總體結果"""
    
    # 識別
    test_id: str = Field(default_factory=lambda: str(uuid4()), description="測試 ID")
    config: WalkForwardConfig = Field(..., description="測試配置")
    
    # 窗口結果
    window_results: List[WindowResult] = Field(default_factory=list, description="各窗口結果")
    
    # 總體統計
    total_windows: int = Field(default=0, description="總窗口數")
    overfitting_windows: int = Field(default=0, description="過擬合窗口數")
    
    # 平均指標
    avg_train_sharpe: float = Field(default=0.0, description="平均訓練期夏普")
    avg_test_sharpe: float = Field(default=0.0, description="平均測試期夏普")
    avg_sharpe_degradation: float = Field(default=0.0, description="平均夏普衰減")
    
    avg_train_return: float = Field(default=0.0, description="平均訓練期收益率")
    avg_test_return: float = Field(default=0.0, description="平均測試期收益率")
    
    # 穩定性指標
    sharpe_stability: float = Field(default=0.0, description="夏普穩定性（標準差）")
    return_stability: float = Field(default=0.0, description="收益率穩定性（標準差）")
    
    # 整體評估
    is_robust: bool = Field(default=False, description="策略是否穩健")
    robustness_score: float = Field(default=0.0, ge=0, le=100, description="穩健性評分")
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def overfitting_rate(self) -> float:
        """過擬合率"""
        if self.total_windows == 0:
            return 0.0
        return self.overfitting_windows / self.total_windows


class WalkForwardTester:
    """
    Walk-Forward 測試引擎
    
    使用滾動窗口方法驗證策略的時間穩定性。
    
    示例：
        >>> from datetime import datetime
        >>> 
        >>> # 配置
        >>> config = WalkForwardConfig(
        ...     name="RSI Strategy WF Test",
        ...     symbol="BTCUSDT",
        ...     start_date=datetime(2025, 1, 1),
        ...     end_date=datetime(2025, 12, 31),
        ...     train_window_days=90,
        ...     test_window_days=30,
        ...     step_days=30,
        ...     param_grid={
        ...         'rsi_period': [10, 14, 20],
        ...         'rsi_oversold': [25, 30, 35],
        ...         'rsi_overbought': [65, 70, 75]
        ...     }
        ... )
        >>> 
        >>> # 定義策略生成函數
        >>> def generate_rsi_strategy(data, params):
        ...     # 返回信號列表
        ...     return signals
        >>> 
        >>> # 執行 Walk-Forward 測試
        >>> tester = WalkForwardTester(config, generate_rsi_strategy)
        >>> result = await tester.run()
        >>> 
        >>> print(f"總窗口: {result.total_windows}")
        >>> print(f"過擬合率: {result.overfitting_rate:.1%}")
        >>> print(f"穩健性評分: {result.robustness_score:.1f}/100")
    """
    
    def __init__(
        self,
        config: WalkForwardConfig,
        strategy_generator: Callable[[pd.DataFrame, Dict[str, Any]], List[Dict]]
    ):
        """
        初始化 Walk-Forward 測試器
        
        Args:
            config: WalkForward 配置
            strategy_generator: 策略生成函數
                - 輸入: (data: DataFrame, params: Dict)
                - 輸出: List[Dict] 信號列表
        """
        self.config = config
        self.strategy_generator = strategy_generator
        self.data_loader = HistoricalDataLoader(use_testnet=config.use_testnet)
        
        logger.info(f"✅ WalkForwardTester 初始化: {config.name}")
        logger.info(f"   交易對: {config.symbol}")
        logger.info(f"   窗口: 訓練 {config.train_window_days} 天 + 測試 {config.test_window_days} 天")
        logger.info(f"   滾動步長: {config.step_days} 天")
    
    def generate_windows(self) -> List[WalkForwardWindow]:
        """
        生成滾動窗口序列
        
        Returns:
            窗口列表
        """
        windows = []
        window_id = 1
        
        current_train_start = self.config.start_date
        
        while True:
            # 計算訓練期
            train_end = current_train_start + timedelta(days=self.config.train_window_days)
            
            # 計算測試期
            test_start = train_end
            test_end = test_start + timedelta(days=self.config.test_window_days)
            
            # 檢查是否超出總體結束日期
            if test_end > self.config.end_date:
                break
            
            window = WalkForwardWindow(
                window_id=window_id,
                train_start=current_train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end
            )
            
            windows.append(window)
            window_id += 1
            
            # 滾動到下一個窗口
            current_train_start += timedelta(days=self.config.step_days)
        
        logger.info(f"📊 生成 {len(windows)} 個滾動窗口")
        return windows
    
    async def optimize_parameters(
        self,
        data: pd.DataFrame,
        window: WalkForwardWindow
    ) -> Tuple[Dict[str, Any], BacktestResult]:
        """
        在訓練期優化參數
        
        Args:
            data: 完整數據
            window: 當前窗口
        
        Returns:
            (最優參數, 訓練期回測結果)
        """
        if not self.config.param_grid:
            # 無參數網格，使用默認參數
            logger.warning("⚠️ 無參數網格，使用默認參數")
            signals = self.strategy_generator(data, {})
            result = await self._run_backtest(data, window.train_start, window.train_end, signals)
            return {}, result
        
        # 訓練期數據
        train_data = data[
            (data['open_time'] >= window.train_start) &
            (data['open_time'] < window.train_end)
        ].copy()
        
        # 生成參數組合
        param_names = list(self.config.param_grid.keys())
        param_values = list(self.config.param_grid.values())
        
        from itertools import product
        param_combinations = list(product(*param_values))
        
        logger.info(f"   🔍 優化參數: {len(param_combinations)} 種組合")
        
        best_params = None
        best_result = None
        best_score = -float('inf')
        
        for param_combo in param_combinations:
            params = dict(zip(param_names, param_combo))
            
            # 生成策略信號
            signals = self.strategy_generator(train_data, params)
            
            # 回測
            result = await self._run_backtest(data, window.train_start, window.train_end, signals)
            
            # 評估
            score = self._evaluate_result(result)
            
            if score > best_score:
                best_score = score
                best_params = params
                best_result = result
        
        logger.info(f"   ✅ 最優參數: {best_params}")
        logger.info(f"   ✅ 訓練期 {self.config.optimization_metric}: {best_score:.4f}")
        
        # 確保返回值不為 None
        if best_params is None or best_result is None:
            logger.error("❌ 優化失敗：無法找到有效參數")
            raise ValueError("參數優化失敗")
        
        return best_params, best_result
    
    async def validate_parameters(
        self,
        data: pd.DataFrame,
        window: WalkForwardWindow,
        params: Dict[str, Any]
    ) -> BacktestResult:
        """
        在測試期驗證參數
        
        Args:
            data: 完整數據
            window: 當前窗口
            params: 在訓練期優化的參數
        
        Returns:
            測試期回測結果
        """
        # 測試期數據
        test_data = data[
            (data['open_time'] >= window.test_start) &
            (data['open_time'] < window.test_end)
        ].copy()
        
        # 生成策略信號（使用訓練期優化的參數）
        signals = self.strategy_generator(test_data, params)
        
        # 回測
        result = await self._run_backtest(data, window.test_start, window.test_end, signals)
        
        logger.info(f"   ✅ 測試期 {self.config.optimization_metric}: {self._evaluate_result(result):.4f}")
        
        return result
    
    async def _run_backtest(
        self,
        data: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        signals: List[Dict]
    ) -> BacktestResult:
        """
        執行回測
        
        Args:
            data: 歷史數據
            start_date: 開始日期
            end_date: 結束日期
            signals: 策略信號
        
        Returns:
            回測結果
        """
        from schemas.enums import StrategyType, TimeFrame
        
        # 映射 interval 到TimeFrame 枚舉
        interval_map = {
            "1m": TimeFrame.MIN_1,
            "3m": TimeFrame.MIN_3,
            "5m": TimeFrame.MIN_5,
            "15m": TimeFrame.MIN_15,
            "30m": TimeFrame.MIN_30,
            "1h": TimeFrame.HOUR_1,
            "2h": TimeFrame.HOUR_2,
            "4h": TimeFrame.HOUR_4,
            "6h": TimeFrame.HOUR_6,
            "8h": TimeFrame.HOUR_8,
            "12h": TimeFrame.HOUR_12,
            "1d": TimeFrame.DAY_1,
            "3d": TimeFrame.DAY_3,
            "1w": TimeFrame.WEEK_1,
            "1M": TimeFrame.MONTH_1,
        }
        
        # 配置回測
        backtest_config = BacktestConfig(
            name=f"{self.config.name}_Backtest",
            description=f"Walk-Forward 回測 - {self.config.name}",
            symbols=[self.config.symbol],  # 轉換為列表
            strategy_type=StrategyType.QUANTITATIVE,  # 使用量化策略類型
            initial_capital=self.config.initial_capital,
            start_date=start_date,
            end_date=end_date,
            timeframe=interval_map.get(self.config.interval, TimeFrame.HOUR_1),
            max_drawdown_limit=Decimal(str(self.config.max_drawdown_pct / 100)),
            stop_loss_pct=None
        )
        
        # 執行回測
        backtest = HistoricalBacktest(backtest_config)
        
        # 過濾時間範圍內的數據
        period_data = data[
            (data['open_time'] >= start_date) &
            (data['open_time'] < end_date)
        ].copy()
        
        # 轉換信號為 DataFrame（BacktestEngine 需要）
        if signals:
            signals_df = pd.DataFrame({
                'timestamp': [s['timestamp'] for s in signals],
                'signal': [1 if s['action'] == 'BUY' else -1 for s in signals],
                'size': [1.0] * len(signals),  # 默認倉位大小
                'price': [0.0] * len(signals)  # 使用市價
            })
            signals_df = signals_df.set_index('timestamp')
        else:
            # 空信號
            signals_df = pd.DataFrame(columns=['signal', 'size', 'price'])
        
        result = await backtest.engine.run_backtest(period_data, signals_df)
        
        return result
    
    def _evaluate_result(self, result: BacktestResult) -> float:
        """
        評估回測結果
        
        Args:
            result: 回測結果
        
        Returns:
            評分（用於參數優化）
        """
        metric = self.config.optimization_metric
        
        if metric == "sharpe_ratio":
            return float(result.sharpe_ratio or 0)
        elif metric == "total_return":
            return float(result.total_return)
        elif metric == "win_rate":
            return float(result.win_rate)
        elif metric == "calmar_ratio":
            return float(result.calmar_ratio or 0)
        else:
            logger.warning(f"⚠️ 未知指標: {metric}，使用夏普比率")
            return float(result.sharpe_ratio or 0)
    
    async def run(self) -> WalkForwardResult:
        """
        執行完整的 Walk-Forward 測試
        
        Returns:
            總體測試結果
        """
        logger.info("="*60)
        logger.info("🚀 開始 Walk-Forward 測試")
        logger.info("="*60)
        logger.info(f"測試名稱: {self.config.name}")
        logger.info(f"交易對: {self.config.symbol}")
        logger.info(f"時間範圍: {self.config.start_date.date()} 到 {self.config.end_date.date()}")
        
        # 1. 載入完整歷史數據
        logger.info("\n📥 載入歷史數據...")
        data = await self.data_loader.load_data(
            symbol=self.config.symbol,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            interval=self.config.interval
        )
        logger.info(f"✅ 載入 {len(data)} 根 K 線")
        
        # 2. 生成窗口
        windows = self.generate_windows()
        
        if len(windows) == 0:
            logger.error("❌ 無法生成窗口，請檢查日期範圍和窗口配置")
            raise ValueError("無法生成滾動窗口")
        
        # 3. 對每個窗口執行訓練和測試
        window_results = []
        
        for i, window in enumerate(windows, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 窗口 {i}/{len(windows)}")
            logger.info(f"{'='*60}")
            logger.info(str(window))
            
            # 訓練期：優化參數
            logger.info(f"\n📚 訓練期 ({window.train_days} 天)")
            optimal_params, train_result = await self.optimize_parameters(data, window)
            
            # 測試期：驗證參數
            logger.info(f"\n🧪 測試期 ({window.test_days} 天)")
            test_result = await self.validate_parameters(data, window, optimal_params)
            
            # 保存結果
            window_result = WindowResult(
                window=window,
                train_result=train_result,
                test_result=test_result,
                optimal_params=optimal_params
            )
            window_results.append(window_result)
            
            # 輸出窗口總結
            logger.info(f"\n📊 窗口 {i} 總結:")
            logger.info(f"   訓練期夏普: {window_result.train_sharpe:.2f}")
            logger.info(f"   測試期夏普: {window_result.test_sharpe:.2f}")
            logger.info(f"   夏普衰減: {window_result.sharpe_degradation:.1f}%")
            logger.info(f"   過擬合: {'❌ 是' if window_result.is_overfitting else '✅ 否'}")
        
        # 4. 計算總體統計
        result = self._calculate_overall_results(window_results)
        
        # 5. 輸出最終報告
        self._print_final_report(result)
        
        return result
    
    def _calculate_overall_results(self, window_results: List[WindowResult]) -> WalkForwardResult:
        """計算總體統計指標"""
        train_sharpes = [wr.train_sharpe for wr in window_results]
        test_sharpes = [wr.test_sharpe for wr in window_results]
        
        train_returns = [float(wr.train_result.total_return_pct) for wr in window_results]
        test_returns = [float(wr.test_result.total_return_pct) for wr in window_results]
        
        overfitting_count = sum(1 for wr in window_results if wr.is_overfitting)
        
        # 穩健性評分（0-100）
        robustness_score = self._calculate_robustness_score(
            test_sharpes,
            overfitting_count,
            len(window_results)
        )
        
        result = WalkForwardResult(
            config=self.config,
            window_results=window_results,
            total_windows=len(window_results),
            overfitting_windows=overfitting_count,
            avg_train_sharpe=float(np.mean(train_sharpes)),
            avg_test_sharpe=float(np.mean(test_sharpes)),
            avg_sharpe_degradation=float(np.mean([wr.sharpe_degradation for wr in window_results])),
            avg_train_return=float(np.mean(train_returns)),
            avg_test_return=float(np.mean(test_returns)),
            sharpe_stability=float(np.std(test_sharpes)),
            return_stability=float(np.std(test_returns)),
            is_robust=robustness_score >= 60,
            robustness_score=robustness_score
        )
        
        return result
    
    def _calculate_robustness_score(
        self,
        test_sharpes: List[float],
        overfitting_count: int,
        total_windows: int
    ) -> float:
        """
        計算策略穩健性評分（0-100）
        
        考慮因素：
        1. 平均測試期夏普（40%）
        2. 夏普穩定性（30%）
        3. 非過擬合率（30%）
        """
        # 1. 平均夏普評分（0-40）
        avg_sharpe = np.mean(test_sharpes)
        sharpe_score = min(avg_sharpe * 20, 40)  # 夏普 2.0 -> 40 分
        
        # 2. 穩定性評分（0-30）
        sharpe_std = np.std(test_sharpes)
        stability_score = max(0, 30 - sharpe_std * 15)  # 標準差低於 2 -> 滿分
        
        # 3. 非過擬合率評分（0-30）
        non_overfitting_rate = 1 - (overfitting_count / total_windows)
        overfitting_score = non_overfitting_rate * 30
        
        total_score = sharpe_score + stability_score + overfitting_score
        
        return float(total_score)
    
    def _print_final_report(self, result: WalkForwardResult):
        """輸出最終報告"""
        logger.info("\n" + "="*60)
        logger.info("📊 Walk-Forward 測試最終報告")
        logger.info("="*60)
        logger.info(f"測試名稱: {self.config.name}")
        logger.info(f"交易對: {self.config.symbol}")
        logger.info(f"總窗口數: {result.total_windows}")
        logger.info("-"*60)
        logger.info("訓練期表現:")
        logger.info(f"  平均夏普: {result.avg_train_sharpe:.2f}")
        logger.info(f"  平均收益率: {result.avg_train_return:.2f}%")
        logger.info("-"*60)
        logger.info("測試期表現:")
        logger.info(f"  平均夏普: {result.avg_test_sharpe:.2f}")
        logger.info(f"  平均收益率: {result.avg_test_return:.2f}%")
        logger.info(f"  夏普穩定性 (σ): {result.sharpe_stability:.2f}")
        logger.info(f"  收益率穩定性 (σ): {result.return_stability:.2f}%")
        logger.info("-"*60)
        logger.info("過擬合分析:")
        logger.info(f"  過擬合窗口: {result.overfitting_windows}/{result.total_windows}")
        logger.info(f"  過擬合率: {result.overfitting_rate:.1%}")
        logger.info(f"  平均夏普衰減: {result.avg_sharpe_degradation:.1f}%")
        logger.info("-"*60)
        logger.info("穩健性評估:")
        logger.info(f"  穩健性評分: {result.robustness_score:.1f}/100")
        logger.info(f"  策略穩健: {'✅ 是' if result.is_robust else '❌ 否'}")
        logger.info("="*60)
        
        # 建議
        if result.is_robust:
            logger.info("✅ 策略通過 Walk-Forward 測試，建議進入實盤測試階段")
        else:
            logger.warning("⚠️ 策略未通過 Walk-Forward 測試，建議:")
            if result.overfitting_rate > 0.3:
                logger.warning("   - 降低模型複雜度，減少參數數量")
            if result.sharpe_stability > 1.0:
                logger.warning("   - 提高策略在不同市場環境下的適應性")
            if result.avg_test_sharpe < 1.0:
                logger.warning("   - 優化策略邏輯，提高風險調整後收益")


if __name__ == "__main__":
    """
    測試示例：簡單的 RSI 策略 Walk-Forward 測試
    """
    import asyncio
    
    def generate_simple_rsi_strategy(data: pd.DataFrame, params: Dict[str, Any]) -> List[Dict]:
        """生成簡單 RSI 策略信號（示例）"""
        # 默認參數
        period = params.get('rsi_period', 14)
        oversold = params.get('rsi_oversold', 30)
        overbought = params.get('rsi_overbought', 70)
        
        # 計算 RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # 生成信號
        signals = []
        position = None
        
        for i in range(period, len(data)):
            if rsi.iloc[i] < oversold and position is None:
                signals.append({
                    'timestamp': data['open_time'].iloc[i],
                    'action': 'BUY',
                    'confidence': 0.8
                })
                position = 'long'
            elif rsi.iloc[i] > overbought and position == 'long':
                signals.append({
                    'timestamp': data['open_time'].iloc[i],
                    'action': 'SELL',
                    'confidence': 0.8
                })
                position = None
        
        return signals
    
    async def main():
        # 配置
        config = WalkForwardConfig(
            name="RSI Strategy WF Test",
            symbol="BTCUSDT",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 6, 30),
            train_window_days=60,
            test_window_days=30,
            step_days=30,
            param_grid={
                'rsi_period': [10, 14, 20],
                'rsi_oversold': [25, 30, 35],
                'rsi_overbought': [65, 70, 75]
            },
            optimization_metric="sharpe_ratio"
        )
        
        # 執行測試
        tester = WalkForwardTester(config, generate_simple_rsi_strategy)
        result = await tester.run()
        
        print("\n✅ 測試完成！")
        print(f"穩健性評分: {result.robustness_score:.1f}/100")
    
    asyncio.run(main())
