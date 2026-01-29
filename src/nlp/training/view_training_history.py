"""
訓練歷史查看器
===============
查看所有訓練記錄和模型版本
"""

import json
from pathlib import Path
from datetime import datetime
import sys


def load_training_log():
    """載入訓練記錄"""
    log_file = Path("training_log.json")
    if not log_file.exists():
        print("❌ 未找到訓練記錄文件 training_log.json")
        return None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_duration(seconds):
    """格式化時長"""
    if seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.1f}分鐘"
    else:
        return f"{seconds/3600:.1f}小時"


def print_summary(log):
    """打印總結"""
    print("=" * 80)
    print("📊 訓練歷史總覽")
    print("=" * 80)
    
    if not log["training_history"]:
        print("\n還沒有任何訓練記錄。")
        return
    
    print(f"\n總訓練次數: {len(log['training_history'])}")
    print(f"當前版本: v{log['current_version']}")
    print(f"最後訓練: {log['last_training_date']}")
    print(f"可用模型: {len(log['models'])} 個")


def print_detailed_history(log):
    """打印詳細歷史"""
    print("\n" + "=" * 80)
    print("📜 詳細訓練記錄")
    print("=" * 80)
    
    for i, record in enumerate(log["training_history"], 1):
        print(f"\n{'─' * 80}")
        print(f"訓練 #{i} - 版本 v{record['version']}")
        print(f"{'─' * 80}")
        
        print(f"📅 日期時間: {record['date']}")
        print(f"⏱️  訓練時長: {format_duration(record['duration_seconds'])}")
        
        print(f"\n📊 數據配置:")
        print(f"   • 樣本數: {record['num_samples']}")
        print(f"   • 訓練輪數: {record['epochs']}")
        print(f"   • 批次大小: {record['batch_size']}")
        print(f"   • 學習率: {record['learning_rate']}")
        print(f"   • 最大長度: {record['max_length']}")
        
        print(f"\n📈 訓練效果:")
        print(f"   • 初始損失: {record['initial_loss']:.4f}")
        print(f"   • 最終損失: {record['final_loss']:.4f}")
        print(f"   • 損失下降: {(1 - record['final_loss']/record['initial_loss'])*100:.1f}%")
        print(f"   • 初始困惑度: {record['initial_perplexity']:.2f}")
        print(f"   • 最終困惑度: {record['final_perplexity']:.2f}")
        
        print(f"\n💾 模型位置:")
        print(f"   {record['model_path']}")
        
        if i < len(log["training_history"]):
            # 與上次訓練比較
            if i > 1:
                prev = log["training_history"][i-2]
                loss_change = record['final_loss'] - prev['final_loss']
                perp_change = record['final_perplexity'] - prev['final_perplexity']
                
                print(f"\n📊 與上次比較:")
                if loss_change < 0:
                    print(f"   • 損失改善: {abs(loss_change):.4f} ⬇️")
                else:
                    print(f"   • 損失上升: {loss_change:.4f} ⬆️")
                
                if perp_change < 0:
                    print(f"   • 困惑度改善: {abs(perp_change):.2f} ⬇️")
                else:
                    print(f"   • 困惑度上升: {perp_change:.2f} ⬆️")


def print_models_comparison(log):
    """打印模型比較"""
    if len(log["models"]) < 2:
        return
    
    print("\n" + "=" * 80)
    print("🏆 模型性能比較")
    print("=" * 80)
    
    models_list = []
    for version, info in log["models"].items():
        models_list.append({
            "version": int(version),
            "loss": info["performance"]["final_loss"],
            "perplexity": info["performance"]["final_perplexity"],
            "date": info["date"],
            "path": info["path"]
        })
    
    # 按損失排序
    models_list.sort(key=lambda x: x["loss"])
    
    print("\n🥇 按損失排序（越低越好）:")
    for i, model in enumerate(models_list, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"{emoji} v{model['version']} - Loss: {model['loss']:.4f}, Perplexity: {model['perplexity']:.2f}")
    
    # 按困惑度排序
    models_list.sort(key=lambda x: x["perplexity"])
    
    print("\n🎯 按困惑度排序（越低越好）:")
    for i, model in enumerate(models_list, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"{emoji} v{model['version']} - Perplexity: {model['perplexity']:.2f}, Loss: {model['loss']:.4f}")
    
    # 最佳模型
    best_model = models_list[0]
    print(f"\n✨ 推薦使用: v{best_model['version']}")
    print(f"   路徑: {best_model['path']}")
    print(f"   性能: Loss={best_model['loss']:.4f}, Perplexity={best_model['perplexity']:.2f}")


def print_training_progress(log):
    """打印訓練進度圖"""
    if len(log["training_history"]) < 2:
        return
    
    print("\n" + "=" * 80)
    print("📈 訓練進度趨勢")
    print("=" * 80)
    
    print("\n損失趨勢:")
    max_loss = max(r["final_loss"] for r in log["training_history"])
    
    for record in log["training_history"]:
        bar_length = int((record["final_loss"] / max_loss) * 50)
        bar = "█" * bar_length
        print(f"v{record['version']:2d} | {bar} {record['final_loss']:.4f}")
    
    print("\n困惑度趨勢:")
    max_perp = max(r["final_perplexity"] for r in log["training_history"])
    
    for record in log["training_history"]:
        bar_length = int((record["final_perplexity"] / max_perp) * 50)
        bar = "█" * bar_length
        print(f"v{record['version']:2d} | {bar} {record['final_perplexity']:.2f}")


def export_to_csv(log):
    """導出到 CSV"""
    import csv
    
    output_file = "training_history.csv"
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'version', 'date', 'duration_seconds', 'num_samples', 'epochs',
            'batch_size', 'learning_rate', 'initial_loss', 'final_loss',
            'initial_perplexity', 'final_perplexity', 'model_path'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in log["training_history"]:
            writer.writerow({k: record[k] for k in fieldnames})
    
    print(f"\n✅ 已導出到: {output_file}")


def main():
    """主函數"""
    log = load_training_log()
    
    if log is None:
        return
    
    # 基本總結
    print_summary(log)
    
    if not log["training_history"]:
        return
    
    # 選擇顯示模式
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        print("\n" + "=" * 80)
        print("選擇查看模式:")
        print("  1. 簡要總覽（默認）")
        print("  2. 詳細記錄")
        print("  3. 模型比較")
        print("  4. 進度趨勢")
        print("  5. 全部信息")
        print("  6. 導出 CSV")
        print("=" * 80)
        
        choice = input("\n請選擇 (1-6) [默認:1]: ").strip() or "1"
        
        mode_map = {
            "1": "summary",
            "2": "detailed",
            "3": "comparison",
            "4": "progress",
            "5": "all",
            "6": "export"
        }
        
        mode = mode_map.get(choice, "summary")
    
    # 顯示內容
    if mode in ["detailed", "all"]:
        print_detailed_history(log)
    
    if mode in ["comparison", "all"]:
        print_models_comparison(log)
    
    if mode in ["progress", "all"]:
        print_training_progress(log)
    
    if mode == "export":
        export_to_csv(log)
    
    print("\n" + "=" * 80)
    print("💡 使用說明:")
    print("  • python view_training_history.py          - 交互式選擇")
    print("  • python view_training_history.py summary  - 簡要總覽")
    print("  • python view_training_history.py detailed - 詳細記錄")
    print("  • python view_training_history.py all      - 全部信息")
    print("=" * 80)


if __name__ == "__main__":
    main()
