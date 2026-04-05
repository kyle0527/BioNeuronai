"""Historical replay data stream.

Responsibilities:
- load historical Binance data from the replay data root
- expose bars in strict time order
- prevent look-ahead access to future bars

This module is a data source. It does not contain strategy logic.
"""

import pandas as pd
import zipfile
import logging
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List, Tuple, Union, cast
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

from .paths import BACKTEST_DATA_DIR, candidate_data_roots

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = BACKTEST_DATA_DIR


@dataclass
class KlineBar:
    """K線數據結構 - 模擬 Binance API 返回格式"""
    symbol: str
    interval: str
    open_time: int          # 毫秒時間戳
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int
    taker_buy_base: float
    taker_buy_quote: float
    
    def to_list(self) -> List:
        """轉換為 Binance API 格式的 list"""
        return [
            self.open_time,
            str(self.open),
            str(self.high),
            str(self.low),
            str(self.close),
            str(self.volume),
            self.close_time,
            str(self.quote_volume),
            self.trades,
            str(self.taker_buy_base),
            str(self.taker_buy_quote),
            "0"  # ignore
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'symbol': self.symbol,
            'interval': self.interval,
            'open_time': self.open_time,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'close_time': self.close_time,
            'quote_volume': self.quote_volume,
            'trades': self.trades,
            'taker_buy_base': self.taker_buy_base,
            'taker_buy_quote': self.taker_buy_quote,
            # 額外便利欄位
            'c': self.close,
            'o': self.open,
            'h': self.high,
            'l': self.low,
            'v': self.volume,
        }


@dataclass 
class StreamState:
    """串流狀態追蹤"""
    current_index: int = 0
    total_bars: int = 0
    current_time: Optional[datetime] = None
    is_running: bool = False
    is_paused: bool = False
    speed_multiplier: float = 1.0
    bars_delivered: int = 0
    start_time: Optional[float] = None


def resolve_data_dir(data_dir: Optional[Union[str, Path]] = None) -> Path:
    """解析回放資料根目錄，優先使用 backtest/ 內資料，再回退到既有專案資料。"""
    candidates = candidate_data_roots(data_dir)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        "找不到歷史資料根目錄。已嘗試:\n" +
        "\n".join(f"  - {candidate}" for candidate in candidates)
    )


