#!/usr/bin/env python3
"""
BioNeuronAI 實際應用場景演示
展示如何在真實問題中使用生物啟發神經元
"""

import numpy as np
import time
from bioneuronai.core import BioNeuron, BioNet
from bioneuronai.improved_core import ImprovedBioNeuron, CuriositDrivenNet


def anomaly_detection_demo():
    """異常檢測應用演示"""
    print("=== 異常檢測應用 ===")
    
    # 創建專門用於異常檢測的神經元
    detector = ImprovedBioNeuron(
        num_inputs=3, 
        threshold=0.4, 
        memory_len=10,
        adaptive_threshold=True,
        seed=42
    )
    
    # 模擬正常數據流
    print("學習正常數據模式...")
    normal_patterns = []
    for _ in range(50):
        # 正常數據：在某個範圍內的隨機值
        normal = [
            np.random.normal(0.5, 0.1),  # 特徵 1: 均值0.5
            np.random.normal(0.3, 0.08), # 特徵 2: 均值0.3  
            np.random.normal(0.7, 0.12)  # 特徵 3: 均值0.7
        ]
        normal_patterns.append(normal)
        detector.improved_hebbian_learn(normal)
    
    # 測試數據（包含異常）
    test_data = [
        ([0.52, 0.28, 0.71], "正常"),     # 正常數據
        ([0.48, 0.32, 0.68], "正常"),     # 正常數據
        ([0.95, 0.85, 0.92], "異常"),     # 異常：值過高
        ([0.05, 0.02, 0.08], "異常"),     # 異常：值過低
        ([0.49, 0.31, 0.69], "正常"),     # 正常數據
        ([0.51, 0.88, 0.12], "異常"),     # 異常：模式不匹配
    ]
    
    print("\n異常檢測結果:")
    print("數據\t\t\t輸出\t新穎性\t判斷\t實際")
    print("-" * 60)
    
    for data, true_label in test_data:
        output = detector.forward(data)
        novelty = detector.enhanced_novelty_score()
        
        # 異常判斷：高新穎性表示異常
        predicted = "異常" if novelty > 0.6 else "正常"
        status = "✓" if predicted == true_label else "✗"
        
        data_str = f"[{data[0]:.2f},{data[1]:.2f},{data[2]:.2f}]"
        print(f"{data_str}\t{output:.3f}\t{novelty:.3f}\t{predicted}\t{true_label} {status}")


def adaptive_learning_demo():
    """自適應學習演示"""
    print("\n=== 自適應學習系統 ===")
    
    # 創建好奇心驅動的網路
    curious_net = CuriositDrivenNet(input_dim=2, hidden_dim=4)
    
    # 模擬環境變化的數據流
    environments = [
        ("環境A", lambda: [np.random.uniform(0.0, 0.5), np.random.uniform(0.0, 0.5)]),
        ("環境B", lambda: [np.random.uniform(0.5, 1.0), np.random.uniform(0.5, 1.0)]),  
        ("環境C", lambda: [np.random.uniform(0.0, 1.0), np.random.uniform(0.0, 1.0)]),
    ]
    
    print("系統適應不同環境的過程:")
    
    for env_name, data_generator in environments:
        print(f"\n--- 切換到 {env_name} ---")
        curiosities = []
        
        # 在每個環境中學習
        for step in range(20):
            data = data_generator()
            curiosity = curious_net.curious_learn(data)
            curiosities.append(curiosity)
            
            if step % 5 == 0:
                avg_curiosity = np.mean(curiosities[-5:]) if curiosities else 0
                print(f"  步驟 {step+1:2d}: 數據={[f'{x:.2f}' for x in data]}, "
                      f"好奇心={curiosity:.3f}, 平均好奇心={avg_curiosity:.3f}")
        
        # 顯示適應結果
        final_curiosity = np.mean(curiosities[-5:])
        adaptation_status = "高度好奇" if final_curiosity > 0.5 else "已適應"
        print(f"  {env_name} 適應狀態: {adaptation_status} (好奇心: {final_curiosity:.3f})")


