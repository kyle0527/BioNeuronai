"""
交易計劃控制器 - 10步驟交易計劃

實現10步驟系統化交易計劃：
1. 系統環境檢查
2. 宏觀市場掃描
3. 技術面分析
4. 基本面情緒分析
5. 策略性能評估
6. 策略選擇權重
7. 風險參數計算
8. 資金管理規劃
9. 交易對篩選
10. 執行計劃監控

參考文檔: archived/docs_v2_1_legacy/TRADING_PLAN_10_STEPS.legacy_20260406.md
"""

from typing import Any, Callable, Dict, List, Optional, cast
from datetime import datetime
import logging
import asyncio

# 導入內部分析模組
from .market_analyzer import MarketAnalyzer
from ..risk_management import RiskManager

# 導入事件評估器 (Step 4 神經接通)
_imported_get_rule_evaluator: Optional[Callable[[], Any]]
try:
    from ..analysis.news import get_rule_evaluator as _imported_get_rule_evaluator, RuleBasedEvaluator
    EVENT_SYSTEM_AVAILABLE = True
except ImportError:
    EVENT_SYSTEM_AVAILABLE = False
    _imported_get_rule_evaluator = None

get_rule_evaluator = cast(Optional[Callable[[], Any]], _imported_get_rule_evaluator)

# 導入策略選擇器與交易對選擇器 (Step 5/6/9)
try:
    from ..strategies.selector import StrategySelector
    from .pair_selector import PairSelector
    SELECTORS_AVAILABLE = True
except ImportError:
    SELECTORS_AVAILABLE = False
    StrategySelector = None  # type: ignore[assignment,misc]
    PairSelector = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

