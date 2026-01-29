#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BioNeuronai - 歷史數據餵送器
============================

按時間順序、可調速度地餵送歷史數據給 AI 系統
模擬實時數據流，用於回測和策略驗證
"""

import pandas as pd
import zipfile
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HistoricalDataFeeder:
    """
    歷史數據餵送器
    
    功能：
    1. 按時間順序逐條餵送數據
    2. 可調整餵送速度（延遲時間）
    3. 支援暫停、繼續、跳過
    4. 可以回調函數處理每一條數據
    """
    
    def __init__(
        self,
        symbol: str = "ETHUSDT",
        interval: str = "1m",
        start_date: str = "2025-12-22",
        end_date: str = "2026-01-21",
        data_dir: str = "binance_historical",
        speed_multiplier: float = 1.0
    ):
        """
        初始化餵送器
        
        Args:
            symbol: 交易對符號
            interval: 時間間隔 (1m, 5m, 15m, 1h)
            start_date: 開始日期
            end_date: 結束日期
            data_dir: 數據目錄
            speed_multiplier: 速度倍數 (1.0=實時速度, 10.0=10倍速, 0.1=1/10速度)
        """
        self.symbol = symbol
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.data_dir = Path(data_dir)
        self.speed_multiplier = speed_multiplier
        
        # 狀態控制
        self.is_running = False
        self.is_paused = False
        self.current_index = 0
        self.data: Optional[pd.DataFrame] = None
        self.total_rows = 0
        
        # 統計信息
        self.stats = {
            'total_fed': 0,
            'start_time': None,
            'elapsed_time': 0,
            'average_speed': 0
        }
        
        logger.info(f"初始化餵送器: {symbol} {interval} ({start_date} ~ {end_date})")
        logger.info(f"速度倍數: {speed_multiplier}x")
    
    def load_data(self) -> pd.DataFrame:
        """載入歷史數據"""
        logger.info("開始載入歷史數據...")
        
        # 構建數據路徑
        data_path = self.data_dir / "data" / "futures" / "um" / "daily" / "klines" / self.symbol / self.interval
        
        if not data_path.exists():
            raise FileNotFoundError(
                f"找不到數據目錄: {data_path}\n"
                f"請先下載數據"
            )
        
        # 載入日期範圍內的所有文件
        start = pd.to_datetime(self.start_date)
        end = pd.to_datetime(self.end_date)
        
        all_dfs = []
        date_range = pd.date_range(start, end, freq='D')
        
        for date in date_range:
            date_str = date.strftime("%Y-%m-%d")
            zip_file = data_path / f"{self.symbol}-{self.interval}-{date_str}.zip"
            
            if zip_file.exists():
                try:
                    df = self._read_kline_zip(zip_file, date_str)
                    all_dfs.append(df)
                    logger.info(f"載入 {date_str}: {len(df)} 條記錄")
                except Exception as e:
                    logger.warning(f"讀取 {date_str} 失敗: {e}")
        
        if not all_dfs:
            raise ValueError(f"在日期範圍 {self.start_date} 至 {self.end_date} 內找不到任何數據")
        
        # 合併並排序
        self.data = pd.concat(all_dfs, ignore_index=True)
        self.data = self.data.sort_values('open_time').reset_index(drop=True)
        self.total_rows = len(self.data)
        
        logger.info(f"[OK] 載入完成: 總共 {self.total_rows:,} 條記錄")
        logger.info(f"時間範圍: {self.data['open_time'].min()} 至 {self.data['open_time'].max()}")
        
        return self.data
    
    def _read_kline_zip(self, zip_file: Path, date_str: str) -> pd.DataFrame:
        """從 zip 文件讀取 K線數據"""
        csv_name = f"{self.symbol}-{self.interval}-{date_str}.csv"
        
        with zipfile.ZipFile(zip_file) as z:
            with z.open(csv_name) as f:
                df = pd.read_csv(f, header=None, names=[
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
        
        # 轉換時間戳
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        # 轉換數值類型
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                       'quote_volume', 'taker_buy_base', 'taker_buy_quote']
        df[numeric_cols] = df[numeric_cols].astype(float)
        df['trades'] = df['trades'].astype(int)
        
        # 刪除 ignore 欄位
        df = df.drop('ignore', axis=1)
        
        return df
    
    def feed(
        self,
        callback: Callable[[Dict[str, Any], int, int], None],
        start_from: int = 0,
        limit: Optional[int] = None
    ):
        """
        開始餵送數據
        
        Args:
            callback: 回調函數，接收參數 (data_row, current_index, total_rows)
            start_from: 從第幾條開始（續傳功能）
            limit: 最多餵送多少條（None=全部）
        """
        if self.data is None:
            self.load_data()
        
        self.is_running = True
        self.current_index = start_from
        self.stats['start_time'] = time.time()
        
        # 計算間隔時間（模擬實時）
        interval_seconds = self._get_interval_seconds()
        delay = interval_seconds / self.speed_multiplier
        
        logger.info(f"\n{'='*60}")
        logger.info(f"開始餵送數據")
        logger.info(f"{'='*60}")
        logger.info(f"間隔: {self.interval} ({interval_seconds}秒)")
        logger.info(f"速度倍數: {self.speed_multiplier}x")
        logger.info(f"實際延遲: {delay:.4f}秒")
        logger.info(f"開始位置: {start_from}/{self.total_rows}")
        if limit:
            logger.info(f"限制數量: {limit} 條")
        logger.info(f"{'='*60}\n")
        
        end_index = min(self.total_rows, start_from + limit if limit else self.total_rows)
        
        try:
            for i in range(start_from, end_index):
                if not self.is_running:
                    logger.info("\n[停止] 餵送已停止")
                    break
                
                # 暫停控制
                while self.is_paused and self.is_running:
                    time.sleep(0.1)
                
                # 獲取當前行數據
                if self.data is None:
                    break
                row = self.data.iloc[i]  # type: ignore
                row_dict = row.to_dict()
                
                # 調用回調函數
                try:
                    callback(row_dict, i, self.total_rows)
                    self.stats['total_fed'] += 1
                except Exception as e:
                    logger.error(f"回調函數錯誤: {e}")
                
                self.current_index = i + 1
                
                # 進度顯示
                if (i + 1) % 100 == 0:
                    progress = (i + 1) / self.total_rows * 100
                    elapsed = time.time() - self.stats['start_time']
                    speed = (i + 1 - start_from) / elapsed if elapsed > 0 else 0
                    logger.info(
                        f"進度: {i+1}/{self.total_rows} ({progress:.1f}%) | "
                        f"速度: {speed:.1f} 條/秒"
                    )
                
                # 延遲（模擬實時）
                if delay > 0:
                    time.sleep(delay)
        
        except KeyboardInterrupt:
            logger.info("\n[中斷] 用戶中斷餵送")
        
        finally:
            self.is_running = False
            self._update_stats()
            self._print_summary()
    
    def feed_realtime_simulation(
        self,
        callback: Callable[[Dict[str, Any], int, int], None],
        start_from: int = 0
    ):
        """
        實時模擬模式（按照真實時間間隔餵送）
        
        適合用於策略實盤前的最終驗證
        """
        logger.info("[實時模擬模式] 將按照真實時間間隔餵送數據")
        original_speed = self.speed_multiplier
        self.speed_multiplier = 1.0  # 強制實時速度
        
        try:
            self.feed(callback, start_from)
        finally:
            self.speed_multiplier = original_speed
    
    def feed_fast_replay(
        self,
        callback: Callable[[Dict[str, Any], int, int], None],
        speed: float = 100.0,
        limit: int = 1000
    ):
        """
        快速回放模式（快速過一遍歷史）
        
        適合用於快速測試和驗證
        
        Args:
            callback: 回調函數
            speed: 速度倍數（預設100倍速）
            limit: 限制條數（預設1000條）
        """
        logger.info(f"[快速回放模式] {speed}倍速，限制 {limit} 條")
        original_speed = self.speed_multiplier
        self.speed_multiplier = speed
        
        try:
            self.feed(callback, limit=limit)
        finally:
            self.speed_multiplier = original_speed
    
    def pause(self):
        """暫停餵送"""
        self.is_paused = True
        logger.info("[暫停] 餵送已暫停")
    
    def resume(self):
        """繼續餵送"""
        self.is_paused = False
        logger.info("[繼續] 餵送已繼續")
    
    def stop(self):
        """停止餵送"""
        self.is_running = False
        logger.info("[停止] 餵送已停止")
    
    def set_speed(self, multiplier: float):
        """調整速度"""
        self.speed_multiplier = multiplier
        interval_seconds = self._get_interval_seconds()
        delay = interval_seconds / multiplier
        logger.info(f"[調速] 速度倍數設為 {multiplier}x，延遲 {delay:.4f}秒")
    
    def _get_interval_seconds(self) -> float:
        """根據時間間隔獲取秒數"""
        interval_map = {
            '1s': 1,
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '2h': 7200,
            '4h': 14400,
            '6h': 21600,
            '8h': 28800,
            '12h': 43200,
            '1d': 86400
        }
        return interval_map.get(self.interval, 60)
    
    def _update_stats(self):
        """更新統計信息"""
        if self.stats['start_time']:
            self.stats['elapsed_time'] = time.time() - self.stats['start_time']
            if self.stats['elapsed_time'] > 0:
                self.stats['average_speed'] = self.stats['total_fed'] / self.stats['elapsed_time']
    
    def _print_summary(self):
        """打印統計摘要"""
        logger.info(f"\n{'='*60}")
        logger.info(f"餵送統計")
        logger.info(f"{'='*60}")
        logger.info(f"已餵送: {self.stats['total_fed']:,} 條")
        logger.info(f"耗時: {self.stats['elapsed_time']:.2f} 秒")
        logger.info(f"平均速度: {self.stats['average_speed']:.2f} 條/秒")
        logger.info(f"進度: {self.current_index}/{self.total_rows} ({self.current_index/self.total_rows*100:.1f}%)")
        logger.info(f"{'='*60}\n")
    
    def get_data_info(self) -> Dict[str, Any]:
        """獲取數據資訊"""
        if self.data is None:
            return {'status': 'not_loaded'}
        
        return {
            'status': 'loaded',
            'total_rows': self.total_rows,
            'symbol': self.symbol,
            'interval': self.interval,
            'start_time': str(self.data['open_time'].min()),
            'end_time': str(self.data['open_time'].max()),
            'price_range': {
                'min': float(self.data['low'].min()),
                'max': float(self.data['high'].max())
            },
            'volume_total': float(self.data['volume'].sum())
        }


# 回調函數範例
def example_callback_print(data: Dict[str, Any], index: int, total: int):
    """範例：打印數據"""
    if index % 10 == 0:  # 每10條打印一次
        print(f"[{index}/{total}] {data['open_time']} | "
              f"O:{data['open']:.2f} H:{data['high']:.2f} "
              f"L:{data['low']:.2f} C:{data['close']:.2f} "
              f"V:{data['volume']:.0f}")


def example_callback_ai_inference(data: Dict[str, Any], index: int, total: int):
    """範例：AI 推論（需要實際整合）"""
    # 這裡可以調用 BioNeuronai 的 InferenceEngine
    # from bioneuronai.core import InferenceEngine
    # signal = inference_engine.predict(data)
    
    print(f"[AI] {data['open_time']} | 價格: {data['close']:.2f} | 模擬推論中...")


def example_callback_strategy_test(data: Dict[str, Any], index: int, total: int):
    """範例：策略測試"""
    # 簡單的移動平均策略示例
    # 實際使用時可以累積歷史數據計算指標
    price = data['close']
    volume = data['volume']
    
    if index % 50 == 0:
        print(f"[策略] {data['open_time']} | 價格: {price:.2f} | 量: {volume:.0f}")


# 使用範例
if __name__ == "__main__":
    print("\n" + "="*60)
    print("BioNeuronai - 歷史數據餵送器")
    print("="*60 + "\n")
    
    # 創建餵送器
    feeder = HistoricalDataFeeder(
        symbol="ETHUSDT",
        interval="5m",
        start_date="2025-12-22",
        end_date="2026-01-21",
        speed_multiplier=100.0  # 100倍速
    )
    
    # 顯示選單
    print("請選擇模式:\n")
    print("  1. 快速測試 (1000條, 100倍速)")
    print("  2. 正常速度 (全部, 1倍速)")
    print("  3. 10倍速 (全部, 10倍速)")
    print("  4. 100倍速 (全部, 100倍速)")
    print("  5. 自訂設定")
    print("  0. 退出\n")
    
    choice = input("請選擇 (0-5): ").strip()
    
    if choice == "1":
        feeder.feed_fast_replay(example_callback_print, speed=100.0, limit=1000)
    
    elif choice == "2":
        feeder.set_speed(1.0)
        feeder.feed(example_callback_print)
    
    elif choice == "3":
        feeder.set_speed(10.0)
        feeder.feed(example_callback_print)
    
    elif choice == "4":
        feeder.set_speed(100.0)
        feeder.feed(example_callback_print)
    
    elif choice == "5":
        symbol = input("交易對 (預設 ETHUSDT): ").strip() or "ETHUSDT"
        interval = input("時間間隔 (1m/5m/15m/1h, 預設 5m): ").strip() or "5m"
        speed = float(input("速度倍數 (預設 10): ").strip() or "10")
        limit = input("限制條數 (空白=全部): ").strip()
        limit = int(limit) if limit else None
        
        feeder = HistoricalDataFeeder(
            symbol=symbol,
            interval=interval,
            start_date="2025-12-22",
            end_date="2026-01-21",
            speed_multiplier=speed
        )
        feeder.feed(example_callback_print, limit=limit)
    
    elif choice == "0":
        print("再見！")
    
    else:
        print("無效選項")
