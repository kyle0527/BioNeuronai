"""
🤖 AI 實際交易執行 - 使用 next_tick() 推進
===========================================

基於您提供的架構：
1. MockBinanceConnector (假交易所) - 用 next_tick() 推進
2. TradingEngine (AI 引擎) - 分析決策
3. 歷史數據 - ETHUSDT 15m
"""

import sys
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from bioneuronai.backtest import MockBinanceConnector
from bioneuronai.core.trading_engine import TradingEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ai_strategy(bar, connector, engine):
    """
    AI 策略：每根 K 線都讓 AI 分析並決策
    """
    symbol = bar.symbol
    current_price = bar.close
    
    # 獲取歷史 K 線 (dict 格式給 AI 用)
    klines = connector.data_stream.get_klines_until_now(100)
    if not klines or len(klines) < 20:
        return
    
    bar_idx = connector.data_stream.state.current_index
    
    # AI 推論
    if engine.inference_engine and engine.ai_model_loaded:
        try:
            signal = engine.inference_engine.predict(
                symbol=symbol,
                current_price=current_price,
                klines=klines
            )
            
            sig_str = signal.signal_type.value
            conf = signal.confidence
            
            # 顯示每根的AI決策
            print(f"Bar{bar_idx:3d}: ${current_price:7.2f} | {sig_str:15s} | {conf:.1%}", end="")
            
            # 檢查持倉
            account = connector.get_account_info()
            pos = None
            for p in account["positions"]:
                if p["symbol"] == symbol and abs(p["positionAmt"]) > 0:
                    pos = p
                    break
            
            # 執行決策
            if "long" in sig_str and (not pos or float(pos["positionAmt"]) <= 0):
                # 平空倉
                if pos:
                    pos_amt = float(pos["positionAmt"])
                    if pos_amt < 0:
                        connector.place_order(symbol, "BUY", "MARKET", abs(pos_amt))
                # 開多倉
                connector.place_order(symbol, "BUY", "MARKET", 0.05)
                print(" -> LONG!")
            elif "short" in sig_str and (not pos or float(pos["positionAmt"]) >= 0):
                # 平多倉
                if pos:
                    pos_amt = float(pos["positionAmt"])
                    if pos_amt > 0:
                        connector.place_order(symbol, "SELL", "MARKET", pos_amt)
                # 開空倉
                connector.place_order(symbol, "SELL", "MARKET", 0.05)
                print(" -> SHORT!")
            else:
                print()
                    
        except Exception as e:
            print(f"\nAI Error: {e}")


def main():
    print("=" * 80)
    print("AI 實際交易 - Next_Tick 推進模式")
    print("=" * 80)
    print()
    
    # 1. 創建 Mock 連接器 (換時間段: 2026-01-10 ~ 2026-01-15)
    print("[1/4] Creating Mock Connector...")
    mock = MockBinanceConnector(
        symbol="ETHUSDT",
        interval="15m",
        start_date="2026-01-10",
        end_date="2026-01-15",
        initial_balance=10000,
    )
    print(f"OK")
    print()
    
    # 2. 創建 AI 交易引擎
    print("[2/4] Creating Trading Engine...")
    engine = TradingEngine(
        api_key="",
        api_secret="",
        testnet=True,
        enable_ai_model=True,
        ai_min_confidence=0.5
    )
    engine.connector = mock
    print("OK")
    print()
    
    # 3. 載入 AI 模型
    print("[3/4] Loading AI Model...")
    if not engine.load_ai_model("my_100m_model", warmup=True):
        print("ERROR: AI model load failed")
        return
    print("OK")
    print()
    
    # 4. 開始 AI 交易
    print("=" * 80)
    print("[4/4] AI Trading Start - Every bar will show signal")
    print("=" * 80)
    print()
    
    bar_count = 0
    
    # 【使用 next_tick() 推進】
    while mock.next_tick():
        bar_count += 1
        
        # 每根 K 線都讓 AI 分析
        if mock._current_bar:
            ai_strategy(mock._current_bar, mock, engine)
    
    # 5. Final Results
    print()
    print("=" * 80)
    print("TRADING COMPLETE")
    print("=" * 80)
    
    account = mock.virtual_account
    stats = account.get_stats()
    
    print(f"\nFinal Balance: {account.balance:.2f} USDT")
    print(f"Total Return: {stats['total_return']:.2f}%")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.1f}%")
    print(f"Total Fees: {stats['total_commission']:.2f} USDT")
    print()
    
    print("DONE")
    print()


if __name__ == "__main__":
    main()
