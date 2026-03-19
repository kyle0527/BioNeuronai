"""
每日報告模組
============

自動生成每日開盤前市場分析報告

主要功能：
1. 市場環境掃描
2. 新聞與情緒分析
3. 交易策略建議
4. 風險參數計算
5. 交易對篩選

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import io
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

# 2. 本地模組 - 資料模型
from .models import (
    MarketEnvironmentCheck,
    TradingPlanCheck,
    MarketCondition,
    StrategyPerformance,
    RiskParameters,
    TradingPairsPriority,
    DailyReport
)

# 3. 本地模組 - 功能模組
from .market_data import MarketDataCollector
from .news_sentiment import NewsSentimentAnalyzer
from .strategy_planner import StrategyPlanner
from .risk_manager import RiskManager
from .report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class SOPAutomationSystem:
    """
    SOP 自動化系統 - 主控制器
    
    整合所有子模組，提供完整的每日市場分析報告功能
    """
    
    def __init__(self):
        """初始化系統及所有子模組"""
        # 初始化子模組
        self.market_data_collector = MarketDataCollector()
        self.news_sentiment_analyzer = None  # 稍後初始化
        self.strategy_planner = StrategyPlanner()
        self.risk_manager = RiskManager()
        self.report_generator = ReportGenerator()
        
        # 系統狀態
        self.modules_available = False
        
        # 嘗試導入相關模組
        self._import_modules()
    
    def _import_modules(self):
        """導入所需模組"""
        try:
            from ..news import CryptoNewsAnalyzer
            
            # 初始化共享的新聞分析器實例
            news_analyzer = CryptoNewsAnalyzer()
            self.news_sentiment_analyzer = NewsSentimentAnalyzer(news_analyzer)
            
            self.modules_available = True
            logger.info("[OK] 所有分析模組導入成功（含共享新聞分析器）")
        except ImportError as e:
            logger.warning(f"[WARN] 部分模組不可用: {e}")
            # 使用 Mock 數據作為後備
            self.news_sentiment_analyzer = NewsSentimentAnalyzer(None)
            self.modules_available = False
    
    # ========================================
    # 主要執行流程
    # ========================================
    
    def execute_daily_premarket_check(self) -> Dict[str, Any]:
        """
        執行每日開盤前分析報告
        
        Returns:
            完整的分析報告字典
        """
        logger.info("📊 [START] 開始生成每日市場分析報告...")
        
        start_time = datetime.now()
        results = {
            "report_time": start_time,
            "report_version": "2.0",
            "report_type": "每日開盤前分析報告"
        }
        
        # Step 1: 市場環境分析
        logger.info("🌍 Step 1/2: 市場環境與情緒分析")
        market_check = self._check_market_environment()
        results["market_environment"] = self._dataclass_to_dict(market_check)
        
        # Step 2: 交易計劃建議
        logger.info("📝 Step 2/2: 交易計劃與策略建議")
        plan_check = self._prepare_trading_plan()
        results["trading_plan"] = self._dataclass_to_dict(plan_check)
        
        # 綜合評估
        overall_assessment = self._assess_overall_readiness(market_check, plan_check)
        results["overall_assessment"] = overall_assessment
        
        # 保存結果
        self.report_generator.save_check_results(results)
        
        completion_time = datetime.now()
        duration = (completion_time - start_time).total_seconds()
        
        logger.info(f"✅ [OK] 報告生成完成 | 耗時: {duration:.1f}秒")
        logger.info(f"🎯 市場評估: {overall_assessment['market_condition']}")
        logger.info(f"💡 交易建議: {overall_assessment['recommendation']}")
        
        return results
    
    # ========================================
    # Step 1: 市場環境檢查
    # ========================================
    
    def _check_market_environment(self) -> MarketEnvironmentCheck:
        """檢查市場環境"""
        check = MarketEnvironmentCheck(timestamp=datetime.now())
        
        try:
            # 1. 全球市場動態檢查
            logger.info("   📈 檢查全球市場動態...")
            market_data = self.market_data_collector.get_global_market_data()
            
            if market_data:
                check.us_futures = market_data.get('us_futures', 'UNKNOWN')
                check.asian_markets = market_data.get('asian_markets', 'UNKNOWN')
                check.european_markets = market_data.get('european_markets', 'UNKNOWN')
                logger.info(f"     ✓ 美股期貨: {check.us_futures}")
                logger.info(f"     ✓ 亞洲市場: {check.asian_markets}")
                logger.info(f"     ✓ 歐洲市場: {check.european_markets}")
            else:
                logger.warning("   [WARN] 無法獲取全球市場數據")
            
            # 2. 經濟數據檢查
            logger.info("   📅 檢查重要經濟數據...")
            economic_events = self.market_data_collector.check_economic_calendar()
            check.economic_events = economic_events or []
            logger.info(f"     ✓ 今日重要事件: {len(check.economic_events)} 項")
            
            # 3. AI 新聞分析
            logger.info("   📰 執行 AI 新聞分析...")
            news_analysis = None
            if self.news_sentiment_analyzer:
                news_analysis = self.news_sentiment_analyzer.perform_ai_news_analysis("BTCUSDT", 24)
            check.news_analysis = news_analysis
            
            if news_analysis:
                sentiment_score = news_analysis.get('sentiment_score', 0.0)
                check.crypto_sentiment = sentiment_score
                
                logger.info(f"     ✓ 整體情緒: {sentiment_score:.2f}")
                logger.info(f"     ✓ 新聞數量: {news_analysis.get('news_count', 0)}")
                
                # 檢查重大事件
                major_events = news_analysis.get('major_events', [])
                for event in major_events:
                    event_type = event.get('type', '')
                    logger.info(f"     🚨 重大事件: {event_type} - {event.get('description', '')}")
            else:
                logger.warning("   [WARN] 新聞分析暫時不可用")
            
            # 4. 綜合評估市場環境
            if self.news_sentiment_analyzer:
                check.overall_status = self.news_sentiment_analyzer.assess_market_status_from_news(
                    news_analysis
                )
            else:
                check.overall_status = "UNKNOWN"
            
        except Exception as e:
            logger.error(f"   [ERROR] 市場環境檢查失敗: {e}")
            check.overall_status = "ERROR"
        
        return check
    
    # ========================================
    # Step 2: 交易計劃準備
    # ========================================
    
    def _prepare_trading_plan(self) -> TradingPlanCheck:
        """制定交易計劃（20步驟詳細版）"""
        check = TradingPlanCheck(timestamp=datetime.now())
        
        try:
            logger.info("   📝 開始制定詳細交易計劃...")
            
            # ========== 第一階段：策略分析與選擇 (步驟1-6) ==========
            
            # 步驟1-2: 市場分析與策略評估
            logger.info("   [INFO] 步驟1-2/20: 市場分析與策略評估...")
            market_condition = self.strategy_planner.analyze_current_market_condition()
            strategy_performance = self.strategy_planner.evaluate_strategy_performance()
            logger.info(f"     ✓ 市場: {market_condition.condition} | 最佳策略: {strategy_performance.best_strategy}")
            
            # 步驟3-4: 策略匹配與參數配置
            logger.info("   📊 步驟3-4/20: 策略匹配與參數配置...")
            strategy_match = self.strategy_planner.match_strategy_to_market(market_condition)
            self.strategy_planner.configure_strategy_parameters(
                strategy_match["recommended"]
            )
            logger.info(f"     ✓ 推薦策略: {strategy_match['recommended']} (匹配度: {strategy_match['match_score']}/10)")
            
            # 步驟5-6: 驗證與最終選擇
            logger.info("   ✅ 步驟5-6/20: 策略驗證與最終選擇...")
            suitability = self.strategy_planner.verify_strategy_suitability(
                strategy_match, market_condition
            )
            final_strategy = self.strategy_planner.finalize_strategy_selection(
                strategy_match, suitability
            )
            check.selected_strategy = final_strategy["name"]
            logger.info(f"     ✓ 最終策略: {final_strategy['name']} (信心: {final_strategy['confidence']:.0%})")
            
            # ========== 第二階段：風險管理與資金配置 (步驟7-12) ==========
            
            # 步驟7-8: 帳戶分析與風險參數
            logger.info("   💰 步驟7-8/20: 帳戶分析與風險參數...")
            account_analysis = self.risk_manager.analyze_account_funds()
            base_risk = self.risk_manager.calculate_base_risk_parameters(account_analysis)
            logger.info(f"     ✓ 可用資金: ${account_analysis['available']:.2f}")
            
            # 步驟9-10: 波動率調整與持倉管理
            logger.info("   📉 步驟9-10/20: 波動率調整與持倉管理...")
            volatility_adjusted_risk = self.risk_manager.adjust_risk_for_volatility(
                base_risk, market_condition
            )
            position_rules = self.risk_manager.configure_position_management(
                volatility_adjusted_risk.get("max_positions", 3)
            )
            logger.info(f"     ✓ 單筆風險: {volatility_adjusted_risk['single_trade']:.1f}%")
            
            # 步驟11-12: 交易頻率與風險整合
            logger.info("   🔄 步驟11-12/20: 交易頻率與風險整合...")
            frequency_limits = self.risk_manager.calculate_trading_frequency(
                market_condition
            )
            integrated_risk = self.risk_manager.integrate_risk_parameters(
                volatility_adjusted_risk, position_rules, frequency_limits
            )
            check.risk_parameters = self._dataclass_to_dict(integrated_risk)
            logger.info(f"     ✓ 每日交易上限: {integrated_risk.max_daily_trades} 次")
            
            # ========== 第三階段：交易對篩選與優化 (步驟13-17) ==========
            
            # 步驟13-15: 交易對掃描與分析
            logger.info("   🎯 步驟13-15/20: 交易對掃描與分析...")
            available_pairs = self.risk_manager.scan_available_trading_pairs()
            liquidity_analysis = self.risk_manager.analyze_liquidity_metrics(available_pairs)
            volatility_match = self.risk_manager.check_volatility_compatibility(
                liquidity_analysis
            )
            logger.info(f"     ✓ 可用交易對: {available_pairs.get('total_count', 0)} 個")
            
            # 步驟16-17: 風險過濾與優先級排序
            logger.info("   🔍 步驟16-17/20: 風險過濾與優先級排序...")
            risk_filtered = self.risk_manager.apply_risk_filters(volatility_match, integrated_risk)
            prioritized_pairs = self.risk_manager.prioritize_trading_pairs(risk_filtered)
            check.trading_pairs = prioritized_pairs.primary + prioritized_pairs.backup
            logger.info(f"     ✓ 主要交易對: {', '.join(prioritized_pairs.primary)}")
            
            # ========== 第四階段：回測驗證與最終確認 (步驟18-20) ==========
            
            # 步驟18: 執行回測驗證
            logger.info("   📊 步驟18/20: 執行回測驗證...")
            backtest_results = self.strategy_planner.perform_plan_backtest()
            
            # 步驟19: 計算每日限制
            logger.info("   💵 步驟19/20: 計算每日限制...")
            daily_limits = self.risk_manager.calculate_comprehensive_daily_limits(
                account_analysis, integrated_risk
            )
            check.daily_limits = daily_limits
            logger.info(f"     ✓ 每日最大虧損: ${daily_limits['max_loss_usd']:.2f}")
            
            # 步驟20: 最終驗證
            logger.info("   [OK] 步驟20/20: 最終計劃驗證與確認...")
            final_validation = self._perform_final_plan_validation(
                backtest_results, final_strategy, suitability
            )
            check.overall_status = final_validation['status']
            
            logger.info(f"     ✓ 計劃評分: {final_validation['score']:.1f}/10")
            logger.info(f"     ✓ 驗證狀態: {final_validation['status']}")
            
        except Exception as e:
            logger.error(f"   [ERROR] 交易計劃制定失敗: {e}")
            check.overall_status = "ERROR"
        
        return check
    
    # ========================================
    # 綜合評估
    # ========================================
    
    def _assess_overall_readiness(
        self, 
        market: MarketEnvironmentCheck, 
        plan: TradingPlanCheck
    ) -> Dict[str, Any]:
        """評估整體市場與計劃狀況"""
        
        # 檢查關鍵指標
        market_ok = market.overall_status in ["BULLISH", "NEUTRAL", "BEARISH"]
        plan_ok = plan.overall_status in ["READY", "APPROVED"]
        
        # 判斷市場狀況
        if market.overall_status == "BULLISH":
            market_condition = "看漲 (BULLISH)"
        elif market.overall_status == "BEARISH":
            market_condition = "看跌 (BEARISH)"
        else:
            market_condition = "中性 (NEUTRAL)"
        
        # 生成建議
        if market_ok and plan_ok:
            recommendation = "✅ 市場狀況良好，交易計劃完整，可考慮執行交易"
        elif plan_ok:
            recommendation = "⚠️ 交易計劃就緒，但需密切關注市場變化"
        else:
            recommendation = "⛔ 建議暫緩交易，等待更好時機"
        
        return {
            "market_condition": market_condition,
            "recommendation": recommendation,
            "market_status": market.overall_status,
            "plan_status": plan.overall_status,
            "crypto_sentiment": market.crypto_sentiment,
            "selected_strategy": plan.selected_strategy,
            "timestamp": datetime.now().isoformat()
        }
    
    def _perform_final_plan_validation(
        self, 
        backtest_results: Dict,
        final_strategy: Dict,
        suitability: Dict
    ) -> Dict[str, Any]:
        """最終計劃驗證與確認"""
        try:
            # 基於策略信心和適用性評分
            strategy_score = final_strategy.get("confidence", 0.5) * 10
            suitability_score = suitability.get("score", 5.0)
            
            # 綜合評分
            score = (strategy_score + suitability_score) / 2
            
            # 判斷狀態
            if score >= 8.0:
                status = "READY"
                risk_level = "LOW"
            elif score >= 6.5:
                status = "APPROVED"
                risk_level = "MEDIUM"
            elif score >= 5.0:
                status = "CAUTION"
                risk_level = "MEDIUM"
            else:
                status = "NOT_READY"
                risk_level = "HIGH"
            
            recommendations = []
            if backtest_results.get("status") == "NOT_IMPLEMENTED":
                recommendations.append("建議實現回測系統以提高決策準確度")
            if suitability.get("status") == "ACCEPTABLE":
                recommendations.append("市場適配度一般，建議謹慎執行")
            
            return {
                "score": round(score, 1),
                "status": status,
                "risk_level": risk_level,
                "recommendations": recommendations
            }
        except Exception as e:
            logger.error(f"最終驗證失敗: {e}")
            return {"score": 5.0, "status": "UNCERTAIN", "risk_level": "HIGH"}
    
    # ========================================
    # 技術分析（需要 K 棒資料）
    # ========================================

    def generate_technical_analysis(
        self,
        klines: list,
        symbol: str,
        current_price: float
    ) -> Dict[str, Any]:
        """
        執行技術分析：市場狀態偵測 + 成交量分布 + 市場微觀結構

        Args:
            klines: K 棒列表（物件需具備 close/high/low/volume/taker_buy_volume 屬性）
            symbol: 交易對符號（如 "BTCUSDT"）
            current_price: 當前價格

        Returns:
            包含各分析文字報告與特徵向量的字典
        """
        result: Dict[str, Any] = {}

        # ── 市場狀態偵測 ──
        try:
            from ..market_regime import MarketRegimeDetector, RegimeBasedStrategySelector

            detector = MarketRegimeDetector()
            for k in klines:
                if hasattr(k, 'close'):
                    c, h, l, v = k.close, k.high, k.low, k.volume
                else:
                    c = k.get('close', current_price)
                    h = k.get('high', current_price)
                    l = k.get('low', current_price)
                    v = k.get('volume', 0)
                detector.update_data(symbol, c, h, l, v)

            regime = detector.detect_regime(symbol)
            selector = RegimeBasedStrategySelector()
            rec = selector.get_strategy_recommendation(regime)

            result['regime_report'] = regime.to_prompt()
            result['regime_recommendation'] = rec
            result['regime_feature_vector'] = regime.to_feature_vector()

            logger.info(
                f"市場狀態: {regime.current_regime.value}, "
                f"信心: {regime.regime_confidence:.0%}"
            )
        except Exception as e:
            logger.error(f"市場狀態分析失敗: {e}")
            result['regime_report'] = f"市場狀態分析失敗: {e}"

        # ── 成交量分布 & 微觀結構 ──
        try:
            from ..feature_engineering import VolumeProfileCalculator, MarketDataProcessor

            vp_calc = VolumeProfileCalculator()
            vp = vp_calc.calculate_from_klines(klines)
            result['volume_profile_report'] = vp.to_prompt()
            logger.info(
                f"POC: {vp.poc_price:.2f}, "
                f"價值區: {vp.value_area_low:.2f}-{vp.value_area_high:.2f}"
            )

            processor = MarketDataProcessor()
            micro = processor.build_market_microstructure(symbol, current_price)
            result['microstructure_report'] = micro.to_prompt()
            result['microstructure_feature_vector'] = micro.to_feature_vector()

        except Exception as e:
            logger.error(f"特徵工程分析失敗: {e}")

        return result

    # ========================================
    # 完整報告輸出（整合所有分析模組）
    # ========================================

    def run_full_report(
        self,
        klines: Optional[List] = None,
        symbol: str = "BTCUSDT",
        current_price: float = 0.0
    ) -> str:
        """
        執行並印出完整分析報告

        整合所有分析子模組：
        1. 關鍵字系統統計（分類 / 權重 / 新聞分析示範）
        2. 技術分析（市場狀態 / 成交量分布 / 微觀結構）——需提供 klines
        3. 全球市場數據（Yahoo Finance / 恐慌貪婪指數）
        4. 每日開盤前完整報告（SOP 流程）

        Args:
            klines: K 棒列表（若提供則執行技術分析，屬性需含
                    close/high/low/volume/taker_buy_volume）
            symbol: 交易對符號，預設 "BTCUSDT"
            current_price: 當前價格；若未指定則自動從 klines 最後一根取得

        Returns:
            完整報告文字（同時在標準輸出列印）
        """
        SECTION = "=" * 64
        parts: List[str] = []

        def section(title: str) -> None:
            parts.append(f"\n{SECTION}")
            parts.append(f"  {title}")
            parts.append(SECTION)

        # ── 1. 關鍵字系統 ──
        section("【1/4】關鍵字系統報告")
        try:
            from ..keywords.manager import KeywordManager
            km = KeywordManager()

            buf = io.StringIO()
            old_stdout = sys.stdout
            try:
                sys.stdout = buf
                km.print_report()
            finally:
                sys.stdout = old_stdout
            parts.append(buf.getvalue())

        except Exception as e:
            logger.error(f"關鍵字系統報告失敗: {e}")
            parts.append(f"  [ERROR] 關鍵字系統: {e}")

        # ── 2. 技術分析 ──
        if klines:
            if not current_price:
                last = klines[-1]
                current_price = (
                    last.close if hasattr(last, 'close')
                    else last.get('close', 95_500.0)
                )
            section(f"【2/4】技術分析 ({symbol} | 當前價格: {current_price:,.0f})")
            tech = self.generate_technical_analysis(klines, symbol, current_price)

            labels = {
                'regime_report': '  ── 市場狀態 ──',
                'volume_profile_report': '  ── 成交量分布 ──',
                'microstructure_report': '  ── 市場微觀結構 ──',
            }
            for key, label in labels.items():
                if key in tech:
                    parts.append(f"\n{label}")
                    parts.append(tech[key])

            rec = tech.get('regime_recommendation', {})
            if rec:
                parts.append(
                    f"\n  建議策略: {rec.get('recommended_strategies', [])}\n"
                    f"  方向偏好: {rec.get('position_bias', 'N/A')}\n"
                    f"  倉位乘數: {rec.get('position_size_multiplier', 'N/A')}"
                )
        else:
            section("【2/4】技術分析（需提供 klines 參數）")
            parts.append(
                "  提示：呼叫 run_full_report(klines=[...]) 以啟用技術分析\n"
                "  K 棒物件需具備屬性：close / high / low / volume / taker_buy_volume"
            )

        # ── 3. 全球市場數據 ──
        section("【3/4】全球市場數據")
        try:
            data = self.market_data_collector.get_global_market_data()
            if data:
                stock = data.get('global_stock_indices', {})
                if stock:
                    parts.append("  全球股市:")
                    for name, info in stock.items():
                        chg = info.get('change_percent', 0)
                        arr = "🔺" if chg >= 0 else "🔻"
                        parts.append(
                            f"    {arr} {name:<12}: "
                            f"{info.get('price', 0):>10,.1f}  ({chg:+.2f}%)"
                        )

                fng = data.get('fear_greed_index', {})
                if fng:
                    parts.append(
                        f"\n  恐慌貪婪指數: "
                        f"{fng.get('value', 'N/A')} ({fng.get('label', 'N/A')})"
                    )

                crypto_an = data.get('crypto_analysis', {})
                if crypto_an:
                    parts.append(
                        f"  加密情緒  : {crypto_an.get('overall_crypto_sentiment', 'N/A')}\n"
                        f"  交易建議  : {crypto_an.get('recommendation', 'N/A')}"
                    )
            else:
                parts.append("  ❌ 無法獲取市場數據（可能無網路連線或 API 限速）")
        except Exception as e:
            logger.error(f"全球市場數據取得失敗: {e}")
            parts.append(f"  [ERROR] 全球市場數據: {e}")

        # ── 4. 每日開盤前報告 ──
        section("【4/4】每日開盤前市場分析報告（SOP 完整流程）")
        try:
            self.execute_daily_premarket_check()
            report_text = self.report_generator.generate_daily_report()
            parts.append(report_text)
        except Exception as e:
            logger.error(f"每日開盤前報告失敗: {e}")
            parts.append(f"  [ERROR] 每日報告: {e}")

        full_report = "\n".join(parts)
        print(full_report)
        return full_report

    # ========================================
    # 報告生成
    # ========================================

    def generate_daily_report(self) -> str:
        """生成每日報告文本"""
        return self.report_generator.generate_daily_report()
    
    # ========================================
    # 工具方法
    # ========================================
    
    def _dataclass_to_dict(self, obj) -> Dict:
        """將 dataclass 轉換為字典"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                elif hasattr(value, '__dataclass_fields__'):
                    result[field_name] = self._dataclass_to_dict(value)
                elif isinstance(value, list):
                    result[field_name] = [
                        self._dataclass_to_dict(item) if hasattr(item, '__dataclass_fields__') else item
                        for item in value
                    ]
                else:
                    result[field_name] = value
            return result
        return obj


# ========================================
# 模組導出
# ========================================

__all__ = [
    # 主控制器
    'SOPAutomationSystem',
    # 主控制器新增方法（對外可呼叫）
    # generate_technical_analysis / run_full_report 為 SOPAutomationSystem 的實例方法
    # 資料模型
    'MarketEnvironmentCheck',
    'TradingPlanCheck',
    'MarketCondition',
    'StrategyPerformance',
    'RiskParameters',
    'TradingPairsPriority',
    'DailyReport',
    # 功能模組
    'MarketDataCollector',
    'NewsSentimentAnalyzer',
    'StrategyPlanner',
    'RiskManager',
    'ReportGenerator',
]
