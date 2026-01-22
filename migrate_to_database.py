"""
數據遷移工具
=============

將舊的 JSON/JSONL 數據遷移到 SQLite 數據庫

使用方法:
    python migrate_to_database.py
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sys

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.bioneuronai.data.database_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_trades(db: DatabaseManager, data_dir: Path):
    """遷移交易記錄"""
    trades_file = data_dir / "trades_history.jsonl"
    
    if not trades_file.exists():
        logger.info("📭 未找到交易記錄文件")
        return 0
    
    logger.info(f"📂 讀取交易記錄: {trades_file}")
    count = 0
    
    with open(trades_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                trade = json.loads(line.strip())
                
                # 標準化字段
                trade_info = {
                    'order_id': trade.get('order_id', f"legacy_{count}"),
                    'symbol': trade.get('symbol'),
                    'side': trade.get('side'),
                    'quantity': trade.get('quantity'),
                    'price': trade.get('price'),
                    'confidence': trade.get('confidence'),
                    'strategy': trade.get('strategy'),
                    'timestamp': trade.get('timestamp', datetime.now().isoformat()),
                    'pnl': trade.get('pnl'),
                    'fee': trade.get('fee')
                }
                
                db.save_trade(trade_info)
                count += 1
                
            except Exception as e:
                logger.error(f"遷移交易記錄失敗: {e}")
    
    logger.info(f"✅ 遷移交易記錄: {count} 條")
    return count


def migrate_signals(db: DatabaseManager, data_dir: Path):
    """遷移信號歷史"""
    signals_file = data_dir / "signals_history.json"
    
    if not signals_file.exists():
        logger.info("📭 未找到信號記錄文件")
        return 0
    
    logger.info(f"📂 讀取信號記錄: {signals_file}")
    
    with open(signals_file, 'r', encoding='utf-8') as f:
        signals = json.load(f)
    
    count = 0
    for signal in signals:
        try:
            signal_info = {
                'symbol': signal.get('symbol'),
                'action': signal.get('action'),
                'confidence': signal.get('confidence'),
                'strategy_name': signal.get('strategy_name'),
                'reason': signal.get('reason'),
                'target_price': signal.get('target_price'),
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit'),
                'timestamp': signal.get('timestamp', datetime.now().isoformat()),
                'executed': signal.get('executed', False)
            }
            
            db.save_signal(signal_info)
            count += 1
            
        except Exception as e:
            logger.error(f"遷移信號記錄失敗: {e}")
    
    logger.info(f"✅ 遷移信號記錄: {count} 條")
    return count


def migrate_risk_stats(db: DatabaseManager, data_dir: Path):
    """遷移風險統計"""
    risk_file = data_dir / "risk_statistics.json"
    
    if not risk_file.exists():
        logger.info("📭 未找到風險統計文件")
        return 0
    
    logger.info(f"📂 讀取風險統計: {risk_file}")
    
    with open(risk_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    # 保存當前快照
    db.save_risk_stats(stats)
    
    logger.info(f"✅ 遷移風險統計: 1 條")
    return 1


def backup_old_files(data_dir: Path):
    """備份舊數據文件"""
    backup_dir = data_dir / "legacy_backup"
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "trades_history.jsonl",
        "signals_history.json",
        "risk_statistics.json",
        "risk_config.json",
        "strategy_weights.json"
    ]
    
    logger.info(f"📦 備份舊數據到: {backup_dir}")
    
    for filename in files_to_backup:
        src = data_dir / filename
        if src.exists():
            dst = backup_dir / f"{filename}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            src.rename(dst)
            logger.info(f"   ✓ {filename} -> {dst.name}")


def main():
    """執行數據遷移"""
    print("\n" + "=" * 60)
    print("🔄 BioNeuronai 數據庫遷移工具")
    print("=" * 60 + "\n")
    
    data_dir = Path("trading_data")
    
    if not data_dir.exists():
        logger.error(f"❌ 數據目錄不存在: {data_dir}")
        return
    
    # 初始化數據庫
    logger.info("🗄️  初始化數據庫...")
    db = DatabaseManager(db_path="trading_data/trading.db", backup_enabled=True)
    
    # 遷移數據
    logger.info("\n📊 開始數據遷移...")
    
    total_trades = migrate_trades(db, data_dir)
    total_signals = migrate_signals(db, data_dir)
    total_risk = migrate_risk_stats(db, data_dir)
    
    # 顯示統計
    print("\n" + "=" * 60)
    print("📈 遷移統計")
    print("=" * 60)
    
    stats = db.get_database_stats()
    print(f"  交易記錄: {stats['trades']} 條")
    print(f"  信號記錄: {stats['signals']} 條")
    print(f"  風險統計: {stats['risk_stats']} 條")
    print(f"  數據庫大小: {stats['db_size_mb']:.2f} MB")
    
    # 詢問是否備份舊文件
    print("\n" + "=" * 60)
    response = input("是否備份並移除舊的 JSON/JSONL 文件? (y/N): ")
    
    if response.lower() == 'y':
        backup_old_files(data_dir)
        logger.info("✅ 舊文件已備份")
    else:
        logger.info("⏭️  保留舊文件")
    
    print("\n" + "=" * 60)
    print("✅ 數據遷移完成!")
    print("=" * 60 + "\n")
    
    # 關閉數據庫
    db.close()


if __name__ == "__main__":
    main()
