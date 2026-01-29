"""
🤖 AI 實際交易執行程式
================================

完整流程：
1. 載入 AI 模型 (111.2M 參數神經網路)
2. 讀取歷史數據 (ETHUSDT 15m)
3. AI 推論決策
4. 執行交易
5. 記錄結果

這是真實 AI 交易，不是隨機策略！
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from bioneuronai.core.trading_engine import TradingEngine
from bioneuronai.backtest import create_mock_connector

# 設定日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("🤖 BioNeuronAI - AI 實際交易執行")
    print("=" * 80)
    print()
    
    # ========== 步驟 1: 創建 Mock 連接器 (使用歷史數據) ==========
    print("📡 步驟 1: 初始化數據連接...")
    mock_connector = create_mock_connector(
        symbol="ETHUSDT",
        start_date="2025-12-22",
        end_date="2025-12-23",
        initial_balance=10000
    )
    print(f"✅ Mock 連接器已創建")
    print(f"   交易對: ETHUSDT")
    print(f"   時間範圍: 2025-12-22 ~ 2025-12-23")
    print(f"   初始資金: 10,000 USDT")
    print()
    
    # ========== 步驟 2: 創建交易引擎並啟用 AI ==========
    print("🧠 步驟 2: 初始化 AI 交易引擎...")
    engine = TradingEngine(
        api_key="",  # Mock 模式不需要真實 API
        api_secret="",
        testnet=True,
        enable_ai_model=True,        # 啟用 AI
        ai_min_confidence=0.5,       # AI 信心閾值
        use_strategy_fusion=True     # 策略融合
    )
    
    # 替換為 Mock 連接器
    engine.connector = mock_connector
    print("✅ 交易引擎已創建")
    print()
    
    # ========== 步驟 3: 載入 AI 模型 ==========
    print("🔧 步驟 3: 載入 AI 神經網路...")
    success = engine.load_ai_model(
        model_name="my_100m_model",
        warmup=True
    )
    
    if not success:
        print("❌ AI 模型載入失敗！")
        print("   請確認 model/my_100m_model.pth 存在")
        return
    
    print("✅ AI 模型已載入並預熱")
    print()
    
    # ========== 步驟 4: 開始 AI 交易 ==========
    print("=" * 80)
    print("🚀 步驟 4: 開始 AI 實際交易")
    print("=" * 80)
    print()
    
    symbol = "ETHUSDT"
    bar_count = 0
    trades_executed = 0
    
    # 使用 next_tick() 推進數據
    print("⏩ 開始逐根 K 線推進...")
    while mock_connector.next_tick():  # 【時間推進器】
        bar_count += 1
        
        # 獲取當前市場數據
        current_price = mock_connector.get_ticker_price(symbol)
        if current_price is None:
            break  # 數據結束
        
        # 獲取 K 線數據
        klines = mock_connector.get_historical_klines(
            symbol=symbol,
            interval="15m",
            limit=100
        )
        
        # 每 20 根 K 線讓 AI 分析一次
        if bar_count % 20 == 0:
            print(f"\n📊 Bar {bar_count}: {current_price:.2f} USDT")
            print(f"   時間: {datetime.fromtimestamp(klines[-1]['close_time']/1000).strftime('%Y-%m-%d %H:%M')}")
            
            # ========== AI 推論 ==========
            if engine.inference_engine and engine.ai_model_loaded:
                # 讓 AI 分析市場
                ai_signal = engine.inference_engine.predict(
                    symbol=symbol,
                    current_price=current_price,
                    klines=klines
                )
                
                print(f"   🤖 AI 信號: {ai_signal.signal_type.value}")
                print(f"   📈 信心度: {ai_signal.confidence:.2%}")
                print(f"   💡 推理: {ai_signal.reasoning[:80] if ai_signal.reasoning else 'N/A'}...")
                
                # 檢查當前持倉
                account_info = mock_connector.get_account_info()
                current_position = None
                
                for pos in account_info.get("positions", []):
                    if pos["symbol"] == symbol and abs(pos["positionAmt"]) > 0:
                        current_position = pos
                        break
                
                # ========== 執行交易決策 ==========
                if ai_signal.confidence >= engine.ai_min_confidence:
                    # AI 信心夠高，執行交易
                    if "long" in ai_signal.signal_type.value:
                        # 看多信號
                        if current_position is None or float(current_position["positionAmt"]) <= 0:
                            # 沒有多倉或持有空倉，開多倉
                            print(f"   🟢 AI 決策: 開多倉")
                            
                            # 先平空倉（如果有）
                            if current_position and float(current_position["positionAmt"]) < 0:
                                    close_result = mock_connector.place_order(
                                        symbol=symbol,
                                        side="BUY",
                                        order_type="MARKET",
                                        quantity=abs(float(current_position["positionAmt"]))
                                    )
                                    print(f"      平空倉: {close_result['orderId']}")
                                    trades_executed += 1
                                
                                # 開新多倉
                                order_result = mock_connector.place_order(
                                    symbol=symbol,
                                    side="BUY",
                                    order_type="MARKET",
                                    quantity=0.05
                                )
                                print(f"      ✅ 訂單: {order_result['orderId']} | {order_result['status']}")
                                trades_executed += 1
                        
                        elif "short" in ai_signal.signal_type.value:
                            # 看空信號
                            if current_position is None or float(current_position["positionAmt"]) >= 0:
                                # 沒有空倉或持有多倉，開空倉
                                print(f"   🔴 AI 決策: 開空倉")
                                
                                # 先平多倉（如果有）
                                if current_position and float(current_position["positionAmt"]) > 0:
                                    close_result = mock_connector.place_order(
                                        symbol=symbol,
                                        side="SELL",
                                        order_type="MARKET",
                                        quantity=float(current_position["positionAmt"])
                                    )
                                    print(f"      平多倉: {close_result['orderId']}")
                                    trades_executed += 1
                                
                                # 開新空倉
                                order_result = mock_connector.place_order(
                                    symbol=symbol,
                                    side="SELL",
                                    order_type="MARKET",
                                    quantity=0.05
                                )
                                print(f"      ✅ 訂單: {order_result['orderId']} | {order_result['status']}")
                                trades_executed += 1
                        
                        else:
                        # 中性信號
                        if current_position:
                            print(f"   ⚪ AI 決策: 平倉")
                            side = "SELL" if float(current_position["positionAmt"]) > 0 else "BUY"
                            order_result = mock_connector.place_order(
                                symbol=symbol,
                                side=side,
                                order_type="MARKET",
                                quantity=abs(float(current_position["positionAmt"]))
                            )
                            print(f"      ✅ 訂單: {order_result['orderId']} | {order_result['status']}")
                            trades_executed += 1
                else:
                    print(f"   ⏸️ AI 信心不足，不交易")
                
                # 顯示當前帳戶狀態
                account = mock_connector.virtual_account
                print(f"   💰 帳戶: {account.balance:.2f} USDT | 盈虧: {account.total_realized_pnl:+.2f} USDT")
    
    # ========== 最終結果 ==========
    print()
    print("=" * 80)
    print("📊 AI 交易完成 - 最終結果")
    print("=" * 80)
    
    account = mock_connector.virtual_account
    print(f"\n💰 帳戶績效:")
    print(f"   初始餘額: 10,000.00 USDT")
    print(f"   最終餘額: {account.balance:.2f} USDT")
    print(f"   實現盈虧: {account.total_realized_pnl:+.2f} USDT")
    print(f"   總收益率: {(account.balance/10000 - 1)*100:+.2f}%")
    
    print(f"\n📈 交易統計:")
    print(f"   處理 K 線: {bar_count} 根")
    print(f"   執行交易: {trades_executed} 筆")
    print(f"   總手續費: {account.total_fees:.2f} USDT")
    
    if account.trade_history:
        winning_trades = [t for t in account.trade_history if t["realized_pnl"] > 0]
        losing_trades = [t for t in account.trade_history if t["realized_pnl"] < 0]
        
        print(f"\n🎯 績效分析:")
        print(f"   盈利交易: {len(winning_trades)} 筆")
        print(f"   虧損交易: {len(losing_trades)} 筆")
        if len(winning_trades) + len(losing_trades) > 0:
            win_rate = len(winning_trades) / (len(winning_trades) + len(losing_trades))
            print(f"   勝率: {win_rate:.1%}")
    
    print()
    print("✅ AI 交易流程完成！")
    print()

if __name__ == "__main__":
    main()
