#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BioNeuronai - 歷史數據載入器
=============================

此模組提供從 Binance 歷史數據載入和處理功能。
與 data_downloads 目錄整合。
"""

import pandas as pd
import zipfile
from pathlib import Path
from typing import List, Optional, cast
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BinanceHistoricalDataLoader:
    """Binance 歷史數據載入器"""
    
    def __init__(self, data_root: str = "data_downloads/binance_historical"):
        """
        初始化數據載入器
        
        Args:
            data_root: 數據根目錄路徑
        """
        self.data_root = Path(data_root)
        if not self.data_root.exists():
            logger.warning(f"數據目錄不存在: {self.data_root}")
            logger.info("請先使用 data_downloads/scripts 下載歷史數據")
    
    def load_klines(
        self,
        symbol: str,
        interval: str,
        market_type: str = "um",
        year_month: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        data_type: str = "monthly"
    ) -> pd.DataFrame:
        """
        載入 K線數據
        
        Args:
            symbol: 交易對符號，如 "BTCUSDT"
            interval: 時間間隔，如 "1h", "4h", "1d"
            market_type: 市場類型 - "spot", "um" (USD-M), "cm" (COIN-M)
            year_month: 年月格式 "YYYY-MM"，如 "2024-01"
            start_date: 開始日期 "YYYY-MM-DD"（用於日度數據）
            end_date: 結束日期 "YYYY-MM-DD"（用於日度數據）
            data_type: "monthly" 或 "daily"
        
        Returns:
            包含 K線數據的 DataFrame
        """
        market_path = self._get_market_path(market_type)
        kline_path = self.data_root / market_path / data_type / "klines" / symbol / interval
        
        if not kline_path.exists():
            raise FileNotFoundError(
                f"找不到數據目錄: {kline_path}\n"
                f"請先下載數據: python data_downloads/scripts/download-kline.py "
                f"-t {market_type} -s {symbol} -i {interval}"
            )
        
        # 載入單個月度文件
        if year_month and data_type == "monthly":
            return self._load_single_kline_file(kline_path, symbol, interval, year_month)
        
        # 載入日期範圍內的數據
        if start_date and end_date:
            return self._load_klines_by_date_range(
                kline_path, symbol, interval, start_date, end_date, data_type
            )
        
        # 載入所有可用數據
        return self._load_all_klines(kline_path, symbol, interval, data_type)
    
    def _load_single_kline_file(
        self, 
        kline_path: Path, 
        symbol: str, 
        interval: str, 
        year_month: str
    ) -> pd.DataFrame:
        """載入單個 K線文件"""
        zip_file = kline_path / f"{symbol}-{interval}-{year_month}.zip"
        
        if not zip_file.exists():
            raise FileNotFoundError(f"找不到文件: {zip_file}")
        
        return self._read_kline_zip(zip_file, symbol, interval, year_month)
    
    def _load_klines_by_date_range(
        self,
        kline_path: Path,
        symbol: str,
        interval: str,
        start_date: str,
        end_date: str,
        data_type: str
    ) -> pd.DataFrame:
        """載入日期範圍內的 K線數據"""
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        dfs: List[pd.DataFrame] = []
        
        if data_type == "monthly":
            # 按月載入
            current = start
            while current <= end:
                year_month = current.strftime("%Y-%m")
                try:
                    monthly_df = self._load_single_kline_file(kline_path, symbol, interval, year_month)
                    # 過濾日期範圍
                    filtered_df = cast(pd.DataFrame, monthly_df[
                        (monthly_df['open_time'] >= start) & (monthly_df['open_time'] <= end)
                    ])
                    dfs.append(filtered_df)
                except FileNotFoundError:
                    logger.warning(f"找不到 {year_month} 的數據")
                
                # 移到下個月
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        
        else:  # daily
            # 按日載入
            date_range = pd.date_range(start, end, freq='D')
            for date in date_range:
                date_str = date.strftime("%Y-%m-%d")
                zip_file = kline_path / f"{symbol}-{interval}-{date_str}.zip"
                
                if zip_file.exists():
                    try:
                        df = self._read_kline_zip(zip_file, symbol, interval, date_str)
                        dfs.append(df)
                    except Exception as e:
                        logger.warning(f"讀取 {date_str} 數據失敗: {e}")
        
        if not dfs:
            raise ValueError(f"在日期範圍 {start_date} 至 {end_date} 內找不到任何數據")
        
        # 合併所有 DataFrame
        result = pd.concat(dfs, ignore_index=True)
        result = result.sort_values('open_time').reset_index(drop=True)
        
        return cast(pd.DataFrame, result)
    
    def _load_all_klines(
        self, 
        kline_path: Path, 
        symbol: str, 
        interval: str,
        data_type: str
    ) -> pd.DataFrame:
        """載入目錄中所有 K線數據"""
        zip_files = sorted(kline_path.glob(f"{symbol}-{interval}-*.zip"))
        
        if not zip_files:
            raise FileNotFoundError(f"在 {kline_path} 找不到任何數據文件")
        
        dfs: List[pd.DataFrame] = []
        for zip_file in zip_files:
            # 從文件名提取日期
            parts = zip_file.stem.split('-')
            if data_type == "monthly" and len(parts) >= 4:
                date_str = f"{parts[-2]}-{parts[-1]}"  # YYYY-MM
            else:
                date_str = '-'.join(parts[-3:])  # YYYY-MM-DD
            
            try:
                df = self._read_kline_zip(zip_file, symbol, interval, date_str)
                dfs.append(df)
            except Exception as e:
                logger.warning(f"讀取 {zip_file.name} 失敗: {e}")
        
        if not dfs:
            raise ValueError("無法載入任何數據文件")
        
        result = pd.concat(dfs, ignore_index=True)
        result = result.sort_values('open_time').reset_index(drop=True)
        
        return cast(pd.DataFrame, result)
    
    def _read_kline_zip(
        self, 
        zip_file: Path, 
        symbol: str, 
        interval: str, 
        date_str: str
    ) -> pd.DataFrame:
        """從 zip 文件讀取 K線數據"""
        csv_name = f"{symbol}-{interval}-{date_str}.csv"
        
        with zipfile.ZipFile(zip_file) as z:
            with z.open(csv_name) as f:
                df = pd.read_csv(f, header=None, names=[
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
        
        # 轉換時間戳（處理毫秒和微秒）
        if df['open_time'].iloc[0] > 1e12:  # 微秒
            df['open_time'] = pd.to_datetime(df['open_time'], unit='us')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='us')
        else:  # 毫秒
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        # 轉換數值類型
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                       'quote_volume', 'taker_buy_base', 'taker_buy_quote']
        df[numeric_cols] = df[numeric_cols].astype(float)
        df['trades'] = df['trades'].astype(int)
        
        # 刪除 ignore 欄位
        df = df.drop('ignore', axis=1)
        
        return cast(pd.DataFrame, df)
    
    def _get_market_path(self, market_type: str) -> str:
        """根據市場類型獲取路徑"""
        market_map = {
            'spot': 'spot',
            'um': 'futures/um',
            'cm': 'futures/cm'
        }
        
        if market_type not in market_map:
            raise ValueError(f"不支援的市場類型: {market_type}，支援: {list(market_map.keys())}")
        
        return market_map[market_type]
    
    def get_available_data(self, symbol: str, interval: str, market_type: str = "um") -> dict:
        """
        獲取可用的數據資訊
        
        Args:
            symbol: 交易對符號
            interval: 時間間隔
            market_type: 市場類型
        
        Returns:
            包含可用數據資訊的字典
        """
        market_path = self._get_market_path(market_type)
        
        result = {
            'symbol': symbol,
            'interval': interval,
            'market_type': market_type,
            'monthly': [],
            'daily': []
        }
        
        # 檢查月度數據
        monthly_path = self.data_root / market_path / "monthly" / "klines" / symbol / interval
        if monthly_path.exists():
            monthly_files = sorted(monthly_path.glob(f"{symbol}-{interval}-*.zip"))
            result['monthly'] = [f.stem for f in monthly_files]
        
        # 檢查日度數據
        daily_path = self.data_root / market_path / "daily" / "klines" / symbol / interval
        if daily_path.exists():
            daily_files = sorted(daily_path.glob(f"{symbol}-{interval}-*.zip"))
            result['daily'] = [f.stem for f in daily_files]
        
        return result


# 便捷函數
def load_btc_hourly(start_date: str = "2023-01-01", end_date: Optional[str] = None) -> pd.DataFrame:
    """
    快速載入 BTCUSDT 小時線數據
    
    Args:
        start_date: 開始日期
        end_date: 結束日期（預設為今天）
    
    Returns:
        K線數據 DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    loader = BinanceHistoricalDataLoader()
    return loader.load_klines("BTCUSDT", "1h", "um", start_date=start_date, end_date=end_date)


