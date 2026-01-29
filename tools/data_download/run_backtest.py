#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BioNeuronai - 歷史數據回測系統
連接 AI 推論引擎進行策略驗證
"""

import sys
sys.path.insert(0, '../src')

import pandas as pd
import zipfile
from pathlib import Path
from datetime import datetime

# 導入 BioNeuronai AI 引擎
from bioneuronai.core import InferenceEngine
from bioneuronai.data_models import MarketData


class HistoricalBacktest:
    """歷史數據回測系統"""
    
    def __init__(self, symbol="ETHUSDT", interval="1m", test_date="2025-12-22"):
        self.symbol = symbol
        self.interval = interval
        self.test_date = test_date
        self.data = None
        
        # 初始化 AI 引擎
        print("初始化 AI 引擎...")
        self.ai = InferenceEngine(min_confidence=0.6, warmup=False)
        
        # 載入模型
        print("載入 AI 模型...")
        import sys
        archived_path = str(Path(__file__).parent.parent / "archived")
        if archived_path not in sys.path:
            sys.path.insert(0, archived_path)
        
        from pytorch_100m_model import HundredMillionModel  # type: ignore
        self.ai.load_model("my_100m_model", HundredMillionModel)
        print("[OK] AI 模型已載入")
        
        # 統計
        self.stats = {
            'total': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0
        }
    
    def load_data(self):
        """載入歷史數據"""
        data_dir = Path("binance_historical/data/futures/um/daily/klines") / self.symbol / self.interval
        subdir = list(data_dir.glob("*_*"))[0]
        zip_file = subdir / f"{self.symbol}-{self.interval}-{self.test_date}.zip"
        
        print(f"載入數據: {zip_file.name}")
        
        with zipfile.ZipFile(zip_file) as z:
            csv_name = f"{self.symbol}-{self.interval}-{self.test_date}.csv"
            with z.open(csv_name) as f:
                self.data = pd.read_csv(f)
        
        print(f"[OK] {len(self.data)} 條 K線數據")
        return self.data
    
    def run(self, limit=None):
        """運行回測"""
        if self.data is None:
            self.load_data()
        
        print(f"\n{'='*60}")
        print(f"開始回測: {self.symbol} {self.interval} ({self.test_date})")
        print(f"{'='*60}\n")
        
        if self.data is None:
            raise RuntimeError("數據未載入")
        
        total = limit if limit else len(self.data)  # type: ignore
        
        for i in range(total):
            row = self.data.iloc[i]  # type: ignore
            
            # 準備 K線數據
            klines = [{
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']),
                'timestamp': int(row['open_time'])
            }]
            
            # AI 推論
            try:
                signal = self.ai.predict(
                    symbol=self.symbol,
                    current_price=float(row['close']),
                    klines=klines
                )
                
                # 統計信號
                self.stats['total'] += 1
                action = getattr(signal, 'action', 'HOLD')
                if action == 'BUY':
                    self.stats['buy_signals'] += 1
                elif action == 'SELL':
                    self.stats['sell_signals'] += 1
                else:
                    self.stats['hold_signals'] += 1
                
                # 顯示關鍵信號
                if action in ['BUY', 'SELL']:
                    ts = datetime.fromtimestamp(row['open_time']/1000)
                    confidence = getattr(signal, 'confidence', 0.0)
                    print(f"[{i:>4}] {ts.strftime('%H:%M:%S')} | "
                          f"價格:{float(row['close']):>8.2f} | "
                          f"信號:{action:>4} | "
                          f"信心:{confidence:.2f}")
            
            except Exception as e:
                print(f"[錯誤] {i}: {e}")
            
            # 進度
            if (i+1) % 100 == 0:
                print(f"進度: {i+1}/{total} ({(i+1)/total*100:.1f}%)")
        
        self._print_summary()
    
    def _print_summary(self):
        """顯示摘要"""
        print(f"\n{'='*60}")
        print("回測結果")
        print(f"{'='*60}")
        print(f"總 K線數: {self.stats['total']}")
        print(f"買入信號: {self.stats['buy_signals']}")
        print(f"賣出信號: {self.stats['sell_signals']}")
        print(f"持有信號: {self.stats['hold_signals']}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    # 創建回測系統
    backtest = HistoricalBacktest(
        symbol="ETHUSDT",
        interval="1m",
        test_date="2025-12-22"
    )
    
    # 運行回測（先測試 100 條）
    print("\n測試模式: 只處理前 100 條數據\n")
    backtest.run(limit=100)
    
    # 如果測試成功，可以跑全部
    input("\n按 Enter 繼續跑完整數據...")
    backtest.run()
