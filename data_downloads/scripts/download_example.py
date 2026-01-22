#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BioNeuronai - Binance 歷史數據下載範例
====================================

此腳本提供常用的數據下載範例，適合快速開始使用。
"""

import os
import sys
from datetime import datetime, timedelta

# 設定數據存放目錄
STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "binance_historical")

def setup_environment():
    """設定環境變數"""
    os.environ['STORE_DIRECTORY'] = STORE_DIR
    print(f"[設定] 數據存放目錄: {STORE_DIR}")

def example_1_download_btc_hourly():
    """
    範例 1: 下載 BTCUSDT 永續合約的小時線數據
    用途: 訓練 AI 模型、長期趨勢分析
    """
    print("\n" + "="*60)
    print("範例 1: 下載 BTCUSDT 永續合約小時線數據")
    print("="*60)
    
    cmd = (
        "python download-kline.py "
        "-t um "  # USD-M 永續合約
        "-s BTCUSDT "  # BTC/USDT 交易對
        "-i 1h 4h "  # 1小時和4小時 K線
        "-startDate 2023-01-01 "  # 從 2023年開始
        "-folder ../binance_historical "  # 存放目錄
        "-c 1"  # 包含校驗和文件
    )
    
    print(f"\n執行命令:\n{cmd}\n")
    os.system(cmd)

def example_2_download_multiple_pairs():
    """
    範例 2: 下載多個主流交易對的日線數據
    用途: 市場相關性分析、交易對選擇
    """
    print("\n" + "="*60)
    print("範例 2: 下載多個主流交易對的日線數據")
    print("="*60)
    
    cmd = (
        "python download-kline.py "
        "-t um "
        "-s BTCUSDT ETHUSDT BNBUSDT SOLUSDT "  # 多個交易對
        "-i 1d "  # 日線
        "-startDate 2023-01-01 "
        "-skip-monthly 1 "  # 只下載日度數據
        "-folder ../binance_historical"
    )
    
    print(f"\n執行命令:\n{cmd}\n")
    os.system(cmd)

def example_3_download_recent_minute_data():
    """
    範例 3: 下載最近 30 天的分鐘線數據
    用途: 策略回測、高頻交易分析
    """
    print("\n" + "="*60)
    print("範例 3: 下載最近 30 天的分鐘線數據")
    print("="*60)
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    cmd = (
        f"python download-kline.py "
        f"-t um "
        f"-s BTCUSDT "
        f"-i 1m 5m 15m "  # 多個時間間隔
        f"-startDate {start_date} "
        f"-endDate {end_date} "
        f"-skip-monthly 1 "
        f"-folder ../binance_historical"
    )
    
    print(f"\n執行命令:\n{cmd}\n")
    print(f"日期範圍: {start_date} 至 {end_date}")
    os.system(cmd)

def example_4_download_trade_data():
    """
    範例 4: 下載交易明細數據
    用途: 流動性分析、訂單簿重建
    """
    print("\n" + "="*60)
    print("範例 4: 下載交易明細數據")
    print("="*60)
    
    cmd = (
        "python download-trade.py "
        "-t um "
        "-s BTCUSDT "
        "-startDate 2024-01-01 "
        "-m 01 02 "  # 只下載 1月和2月
        "-folder ../binance_historical"
    )
    
    print(f"\n執行命令:\n{cmd}\n")
    os.system(cmd)

def example_5_download_for_backtesting():
    """
    範例 5: 為回測準備數據集
    用途: 完整的策略回測數據
    """
    print("\n" + "="*60)
    print("範例 5: 下載回測數據集")
    print("="*60)
    
    # 下載 K線數據
    cmd_kline = (
        "python download-kline.py "
        "-t um "
        "-s BTCUSDT ETHUSDT "
        "-i 15m 1h "
        "-startDate 2024-01-01 "
        "-skip-monthly 1 "
        "-folder ../binance_historical "
        "-c 1"
    )
    
    # 下載聚合交易數據
    cmd_agg = (
        "python download-aggTrade.py "
        "-t um "
        "-s BTCUSDT ETHUSDT "
        "-startDate 2024-01-01 "
        "-skip-monthly 1 "
        "-folder ../binance_historical"
    )
    
    print(f"\n第一步 - 下載 K線數據:\n{cmd_kline}\n")
    os.system(cmd_kline)
    
    print(f"\n第二步 - 下載聚合交易數據:\n{cmd_agg}\n")
    os.system(cmd_agg)

def show_menu():
    """顯示互動式選單"""
    print("\n" + "="*60)
    print("BioNeuronai - Binance 歷史數據下載工具")
    print("="*60)
    print("\n請選擇要執行的範例:\n")
    print("  1. 下載 BTCUSDT 小時線數據（適合訓練 AI 模型）")
    print("  2. 下載多個交易對的日線數據（適合相關性分析）")
    print("  3. 下載最近 30 天的分鐘線數據（適合策略回測）")
    print("  4. 下載交易明細數據（適合流動性分析）")
    print("  5. 下載完整回測數據集（K線+聚合交易）")
    print("  6. 顯示當前數據存放目錄")
    print("  0. 退出")
    print("\n" + "="*60)

def show_data_directory():
    """顯示數據存放目錄資訊"""
    print("\n" + "="*60)
    print("數據存放目錄資訊")
    print("="*60)
    print(f"\n路徑: {STORE_DIR}")
    
    if os.path.exists(STORE_DIR):
        # 統計目錄大小
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(STORE_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
        
        print(f"總文件數: {file_count}")
        print(f"總大小: {total_size / (1024**3):.2f} GB")
        
        # 列出子目錄
        subdirs = [d for d in os.listdir(STORE_DIR) if os.path.isdir(os.path.join(STORE_DIR, d))]
        if subdirs:
            print(f"\n子目錄:")
            for subdir in subdirs:
                print(f"  - {subdir}")
    else:
        print("\n[警告] 目錄不存在，將在首次下載時建立")
    
    print("="*60)

def main():
    """主函數"""
    # 設定環境
    setup_environment()
    
    # 檢查是否在正確的目錄
    if not os.path.exists("download-kline.py"):
        print("\n[錯誤] 請在 data_downloads/scripts 目錄下執行此腳本")
        print(f"當前目錄: {os.getcwd()}")
        return
    
    # 互動式選單
    while True:
        show_menu()
        choice = input("\n請輸入選項 (0-6): ").strip()
        
        if choice == "1":
            example_1_download_btc_hourly()
        elif choice == "2":
            example_2_download_multiple_pairs()
        elif choice == "3":
            example_3_download_recent_minute_data()
        elif choice == "4":
            example_4_download_trade_data()
        elif choice == "5":
            example_5_download_for_backtesting()
        elif choice == "6":
            show_data_directory()
        elif choice == "0":
            print("\n再見！")
            break
        else:
            print("\n[錯誤] 無效的選項，請重新輸入")
        
        input("\n按 Enter 繼續...")

if __name__ == "__main__":
    main()
