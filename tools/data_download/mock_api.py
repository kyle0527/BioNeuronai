#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BioNeuronai - 模擬實盤數據流
============================

模擬真實 API 連接，按順序餵送 K線數據給 AI 系統
"""

import pandas as pd
import zipfile
import time
from pathlib import Path
from datetime import datetime

# ========== 配置區 ==========
SYMBOL = "ETHUSDT"
INTERVAL = "1m"  # 1m, 5m, 15m, 1h
DATA_DIR = Path("binance_historical/data/futures/um/daily/klines/ETHUSDT")
SPEED = 100  # 速度倍數 (1=實時, 100=100倍速, 0=無延遲)
TEST_DATE = "2025-12-22"  # 只載入這一天的數據
# ============================


class MockBinanceAPI:
    """模擬 Binance API - 就像真的連接 API 一樣"""
    
    def __init__(self, symbol=SYMBOL, interval=INTERVAL):
        self.symbol = symbol
        self.interval = interval
        self.data = None
        self.current_idx = 0
        self._load_all_data()
    
    def _load_all_data(self):
        """載入歷史數據"""
        data_path = DATA_DIR / self.interval
        
        # 找到數據子目錄
        subdirs = list(data_path.glob("*_*"))
        if subdirs:
            data_path = subdirs[0]
        
        print(f"載入數據從: {data_path}")
        
        # 只載入指定日期（測試用）
        if TEST_DATE:
            zip_file = data_path / f"{SYMBOL}-{self.interval}-{TEST_DATE}.zip"
            csv_name = f"{SYMBOL}-{self.interval}-{TEST_DATE}.csv"
            print(f"測試模式: 只載入 {TEST_DATE}")
            with zipfile.ZipFile(zip_file) as z:
                with z.open(csv_name) as f:
                    self.data = pd.read_csv(f)
        else:
            # 載入全部數據
            all_dfs = []
            for zip_file in sorted(data_path.glob("*.zip")):
                if "CHECKSUM" in zip_file.name:
                    continue
                try:
                    csv_name = zip_file.stem + ".csv"
                    with zipfile.ZipFile(zip_file) as z:
                        with z.open(csv_name) as f:
                            df = pd.read_csv(f)
                            all_dfs.append(df)
                except:
                    pass
            self.data = pd.concat(all_dfs, ignore_index=True)
        
        self.data = self.data.sort_values('open_time').reset_index(drop=True)
        print(f"[OK] 載入 {len(self.data):,} 條 K線數據")
        print(f"時間範圍: {self._ts_to_str(self.data['open_time'].iloc[0])} ~ {self._ts_to_str(self.data['open_time'].iloc[-1])}")
    
    def _ts_to_str(self, ts):
        return datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M')
    
    def get_kline(self):
        """
        模擬 API 調用 - 獲取當前 K線
        就像調用 client.futures_klines() 一樣
        
        返回格式同 Binance API:
        [open_time, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_vol, taker_buy_quote, ignore]
        """
        if self.data is None or self.current_idx >= len(self.data):
            return None  # 數據結束
        
        row = self.data.iloc[self.current_idx]  # type: ignore
        self.current_idx = int(self.current_idx) + 1
        
        # 返回格式完全模擬 Binance API
        return {
            'symbol': self.symbol,
            'interval': self.interval,
            'open_time': int(row['open_time']),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume']),
            'close_time': int(row['close_time']),
            'quote_volume': float(row['quote_volume']),
            'trades': int(row['count']),
            'taker_buy_volume': float(row['taker_buy_volume']),
            'taker_buy_quote_volume': float(row['taker_buy_quote_volume']),
            # 額外信息
            'timestamp': datetime.fromtimestamp(row['open_time']/1000),
        }
    
    def reset(self):
        """重置到開頭"""
        self.current_idx = 0
    
    def skip_to_date(self, date_str):
        """跳到指定日期"""
        if self.data is None:
            print("數據未載入")
            return
        
        target = pd.to_datetime(date_str)
        target_ts = int(target.timestamp() * 1000)
        
        for i, row in self.data.iterrows():  # type: ignore
            if int(row['open_time']) >= target_ts:  # type: ignore
                self.current_idx = int(i)  # type: ignore
                print(f"跳到: {self._ts_to_str(row['open_time'])}")
                return
        print("找不到指定日期")


def run_simulation():
    """運行模擬"""
    print("\n" + "="*60)
    print("BioNeuronai - 模擬實盤數據流")
    print("="*60)
    
    # 初始化模擬 API
    api = MockBinanceAPI(interval=INTERVAL)
    
    # 計算延遲時間
    interval_seconds = {'1m': 60, '5m': 300, '15m': 900, '1h': 3600}.get(INTERVAL, 60)
    delay = interval_seconds / SPEED if SPEED > 0 else 0
    
    print(f"\n設定: {INTERVAL} K線, {SPEED}倍速 (延遲 {delay:.3f}秒)")
    print("="*60)
    
    # 這裡放你的 AI 策略
    # from bioneuronai.core import InferenceEngine
    # ai = InferenceEngine()
    
    count = 0
    try:
        while True:
            # 獲取 K線 (模擬 API 調用)
            kline = api.get_kline()
            
            if kline is None:
                print("\n[結束] 數據播放完畢")
                break
            
            # ========== 這裡是你的策略邏輯 ==========
            # signal = ai.predict(kline)
            # if signal.action == 'BUY':
            #     execute_buy(kline['close'])
            # ========================================
            
            # 顯示進度
            count += 1
            if count % 100 == 0:
                print(f"[{count:>6}] {kline['timestamp']} | "
                      f"O:{kline['open']:.2f} H:{kline['high']:.2f} "
                      f"L:{kline['low']:.2f} C:{kline['close']:.2f} "
                      f"V:{kline['volume']:.0f}")
            
            # 延遲 (模擬實時)
            if delay > 0:
                time.sleep(delay)
    
    except KeyboardInterrupt:
        print(f"\n[中斷] 已處理 {count} 條數據")
    
    print(f"\n總共處理: {count:,} 條 K線")


if __name__ == "__main__":
    run_simulation()
