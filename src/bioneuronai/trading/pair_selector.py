"""
交易對選擇器 - 根據 Binance 24 小時行情真實篩選最優交易對
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# 預設候選池（USDT 永續合約，流動性較佳）
_CANDIDATE_PAIRS: List[str] = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
    "DOTUSDT", "LINKUSDT", "LTCUSDT", "AVAXUSDT", "MATICUSDT",
]

# 篩選門檻
_MIN_VOLUME_USDT = 50_000_000   # 24h 成交量最低 5000 萬 USDT
_MAX_PRICE_CHANGE_PCT = 15.0    # 24h 漲跌幅不超過 15%（避免極端行情）


class PairSelector:
    """交易對選擇器 — 使用 BinanceFuturesConnector 取得真實 24h 行情來篩選標的"""

    def __init__(self, connector=None):
        self.name = "PairSelector"
        self._connector = connector  # 可注入 BinanceFuturesConnector；None 時降級為預設清單

    async def select_optimal_pairs(self, market_analysis=None, risk_params=None) -> Dict:
        """根據真實市場資料選擇最優交易對。

        使用注入的 BinanceFuturesConnector 取得各幣對 24h 行情，
        依成交量降序排列並過濾極端波動的幣對。
        若 connector 未設定或 API 呼叫失敗，則降級使用主流預設清單。
        """
        logger.info("💱 PairSelector：篩選最優交易對...")
        _market_analysis = market_analysis  # 保留供未來整合使用
        scored: List[Dict] = []

        if self._connector is not None:
            scored = self._fetch_and_score(self._candidate_pairs(risk_params))
        
        # API 失敗或 connector 不可用時的保守降級
        if not scored:
            logger.warning("PairSelector：無法取得即時行情，使用預設主流幣對")
            return self._default_result()

        # 依 24h 成交量降序排列
        scored.sort(key=lambda x: x["volume_usdt"], reverse=True)
        symbols = [s["symbol"] for s in scored]

        return {
            "primary_pairs": symbols[:3],
            "backup_pairs": symbols[3:6],
            "excluded_pairs": [p for p in _CANDIDATE_PAIRS if p not in symbols],
            "selection_criteria": {
                "min_volume_usdt": _MIN_VOLUME_USDT,
                "max_price_change_pct": _MAX_PRICE_CHANGE_PCT,
            },
            "pair_details": {s["symbol"]: s for s in scored},
        }

    # ------------------------------------------------------------------
    # 私有輔助方法
    # ------------------------------------------------------------------

    def _candidate_pairs(self, risk_params=None) -> List[str]:
        """根據風險參數決定候選池大小"""
        _risk_params = risk_params  # 保留供未來依風險偏好縮小候選池使用
        return _CANDIDATE_PAIRS

    def _fetch_and_score(self, candidates: List[str]) -> List[Dict]:
        """呼叫 API 取得行情並評分，回傳通過篩選的幣對清單"""
        result = []
        for symbol in candidates:
            try:
                ticker = self._connector.get_ticker_24hr(symbol)
                if not ticker or isinstance(ticker, dict) and "code" in ticker:
                    continue

                volume_usdt = float(ticker.get("quoteVolume", 0))
                price_change_pct = abs(float(ticker.get("priceChangePercent", 0)))

                # 過濾流動性不足或波動過大的幣對
                if volume_usdt < _MIN_VOLUME_USDT:
                    logger.debug(f"  排除 {symbol}：24h 成交量 {volume_usdt:,.0f} USDT < 門檻")
                    continue
                if price_change_pct > _MAX_PRICE_CHANGE_PCT:
                    logger.debug(f"  排除 {symbol}：24h 漲跌幅 {price_change_pct:.1f}% 過大")
                    continue

                result.append({
                    "symbol": symbol,
                    "volume_usdt": volume_usdt,
                    "price_change_pct": price_change_pct,
                    "last_price": float(ticker.get("lastPrice", 0)),
                })
            except Exception as e:
                logger.warning(f"  取得 {symbol} 行情失敗: {e}")

        return result

    @staticmethod
    def _default_result() -> Dict:
        return {
            "primary_pairs": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            "backup_pairs": ["SOLUSDT", "ADAUSDT"],
            "excluded_pairs": [],
            "selection_criteria": {"source": "default_fallback"},
            "pair_details": {},
        }