#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""超簡單測試 - 確認數據能讀取"""

import pandas as pd
import zipfile
from pathlib import Path

# 讀取一天的數據
data_dir = Path("binance_historical/data/futures/um/daily/klines/ETHUSDT/1m")
subdir = list(data_dir.glob("*_*"))[0]
zip_file = subdir / "ETHUSDT-1m-2025-12-22.zip"

print(f"讀取: {zip_file}")

with zipfile.ZipFile(zip_file) as z:
    with z.open("ETHUSDT-1m-2025-12-22.csv") as f:
        df = pd.read_csv(f)

print(f"[OK] 載入 {len(df)} 條數據")
print("\n前 3 條:")
print(df.head(3))

print("\n模擬餵送給 AI:")
for i in range(5):
    row = df.iloc[i]
    print(f"[{i}] 時間:{row['open_time']} 價格:{row['close']} -> 這裡調用 AI 推論")

print("\n[測試成功] 程式可以運行")