def load_multiple_symbols(
    symbols: List[str],
    interval: str = "1h",
    start_date: str = "2023-01-01",
    end_date: Optional[str] = None
) -> dict:
    """
    載入多個交易對的數據
    
    Args:
        symbols: 交易對符號列表
        interval: 時間間隔
        start_date: 開始日期
        end_date: 結束日期
    
    Returns:
        字典，鍵為交易對符號，值為 DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    loader = BinanceHistoricalDataLoader()
    result = {}
    
    for symbol in symbols:
        try:
            df = loader.load_klines(symbol, interval, "um", start_date=start_date, end_date=end_date)
            result[symbol] = df
            logger.info(f"載入 {symbol}: {len(df)} 條記錄")
        except Exception as e:
            logger.error(f"載入 {symbol} 失敗: {e}")
    
    return result


# 使用範例
if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(level=logging.INFO)
    
    # 範例 1: 載入單個月份的數據
    print("範例 1: 載入 2024-01 的 BTCUSDT 1小時 K線")
    loader = BinanceHistoricalDataLoader()
    
    try:
        df = loader.load_klines("BTCUSDT", "1h", "um", year_month="2024-01")
        print(f"載入 {len(df)} 條記錄")
        print(df.head())
        print(f"\n時間範圍: {df['open_time'].min()} 至 {df['open_time'].max()}")
    except FileNotFoundError as e:
        print(f"找不到數據: {e}")
        print("請先下載數據：")
        print("cd data_downloads/scripts")
        print("python download-kline.py -t um -s BTCUSDT -i 1h -y 2024 -m 01")
    
    # 範例 2: 載入日期範圍的數據
    print("\n範例 2: 載入 2024-01-01 至 2024-03-31 的數據")
    try:
        df = loader.load_klines(
            "BTCUSDT", "1h", "um",
            start_date="2024-01-01",
            end_date="2024-03-31"
        )
        print(f"載入 {len(df)} 條記錄")
        print(df.tail())
    except Exception as e:
        print(f"載入失敗: {e}")
    
    # 範例 3: 使用便捷函數
    print("\n範例 3: 使用便捷函數載入 BTC 小時線")
    try:
        df = load_btc_hourly("2024-01-01", "2024-01-31")
        print(f"載入 {len(df)} 條記錄")
        print(f"價格範圍: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    except Exception as e:
        print(f"載入失敗: {e}")
    
    # 範例 4: 檢查可用數據
    print("\n範例 4: 檢查 BTCUSDT 1h 可用數據")
    info = loader.get_available_data("BTCUSDT", "1h", "um")
    print(f"月度數據: {len(info['monthly'])} 個文件")
    print(f"日度數據: {len(info['daily'])} 個文件")
    if info['monthly']:
        print(f"最早月份: {info['monthly'][0]}")
        print(f"最新月份: {info['monthly'][-1]}")
