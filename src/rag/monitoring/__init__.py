# -*- coding: utf-8 -*-
"""
RAG 系統基本監控
================

追蹤 RAG 系統的重要指標：
- 檢索請求數量
- 平均延遲時間
- 快取命中率
- 錯誤率和類型

使用範例:
    from rag.monitoring import get_monitor
    
    monitor = get_monitor()
    monitor.log_retrieval(latency_ms=12.5, cache_hit=True)
    stats = monitor.get_stats()

遵循 CODE_FIX_GUIDE.md 規範
"""

import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """檢索指標"""
    timestamp: datetime
    latency_ms: float
    cache_hit: bool
    result_count: int
    source: str  # "internal_kb", "news_api", "web", "hybrid"
    error: Optional[str] = None


class RAGMonitor:
    """
    RAG 系統監控器
    
    線程安全的輕量級監控，追蹤系統性能指標。
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Args:
            max_history: 保留的歷史記錄數量（防止內存過載）
        """
        self.max_history = max_history
        self._lock = threading.Lock()
        
        # 基本計數器
        self.total_requests = 0
        self.total_errors = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # 延遲統計
        self.latencies: List[float] = []
        
        # 按來源統計
        self.requests_by_source = defaultdict(int)
        self.errors_by_type = defaultdict(int)
        
        # 詳細歷史（可選存儲）
        self.history: List[RetrievalMetrics] = []
        
        # 啟動時間
        self.start_time = datetime.now()
        
        logger.info("✅ RAG 監控器已初始化")
    
    def log_retrieval(
        self,
        latency_ms: float,
        cache_hit: bool = False,
        result_count: int = 0,
        source: str = "unknown",
        error: Optional[str] = None
    ):
        """
        記錄一次檢索操作
        
        Args:
            latency_ms: 延遲時間（毫秒）
            cache_hit: 是否命中快取
            result_count: 返回結果數量
            source: 數據來源
            error: 錯誤信息（如果有）
        """
        with self._lock:
            self.total_requests += 1
            
            # 快取統計
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
            
            # 延遲統計
            if not error:
                self.latencies.append(latency_ms)
                # 限制歷史長度
                if len(self.latencies) > self.max_history:
                    self.latencies = self.latencies[-self.max_history:]
            
            # 來源統計
            self.requests_by_source[source] += 1
            
            # 錯誤統計
            if error:
                self.total_errors += 1
                self.errors_by_type[error] += 1
            
            # 保存詳細記錄（僅保留最近的）
            metric = RetrievalMetrics(
                timestamp=datetime.now(),
                latency_ms=latency_ms,
                cache_hit=cache_hit,
                result_count=result_count,
                source=source,
                error=error
            )
            self.history.append(metric)
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
    
    def get_stats(self) -> Dict:
        """獲取統計摘要"""
        with self._lock:
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # 延遲統計
            if self.latencies:
                avg_latency = sum(self.latencies) / len(self.latencies)
                min_latency = min(self.latencies)
                max_latency = max(self.latencies)
                # 計算 p50, p95, p99
                sorted_latencies = sorted(self.latencies)
                n = len(sorted_latencies)
                p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0
                p95 = sorted_latencies[int(n * 0.95)] if n > 0 else 0
                p99 = sorted_latencies[int(n * 0.99)] if n > 0 else 0
            else:
                avg_latency = min_latency = max_latency = p50 = p95 = p99 = 0
            
            # 快取命中率
            total_cache_ops = self.cache_hits + self.cache_misses
            cache_hit_rate = (
                self.cache_hits / total_cache_ops if total_cache_ops > 0 else 0
            )
            
            # 錯誤率
            error_rate = (
                self.total_errors / self.total_requests 
                if self.total_requests > 0 else 0
            )
            
            # QPS (Queries Per Second)
            qps = self.total_requests / uptime if uptime > 0 else 0
            
            return {
                "uptime_seconds": uptime,
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate": error_rate,
                "qps": qps,
                "latency": {
                    "avg_ms": avg_latency,
                    "min_ms": min_latency,
                    "max_ms": max_latency,
                    "p50_ms": p50,
                    "p95_ms": p95,
                    "p99_ms": p99,
                },
                "cache": {
                    "hits": self.cache_hits,
                    "misses": self.cache_misses,
                    "hit_rate": cache_hit_rate,
                },
                "by_source": dict(self.requests_by_source),
                "errors_by_type": dict(self.errors_by_type),
            }
    
    def get_recent_history(self, minutes: int = 5) -> List[RetrievalMetrics]:
        """獲取最近的歷史記錄"""
        with self._lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            return [m for m in self.history if m.timestamp >= cutoff]
    
    def reset(self):
        """重置所有統計"""
        with self._lock:
            self.total_requests = 0
            self.total_errors = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.latencies.clear()
            self.requests_by_source.clear()
            self.errors_by_type.clear()
            self.history.clear()
            self.start_time = datetime.now()
            logger.info("監控器統計已重置")
    
    def print_stats(self):
        """打印格式化的統計信息"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 RAG 系統性能監控")
        print("="*60)
        print(f"運行時間: {stats['uptime_seconds']:.1f} 秒")
        print(f"總請求數: {stats['total_requests']}")
        print(f"總錯誤數: {stats['total_errors']} ({stats['error_rate']*100:.2f}%)")
        print(f"QPS: {stats['qps']:.2f}")
        
        print("\n延遲統計 (ms):")
        print(f"  平均: {stats['latency']['avg_ms']:.2f}")
        print(f"  最小: {stats['latency']['min_ms']:.2f}")
        print(f"  最大: {stats['latency']['max_ms']:.2f}")
        print(f"  P50: {stats['latency']['p50_ms']:.2f}")
        print(f"  P95: {stats['latency']['p95_ms']:.2f}")
        print(f"  P99: {stats['latency']['p99_ms']:.2f}")
        
        print("\n快取統計:")
        print(f"  命中: {stats['cache']['hits']}")
        print(f"  未命中: {stats['cache']['misses']}")
        print(f"  命中率: {stats['cache']['hit_rate']*100:.2f}%")
        
        if stats['by_source']:
            print("\n按來源統計:")
            for source, count in stats['by_source'].items():
                print(f"  {source}: {count}")
        
        if stats['errors_by_type']:
            print("\n錯誤類型:")
            for error_type, count in stats['errors_by_type'].items():
                print(f"  {error_type}: {count}")
        
        print("="*60 + "\n")


# 全局單例
_monitor: Optional[RAGMonitor] = None
_monitor_lock = threading.Lock()


def get_monitor() -> RAGMonitor:
    """獲取全局監控器實例（單例）"""
    global _monitor
    if _monitor is None:
        with _monitor_lock:
            if _monitor is None:
                _monitor = RAGMonitor()
    return _monitor


def reset_monitor():
    """重置全局監控器"""
    global _monitor
    with _monitor_lock:
        if _monitor is not None:
            _monitor.reset()
        else:
            _monitor = RAGMonitor()