class HistoricalDataStream:
    """
    歷史數據串流生成器
    
    核心原則：
    1. 嚴格防偷看 - 使用 yield 確保數據只能按時間順序讀取
    2. 時間隔離 - 在 T 時刻，只能看到 T 及之前的數據
    3. 狀態追蹤 - 完整記錄當前播放位置
    
    使用方式：
        stream = HistoricalDataStream(
            data_dir="backtest/data/binance_historical",
            symbol="BTCUSDT",
            interval="1m",
            start_date="2025-01-01",
            end_date="2025-06-30"
        )
        
        # 方法 1: 生成器逐根吐出
        for bar in stream.stream_bars():
            process_bar(bar)
            
        # 方法 2: 獲取到當前時間點的所有歷史數據
        historical_klines = stream.get_klines_until_now(limit=100)
    """
    
    # Binance K線 CSV 欄位名稱
    KLINE_COLUMNS = [
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ]
    
    def __init__(
        self,
        data_dir: Union[str, Path] = DEFAULT_DATA_DIR,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        speed_multiplier: float = 0.0,  # 0 = 無延遲, 1.0 = 實時, >1 = 加速
        preload: bool = True
    ):
        """
        初始化歷史數據串流
        
        Args:
            data_dir: 數據目錄路徑 (包含 data/futures/um/daily/klines/...)
            symbol: 交易對符號
            interval: K線間隔 (1m, 5m, 15m, 1h, 4h, 1d)
            start_date: 開始日期 (YYYY-MM-DD)，None 表示從最早數據開始
            end_date: 結束日期 (YYYY-MM-DD)，None 表示到最新數據結束
            speed_multiplier: 播放速度倍數 (0=無延遲, 1=實時, 10=10倍速)
            preload: 是否預載入所有數據到內存
        """
        self.data_dir = resolve_data_dir(data_dir)
        self.symbol = symbol.upper()
        self.interval = interval
        self.start_date = start_date
        self.end_date = end_date
        self.speed_multiplier = speed_multiplier
        
        # 數據存儲
        self._data: Optional[pd.DataFrame] = None
        self._data_loaded = False
        
        # 串流狀態
        self.state = StreamState(speed_multiplier=speed_multiplier)
        
        # 歷史窗口 - 用於模擬 get_klines 的回傳
        self._history_window: List[KlineBar] = []
        self._max_history_size = 1500  # 最多保留 1500 根 K線歷史
        
        # 計算間隔秒數
        self._interval_seconds = self._parse_interval(interval)
        
        logger.info(f"初始化歷史數據串流: {symbol} {interval}")
        logger.info(f"日期範圍: {start_date or '最早'} ~ {end_date or '最新'}")
        logger.info(f"播放速度: {speed_multiplier}x {'(無延遲)' if speed_multiplier == 0 else ''}")
        
        if preload:
            self.load_data()
    
    def _parse_interval(self, interval: str) -> int:
        """解析 K線間隔為秒數"""
        unit = interval[-1]
        value = int(interval[:-1])
        
        multipliers = {
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800,
            'M': 2592000  # 30 天
        }
        
        return value * multipliers.get(unit, 60)
    
    def _find_data_path(self) -> Path:
        """尋找數據目錄路徑"""
        # 嘗試標準 Binance 歷史數據目錄結構
        possible_paths = [
            self.data_dir / "data" / "futures" / "um" / "daily" / "klines" / self.symbol / self.interval,
            self.data_dir / "futures" / "um" / "daily" / "klines" / self.symbol / self.interval,
            self.data_dir / self.symbol / self.interval,
            self.data_dir / self.interval,
            self.data_dir,
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        raise FileNotFoundError(
            "找不到數據目錄。已嘗試:\n" + 
            "\n".join(f"  - {p}" for p in possible_paths)
        )

    def _iter_zip_files(self, data_path: Path) -> List[Path]:
        """列出 interval 目錄底下所有可讀取的 zip，支援分段子資料夾。"""
        direct = sorted(
            path for path in data_path.glob("*.zip")
            if "CHECKSUM" not in path.name
        )
        if direct:
            return direct

        nested = sorted(
            path for path in data_path.rglob("*.zip")
            if "CHECKSUM" not in path.name
        )
        return nested
    
    def load_data(self) -> pd.DataFrame:
        """
        載入歷史數據
        
        Returns:
            載入的 DataFrame
        """
        if self._data_loaded and self._data is not None:
            return self._data
        
        logger.info("開始載入歷史數據...")
        
        data_path = self._find_data_path()
        logger.info(f"數據路徑: {data_path}")
        
        # 確定日期範圍
        start = pd.to_datetime(self.start_date) if self.start_date else None
        end = pd.to_datetime(self.end_date) if self.end_date else None
        
        all_dfs = []
        
        # 載入 ZIP 文件（支援 interval 目錄下再分日期區段子資料夾）
        zip_files = self._iter_zip_files(data_path)
        
        for zip_file in zip_files:
            if "CHECKSUM" in zip_file.name:
                continue
            
            try:
                # 從文件名提取日期
                # 格式: BTCUSDT-1m-2025-01-01.zip
                parts = zip_file.stem.split("-")
                if len(parts) >= 4:
                    file_date_str = "-".join(parts[-3:])
                    file_date = pd.to_datetime(file_date_str)
                    
                    # 日期過濾
                    if start and file_date < start:
                        continue
                    if end and file_date > end:
                        continue
                
                df = self._read_kline_zip(zip_file)
                all_dfs.append(df)
                
            except Exception as e:
                logger.warning(f"讀取 {zip_file.name} 失敗: {e}")
        
        if not all_dfs:
            raise ValueError("在指定日期範圍內找不到任何數據")
        
        # 合併並排序
        combined = cast(pd.DataFrame, pd.concat(all_dfs, ignore_index=True))
        combined = cast(pd.DataFrame, combined.sort_values('open_time').reset_index(drop=True))

        # 日期範圍精確過濾
        if start:
            start_ts = int(start.timestamp() * 1000)
            combined = cast(pd.DataFrame, combined[combined['open_time'] >= start_ts])
        if end:
            end_ts = int((end + timedelta(days=1)).timestamp() * 1000)
            combined = cast(pd.DataFrame, combined[combined['open_time'] < end_ts])

        self._data = cast(pd.DataFrame, combined.reset_index(drop=True))
        self._data_loaded = True
        
        # 更新狀態
        self.state.total_bars = len(self._data)
        
        # 轉換時間顯示
        first_time = datetime.fromtimestamp(self._data['open_time'].iloc[0] / 1000)
        last_time = datetime.fromtimestamp(self._data['open_time'].iloc[-1] / 1000)
        
        logger.info(f"✅ 載入完成: {len(self._data):,} 根 K線")
        logger.info(f"時間範圍: {first_time} ~ {last_time}")
        
        return self._data
    
    def _read_kline_zip(self, zip_file: Path) -> pd.DataFrame:
        """從 ZIP 文件讀取 K線數據"""
        with zipfile.ZipFile(zip_file) as z:
            csv_candidates = [name for name in z.namelist() if name.endswith(".csv")]
            if not csv_candidates:
                raise FileNotFoundError(f"{zip_file.name} 內沒有 CSV")
            csv_name = csv_candidates[0]
            with z.open(csv_name) as f:
                # CSV 有表頭，使用 header=0 跳過第一行
                df = pd.read_csv(f, header=0, names=self.KLINE_COLUMNS)
        
        # 數值類型轉換
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                       'quote_volume', 'taker_buy_base', 'taker_buy_quote']
        df[numeric_cols] = df[numeric_cols].astype(float)
        df['trades'] = df['trades'].astype(int)
        df['open_time'] = df['open_time'].astype(int)
        df['close_time'] = df['close_time'].astype(int)
        
        # 刪除 ignore 欄位
        df = cast(pd.DataFrame, df.drop('ignore', axis=1, errors='ignore'))

        return df
    
    def stream_bars(self, start_from: int = 0) -> Generator[KlineBar, None, None]:
        """
        🔥 核心方法：生成器逐根吐出 K線數據
        
        這是防偷看的關鍵！使用 yield 確保數據只能按時間順序讀取
        在 T 時刻，絕對不可能讀取到 T+1 的數據
        
        Args:
            start_from: 從第幾根開始 (0-indexed)
            
        Yields:
            KlineBar: 每根 K線數據
        """
        if not self._data_loaded:
            self.load_data()
        
        if self._data is None:
            raise RuntimeError("數據未載入")
        
        self.state.is_running = True
        self.state.current_index = start_from
        self.state.start_time = time.time()
        self.state.bars_delivered = 0
        
        # 清空歷史窗口
        self._history_window.clear()
        
        # 計算延遲
        delay = self._interval_seconds / self.speed_multiplier if self.speed_multiplier > 0 else 0
        
        logger.info(f"🚀 開始串流 (從第 {start_from} 根開始)")
        
        try:
            for i in range(start_from, len(self._data)):
                if not self.state.is_running:
                    logger.info("串流已停止")
                    break
                
                # 暫停控制
                while self.state.is_paused and self.state.is_running:
                    time.sleep(0.01)
                
                # 讀取當前行
                row = self._data.iloc[i]
                
                # 創建 KlineBar
                bar = KlineBar(
                    symbol=self.symbol,
                    interval=self.interval,
                    open_time=int(row['open_time']),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row['volume']),
                    close_time=int(row['close_time']),
                    quote_volume=float(row['quote_volume']),
                    trades=int(row['trades']),
                    taker_buy_base=float(row['taker_buy_base']),
                    taker_buy_quote=float(row['taker_buy_quote'])
                )
                
                # 更新歷史窗口 (用於 get_klines)
                self._history_window.append(bar)
                if len(self._history_window) > self._max_history_size:
                    self._history_window.pop(0)
                
                # 更新狀態
                self.state.current_index = i
                self.state.current_time = datetime.fromtimestamp(bar.open_time / 1000)
                self.state.bars_delivered += 1
                
                # 🔥 yield - 這是防偷看的關鍵！
                yield bar
                
                # 速度控制延遲
                if delay > 0:
                    time.sleep(delay)
                    
        finally:
            self.state.is_running = False
            logger.info(f"串流結束: 共輸出 {self.state.bars_delivered} 根 K線")
    
    def get_klines_until_now(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        獲取到當前時間點的歷史 K線 (防偷看)
        
        這個方法只會返回已經通過 stream_bars() 輸出的數據
        絕對不會包含未來數據！
        
        Args:
            limit: 最多返回多少根 K線
            
        Returns:
            K線列表 (格式與 Binance API 相同)
        """
        if not self._history_window:
            return []
        
        # 只返回已經「發生」的數據
        recent = self._history_window[-limit:] if limit < len(self._history_window) else self._history_window
        return [bar.to_dict() for bar in recent]
    
    def get_klines_list_format(self, limit: int = 500) -> List[List]:
        """
        獲取 K線數據 (Binance API list 格式)
        
        返回格式與 BinanceFuturesConnector.get_klines() 完全相同
        """
        if not self._history_window:
            return []
        
        recent = self._history_window[-limit:] if limit < len(self._history_window) else self._history_window
        return [bar.to_list() for bar in recent]
    
    def get_current_bar(self) -> Optional[KlineBar]:
        """獲取當前 K線"""
        if self._history_window:
            return self._history_window[-1]
        return None
    
    def get_current_price(self) -> float:
        """獲取當前價格 (最新 K線的 close)"""
        if self._history_window:
            return self._history_window[-1].close
        return 0.0
    
    def get_current_time(self) -> Optional[datetime]:
        """獲取當前模擬時間"""
        return self.state.current_time
    
    def peek_next_bar(self) -> Optional[KlineBar]:
        """
        ⚠️ 偵錯用：偷看下一根 K線 (正式回測不應使用！)
        
        這個方法違反防偷看原則，僅用於偵錯和驗證
        """
        if self._data is None or self.state.current_index + 1 >= len(self._data):
            return None
        
        logger.warning("⚠️ peek_next_bar: 偷看未來數據 (僅供偵錯)")
        
        row = self._data.iloc[self.state.current_index + 1]
        return KlineBar(
            symbol=self.symbol,
            interval=self.interval,
            open_time=int(row['open_time']),
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=float(row['volume']),
            close_time=int(row['close_time']),
            quote_volume=float(row['quote_volume']),
            trades=int(row['trades']),
            taker_buy_base=float(row['taker_buy_base']),
            taker_buy_quote=float(row['taker_buy_quote'])
        )
    
    def pause(self):
        """暫停串流"""
        self.state.is_paused = True
        logger.info("⏸️ 串流已暫停")
    
    def resume(self):
        """繼續串流"""
        self.state.is_paused = False
        logger.info("▶️ 串流已繼續")
    
    def stop(self):
        """停止串流"""
        self.state.is_running = False
        logger.info("⏹️ 串流已停止")
    
    def reset(self):
        """重置串流狀態"""
        self.state = StreamState(speed_multiplier=self.speed_multiplier)
        self._history_window.clear()
        logger.info("🔄 串流已重置")
    
    def get_progress(self) -> Tuple[int, int, float]:
        """
        獲取進度
        
        Returns:
            (current_index, total_bars, percentage)
        """
        pct = (self.state.current_index / self.state.total_bars * 100) if self.state.total_bars > 0 else 0
        return self.state.current_index, self.state.total_bars, pct
    
    def seek(self, index: int):
        """
        跳轉到指定位置
        
        注意：這會清空歷史窗口，需要重新填充
        
        Args:
            index: 目標索引 (0-indexed)
        """
        if self._data is None:
            raise RuntimeError("數據未載入")
        
        if index < 0 or index >= len(self._data):
            raise ValueError(f"索引超出範圍: {index} (總共 {len(self._data)} 根)")
        
        # 清空歷史並重新填充
        self._history_window.clear()
        
        # 填充歷史窗口 (從 index 往前推)
        start = max(0, index - self._max_history_size + 1)
        for i in range(start, index + 1):
            row = self._data.iloc[i]
            bar = KlineBar(
                symbol=self.symbol,
                interval=self.interval,
                open_time=int(row['open_time']),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=float(row['volume']),
                close_time=int(row['close_time']),
                quote_volume=float(row['quote_volume']),
                trades=int(row['trades']),
                taker_buy_base=float(row['taker_buy_base']),
                taker_buy_quote=float(row['taker_buy_quote'])
            )
            self._history_window.append(bar)
        
        self.state.current_index = index
        self.state.current_time = datetime.fromtimestamp(
            self._data.iloc[index]['open_time'] / 1000
        )
        
        logger.info(f"⏭️ 跳轉至索引 {index} ({self.state.current_time})")


# ============================================================
# 便利函數
# ============================================================

def create_stream(
    symbol: str = "BTCUSDT",
    interval: str = "1m",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_dir: Union[str, Path] = DEFAULT_DATA_DIR
) -> HistoricalDataStream:
    """
    快速創建數據串流
    
    Example:
        stream = create_stream("ETHUSDT", "5m", "2025-01-01", "2025-06-30")
        for bar in stream.stream_bars():
            print(bar.close)
    """
    return HistoricalDataStream(
        data_dir=data_dir,
        symbol=symbol,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        speed_multiplier=0  # 無延遲
    )
