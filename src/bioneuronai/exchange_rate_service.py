"""
即時匯率服務
============
從外部 API 獲取即時匯率，不存資料庫

支援的 API：
1. ExchangeRate-API (免費)
2. Binance (USDT 對穩定幣)
3. 備用：固定匯率（離線時使用）
"""

import requests
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading

logger = logging.getLogger(__name__)


@dataclass
class ExchangeRateInfo:
    """匯率資訊"""
    from_currency: str
    to_currency: str
    rate: float
    source: str  # API 來源
    updated_at: datetime
    is_realtime: bool  # 是否為即時匯率


class ExchangeRateService:
    """
    即時匯率服務
    
    特點：
    - 從外部 API 即時獲取
    - 短期快取（避免頻繁請求）
    - 支援多種貨幣
    - 自動備用機制
    """
    
    # 快取有效期（秒）
    CACHE_TTL = 300  # 5 分鐘
    
    # 備用匯率（當 API 不可用時使用，需要定期手動更新）
    FALLBACK_RATES = {
        ("USDT", "USD"): 1.0,
        ("USDT", "TWD"): 32.0,
        ("USDT", "EUR"): 0.92,
        ("USDT", "GBP"): 0.79,
        ("USDT", "JPY"): 149.5,
        ("USDT", "CNY"): 7.24,
        ("USDT", "KRW"): 1320.0,
        ("USDT", "HKD"): 7.82,
        ("USDT", "SGD"): 1.34,
    }
    
    def __init__(self):
        self._cache: Dict[tuple, ExchangeRateInfo] = {}
        self._lock = threading.Lock()
        self._last_api_error = None
        
        logger.info("💱 即時匯率服務已啟動")
    
    def get_rate(self, from_currency: str, to_currency: str) -> Optional[ExchangeRateInfo]:
        """
        獲取匯率（優先即時，否則用快取或備用）
        
        Args:
            from_currency: 來源貨幣（如 USDT）
            to_currency: 目標貨幣（如 TWD）
        
        Returns:
            ExchangeRateInfo 或 None
        """
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        
        # 相同貨幣
        if from_curr == to_curr:
            return ExchangeRateInfo(
                from_currency=from_curr,
                to_currency=to_curr,
                rate=1.0,
                source="identity",
                updated_at=datetime.now(),
                is_realtime=True
            )
        
        cache_key = (from_curr, to_curr)
        
        # 檢查快取
        with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                age = (datetime.now() - cached.updated_at).total_seconds()
                if age < self.CACHE_TTL:
                    return cached
        
        # 嘗試從 API 獲取
        rate_info = self._fetch_from_api(from_curr, to_curr)
        
        if rate_info:
            with self._lock:
                self._cache[cache_key] = rate_info
            return rate_info
        
        # 使用備用匯率
        return self._get_fallback_rate(from_curr, to_curr)
    
    def _fetch_from_api(self, from_curr: str, to_curr: str) -> Optional[ExchangeRateInfo]:
        """從外部 API 獲取匯率"""
        
        # 方法 1: 如果是 USDT 對 USD，直接返回 1:1（穩定幣）
        if from_curr == "USDT" and to_curr == "USD":
            return ExchangeRateInfo(
                from_currency=from_curr,
                to_currency=to_curr,
                rate=1.0,
                source="stablecoin",
                updated_at=datetime.now(),
                is_realtime=True
            )
        
        # 方法 2: 使用免費匯率 API
        try:
            import requests
            
            # 先將 USDT 視為 USD
            base = "USD" if from_curr == "USDT" else from_curr
            
            # 使用 exchangerate-api.com (免費，每月 1500 次)
            url = f"https://open.er-api.com/v6/latest/{base}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("result") == "success" and to_curr in data.get("rates", {}):
                    rate = data["rates"][to_curr]
                    
                    logger.debug(f"💱 API 匯率: {from_curr}/{to_curr} = {rate}")
                    
                    return ExchangeRateInfo(
                        from_currency=from_curr,
                        to_currency=to_curr,
                        rate=rate,
                        source="exchangerate-api",
                        updated_at=datetime.now(),
                        is_realtime=True
                    )
        
        except requests.exceptions.Timeout:
            logger.warning("匯率 API 請求超時")
        except requests.exceptions.RequestException as e:
            logger.warning(f"匯率 API 請求失敗: {e}")
        except Exception as e:
            logger.error(f"獲取匯率時發生錯誤: {e}")
        
        return None
    
    def _get_fallback_rate(self, from_curr: str, to_curr: str) -> Optional[ExchangeRateInfo]:
        """獲取備用匯率"""
        
        # 直接查找
        key = (from_curr, to_curr)
        if key in self.FALLBACK_RATES:
            logger.warning(f"⚠️ 使用備用匯率: {from_curr}/{to_curr} = {self.FALLBACK_RATES[key]}")
            return ExchangeRateInfo(
                from_currency=from_curr,
                to_currency=to_curr,
                rate=self.FALLBACK_RATES[key],
                source="fallback",
                updated_at=datetime.now(),
                is_realtime=False
            )
        
        # 反向查找
        reverse_key = (to_curr, from_curr)
        if reverse_key in self.FALLBACK_RATES:
            rate = 1.0 / self.FALLBACK_RATES[reverse_key]
            logger.warning(f"⚠️ 使用備用匯率（反向）: {from_curr}/{to_curr} = {rate}")
            return ExchangeRateInfo(
                from_currency=from_curr,
                to_currency=to_curr,
                rate=rate,
                source="fallback_inverse",
                updated_at=datetime.now(),
                is_realtime=False
            )
        
        # 透過 USD 中轉
        if from_curr != "USD" and to_curr != "USD":
            usd_rate = self._get_fallback_rate(from_curr, "USD")
            target_rate = self._get_fallback_rate("USD", to_curr)
            
            if usd_rate and target_rate:
                rate = usd_rate.rate * target_rate.rate
                return ExchangeRateInfo(
                    from_currency=from_curr,
                    to_currency=to_curr,
                    rate=rate,
                    source="fallback_via_usd",
                    updated_at=datetime.now(),
                    is_realtime=False
                )
        
        logger.error(f"❌ 找不到匯率: {from_curr}/{to_curr}")
        return None
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """
        貨幣轉換
        
        Args:
            amount: 金額
            from_currency: 來源貨幣
            to_currency: 目標貨幣
        
        Returns:
            轉換後金額，或 None（如果無法獲取匯率）
        """
        rate_info = self.get_rate(from_currency, to_currency)
        if rate_info:
            return amount * rate_info.rate
        return None
    
    def get_all_rates(self, base_currency: str = "USDT") -> Dict[str, ExchangeRateInfo]:
        """獲取所有常用貨幣的匯率"""
        currencies = ["USD", "TWD", "EUR", "GBP", "JPY", "CNY", "KRW", "HKD", "SGD"]
        rates = {}
        
        for curr in currencies:
            rate_info = self.get_rate(base_currency, curr)
            if rate_info:
                rates[curr] = rate_info
        
        return rates
    
    def clear_cache(self):
        """清除快取（強制下次從 API 獲取）"""
        with self._lock:
            self._cache.clear()
        logger.info("💱 匯率快取已清除")
    
    def format_conversion(self, amount: float, from_currency: str, to_currency: str) -> str:
        """格式化顯示貨幣轉換"""
        rate_info = self.get_rate(from_currency, to_currency)
        if rate_info:
            converted = amount * rate_info.rate
            realtime_mark = "🔴" if rate_info.is_realtime else "⚪"
            return f"{amount:,.2f} {from_currency} = {converted:,.2f} {to_currency} {realtime_mark}"
        return f"無法轉換 {from_currency} → {to_currency}"


