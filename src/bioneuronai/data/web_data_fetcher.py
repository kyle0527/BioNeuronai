"""
BioNeuronai 外部數據源統一抓取器

職責：統一管理外部數據 API 調用（遵循 CODE_FIX_GUIDE.md 單一數據來源原則）

數據源：
1. Alternative.me - 恐慌貪婪指數
2. CoinGecko - 全球市場數據、穩定幣供應
3. DefiLlama - DeFi TVL 數據
4. （待擴展）經濟日曆 API

更新日期: 2026-02-15
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, cast
from dataclasses import dataclass

# 從 schemas 導入數據模型（遵循單一數據來源原則）
from schemas.external_data import (
    FearGreedIndex,
    GlobalMarketData,
    DeFiMetrics,
    StablecoinMetrics,
    EconomicEvent,
    ExternalDataSnapshot,
    DataSourceType,
)

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """API 配置"""
    # Alternative.me
    fear_greed_url: str = "https://api.alternative.me/fng/"
    
    # CoinGecko (免費版)
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    coingecko_api_key: Optional[str] = None  # 可選
    
    # DefiLlama
    defillama_base_url: str = "https://api.llama.fi"
    
    # 請求配置
    timeout: int = 10  # 秒
    max_retries: int = 3
    retry_delay: float = 1.0  # 秒


class WebDataFetcher:
    """
    外部數據源統一抓取器
    
    特性：
    - 異步 HTTP 請求
    - 自動重試機制
    - 錯誤處理與日誌
    - 數據驗證（Pydantic 模型）
    """
    
    def __init__(self, config: Optional[APIConfig] = None):
        """
        初始化數據抓取器
        
        Args:
            config: API 配置，如不提供則使用默認值
        """
        self.config = config or APIConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info("✅ WebDataFetcher 初始化完成")
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        發送 HTTP GET 請求（帶重試機制）
        
        Args:
            url: API URL
            params: 查詢參數
            headers: 請求頭
            
        Returns:
            JSON 響應數據，失敗返回 None
        """
        if not self.session:
            raise RuntimeError("請在異步上下文中使用 WebDataFetcher")
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.get(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data
            
            except aiohttp.ClientError as e:
                logger.warning(f"請求失敗 (嘗試 {attempt + 1}/{self.config.max_retries}): {url} - {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    logger.error(f"❌ 請求最終失敗: {url}")
                    return None
            
            except Exception as e:
                logger.error(f"❌ 未預期的錯誤: {url} - {e}", exc_info=True)
                return None
    
    async def fetch_fear_greed_index(self) -> Optional[FearGreedIndex]:
        """
        抓取恐慌貪婪指數
        
        數據源: Alternative.me API （免費，無需 API 密鑰）
        更新頻率: 每 24 小時，UTC 00:00 更新
        
        Returns:
            FearGreedIndex 對象，失敗返回 None
        """
        logger.info("📊 抓取恐慌貪婪指數...")
        
        try:
            data = await self._make_request(self.config.fear_greed_url)
            if not data or "data" not in data or len(data["data"]) == 0:
                logger.error("❌ 恐慌貪婪指數數據格式錯誤")
                return None
            
            latest = data["data"][0]
            
            # 使用 Pydantic 模型驗證數據
            index = FearGreedIndex(
                value=int(latest["value"]),
                value_classification=latest["value_classification"],
                timestamp=datetime.fromtimestamp(int(latest["timestamp"])),
                time_until_update=int(latest.get("time_until_update", 0))
            )
            
            logger.info(f"  ✓ 恐慌貪婪指數: {index.value} ({index.value_classification})")
            return index
        
        except Exception as e:
            logger.error(f"❌ 解析恐慌貪婪指數失敗: {e}", exc_info=True)
            return None
    
    async def fetch_global_market_data(self) -> Optional[GlobalMarketData]:
        """
        抓取全球加密貨幣市場數據
        
        數據源: CoinGecko API（免費，無需 API 密鑰）
        限制: 50 calls/minute (免費版)
        
        Returns:
            GlobalMarketData 對象，失敗返回 None
        """
        logger.info("🌍 抓取全球市場數據...")
        
        url = f"{self.config.coingecko_base_url}/global"
        headers = {}
        if self.config.coingecko_api_key:
            headers["x-cg-demo-api-key"] = self.config.coingecko_api_key
        
        try:
            data = await self._make_request(url, headers=headers)
            if not data or "data" not in data:
                logger.error("❌ 全球市場數據格式錯誤")
                return None
            
            market_data = data["data"]
            
            # 使用 Pydantic 模型驗證數據
            global_market = GlobalMarketData(
                total_market_cap=float(market_data["total_market_cap"].get("usd", 0)),
                total_volume_24h=float(market_data["total_volume"].get("usd", 0)),
                btc_dominance=float(market_data["market_cap_percentage"].get("btc", 0)),
                eth_dominance=float(market_data["market_cap_percentage"].get("eth", 0)),
                active_cryptocurrencies=int(market_data.get("active_cryptocurrencies", 0)),
                markets=int(market_data.get("markets", 0)),
                market_cap_change_24h=float(market_data.get("market_cap_change_percentage_24h_usd", 0)),
                timestamp=datetime.now()
            )
            
            logger.info(f"  ✓ 全球市值: ${global_market.total_market_cap/1e12:.2f}T")
            logger.info(f"  ✓ BTC 占比: {global_market.btc_dominance:.1f}%")
            return global_market
        
        except Exception as e:
            logger.error(f"❌ 解析全球市場數據失敗: {e}", exc_info=True)
            return None
    
    async def fetch_defi_metrics(self) -> Optional[DeFiMetrics]:
        """
        抓取 DeFi 總鎖倉價值 (TVL)
        
        數據源: DefiLlama API（免費，無需 API 密鑰）
        
        Returns:
            DeFiMetrics 對象，失敗返回 None
        """
        logger.info("🏦 抓取 DeFi TVL 數據...")
        
        try:
            # 抓取當前 TVL
            tvl_url = f"{self.config.defillama_base_url}/v2/chains"
            data = await self._make_request(tvl_url)
            if not data or not isinstance(data, list):
                logger.error("❌ DeFi TVL 數據格式錯誤")
                return None
            
            # 計算總 TVL 和分布
            total_tvl = 0.0
            chains_tvl: Dict[str, float] = {}
            
            for chain in data:
                if not isinstance(chain, dict):
                    continue
                chain_name = str(chain.get("name", "unknown")).lower()
                chain_tvl = float(chain.get("tvl", 0))
                chains_tvl[chain_name] = chain_tvl
                total_tvl += chain_tvl
            
            # 獲取前 3 條鏈
            top_chains = dict(sorted(chains_tvl.items(), key=lambda x: x[1], reverse=True)[:3])
            
            defi_metrics = DeFiMetrics(
                total_tvl=total_tvl,
                chains=top_chains,
                protocols={},  # 如需要可以另外抓取
                tvl_change_24h=0.0,  # 需要歷史數據計算
                timestamp=datetime.now()
            )
            
            logger.info(f"  ✓ DeFi 總 TVL: ${defi_metrics.total_tvl/1e9:.1f}B")
            return defi_metrics
        
        except Exception as e:
            logger.error(f"❌ 解析 DeFi 數據失敗: {e}", exc_info=True)
            return None
    
    async def fetch_stablecoin_metrics(self) -> Optional[StablecoinMetrics]:
        """
        抓取穩定幣供應量數據
        
        數據源: CoinGecko API
        
        Returns:
            StablecoinMetrics 對象，失敗返回 None
        """
        logger.info("💵 抓取穩定幣數據...")
        
        stablecoin_ids = "tether,usd-coin,dai,first-digital-usd"
        url = f"{self.config.coingecko_base_url}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": stablecoin_ids,
            "order": "market_cap_desc"
        }
        
        headers = {}
        if self.config.coingecko_api_key:
            headers["x-cg-demo-api-key"] = self.config.coingecko_api_key
        
        try:
            data = await self._make_request(url, params=params, headers=headers)
            if not data or not isinstance(data, list):
                logger.error("❌ 穩定幣數據格式錯誤")
                return None
            
            total_supply = 0.0
            supply_by_token: Dict[str, float] = {}
            
            for token in data:
                if not isinstance(token, dict):
                    continue
                symbol = str(token.get("symbol", "unknown")).upper()
                market_cap = float(token.get("market_cap", 0))
                supply_by_token[symbol] = market_cap
                total_supply += market_cap
            
            stablecoin_metrics = StablecoinMetrics(
                total_supply=total_supply,
                supply_by_token=supply_by_token,
                supply_change_24h=0.0,  # 需要歷史數據
                supply_change_7d=0.0,    # 需要歷史數據
                timestamp=datetime.now()
            )
            
            logger.info(f"  ✓ 穩定幣總供應: ${stablecoin_metrics.total_supply/1e9:.1f}B")
            return stablecoin_metrics
        
        except Exception as e:
            logger.error(f"❌ 解析穩定幣數據失敗: {e}", exc_info=True)
            return None
    
    async def fetch_all(self) -> ExternalDataSnapshot:
        """
        抓取所有外部數據（並行執��）
        
        Returns:
            ExternalDataSnapshot 包含所有數據的快照
        """
        logger.info("=" * 70)
        logger.info("🚀 開始抓取外部市場數據...")
        logger.info("=" * 70)
        
        start_time = datetime.now()
        snapshot_id = f"snapshot_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # 並行抓取所有數據
        results = await asyncio.gather(
            self.fetch_fear_greed_index(),
            self.fetch_global_market_data(),
            self.fetch_defi_metrics(),
            self.fetch_stablecoin_metrics(),
            return_exceptions=True
        )
        
        # 解析結果並處理異常
        fear_greed_result: Optional[FearGreedIndex] = None
        global_market_result: Optional[GlobalMarketData] = None
        defi_result: Optional[DeFiMetrics] = None
        stablecoin_result: Optional[StablecoinMetrics] = None
        
        raw_fear_greed, raw_global_market, raw_defi, raw_stablecoin = results
        
        # 收集錯誤
        errors: List[str] = []
        data_sources: List[DataSourceType] = []
        
        if isinstance(raw_fear_greed, Exception):
            errors.append(f"FearGreed: {str(raw_fear_greed)}")
        elif raw_fear_greed:
            fear_greed_result = cast(FearGreedIndex, raw_fear_greed)
            data_sources.append(DataSourceType.ALTERNATIVE_ME)
        
        if isinstance(raw_global_market, Exception):
            errors.append(f"GlobalMarket: {str(raw_global_market)}")
        elif raw_global_market:
            global_market_result = cast(GlobalMarketData, raw_global_market)
            data_sources.append(DataSourceType.COINGECKO)
        
        if isinstance(raw_defi, Exception):
            errors.append(f"DeFi: {str(raw_defi)}")
        elif raw_defi:
            defi_result = cast(DeFiMetrics, raw_defi)
            data_sources.append(DataSourceType.DEFI_LLAMA)
        
        if isinstance(raw_stablecoin, Exception):
            errors.append(f"Stablecoin: {str(raw_stablecoin)}")
        elif raw_stablecoin:
            stablecoin_result = cast(StablecoinMetrics, raw_stablecoin)
        
        # 計算耗時
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # 創建快照
        snapshot = ExternalDataSnapshot(
            snapshot_id=snapshot_id,
            timestamp=start_time,
            fear_greed=fear_greed_result,
            global_market=global_market_result,
            defi_metrics=defi_result,
            stablecoin_metrics=stablecoin_result,
            market_sentiment=None,  # 需要後續計算
            economic_events=[],      # 需要其他 API
            data_sources=data_sources,
            fetch_duration_ms=duration_ms,
            errors=errors
        )
        
        logger.info("=" * 70)
        logger.info(f"✅ 數據抓取完成！耗時: {duration_ms}ms")
        logger.info(f"   成功: {len(data_sources)} 個數據源")
        if errors:
            logger.warning(f"   失敗: {len(errors)} 個數據源")
            for error in errors:
                logger.warning(f"     - {error}")
        logger.info("=" * 70)
        
        return snapshot


# ========== 可直接運行的示例 ==========
if __name__ == "__main__":
    """
    演示如何使用 WebDataFetcher
    
    運行方式:
        python -m src.bioneuronai.data.web_data_fetcher
    """
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        """主函數"""
        async with WebDataFetcher() as fetcher:
            # 方式 1: 抓取所有數據
            snapshot = await fetcher.fetch_all()
            
            print("\n" + "=" * 70)
            print("📸 外部數據快照")
            print("=" * 70)
            print(f"快照ID: {snapshot.snapshot_id}")
            print(f"時間戳: {snapshot.timestamp}")
            print(f"數據源: {[ds.value for ds in snapshot.data_sources]}")
            print(f"耗時: {snapshot.fetch_duration_ms}ms")
            print()
            
            if snapshot.fear_greed:
                print(f"恐慌貪婪指數: {snapshot.fear_greed.value} ({snapshot.fear_greed.value_classification})")
            
            if snapshot.global_market:
                print(f"全球市值: ${snapshot.global_market.total_market_cap/1e12:.2f}T")
                print(f"BTC 占比: {snapshot.global_market.btc_dominance:.1f}%")
                print(f"24h 變化: {snapshot.global_market.market_cap_change_24h:+.2f}%")
            
            if snapshot.defi_metrics:
                print(f"DeFi 總 TVL: ${snapshot.defi_metrics.total_tvl/1e9:.1f}B")
            
            if snapshot.stablecoin_metrics:
                print(f"穩定幣供應: ${snapshot.stablecoin_metrics.total_supply/1e9:.1f}B")
            
            if snapshot.errors:
                print(f"\n⚠️ 錯誤: {len(snapshot.errors)} 個")
                for error in snapshot.errors:
                    print(f"  - {error}")
            
            print("=" * 70)
    
    # 運行異步主函數
    asyncio.run(main())