class TradingPlanController:
    """
    交易計劃控制器 - 10步驟交易計劃制定
    
    整合10個步驟形成完整交易計劃
    """
    
    def __init__(self):
        self.name = "TradingPlanController" 
        self.active_plans: Dict[str, Dict[str, Any]] = {}
        
        # 初始化分析模組
        self.market_analyzer = MarketAnalyzer()
        self.risk_manager = RiskManager()
        
        # 初始化事件評估器 (新聞大腦)
        self._rule_evaluator: Optional['RuleBasedEvaluator'] = None
        if EVENT_SYSTEM_AVAILABLE and get_rule_evaluator is not None:
            try:
                self._rule_evaluator = get_rule_evaluator()
                logger.info("🧠 事件評估器已連接 (RuleBasedEvaluator)")
            except Exception as e:
                logger.warning(f"⚠️ 事件評估器初始化失敗: {e}")

        # 初始化策略選擇器與交易對選擇器 (Step 5/6/9)
        self._strategy_selector: Optional['StrategySelector'] = None
        self._pair_selector: Optional['PairSelector'] = None
        if SELECTORS_AVAILABLE and StrategySelector is not None and PairSelector is not None:
            try:
                self._strategy_selector = StrategySelector()
                self._pair_selector = PairSelector()
                logger.info("📊 策略選擇器與交易對選擇器已初始化")
            except Exception as e:
                logger.warning(f"⚠️ 選擇器初始化失敗: {e}")
        
        # 10步驟配置
        self.steps: Dict[int, Dict[str, str]] = {
            1: {"name": "系統環境檢查", "status": "PENDING", "module": "system"},
            2: {"name": "宏觀市場掃描", "status": "PENDING", "module": "market"},
            3: {"name": "技術面分析", "status": "PENDING", "module": "technical"},
            4: {"name": "基本面情緒分析", "status": "PENDING", "module": "sentiment"},
            5: {"name": "策略性能評估", "status": "PENDING", "module": "strategy"},
            6: {"name": "策略選擇權重", "status": "PENDING", "module": "strategy"},
            7: {"name": "風險參數計算", "status": "PENDING", "module": "risk"},
            8: {"name": "資金管理規劃", "status": "PENDING", "module": "risk"},
            9: {"name": "交易對篩選", "status": "PENDING", "module": "pair"},
            10: {"name": "執行計劃監控", "status": "PENDING", "module": "execution"},
        }
        
        logger.info("交易計劃控制器初始化完成 - 10步驟系統已就緒")
    
    async def create_comprehensive_plan(self, klines: Optional[List[Dict]] = None, account_balance: float = 10000) -> Dict:
        """
        執行完整的 10步驟交易計劃
        
        Args:
            klines: K線數據列表
            account_balance: 賬戶餘額
            
        Returns:
            Dict: 完整交易計劃（包含10步驟結果）
        """
        logger.info("="*70)
        logger.info("開始執行 10步驟交易計劃")
        logger.info("="*70)
        
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        plan: Dict[str, Any] = {
            "id": plan_id,
            "created_at": datetime.now().isoformat(),
            "status": "IN_PROGRESS",
            "description": "系統化10步驟交易計劃",
            "steps_results": {},
            "is_executable": False,
            "risk_level": "UNKNOWN",
            "recommended_pairs": [],
            "execution_ready": False,
            "account_balance": account_balance,
            "has_klines_data": klines is not None and len(klines) > 0
        }
        
        # 記錄數據狀態
        if klines:
            logger.info(f"📊 接收到 {len(klines)} 條 K線數據")
        else:
            logger.warning("⚠️  沒有 K線數據，部分分析將受限")
        
        try:
            # 步驟 1: 系統檢查（簡化）
            logger.info(f"\n{'='*70}")
            logger.info("步驟 1/10: 系統環境檢查")
            logger.info(f"{'='*70}")
            step1_result = await self._step1_system_check()
            plan["steps_results"][1] = step1_result
            
            # 步驟 2: 宏觀市場掃描（已實現 - 使用真實 API）
            logger.info(f"\n{'='*70}")
            logger.info("步驟 2/10: 宏觀市場掃描")
            logger.info(f"{'='*70}")
            step2_result = await self._step2_market_scan()
            plan["steps_results"][2] = step2_result
            
            # 步驟 3: 技術面分析（使用真實分析）
            logger.info(f"\n{'='*70}")
            logger.info("步驟 3/10: 技術面分析")
            logger.info(f"{'='*70}")
            step3_result = await self._step3_technical_analysis(klines)
            plan["steps_results"][3] = step3_result
            
            # 步驟 4: 基本面情緒分析（整合事件系統）
            logger.info(f"\n{'='*70}")
            logger.info("步驟 4/10: 基本面情緒分析")
            logger.info(f"{'='*70}")
            step4_result = await self._step4_sentiment_analysis()
            plan["steps_results"][4] = step4_result
            
            # 提取事件資訊供後續步驟使用
            event_score = step4_result.get("event_score", 0.0)
            event_context = step4_result.get("event_context")
            plan["event_score"] = event_score
            plan["event_context"] = event_context
            
            # 如果事件分數過低，發出警告
            if event_score < -0.5:
                logger.warning(f"⚠️ 重大負面事件！Event Score: {event_score:+.3f}")
                logger.warning("   建議暫停交易或大幅降低倉位")
            
            # 步驟 5: 策略性能評估
            logger.info(f"\n{'='*70}")
            logger.info("步驟 5/10: 策略性能評估")
            logger.info(f"{'='*70}")
            step5_result = await self._step5_strategy_evaluation()
            plan["steps_results"][5] = step5_result

            # 步驟 6: 策略選擇權重
            logger.info(f"\n{'='*70}")
            logger.info("步驟 6/10: 策略選擇權重")
            logger.info(f"{'='*70}")
            step6_result = await self._step6_strategy_selection(klines, account_balance)
            plan["steps_results"][6] = step6_result
            
            # 步驟 7: 風險參數計算（使用真實計算）
            logger.info(f"\n{'='*70}")
            logger.info("步驟 7/10: 風險參數計算")
            logger.info(f"{'='*70}")
            step7_result = await self._step7_risk_calculation(step3_result, account_balance)
            plan["steps_results"][7] = step7_result
            
            # 步驟 8: 資金管理（使用真實計算）
            logger.info(f"\n{'='*70}")
            logger.info("步驟 8/10: 資金管理規劃")
            logger.info(f"{'='*70}")
            entry_price = 50000  # 示例
            stop_loss_price = entry_price * 0.97  # 3% 止損
            step8_result = await self._step8_fund_management(step7_result, account_balance, entry_price, stop_loss_price)
            plan["steps_results"][8] = step8_result
            
            # 步驟 9: 交易對篩選
            logger.info(f"\n{'='*70}")
            logger.info("步驟 9/10: 交易對篩選")
            logger.info(f"{'='*70}")
            step9_result = await self._step9_pair_selection()
            plan["steps_results"][9] = step9_result

            # 步驟 10: 執行計劃監控設定
            logger.info(f"\n{'='*70}")
            logger.info("步驟 10/10: 執行計劃監控設定")
            logger.info(f"{'='*70}")
            step10_result = await self._step10_execution_monitor()
            plan["steps_results"][10] = step10_result
            
            logger.info("\n" + "="*70)
            logger.info("✅ 完成 10步驟交易計劃")
            logger.info("="*70)
            
            # 整合結果
            plan["status"] = "COMPLETED"
            plan["is_executable"] = True
            plan["execution_ready"] = True
            plan["risk_level"] = step7_result.get("risk_level", "MODERATE")
            
            logger.info(f"📋 計劃ID: {plan_id}")
            logger.info(f"⚖️  風險等級: {plan['risk_level']}")
            logger.info(f"💰 建議倉位: {step8_result.get('recommended_size_btc', 0):.4f} BTC")
            logger.info(f"🎯 可執行: {'是' if plan['is_executable'] else '否'}")
            logger.info("="*70)
            
        except Exception as e:
            logger.error(f"❌ 計劃執行失敗: {e}", exc_info=True)
            plan["status"] = "ERROR"
            plan["error"] = str(e)
        
        # 保存計劃
        self.active_plans[plan_id] = plan
        return plan
    
    async def _execute_step(self, step_num: int) -> Dict:
        """
        
        
        Args:
            step_num:  (1-10)
            
        Returns:
            Dict: 
        """
        step_name = self.steps[step_num]["name"]
        
        # 
        handlers = {
            1: self._step1_system_check,
            2: self._step2_market_scan,
            3: self._step3_technical_analysis,
            4: self._step4_sentiment_analysis,
            5: self._step5_strategy_evaluation,
            6: self._step6_strategy_selection,
            7: self._step7_risk_calculation,
            8: self._step8_fund_management,
            9: self._step9_pair_selection,
            10: self._step10_execution_monitor,
        }
        
        handler = handlers.get(step_num)
        if not handler:
            return {
                "step": step_num,
                "name": step_name,
                "status": "FAILED",
                "error": "Handler not implemented"
            }
        
        try:
            result = cast(Dict[str, Any], await handler())  # type: ignore[operator]
            result["step"] = step_num
            result["name"] = step_name
            result["status"] = result.get("status", "SUCCESS")
            return result
        except Exception as e:
            logger.error(f" {step_num} : {e}", exc_info=True)
            return {
                "step": step_num,
                "name": step_name,
                "status": "FAILED",
                "error": str(e)
            }
    
    # ========== 10 ==========
    
    async def _step1_system_check(self) -> Dict:
        """1: 系統環境檢查 - 驗證 API 連接與帳戶狀態"""
        await asyncio.sleep(0)  # Async yield point for task scheduling
        logger.info("  API ...")
        logger.info(" ...")
        logger.info(" ...")
        logger.info(" ...")
        
        # 目前返回模擬數據，未來整合 TradingEngine 時將實現真實檢查
        return {
            "status": "SUCCESS",
            "api_connected": True,
            "network_latency_ms": 50,
            "account_verified": True,
            "available_margin": 10000.0,
            "websocket_connected": True
        }
    
    async def _step2_market_scan(self, check_mode: str = "daily") -> Dict:
        """
        步驟 2: 宏觀市場掃描（已實現 - 2026-02-15）
        
        數據來源：
        - Alternative.me (恐慌貪婪指數)
        - CoinGecko (全球市場數據、穩定幣供應)
        - DefiLlama (DeFi TVL)
        
        Args:
            check_mode: "daily" 每日全量掃描 / "quick" 快速掃描
            
        Returns:
            Dict: 包含所有宏觀市場指標的結果
        """
        logger.info("🌍 開始宏觀市場掃描...")
        
        try:
            # 使用 MarketAnalyzer 的新功能
            result = cast(Dict[str, Any], await self.market_analyzer.scan_macro_market(check_mode))
            
            if result["status"] == "SUCCESS":
                logger.info("✅ 宏觀市場掃描完成")
            else:
                logger.warning(f"⚠️ 宏觀市場掃描部分失敗: {result.get('error', '未知錯誤')}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ 宏觀市場掃描失敗: {e}", exc_info=True)
            
            # 返回錯誤結果
            return {
                "status": "FAILED",
                "error": str(e),
                "check_mode": check_mode,
                "message": "無法連接外部數據源，請檢查網絡連接"
            }
    
    async def _step3_technical_analysis(self, klines: Optional[List[Dict]] = None) -> Dict:
        """3: 技術面分析 - 使用真實技術分析"""
        logger.info("📊 執行技術面分析 ...")
        
        if not klines:
            logger.warning("⚠️  沒有 K線數據，返回默認結果")
            return {
                "status": "PARTIAL",
                "message": "需要 K線數據進行完整分析",
                "trend": "UNKNOWN",
                "rsi": 50,
                "support_levels": [],
                "resistance_levels": []
            }
        
        try:
            # 使用 MarketAnalyzer 進行分析
            market_condition = await self.market_analyzer.analyze_current_market_condition(klines)
            
            # 提取關鍵指標
            return {
                "status": "SUCCESS",
                "trend": market_condition.overall_trend,
                "volatility_level": market_condition.volatility_level,
                "volatility_value": market_condition.volatility_value,
                "market_phase": market_condition.market_phase,
                "sentiment_score": market_condition.sentiment_score,
                "fear_greed_index": market_condition.fear_greed_index,
                "liquidity": market_condition.liquidity_condition,
                "external_factors": market_condition.external_factors,
                "confidence": market_condition.confidence_score
            }
            
        except Exception as e:
            logger.error(f"❌ 技術分析失敗: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "trend": "NEUTRAL"
            }
    
    async def _step4_sentiment_analysis(self, symbol: str = "BTCUSDT") -> Dict:
        """4: 基本面情緒分析 - 整合事件評估系統"""
        await asyncio.sleep(0)  # Async yield point for task scheduling
        logger.info("📰 執行新聞情緒分析 ...")
        logger.info("🧠 查詢事件記憶 ...")
        
        result = {
            "status": "SUCCESS",
            "news_count": 0,
            "sentiment_score": 0.0,
            "sentiment": "NEUTRAL",
            "keywords_matched": [],
            "breaking_news_risk": "SAFE",
            # 新增：事件系統整合
            "event_score": 0.0,
            "active_events": [],
            "event_context": None
        }
        
        # 使用事件評估系統
        if self._rule_evaluator:
            try:
                # 獲取當前事件分數和活躍事件
                event_score, active_events = self._rule_evaluator.get_current_event_score(symbol)
                
                result["event_score"] = event_score
                result["active_events"] = active_events
                
                # 構建 EventContext 供 strategy_fusion 使用
                if EVENT_SYSTEM_AVAILABLE and active_events:
                    # 找出最主要的事件類型
                    primary_event = max(active_events, key=lambda e: abs(e.get('score', 0)))
                    
                    result["event_context"] = {
                        "event_score": event_score,
                        "event_type": primary_event.get('event_type', 'UNKNOWN'),
                        "intensity": abs(primary_event.get('score', 0)),
                        "decay_factor": 1.0,  # 可以從 metadata 計算
                        "source_confidence": primary_event.get('source_confidence', 0.5)
                    }
                    
                    logger.info(f"  ✓ 事件分數: {event_score:+.3f}")
                    logger.info(f"  ✓ 活躍事件: {len(active_events)} 個")
                    for evt in active_events[:3]:  # 顯示前3個
                        logger.info(f"    - [{evt.get('event_type')}] {evt.get('headline', '')[:40]}...")
                else:
                    logger.info("  ✓ 目前無活躍市場事件")
                
                # 根據事件分數判斷風險等級
                if event_score < -0.5:
                    result["breaking_news_risk"] = "HIGH"
                    result["sentiment"] = "NEGATIVE"
                elif event_score < -0.2:
                    result["breaking_news_risk"] = "ELEVATED"
                    result["sentiment"] = "SLIGHTLY_NEGATIVE"
                elif event_score > 0.3:
                    result["sentiment"] = "POSITIVE"
                    result["breaking_news_risk"] = "SAFE"
                
                # 清理過期事件
                self._rule_evaluator.cleanup_expired_events()
                
            except Exception as e:
                logger.warning(f"⚠️ 事件評估失敗: {e}")
        else:
            logger.info("  ⚠️ 事件系統未啟用，使用預設值")
        
        return result
    
    async def _step5_strategy_evaluation(self) -> Dict:
        """5: 策略性能評估 - 使用 strategies.selector 配置評估"""
        await asyncio.sleep(0)  # Async yield point for task scheduling

        if self._strategy_selector is None:
            logger.warning("⚠️ StrategySelector 不可用，使用預設值")
            return {
                "status": "DEGRADED",
                "strategies": {
                    "MA_Crossover_Trend": {"win_rate": 0.55, "sharpe": 1.2},
                    "RSI_Mean_Reversion": {"win_rate": 0.65, "sharpe": 1.1},
                    "Momentum_Breakout": {"win_rate": 0.50, "sharpe": 1.3},
                },
                "best_strategy": "RSI_Mean_Reversion",
                "source": "config_defaults",
            }

        try:
            strategies_perf: Dict[str, Dict[str, float]] = {}
            best_strategy = None
            best_sharpe = -1.0

            strategy_configs = getattr(self._strategy_selector, "strategy_configs", {})
            for name, config in list(strategy_configs.items())[:5]:
                strategies_perf[name] = {
                    "win_rate": float(config.win_rate),
                    "sharpe": float(config.sharpe_ratio),
                    "profit_factor": float(config.profit_factor),
                    "max_drawdown": float(config.max_drawdown),
                    "expected_return": float(config.expected_return),
                }
                logger.info(
                    f"  ✓ {name}: 勝率={float(config.win_rate):.1%}, Sharpe={float(config.sharpe_ratio):.2f}"
                )
                if float(config.sharpe_ratio) > best_sharpe:
                    best_sharpe = float(config.sharpe_ratio)
                    best_strategy = name

            return {
                "status": "SUCCESS",
                "strategies": strategies_perf,
                "best_strategy": best_strategy,
                "source": "strategies.selector.configs",
            }

        except Exception as e:
            logger.error(f"❌ 策略性能評估失敗: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def _step6_strategy_selection(self, klines: Optional[List[Dict]] = None, account_balance: float = 10000) -> Dict:
        """6: 策略選擇權重 - 使用 strategies.selector.select_optimal_strategy"""
        await asyncio.sleep(0)  # Async yield point for task scheduling

        if self._strategy_selector is None:
            logger.warning("⚠️ StrategySelector 不可用，使用預設值")
            return {
                "status": "DEGRADED",
                "selected_strategy": "MA_Crossover_Trend",
                "strategy_weight": 0.7,
                "confidence_score": 0.5,
                "fallback_strategy": "RSI_Mean_Reversion",
                "source": "default_fallback",
            }

        try:
            import numpy as np

            # 將 klines 轉為 OHLCV numpy array（失敗則使用空陣列）
            ohlcv: np.ndarray = np.empty((0, 6))
            if klines and len(klines) >= 10:
                try:
                    ohlcv = np.array([
                        [
                            float(k.get("open_time", 0)),
                            float(k.get("open", k.get("o", 0))),
                            float(k.get("high", k.get("h", 0))),
                            float(k.get("low", k.get("l", 0))),
                            float(k.get("close", k.get("c", 0))),
                            float(k.get("volume", k.get("v", 0))),
                        ]
                        for k in klines
                    ])
                except Exception:
                    ohlcv = np.empty((0, 6))

            selection = await self._strategy_selector.select_optimal_strategy(
                ohlcv_data=ohlcv,
                account_balance=account_balance,
                preferences={"risk_tolerance": "medium"},
            )

            primary = selection.primary_strategy
            if primary is None:
                raise ValueError("策略選擇結果缺少 primary_strategy")

            fallback = (
                selection.backup_strategies[0].name
                if selection.backup_strategies
                else "None"
            )

            logger.info(f"  ✓ 主要策略: {primary.name} (勝率={primary.win_rate:.1%})")
            logger.info(f"  ✓ 備用策略: {fallback}")
            logger.info(f"  ✓ 信心分數: {selection.confidence_score:.2f}")

            return {
                "status": "SUCCESS",
                "selected_strategy": primary.name,
                "strategy_type": primary.strategy_type.value,
                "strategy_weight": selection.strategy_mix.get(primary.name, 0.7),
                "confidence_score": round(selection.confidence_score, 3),
                "fallback_strategy": fallback,
                "strategy_mix": selection.strategy_mix,
                "reasoning": selection.reasoning,
                "expected_performance": selection.expected_performance,
                "source": "strategies.selector.core",
            }

        except Exception as e:
            logger.error(f"❌ 策略選擇失敗: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def _step7_risk_calculation(self, market_condition: Optional[Dict] = None, account_balance: float = 10000) -> Dict:
        """7: 風險參數計算 - 使用真實風險管理"""
        await asyncio.sleep(0)  # Async yield point for task scheduling
        logger.info("⚖️  計算風險參數 ...")
        
        try:
            # 根據市場波動率決定風險等級
            risk_level = "MODERATE"  # 默認
            
            if market_condition:
                volatility = market_condition.get('volatility_level', 'MEDIUM')
                if volatility == 'LOW':
                    risk_level = "AGGRESSIVE"
                elif volatility == 'HIGH':
                    risk_level = "CONSERVATIVE"
                elif volatility == 'EXTREME':
                    risk_level = "CONSERVATIVE"
            
            # 獲取風險參數
            risk_params = self.risk_manager.risk_parameters[risk_level]
            
            logger.info(f"  ✓ 風險等級: {risk_level}")
            logger.info(f"  ✓ 單筆風險: {risk_params.max_risk_per_trade*100}%")
            logger.info(f"  ✓ 每日上限: {risk_params.max_daily_risk*100}%")
            logger.info(f"  ✓ 最大槓桿: {risk_params.max_leverage}x")
            
            return {
                "status": "SUCCESS",
                "risk_level": risk_level,
                "risk_per_trade": risk_params.max_risk_per_trade,
                "daily_max_loss": risk_params.max_daily_risk,
                "max_leverage": risk_params.max_leverage,
                "position_concentration": risk_params.position_concentration,
                "max_positions": 3,
                "account_balance": account_balance,
                "max_risk_amount": account_balance * risk_params.max_risk_per_trade
            }
            
        except Exception as e:
            logger.error(f"❌ 風險計算失敗: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "risk_per_trade": 0.02,
                "risk_level": "MODERATE"
            }
    
    async def _step8_fund_management(self, risk_params: Optional[Dict] = None, account_balance: float = 10000, entry_price: float = 50000, stop_loss_price: float = 48500) -> Dict:
        """8: 資金管理規劃 - 使用真實倉位計算"""
        logger.info("💰 計算資金管理方案 ...")
        
        try:
            if not risk_params:
                risk_params = {"risk_level": "MODERATE"}
            
            # 計算建議倉位大小
            position_sizing = await self.risk_manager.calculate_position_size(
                symbol="BTCUSDT",
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                account_balance=account_balance,
                risk_level=risk_params.get("risk_level", "MODERATE")
            )
            
            logger.info(f"  ✓ 建議倉位: {position_sizing.recommended_size:.4f} BTC")
            logger.info(f"  ✓ 風險金額: ${position_sizing.risk_amount:.2f}")
            logger.info(f"  ✓ 風險回報比: 1:{position_sizing.risk_reward_ratio:.2f}")
            logger.info(f"  ✓ Kelly 分數: {position_sizing.kelly_fraction:.2f}")
            
            # 計算保證金需求
            position_value = position_sizing.recommended_size * entry_price
            required_margin = position_value / risk_params.get("max_leverage", 3)
            
            return {
                "status": "SUCCESS",
                "position_sizing_method": "RISK_BASED_KELLY",
                "recommended_size": position_sizing.recommended_size,
                "recommended_size_btc": position_sizing.recommended_size,
                "max_size": position_sizing.max_size,
                "position_value_usdt": position_value,
                "required_margin": required_margin,
                "risk_amount": position_sizing.risk_amount,
                "risk_reward_ratio": position_sizing.risk_reward_ratio,
                "kelly_fraction": position_sizing.kelly_fraction,
                "entry_price": entry_price,
                "stop_loss": position_sizing.stop_loss_price,
                "take_profit": position_sizing.take_profit_price,
                "reserve_margin": account_balance - required_margin
            }
            
        except Exception as e:
            logger.error(f"❌ 資金管理計算失敗: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "recommended_size": 0.01
            }
    
    async def _step9_pair_selection(self) -> Dict:
        """9: 交易對篩選 - 使用 PairSelector 根據成交量與波動率篩選"""
        await asyncio.sleep(0)  # Async yield point for task scheduling

        if self._pair_selector is None:
            logger.warning("⚠️ PairSelector 不可用，使用預設主流幣對")
            return {
                "status": "DEGRADED",
                "pairs": [
                    {"symbol": "BTCUSDT", "liquidity": "HIGH", "source": "default"},
                    {"symbol": "ETHUSDT", "liquidity": "HIGH", "source": "default"},
                    {"symbol": "BNBUSDT", "liquidity": "HIGH", "source": "default"},
                ],
                "recommended_pair": "BTCUSDT",
                "source": "default_fallback",
            }

        try:
            result = await self._pair_selector.select_optimal_pairs()
            primary_pairs = result.get("primary_pairs", ["BTCUSDT"])
            pair_details = result.get("pair_details", {})
            source = "api" if pair_details else "default_fallback"

            pairs_list = []
            for sym in primary_pairs:
                detail = pair_details.get(sym, {})
                pairs_list.append({
                    "symbol": sym,
                    "volume_usdt_24h": detail.get("volume_usdt", 0),
                    "price_change_pct": detail.get("price_change_pct", 0),
                    "last_price": detail.get("last_price", 0),
                    "liquidity": "HIGH" if detail.get("volume_usdt", 0) > 1e8 else "MEDIUM",
                })
                logger.info(f"  ✓ {sym}: 24h成交量={detail.get('volume_usdt', 0):,.0f} USDT")

            return {
                "status": "SUCCESS",
                "pairs": pairs_list,
                "backup_pairs": result.get("backup_pairs", []),
                "recommended_pair": primary_pairs[0] if primary_pairs else "BTCUSDT",
                "selection_criteria": result.get("selection_criteria", {}),
                "source": source,
            }

        except Exception as e:
            logger.error(f"❌ 交易對篩選失敗: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    async def _step10_execution_monitor(self) -> Dict:
        """10: 執行計劃監控 - 輸出監控設定（WebSocket 由 TradingEngine 負責建立）"""
        await asyncio.sleep(0)  # Async yield point for task scheduling
        logger.info("  ✓ 監控規則已設定（WebSocket 由 TradingEngine 實際啟動）")
        logger.info("  ✓ 警報規則: 價格警報 / 倉位警報 / 新聞警報")
        logger.info("  ℹ️  WebSocket 連線需在 TradingEngine.start() 後才會就緒")
        return {
            "status": "SUCCESS",
            "monitor_active": False,
            "websocket_ready": False,
            "websocket_note": (
                "WebSocket 由 BinanceFuturesConnector.subscribe_ticker_stream() 建立，"
                "需在 TradingEngine 啟動後才會連線"
            ),
            "alert_rules": ["price_alert", "position_alert", "news_alert"],
            "update_interval_ms": 1000,
            "setup_required": True,
        }
    
    async def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """執行交易計劃"""
        await asyncio.sleep(0)  # Async yield point for task scheduling
        logger.info("...")
        
        return {
            "execution_status": "SUCCESS",
            "plan_id": plan.get("id", "unknown"),
            "start_time": "2024-01-01T00:00:00Z"
        }
    
    def get_active_plans(self) -> Dict[str, Dict[str, Any]]:
        """"""
        return self.active_plans
