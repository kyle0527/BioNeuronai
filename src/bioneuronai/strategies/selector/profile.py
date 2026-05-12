"""
BioNeuronAI Golden Strategy Profile Manager
===========================================

負責處理「整合後策略」的持久化與載入。
核心理念：將回測優化後的「最優策略配置」固化為一個 Golden Profile，
確保實盤執行時使用的是經過驗證的完整融合體系。

設計架構：
1. Metadata: 追蹤版本、日期與回測績效基準。
2. Strategy Weights: 按 StrategyType.value 聚合後的歸一化權重。
3. Template Rankings: 原始模板排行榜（用於審計追蹤）。
4. Regime Overrides: 不同市場體制下的策略優先級覆寫。
5. Risk Configuration: 經過優化後的風險參數。

關鍵設計決策：
- 路徑錨定至 PROJECT_ROOT，確保回測保存與實盤載入路徑一致。
- 權重 key 使用 StrategyType.value（如 "trend_following"），
  與 StrategySelector._calculate_strategy_weights 的 blend 邏輯對齊。
- 多個模板若屬同一 StrategyType，其回測績效會被聚合。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# 錨定到專案根目錄，確保無論 CWD 為何都能找到同一個檔案
# profile.py 位於 src/bioneuronai/strategies/selector/，5 層 parent = 專案根目錄
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_PROFILE_PATH = _PROJECT_ROOT / "config" / "golden_strategy_profile.json"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class GoldenStrategyProfile:
    """整合後的黃金策略配置檔

    所有欄位以 dict 形式儲存，便於 JSON 序列化/反序列化，
    避免 dataclass + from_dict 在欄位變動時崩潰。
    """

    # 必要欄位名稱（用於驗證）
    _REQUIRED_KEYS = {"version", "strategy_weights"}

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        d = data or {}
        # ── Metadata ──
        self.version: str = d.get("version", "2.2.0")
        self.generated_at: str = d.get("generated_at", datetime.now().isoformat())
        self.backtest_period: str = d.get("backtest_period", "unknown")
        self.symbol: str = d.get("symbol", "BTCUSDT")
        self.interval: str = d.get("interval", "1h")

        # ── 總體績效基準 ──
        self.total_return_pct: float = _safe_float(d.get("total_return_pct"))
        self.sharpe_ratio: float = _safe_float(d.get("sharpe_ratio"))
        self.max_drawdown: float = _safe_float(d.get("max_drawdown"))

        # ── 核心：按 StrategyType.value 聚合的歸一化權重 ──
        # 格式: {"trend_following": 0.35, "mean_reversion": 0.25, ...}
        self.strategy_weights: Dict[str, float] = d.get("strategy_weights", {})

        # ── 原始模板排行榜（審計用）──
        # 格式: [{"template_key": "News_Trading", "strategy_type": "news_trading",
        #         "rank": 1, "return_pct": 0.12, "sharpe_ratio": 1.8}, ...]
        self.template_rankings: List[Dict[str, Any]] = d.get("template_rankings", [])

        # ── 市場體制覆寫 ──
        # 格式: {"bull": "trend_following", "sideways": "mean_reversion", ...}
        self.regime_overrides: Dict[str, str] = d.get("regime_overrides", {})

        # ── 風險參數 ──
        self.risk_params: Dict[str, Any] = d.get("risk_params", {
            "max_position_size_pct": 5.0,
            "max_risk_per_trade_pct": 1.0,
            "min_risk_reward_ratio": 2.0,
            "trailing_stop_activation": 1.5,
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "backtest_period": self.backtest_period,
            "symbol": self.symbol,
            "interval": self.interval,
            "total_return_pct": self.total_return_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "strategy_weights": self.strategy_weights,
            "template_rankings": self.template_rankings,
            "regime_overrides": self.regime_overrides,
            "risk_params": self.risk_params,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def validate(self) -> List[str]:
        """驗證 Profile 完整性，回傳錯誤訊息清單（空 = 通過）。"""
        errors: List[str] = []
        if not self.strategy_weights:
            errors.append("strategy_weights 為空")
        else:
            total = sum(self.strategy_weights.values())
            if abs(total - 1.0) > 0.05:
                errors.append(f"strategy_weights 總和 {total:.4f} 偏離 1.0 過大")
            for k, v in self.strategy_weights.items():
                if v < 0:
                    errors.append(f"策略 '{k}' 權重為負數: {v}")
        return errors


class GoldenProfileManager:
    """管理 Golden Profile 的生成、保存與載入"""

    @staticmethod
    def _build_template_to_type_map() -> Dict[str, str]:
        """建立 template_key → StrategyType.value 的映射。

        從 configs.py 的 STRATEGY_ALIASES 反轉而來，
        確保映射與實際策略配置一致。
        """
        try:
            from .configs import get_default_strategy_configs
            configs = get_default_strategy_configs()
            return {
                tpl_key: tpl.strategy_type.value
                for tpl_key, tpl in configs.items()
            }
        except Exception as e:
            logger.warning("無法建立 template→type 映射: %s", e)
            return {}

    @staticmethod
    def generate_from_backtest(
        result: Dict[str, Any],
        output_path: Optional[Path] = None,
    ) -> Optional[GoldenStrategyProfile]:
        """從 run_strategy_suite_backtest 的結果自動生成 Golden Profile。

        核心邏輯：
        1. 讀取 ranking，建立 template_key → StrategyType.value 映射。
        2. 以 Sharpe Ratio 為基準，將同類 StrategyType 的績效聚合。
        3. 歸一化為權重分配。
        4. 保存至 JSON。
        """
        ranking = result.get("ranking", [])
        if not ranking:
            logger.warning("回測結果中沒有排名數據，無法生成 Golden Profile")
            return None

        tpl_to_type = GoldenProfileManager._build_template_to_type_map()

        # ── Step 1: 收集每個 StrategyType 的最佳 Sharpe ──
        type_best_sharpe: Dict[str, float] = {}
        type_best_return: Dict[str, float] = {}
        template_rankings: List[Dict[str, Any]] = []

        for rank_idx, item in enumerate(ranking):
            tpl_key = item.get("template_key", "")
            stats = item.get("stats", {})
            sharpe = _safe_float(stats.get("sharpe_ratio"))
            ret = _safe_float(stats.get("total_return"))
            stype = tpl_to_type.get(tpl_key, "")

            template_rankings.append({
                "template_key": tpl_key,
                "strategy_type": stype,
                "rank": rank_idx + 1,
                "return_pct": ret,
                "sharpe_ratio": sharpe,
            })

            if not stype:
                continue

            # 取同一 StrategyType 中的最佳 Sharpe
            if stype not in type_best_sharpe or sharpe > type_best_sharpe[stype]:
                type_best_sharpe[stype] = sharpe
                type_best_return[stype] = ret

        # ── Step 2: 計算歸一化權重（Sharpe 為正的才分配權重）──
        positive_sharpe = {k: max(0.0, v) for k, v in type_best_sharpe.items()}
        total_sharpe = sum(positive_sharpe.values())

        if total_sharpe <= 0:
            # 所有 Sharpe 都是負的，均分
            n = len(positive_sharpe) or 1
            strategy_weights = {k: round(1.0 / n, 4) for k in positive_sharpe}
        else:
            strategy_weights = {
                k: round(v / total_sharpe, 4)
                for k, v in positive_sharpe.items()
            }

        # ── Step 3: 建立 regime_overrides（從排行榜第一名的 suitable_markets 推導）──
        regime_overrides: Dict[str, str] = {}
        try:
            from .configs import get_default_strategy_configs
            configs = get_default_strategy_configs()
            # 對每個 regime，找出 suitable 且權重最高的 strategy_type
            from .types import MarketRegime
            for regime in MarketRegime:
                best_type = ""
                best_w = -1.0
                for tpl_key, tpl in configs.items():
                    stype = tpl.strategy_type.value
                    w = strategy_weights.get(stype, 0.0)
                    if regime in tpl.suitable_markets and w > best_w:
                        best_w = w
                        best_type = stype
                if best_type:
                    regime_overrides[regime.value] = best_type
        except Exception:
            pass  # regime_overrides 是可選的增強功能

        # ── Step 4: 組裝 Profile ──
        best_item = ranking[0]
        best_stats = best_item.get("stats", {})

        profile = GoldenStrategyProfile({
            "version": "2.2.0",
            "generated_at": datetime.now().isoformat(),
            "backtest_period": f"{result.get('start_date')} ~ {result.get('end_date')}",
            "symbol": result.get("symbol", "BTCUSDT"),
            "interval": result.get("interval", "1h"),
            "total_return_pct": _safe_float(best_stats.get("total_return")),
            "sharpe_ratio": _safe_float(best_stats.get("sharpe_ratio")),
            "max_drawdown": _safe_float(best_stats.get("max_drawdown")),
            "strategy_weights": strategy_weights,
            "template_rankings": template_rankings,
            "regime_overrides": regime_overrides,
        })

        # ── Step 5: 驗證 & 保存 ──
        errors = profile.validate()
        if errors:
            logger.warning("Golden Profile 驗證有警告: %s", errors)

        save_path = output_path or DEFAULT_PROFILE_PATH
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(profile.to_json(), encoding="utf-8")
            logger.info("✨ Golden Profile 已生成: %s", save_path)
            logger.info("   策略權重: %s", strategy_weights)
            return profile
        except Exception as e:
            logger.error("儲存 Golden Profile 失敗: %s", e)
            return None

    @staticmethod
    def load(profile_path: Optional[Path] = None) -> Optional[GoldenStrategyProfile]:
        """從檔案讀取 Golden Profile。"""
        path = profile_path or DEFAULT_PROFILE_PATH
        if not path.exists():
            logger.info("未找到 Golden Profile: %s（將使用預設權重）", path)
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            profile = GoldenStrategyProfile(data)

            errors = profile.validate()
            if errors:
                logger.warning("載入的 Golden Profile 有驗證問題: %s", errors)
                return None

            logger.info(
                "📂 已載入 Golden Profile (v%s, %s)",
                profile.version,
                profile.backtest_period,
            )
            return profile
        except Exception as e:
            logger.error("讀取 Golden Profile 失敗: %s", e)
            return None

    @staticmethod
    def apply_to_selector(selector: Any, profile: GoldenStrategyProfile) -> bool:
        """將 Golden Profile 應用到 StrategySelector 實例。

        注入內容：
        1. strategy_weights → load_performance_weights()（核心 blend）
        2. regime_overrides → _regime_strategy_overrides（如果 selector 支援）
        """
        try:
            # 1. 注入績效權重（key 已是 StrategyType.value，與 blend 邏輯對齊）
            if profile.strategy_weights:
                selector.load_performance_weights(
                    profile.strategy_weights,
                    blend_alpha=0.7,
                )

            # 2. 注入 regime 覆寫（如果 selector 支援此屬性）
            if profile.regime_overrides and hasattr(selector, "_regime_strategy_overrides"):
                selector._regime_strategy_overrides = dict(profile.regime_overrides)
                logger.info("📊 已注入 regime 覆寫: %d 個體制", len(profile.regime_overrides))

            logger.info("🚀 Golden Profile 已成功應用於 StrategySelector")
            return True
        except Exception as e:
            logger.error("應用 Golden Profile 到 Selector 失敗: %s", e)
            return False
