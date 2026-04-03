"""
風險管理器
==========

負責風險參數計算、交易對篩選、倉位管理

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import logging
import requests
from typing import Any, Dict, List, cast

# 2. 本地模組
from .models import DailyRiskLimits, TradingPairsPriority, DailyMarketCondition

logger = logging.getLogger(__name__)

# Binance Futures 公開 REST API（無需 API Key）
_BINANCE_FUTURES_API = "https://fapi.binance.com"

# 主流 USDT 永續合約（用於優先級排序）
_MAJOR_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
}


class RiskManager:
    """
    風險管理器

    功能：
    1. 帳戶資金分析（需 Binance connector）
    2. 計算基礎風險參數
    3. 根據波動率調整風險
    4. 配置持倉管理規則
    5. 計算交易頻率限制
    6. 交易對篩選與優先級排序（Binance 公開 API）
    """

    def __init__(self, connector: Any = None) -> None:
        # connector: BinanceFuturesConnector instance（可選，用於取得帳戶資料）
        self.connector = connector
        self.request_timeout: int = 10
        self.user_agent: str = "Mozilla/5.0"
        self.default_risk: Dict[str, Any] = {
            "single_trade": 1.0,  # 1%
            "daily_limit": 3.0,   # 3%
            "max_positions": 1
        }
    
    # ========================================
    # 帳戶分析
    # ========================================
    
    def analyze_account_funds(self) -> Dict[str, Any]:
        """
        分析帳戶資金狀況。

        使用 Binance /fapi/v2/account（需要已設定 API Key 的 connector）。
        若無有效連線，回傳錯誤狀態而非假數據。

        Returns:
            帳戶分析結果，含 available / total / in_use / risk_tolerance /
            max_position_size / leverage / error
        """
        try:
            if self.connector and getattr(self.connector, "api_key", ""):
                account = self.connector.get_account_info()
                if account:
                    total = float(account.get("totalWalletBalance", 0.0))
                    available = float(account.get("availableBalance", 0.0))
                    in_use = total - available
                    unrealized_pnl = float(account.get("totalUnrealizedProfit", 0.0))

                    # 根據可用餘額決定風險承受度
                    if available < 500:
                        risk_tolerance = "LOW"
                    elif available < 5000:
                        risk_tolerance = "MEDIUM"
                    else:
                        risk_tolerance = "HIGH"

                    # 單筆最大倉位：可用餘額的 10%
                    max_position_size = available * 0.1

                    logger.info(
                        f"帳戶資金: 可用=${available:.2f}, 總計=${total:.2f}, "
                        f"未實現盈虧=${unrealized_pnl:.2f}, 風險承受度={risk_tolerance}"
                    )
                    return {
                        "available": available,
                        "total": total,
                        "in_use": in_use,
                        "unrealized_pnl": unrealized_pnl,
                        "risk_tolerance": risk_tolerance,
                        "max_position_size": max_position_size,
                        "leverage": 1.0,
                        "error": None,
                    }

            # 無有效連線：回傳明確錯誤狀態，不使用假數據
            msg = "無 Binance API 連線，請設定 BINANCE_API_KEY / BINANCE_API_SECRET"
            logger.warning(f"帳戶資金分析：{msg}")
            return {
                "available": 0.0,
                "total": 0.0,
                "in_use": 0.0,
                "unrealized_pnl": 0.0,
                "risk_tolerance": "LOW",
                "max_position_size": 0.0,
                "leverage": 1.0,
                "error": msg,
            }

        except Exception as e:
            raise RuntimeError(f"帳戶資金分析失敗: {e}") from e
    
    # ========================================
    # 風險參數計算
    # ========================================
    
    def calculate_base_risk_parameters(self, account_analysis: Dict) -> Dict[str, Any]:
        """
        計算基礎風險參數
        
        Args:
            account_analysis: 帳戶分析結果
        
        Returns:
            基礎風險參數
        """
        try:
            risk_tolerance = account_analysis.get("risk_tolerance", "LOW")
            
            # 根據風險承受度調整參數
            risk_profiles = {
                "LOW": {
                    "single_trade": 1.0,
                    "daily_limit": 3.0,
                    "max_positions": 1
                },
                "MEDIUM": {
                    "single_trade": 2.0,
                    "daily_limit": 6.0,
                    "max_positions": 3
                },
                "HIGH": {
                    "single_trade": 3.0,
                    "daily_limit": 10.0,
                    "max_positions": 5
                }
            }
            
            return cast(Dict[str, Any], risk_profiles.get(risk_tolerance, self.default_risk))
            
        except Exception as e:
            raise RuntimeError(f"基礎風險參數計算失敗: {e}") from e
    
    def adjust_risk_for_volatility(
        self, 
        base_risk: Dict, 
        market_condition: DailyMarketCondition
    ) -> Dict[str, Any]:
        """
        根據市場波動調整風險
        
        Args:
            base_risk: 基礎風險參數
            market_condition: 市場狀況
        
        Returns:
            調整後的風險參數
        """
        try:
            volatility = market_condition.volatility
            
            # 波動率調整係數
            adjustment_factors = {
                "LOW": 1.2,      # 低波動可以增加風險
                "MEDIUM": 1.0,   # 正常波動
                "HIGH": 0.8,     # 高波動降低風險
                "EXTREME": 0.5   # 極端波動大幅降低
            }
            
            adjustment_factor = adjustment_factors.get(volatility, 1.0)
            
            return {
                "single_trade": base_risk["single_trade"] * adjustment_factor,
                "daily_limit": base_risk["daily_limit"] * adjustment_factor,
                "max_positions": base_risk.get("max_positions", 1),
                "adjustment_factor": adjustment_factor,
                "reason": f"市場波動率: {volatility}"
            }
        except Exception as e:
            raise RuntimeError(f"風險波動調整失敗: {e}") from e
    
    # ========================================
    # 持倉管理
    # ========================================
    
    def configure_position_management(self, max_positions: int = 3) -> Dict[str, Any]:
        """
        配置持倉管理規則
        
        Args:
            max_positions: 最大持倉數
        
        Returns:
            持倉管理配置
        """
        try:
            return {
                "max_positions": max_positions,
                "correlation_limit": 0.7,  # 相關性上限
                "position_sizing": "EQUAL_WEIGHT",  # 等權重
                "rebalance_threshold": 0.1,  # 重平衡閾值 10%
                "stop_loss_multiplier": 1.0,
                "take_profit_multiplier": 2.0
            }
        except Exception as e:
            raise RuntimeError(f"持倉管理配置失敗: {e}") from e
    
    def calculate_trading_frequency(
        self, 
        market_condition: DailyMarketCondition
    ) -> Dict[str, Any]:
        """
        計算交易頻率限制
        
        Args:
            market_condition: 市場狀況
        
        Returns:
            交易頻率限制
        """
        try:
            # 根據市場狀況調整頻率
            if market_condition.volatility in ["HIGH", "EXTREME"]:
                daily_max = 3
                interval_minutes = 60
            elif market_condition.volatility == "MEDIUM":
                daily_max = 5
                interval_minutes = 30
            else:
                daily_max = 8
                interval_minutes = 15
            
            return {
                "daily_max": daily_max,
                "interval_minutes": interval_minutes,
                "cooling_period": 60,  # 冷卻期（分鐘）
                "max_consecutive_losses": 3  # 連續虧損上限
            }
        except Exception as e:
            raise RuntimeError(f"交易頻率計算失敗: {e}") from e
    
    def integrate_risk_parameters(
        self, 
        volatility_adjusted_risk: Dict, 
        position_rules: Dict, 
        frequency_limits: Dict
    ) -> DailyRiskLimits:
        """
        整合風險參數
        
        Args:
            volatility_adjusted_risk: 波動率調整後的風險
            position_rules: 持倉規則
            frequency_limits: 頻率限制
        
        Returns:
            DailyRiskLimits 實例
        """
        try:
            return DailyRiskLimits(
                single_trade_risk=volatility_adjusted_risk.get("single_trade", 1.0),
                daily_max_loss=volatility_adjusted_risk.get("daily_limit", 3.0),
                max_positions=position_rules.get("max_positions", 1),
                max_daily_trades=frequency_limits.get("daily_max", 3),
                adjustment_factor=volatility_adjusted_risk.get("adjustment_factor", 1.0)
            )
        except Exception as e:
            raise RuntimeError(f"風險參數整合失敗: {e}") from e
    
    # ========================================
    # 交易對篩選
    # ========================================
    
    def scan_available_trading_pairs(self) -> Dict[str, Any]:
        """
        從 Binance 掃描所有可用的 USDT 永續合約。

        端點：GET /fapi/v1/exchangeInfo（公開，無需 API Key）
        過濾條件：contractType == PERPETUAL，status == TRADING，quoteAsset == USDT

        Returns:
            分類的交易對列表
        """
        try:
            url = f"{_BINANCE_FUTURES_API}/fapi/v1/exchangeInfo"
            response = requests.get(
                url,
                timeout=self.request_timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            data = response.json()

            all_pairs: List[str] = []
            for sym in data.get("symbols", []):
                if (
                    sym.get("contractType") == "PERPETUAL"
                    and sym.get("status") == "TRADING"
                    and sym.get("quoteAsset") == "USDT"
                ):
                    all_pairs.append(sym["symbol"])

            major = [p for p in all_pairs if p in _MAJOR_SYMBOLS]
            altcoins = [p for p in all_pairs if p not in _MAJOR_SYMBOLS]

            logger.info(
                f"交易對掃描完成：共 {len(all_pairs)} 個 USDT 永續合約"
                f"（主流 {len(major)}，山寨 {len(altcoins)}）"
            )
            return {
                "all": all_pairs,
                "major": major,
                "altcoins": altcoins,
                "total_count": len(all_pairs),
                "error": None,
            }

        except Exception as e:
            raise RuntimeError(f"交易對掃描失敗: {e}") from e
    
    def analyze_liquidity_metrics(self, available_pairs: Dict) -> Dict[str, Any]:
        """
        從 Binance 取得 24 小時成交量並分析流動性。

        端點：GET /fapi/v1/ticker/24hr（公開，無需 API Key）
        分級標準（以 USDT 計價日成交量）：
          高流動性：≥ 10 億 USDT
          中流動性：≥ 1 億 USDT
          低流動性：< 1 億 USDT

        Args:
            available_pairs: scan_available_trading_pairs() 的回傳值

        Returns:
            流動性分析結果
        """
        try:
            url = f"{_BINANCE_FUTURES_API}/fapi/v1/ticker/24hr"
            response = requests.get(
                url,
                timeout=self.request_timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            tickers = response.json()

            # 建立成交量與價差映射
            volume_map: Dict[str, float] = {}
            spread_map: Dict[str, float] = {}
            for t in tickers:
                sym: str = t.get("symbol", "")
                if not sym.endswith("USDT"):
                    continue
                quote_vol = float(t.get("quoteVolume", 0.0))
                high_price = float(t.get("highPrice", 0.0))
                low_price = float(t.get("lowPrice", 0.0))
                spread_pct = (
                    (high_price - low_price) / low_price * 100
                    if low_price > 0 else 0.0
                )
                volume_map[sym] = quote_vol
                spread_map[sym] = round(spread_pct, 4)

            # 依照 available_pairs 的清單分類流動性
            all_pairs: List[str] = available_pairs.get("all", list(volume_map.keys()))
            high_liq: List[str] = []
            medium_liq: List[str] = []
            low_liq: List[str] = []

            for sym in all_pairs:
                vol = volume_map.get(sym, 0.0)
                if vol >= 1_000_000_000:     # ≥ 10 億 USDT/天
                    high_liq.append(sym)
                elif vol >= 100_000_000:     # ≥ 1 億 USDT/天
                    medium_liq.append(sym)
                else:
                    low_liq.append(sym)

            # 按成交量由大到小排序
            high_liq.sort(key=lambda s: volume_map.get(s, 0.0), reverse=True)
            medium_liq.sort(key=lambda s: volume_map.get(s, 0.0), reverse=True)

            avg_spread = (
                sum(spread_map.values()) / len(spread_map) if spread_map else 0.0
            )

            logger.info(
                f"流動性分析完成：高={len(high_liq)}, 中={len(medium_liq)}, 低={len(low_liq)}"
                f"，平均波幅={avg_spread:.4f}%"
            )
            return {
                "high_liquidity": high_liq,
                "medium_liquidity": medium_liq,
                "low_liquidity": low_liq,
                "avg_spread": round(avg_spread, 4),
                "volume_24h": volume_map,
                "error": None,
            }

        except Exception as e:
            raise RuntimeError(f"流動性分析失敗: {e}") from e
    
    def check_volatility_compatibility(
        self, 
        liquidity_analysis: Dict
    ) -> Dict[str, Any]:
        """
        檢查波動率適配性
        
        Args:
            liquidity_analysis: 流動性分析
        
        Returns:
            波動率適配結果
        """
        try:
            high_liquidity_pairs = liquidity_analysis.get("high_liquidity", [])
            
            return {
                "compatible": high_liquidity_pairs,
                "incompatible": [],
                "best_match": high_liquidity_pairs[0] if high_liquidity_pairs else "BTCUSDT",
                "volatility_range": "MEDIUM_TO_HIGH"
            }
        except Exception as e:
            raise RuntimeError(f"波動率適配性檢查失敗: {e}") from e
    
    def apply_risk_filters(
        self, 
        volatility_match: Dict, 
        integrated_risk: DailyRiskLimits
    ) -> Dict[str, Any]:
        """
        應用風險過濾器
        
        Args:
            volatility_match: 波動率匹配結果
            integrated_risk: 整合風險參數
        
        Returns:
            過濾後的交易對
        """
        try:
            compatible_pairs = volatility_match.get("compatible", [])
            
            # 根據風險參數過濾
            if integrated_risk.single_trade_risk < 1.5:
                approved = [p for p in compatible_pairs if p in ["BTCUSDT", "ETHUSDT"]]
            else:
                approved = compatible_pairs
            
            excluded = [p for p in compatible_pairs if p not in approved]
            
            return {
                "approved": approved,
                "excluded": excluded,
                "reason": f"風險級別: {integrated_risk.single_trade_risk:.1f}%"
            }
        except Exception as e:
            raise RuntimeError(f"風險過濾失敗: {e}") from e
    
    def prioritize_trading_pairs(self, risk_filtered: Dict) -> TradingPairsPriority:
        """
        生成交易對優先級清單
        
        Args:
            risk_filtered: 風險過濾結果
        
        Returns:
            TradingPairsPriority 實例
        """
        try:
            approved = risk_filtered.get("approved", [])
            excluded = risk_filtered.get("excluded", [])
            
            # 優先級排序：BTC > ETH > 其他
            priority_order = ["BTCUSDT", "ETHUSDT"]
            
            primary = []
            backup = []
            
            for pair in approved:
                if pair in priority_order:
                    primary.append(pair)
                else:
                    backup.append(pair)
            
            # 確保順序
            primary.sort(key=lambda x: priority_order.index(x) if x in priority_order else 999)
            
            return TradingPairsPriority(
                primary=primary[:3],  # 最多3個主要交易對
                backup=backup[:2],    # 最多2個備用交易對
                excluded=excluded
            )
        except Exception as e:
            raise RuntimeError(f"交易對優先級排序失敗: {e}") from e
    
    # ========================================
    # 每日限制計算
    # ========================================
    
    def calculate_comprehensive_daily_limits(
        self, 
        account_analysis: Dict, 
        integrated_risk: DailyRiskLimits
    ) -> Dict[str, Any]:
        """
        計算每日交易限制
        
        Args:
            account_analysis: 帳戶分析
            integrated_risk: 整合風險參數
        
        Returns:
            每日限制配置
        """
        try:
            account_balance = account_analysis.get("available", 1000.0)
            max_daily_loss_pct = integrated_risk.daily_max_loss / 100
            single_trade_risk_pct = integrated_risk.single_trade_risk / 100
            
            return {
                "max_loss_usd": round(account_balance * max_daily_loss_pct, 2),
                "max_single_trade_usd": round(account_balance * single_trade_risk_pct, 2),
                "max_trades": integrated_risk.max_daily_trades,
                "max_positions": integrated_risk.max_positions,
                "daily_reset_time": "00:00 UTC"
            }
        except Exception as e:
            raise RuntimeError(f"每日限制計算失敗: {e}") from e
