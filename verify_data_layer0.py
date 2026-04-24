import asyncio
from bioneuronai.data import BinanceFuturesConnector, ExchangeRateService, get_database_manager
from bioneuronai.data.web_data_fetcher import WebDataFetcher

async def verify_layer0():
    print("=== Layer 0 (data) 實機操作驗證 ===")
    
    print("\n[1/4] 驗證 BinanceFuturesConnector (幣安即時報價)")
    try:
        # 使用 testnet，無金鑰即可獲取公開報價
        connector = BinanceFuturesConnector(testnet=True)
        price = connector.get_ticker_price("BTCUSDT")
        print(f"✅ 成功連線！BTCUSDT 目前測試網最新價格: {price} USDT")
    except Exception as e:
        print(f"❌ 幣安連線失敗: {e}")

    print("\n[2/4] 驗證 ExchangeRateService (三層匯率回退機制)")
    try:
        rate_service = ExchangeRateService()
        rate_info = rate_service.get_rate("USD", "TWD")
        print(f"✅ 成功獲取匯率！USD/TWD = {rate_info.rate:.2f} (資料來源: {rate_info.source})")
    except Exception as e:
        print(f"❌ 匯率服務失敗: {e}")

    print("\n[3/4] 驗證 DatabaseManager (SQLite 表結構與管理)")
    try:
        db = get_database_manager()
        stats = db.get_database_stats()
        print("✅ 成功存取資料庫！目前資料表狀態:")
        for table, count in stats.items():
            print(f"   - {table}: {count} 筆記錄")
    except Exception as e:
        print(f"❌ 資料庫存取失敗: {e}")

    print("\n[4/4] 驗證 WebDataFetcher (非同步總體經濟數據)")
    try:
        async with WebDataFetcher() as fetcher:
            snapshot = await fetcher.fetch_all()
            print("✅ 成功並行抓取外部數據！")
            if snapshot.fear_greed:
                print(f"   - 恐慌貪婪指數: {snapshot.fear_greed.value} ({snapshot.fear_greed.classification})")
            if snapshot.global_market:
                print(f"   - 全球市值 BTC 佔比: {snapshot.global_market.btc_dominance:.2f}%")
            if snapshot.defi_metrics:
                print(f"   - DeFi TVL: ${snapshot.defi_metrics.total_tvl / 1e9:.2f} B")
    except Exception as e:
        print(f"❌ 外部數據抓取失敗: {e}")

if __name__ == "__main__":
    asyncio.run(verify_layer0())