# 全局服務實例
_rate_service: Optional[ExchangeRateService] = None


def get_exchange_rate_service() -> ExchangeRateService:
    """獲取全局匯率服務實例"""
    global _rate_service
    if _rate_service is None:
        _rate_service = ExchangeRateService()
    return _rate_service


if __name__ == "__main__":
    print("💱 即時匯率服務測試\n")
    print("=" * 50)
    
    service = ExchangeRateService()
    
    # 測試轉換
    test_amount = 1000  # USDT
    
    print(f"\n📊 {test_amount} USDT 轉換為各國貨幣：\n")
    
    rates = service.get_all_rates("USDT")
    for curr, rate_info in rates.items():
        converted = test_amount * rate_info.rate
        source = f"[{rate_info.source}]"
        realtime = "✅ 即時" if rate_info.is_realtime else "⚠️ 備用"
        print(f"  {curr}: {converted:>12,.2f} {source:20} {realtime}")
    
    # 測試特定轉換
    print("\n" + "=" * 50)
    print("\n📊 貨幣轉換範例：\n")
    
    examples = [
        (1000, "USDT", "TWD"),
        (100, "USDT", "EUR"),
        (50000, "TWD", "USDT"),
        (1, "BTC", "USD"),  # 這個會失敗，因為沒有 BTC 匯率
    ]
    
    for amount, from_c, to_c in examples:
        result = service.format_conversion(amount, from_c, to_c)
        print(f"  {result}")
    
    print("\n✅ 測試完成！")
