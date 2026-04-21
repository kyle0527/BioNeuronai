"""
報告生成器
==========

負責生成每日市場分析報告的文本輸出

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, cast

# 2. 本地模組

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    報告生成器
    
    功能：
    1. 生成每日報告文本
    2. 保存報告為 JSON
    3. 提供報告摘要
    """
    
    def __init__(
        self,
        data_dir: str = "sop_automation_data",
        knowledge_base: Optional[Any] = None,
        kb_storage_path: Optional[str] = None,
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._knowledge_base = knowledge_base
        self._kb_storage_path = kb_storage_path
    
    # ========================================
    # 報告生成
    # ========================================
    
    def generate_daily_report(self) -> str:
        """
        生成每日市場分析報告
        
        Returns:
            格式化的報告文本
        """
        try:
            latest_result = self._get_latest_check_result()
            
            if not latest_result:
                return "❌ 無法找到最新的檢查結果，請先執行 execute_daily_premarket_check()"
            
            check_time = latest_result.get('report_time', datetime.now().isoformat())
            if isinstance(check_time, str):
                check_time = datetime.fromisoformat(check_time).strftime("%Y-%m-%d %H:%M:%S")
            
            # 構建報告
            report = self._build_report_text(latest_result, check_time)
            
            return report
            
        except Exception as e:
            raise RuntimeError(f"生成報告失敗: {e}") from e
    
    def _build_report_text(self, result: Dict, check_time: str) -> str:
        """構建報告文本"""
        market_env = result.get('market_environment', {})
        trading_plan = result.get('trading_plan', {})
        overall = result.get('overall_assessment', {})
        
        report = f"""
{'='*60}
🎯 每日開盤前市場分析報告
{'='*60}
📅 報告時間: {check_time}
📋 報告版本: {result.get('report_version', 'Unknown')}

{'='*60}
📊 市場環境分析
{'='*60}
整體狀態: {market_env.get('overall_status', 'UNKNOWN')}
加密情緒: {self._format_sentiment(market_env.get('crypto_sentiment'))}

全球市場:
  • 美股期貨: {market_env.get('us_futures', 'N/A')}
  • 歐洲市場: {market_env.get('european_markets', 'N/A')}
  • 亞洲市場: {market_env.get('asian_markets', 'N/A')}

重要事件: {len(market_env.get('economic_events', []))} 項
{self._format_economic_events(market_env.get('economic_events', []))}

新聞分析:
{self._format_news_analysis(market_env.get('news_analysis', {}))}

{'='*60}
📝 交易計劃建議
{'='*60}
計劃狀態: {trading_plan.get('overall_status', 'UNKNOWN')}
選定策略: {trading_plan.get('selected_strategy', 'N/A')}

風險參數:
{self._format_risk_parameters(trading_plan.get('risk_parameters', {}))}

交易標的 ({len(trading_plan.get('trading_pairs', []))} 個):
{self._format_trading_pairs(trading_plan.get('trading_pairs', []))}

每日限制:
{self._format_daily_limits(trading_plan.get('daily_limits', {}))}

{'='*60}
🎯 綜合評估
{'='*60}
市場狀況: {overall.get('market_condition', 'UNKNOWN')}
計劃狀態: {overall.get('plan_status', 'UNKNOWN')}

💡 交易建議:
{overall.get('recommendation', '無建議')}

{'='*60}
"""
        return report
    
    # ========================================
    # 格式化輔助方法
    # ========================================
    
    def _format_sentiment(self, sentiment: Optional[float]) -> str:
        """格式化情緒評分"""
        if sentiment is None:
            return "N/A"
        
        if sentiment > 0.3:
            emoji = "📈"
            label = "看漲"
        elif sentiment < -0.3:
            emoji = "📉"
            label = "看跌"
        else:
            emoji = "➡️"
            label = "中性"
        
        return f"{emoji} {sentiment:.2f} ({label})"
    
    def _format_economic_events(self, events: list) -> str:
        """格式化經濟事件"""
        if not events:
            return "  無重要事件"
        
        return "\n".join([f"  • {event}" for event in events[:3]])
    
    def _format_news_analysis(self, news: Dict) -> str:
        """格式化新聞分析"""
        if not news:
            return "  ⚠️ 新聞分析暫不可用"
        
        sentiment = news.get('sentiment', 'neutral')
        score = news.get('sentiment_score', 0.0)
        count = news.get('news_count', 0)
        
        return f"""  情緒: {sentiment.upper()} ({score:+.2f})
  新聞數: {count} 篇
  正面: {news.get('positive_count', 0)} | 負面: {news.get('negative_count', 0)}"""
    
    def _format_risk_parameters(self, risk: Dict) -> str:
        """格式化風險參數"""
        if not risk:
            return "  N/A"
        
        return f"""  單筆風險: {risk.get('single_trade_risk', 0):.1f}%
  每日上限: {risk.get('daily_max_loss', 0):.1f}%
  最大倉位: {risk.get('max_positions', 0)}
  每日交易: {risk.get('max_daily_trades', 0)} 次"""
    
    def _format_trading_pairs(self, pairs: list) -> str:
        """格式化交易對"""
        if not pairs:
            return "  無推薦交易對"
        
        return "  " + ", ".join(pairs)
    
    def _format_daily_limits(self, limits: Dict) -> str:
        """格式化每日限制"""
        if not limits:
            return "  N/A"
        
        return f"""  最大虧損: ${limits.get('max_loss_usd', 0):.2f}
  單筆上限: ${limits.get('max_single_trade_usd', 0):.2f}
  交易次數: {limits.get('max_trades', 0)}"""
    
    # ========================================
    # 數據保存
    # ========================================
    
    def save_check_results(self, results: Dict) -> Dict[str, Any]:
        """
        保存檢查結果為 JSON
        
        Args:
            results: 檢查結果字典
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sop_check_{timestamp}.json"
            filepath = self.data_dir / filename
            
            # 轉換為可序列化格式
            serializable_results = self._convert_to_serializable(results)
            kb_status = self._write_market_analysis_to_knowledge_base(
                serializable_results,
                filepath,
            )
            serializable_results["report_storage"] = {"json_path": str(filepath)}
            serializable_results["knowledge_base_writeback"] = kb_status
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 檢查結果已保存: {filepath}")
            return {
                "file_path": str(filepath),
                "knowledge_base": kb_status,
            }
            
        except Exception as e:
            raise RuntimeError(f"保存檢查結果失敗: {e}") from e

    def _ensure_knowledge_base(self) -> Optional[Any]:
        """確保 InternalKnowledgeBase 已初始化。"""
        if self._knowledge_base is not None:
            return self._knowledge_base

        try:
            from rag.internal import InternalKnowledgeBase  # noqa: PLC0415

            storage_path = self._kb_storage_path
            if not storage_path:
                project_root = Path(__file__).parent.parent.parent.parent.parent
                storage_path = str(project_root / "data" / "bioneuronai" / "rag" / "internal")

            self._knowledge_base = InternalKnowledgeBase(
                storage_path=storage_path,
                auto_load=True,
                use_faiss=False,
            )
            logger.info("✅ Daily report InternalKnowledgeBase 已初始化")
        except Exception as exc:
            logger.warning(f"Daily report 知識庫初始化失敗: {exc}")
            self._knowledge_base = None

        return self._knowledge_base

    def _write_market_analysis_to_knowledge_base(
        self,
        results: Dict[str, Any],
        filepath: Path,
    ) -> Dict[str, Any]:
        """將每日報告分析結果寫回 RAG 知識庫。"""
        knowledge_base = self._ensure_knowledge_base()
        if knowledge_base is None:
            return {
                "status": "ERROR",
                "document_id": None,
                "message": "InternalKnowledgeBase 不可用",
            }

        try:
            from rag.internal.knowledge_base import DocumentType  # noqa: PLC0415

            report_time = self._normalize_report_time(results.get("report_time"))
            report_time_text = report_time.strftime("%Y-%m-%d %H:%M:%S")
            report_text = self._build_report_text(results, report_time_text)
            document_id = self._build_market_analysis_doc_id(results, filepath)

            market_env = results.get("market_environment", {})
            trading_plan = results.get("trading_plan", {})
            overall = results.get("overall_assessment", {})
            trading_pairs = trading_plan.get("trading_pairs", []) or []

            knowledge_base.add_document(
                doc_id=document_id,
                title=f"Daily Market Report {report_time_text}",
                content=report_text,
                doc_type=DocumentType.MARKET_ANALYSIS,
                tags=[
                    "daily_report",
                    "market_analysis",
                    str(market_env.get("overall_status", "unknown")).lower(),
                    str(overall.get("plan_status", "unknown")).lower(),
                ],
                metadata={
                    "report_time": report_time.isoformat(),
                    "report_version": results.get("report_version", "Unknown"),
                    "report_type": results.get("report_type", "daily_report"),
                    "json_path": str(filepath),
                    "market_condition": overall.get("market_condition", "UNKNOWN"),
                    "plan_status": overall.get("plan_status", "UNKNOWN"),
                    "crypto_sentiment": market_env.get("crypto_sentiment"),
                    "selected_strategy": trading_plan.get("selected_strategy"),
                    "trading_pairs": trading_pairs,
                    "trading_pair_count": len(trading_pairs),
                },
                update_index=True,
            )
            knowledge_base.save_to_storage()
            return {
                "status": "OK",
                "document_id": document_id,
                "message": "每日報告已寫入知識庫",
            }
        except Exception as exc:
            logger.error(f"每日報告知識庫寫入失敗: {exc}")
            return {
                "status": "ERROR",
                "document_id": None,
                "message": str(exc),
            }

    @staticmethod
    def _normalize_report_time(value: Any) -> datetime:
        """將報告時間標準化為 datetime。"""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.now()
        return datetime.now()

    def _build_market_analysis_doc_id(self, results: Dict[str, Any], filepath: Path) -> str:
        """建立穩定的 daily report 文檔 ID，避免重複漂移。"""
        report_time = self._normalize_report_time(results.get("report_time"))
        raw = "|".join(
            [
                report_time.isoformat(),
                str(results.get("report_version", "")),
                filepath.stem,
            ]
        )
        digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]
        return f"market_analysis_{report_time.strftime('%Y%m%d_%H%M%S')}_{digest}"
    
    def _convert_to_serializable(self, obj):
        """
        轉換物件為可序列化格式
        
        Args:
            obj: 任意物件
        
        Returns:
            可序列化的物件
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._convert_to_serializable(obj.__dict__)
        else:
            return obj
    
    def _get_latest_check_result(self) -> Optional[Dict[str, Any]]:
        """
        獲取最新檢查結果
        
        Returns:
            最新的檢查結果字典
        """
        try:
            check_files = list(self.data_dir.glob("sop_check_*.json"))
            if not check_files:
                return None
            
            latest_file = max(check_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return cast(Dict[str, Any], json.load(f))
                
        except Exception as e:
            raise RuntimeError(f"讀取檢查結果失敗: {e}") from e
    
    # ========================================
    # 報告摘要
    # ========================================
    
    def generate_summary(self, results: Dict) -> str:
        """
        生成報告摘要
        
        Args:
            results: 檢查結果
        
        Returns:
            簡短的摘要文本
        """
        try:
            overall = results.get('overall_assessment', {})
            market_env = results.get('market_environment', {})
            
            status_emoji = "✅" if overall.get('market_condition') == "看漲 (BULLISH)" else "⚠️"
            
            summary = f"""
{status_emoji} 市場狀況: {overall.get('market_condition', 'UNKNOWN')}
💡 建議: {overall.get('recommendation', '無建議')[:50]}...
📊 情緒: {market_env.get('crypto_sentiment', 0.0):.2f}
"""
            return summary.strip()
            
        except Exception as e:
            raise RuntimeError(f"生成摘要失敗: {e}") from e