def real_time_monitoring_demo():
    """即時監控系統演示"""
    print("\n=== 即時監控系統 ===")
    
    # 創建監控神經元陣列
    monitors = [
        ImprovedBioNeuron(num_inputs=2, threshold=0.6, seed=i, memory_len=15)
        for i in range(3)
    ]
    
    monitor_names = ["CPU使用率監控", "記憶體監控", "網路流量監控"]
    
    print("模擬系統監控（10秒運行）...")
    print("時間\tCPU\t記憶體\t網路\t警報")
    print("-" * 50)
    
    start_time = time.time()
    step = 0
    
    while time.time() - start_time < 3:  # 運行3秒作為演示
        # 模擬系統指標數據
        cpu_usage = np.random.uniform(0.1, 0.9) + (0.3 if step > 15 else 0)  # 中途增加負載
        memory_usage = np.random.uniform(0.2, 0.8)
        network_traffic = np.random.uniform(0.0, 1.0)
        
        # 模擬異常情況
        if step == 20:
            cpu_usage = 0.95  # CPU突然飆高
        if step == 25:
            network_traffic = 1.5  # 網路異常
        
        # 各監控器處理數據
        data = [cpu_usage, memory_usage]  # 簡化為2D輸入
        alerts = []
        
        for i, (monitor, name) in enumerate(zip(monitors, monitor_names)):
            output = monitor.forward(data)
            novelty = monitor.enhanced_novelty_score()
            
            # 異常警報條件
            if novelty > 0.7 or output > 0.9:
                alerts.append(name)
            
            # 自適應學習
            monitor.improved_hebbian_learn(data)
        
        # 顯示監控結果
        alert_str = ", ".join(alerts) if alerts else "正常"
        print(f"{step:2d}s\t{cpu_usage:.2f}\t{memory_usage:.2f}\t{network_traffic:.2f}\t{alert_str}")
        
        step += 1
        time.sleep(0.1)  # 模擬即時處理


def pattern_discovery_demo():
    """模式發現演示"""
    print("\n=== 自動模式發現 ===")
    
    # 創建模式發現系統
    discoverer = ImprovedBioNeuron(
        num_inputs=4, 
        threshold=0.3,
        memory_len=20,
        adaptive_threshold=True,
        seed=42
    )
    
    # 生成含有隱藏模式的數據
    print("生成含隱藏模式的數據流...")
    
    patterns = {
        "模式A": [0.8, 0.2, 0.7, 0.3],
        "模式B": [0.3, 0.8, 0.2, 0.7], 
        "模式C": [0.6, 0.6, 0.4, 0.4],
        "隨機": None
    }
    
    # 數據序列：模式會重複出現
    sequence = ["模式A", "隨機", "模式B", "隨機", "模式A", "隨機", "模式C", 
                "隨機", "模式B", "模式A", "隨機", "模式C"]
    
    discovered_patterns = []
    
    print("\n模式發現過程:")
    print("步驟\t數據類型\t\t新穎性\t判斷")
    print("-" * 45)
    
    for step, pattern_type in enumerate(sequence):
        if pattern_type == "隨機":
            data = [np.random.uniform(0, 1) for _ in range(4)]
        else:
            # 在模式基礎上加入小量噪音
            base_pattern = patterns[pattern_type]
            data = [p + np.random.normal(0, 0.05) for p in base_pattern]
        
        output = discoverer.forward(data)
        novelty = discoverer.enhanced_novelty_score()
        
        # 模式判斷：低新穎性表示已知模式
        if novelty < 0.3 and len(discoverer.input_memory) > 3:
            judgment = "已知模式"
        elif novelty > 0.7:
            judgment = "新模式!"
            if pattern_type not in ["隨機"] and pattern_type not in discovered_patterns:
                discovered_patterns.append(pattern_type)
        else:
            judgment = "普通數據"
        
        print(f"{step+1:2d}\t{pattern_type:12s}\t{novelty:.3f}\t{judgment}")
        
        # 學習
        discoverer.improved_hebbian_learn(data)
    
    print(f"\n發現的模式: {discovered_patterns}")
    
    # 顯示學習統計
    stats = discoverer.get_statistics()
    print(f"學習統計: 激活率={stats['activation_rate']:.2f}, "
          f"閾值={stats['current_threshold']:.3f}")


def main():
    """主函數"""
    print("BioNeuronAI 實際應用演示")
    print("=" * 60)
    
    try:
        anomaly_detection_demo()
        adaptive_learning_demo()
        real_time_monitoring_demo()
        pattern_discovery_demo()
        
        print("\n" + "=" * 60)
        print("所有演示完成！")
        print("\n💡 這些範例展示了 BioNeuronAI 在以下場景的應用:")
        print("• 異常檢測系統")
        print("• 自適應學習系統")  
        print("• 即時監控系統")
        print("• 自動模式發現")
        print("\n🚀 您可以基於這些範例開發自己的應用！")
        
    except KeyboardInterrupt:
        print("\n演示被用戶中斷")
    except Exception as e:
        print(f"\n演示過程中出現錯誤: {e}")


if __name__ == "__main__":
    main()