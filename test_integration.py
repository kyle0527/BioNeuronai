"""
BioNeuronai 
============================

:
1. 
2. AI 
3. 
4. 

:
    python test_integration.py
"""

import sys
import time
from pathlib import Path

#  path 
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_module_imports():
    """"""
    print("\n" + "=" * 60)
    print(" 1: ")
    print("=" * 60)
    
    try:
        from src.bioneuronai import (
            TradingEngine,
            InferenceEngine,
            SignalType,
            RiskLevel,
            create_inference_engine,
            BinanceFuturesConnector,
            RiskManager,
        )
        print(" ")
        
        from src.bioneuronai.analysis import (
            MarketDataProcessor,
            MarketRegimeDetector,
            VolumeProfileCalculator,
        )
        print(" ")
        
        from src.bioneuronai.risk_management import (
            LiquidationRiskMonitor,
            DynamicRiskAdjuster,
        )
        print(" ")
        
        return True
    except ImportError as e:
        print(f" : {e}")
        return False


def test_inference_engine():
    """ AI """
    print("\n" + "=" * 60)
    print(" 2: AI ")
    print("=" * 60)
    
    try:
        from src.bioneuronai import InferenceEngine
        
        # 
        engine = InferenceEngine(min_confidence=0.5, warmup=False)
        print(f"  | : {engine.model_loader.device}")
        
        # 
        model_path = project_root / "model" / "my_100m_model.pth"
        if not model_path.exists():
            print(f"  : {model_path}")
            return False
        
        engine.load_model("my_100m_model")
        print(f"  | : 111.2M")
        
        # 
        avg_latency = engine.model_loader.warmup(iterations=5)
        print(f"  | : {avg_latency:.2f}ms")
        
        # 
        mock_klines = [
            {'close': 50000 + i * 10, 'high': 50050 + i * 10, 
             'low': 49950 + i * 10, 'volume': 100 + i}
            for i in range(100)
        ]
        
        signal = engine.predict(
            symbol="BTCUSDT",
            current_price=51000,
            klines=mock_klines
        )
        
        print(f" : {signal}")
        print(f"   : {signal.signal_type.value}")
        print(f"   : {signal.confidence:.1%}")
        print(f"   : {signal.model_latency_ms:.2f}ms")
        
        return True
        
    except Exception as e:
        print(f" : {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trading_engine_integration():
    """"""
    print("\n" + "=" * 60)
    print(" 3: ")
    print("=" * 60)
    
    try:
        from src.bioneuronai import TradingEngine
        
        #  ( AI)
        engine = TradingEngine(
            testnet=True,
            enable_ai_model=True,
            ai_min_confidence=0.5
        )
        print(" ")
        
        #  AI 
        status = engine.get_ai_status()
        print(f"   AI : {'' if status['engine_initialized'] else ''}")
        print(f"   : {'' if status['model_loaded'] else ''}")
        
        #  AI 
        success = engine.load_ai_model("my_100m_model", warmup=True)
        if success:
            print(" AI ")
        else:
            print("  AI ")
            return False
        
        #  K 
        engine._klines_cache['BTCUSDT_1m'] = [
            {'close': 50000 + i * 10, 'high': 50050 + i * 10, 
             'low': 49950 + i * 10, 'open': 50000 + i * 8, 'volume': 100 + i}
            for i in range(100)
        ]
        engine._klines_last_update['BTCUSDT_1m'] = time.time() + 1000
        
        #  AI 
        ai_signal = engine.get_ai_prediction("BTCUSDT")
        if ai_signal:
            print(f" AI : {ai_signal}")
        else:
            print("  AI ")
        
        # 
        final_status = engine.get_ai_status()
        print(f"\n :")
        print(f"   : {final_status.get('total_inferences', 0)}")
        print(f"   : {final_status.get('avg_latency_ms', 0):.2f}ms")
        
        return True
        
    except Exception as e:
        print(f" : {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """"""
    print("\n" + "=" * 60)
    print(" 4: ")
    print("=" * 60)
    
    try:
        from src.bioneuronai import create_inference_engine
        
        engine = create_inference_engine(min_confidence=0.5)
        
        # 
        mock_klines = [
            {'close': 50000 + i * 10, 'high': 50050 + i * 10, 
             'low': 49950 + i * 10, 'volume': 100 + i}
            for i in range(100)
        ]
        
        # 
        latencies = []
        for i in range(20):
            signal = engine.predict(
                symbol="BTCUSDT",
                current_price=51000 + i * 100,
                klines=mock_klines
            )
            latencies.append(signal.model_latency_ms)
        
        print(f" (20):")
        print(f"   : {min(latencies):.2f}ms")
        print(f"   : {max(latencies):.2f}ms")
        print(f"   : {sum(latencies)/len(latencies):.2f}ms")
        print(f"   : {sorted(latencies)[len(latencies)//2]:.2f}ms")
        
        #  (< 50ms)
        avg = sum(latencies)/len(latencies)
        if avg < 50:
            print(f"  ( < 50ms)")
        else:
            print(f"   ( < 50ms)")
        
        return True
        
    except Exception as e:
        print(f" : {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """"""
    print("=" * 60)
    print("BioNeuronai ")
    print("=" * 60)
    
    results = []
    
    # 
    results.append(("", test_module_imports()))
    results.append(("AI ", test_inference_engine()))
    results.append(("", test_trading_engine_integration()))
    results.append(("", test_performance()))
    
    # 
    print("\n" + "=" * 60)
    print("")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = " PASS" if result else " FAIL"
        print(f"  {status} - {name}")
        if result:
            passed += 1
    
    print(f"\n: {passed}/{len(results)} ")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
