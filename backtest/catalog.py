"""回放資料目錄掃描與摘要工具。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from .data_stream import DEFAULT_DATA_DIR, resolve_data_dir


@dataclass
class DatasetInfo:
    symbol: str
    interval: str
    zip_count: int
    start_date: Optional[str]
    end_date: Optional[str]
    path: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "zip_count": self.zip_count,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "path": self.path,
        }


def _extract_date_from_name(filename: str) -> Optional[str]:
    parts = Path(filename).stem.split("-")
    if len(parts) < 5:
        return None
    return "-".join(parts[-3:])


def get_catalog(
    data_dir: Optional[Union[str, Path]] = DEFAULT_DATA_DIR,
    symbol: Optional[str] = None,
    interval: Optional[str] = None,
) -> Dict[str, object]:
    root = resolve_data_dir(data_dir)
    klines_root = root / "data" / "futures" / "um" / "daily" / "klines"

    datasets: List[DatasetInfo] = []
    if klines_root.exists():
        for symbol_dir in sorted(path for path in klines_root.iterdir() if path.is_dir()):
            if symbol and symbol_dir.name.upper() != symbol.upper():
                continue

            for interval_dir in sorted(path for path in symbol_dir.iterdir() if path.is_dir()):
                if interval and interval_dir.name != interval:
                    continue

                zip_files = sorted(
                    path for path in interval_dir.rglob("*.zip")
                    if "CHECKSUM" not in path.name
                )
                if not zip_files:
                    continue

                dates = [_extract_date_from_name(path.name) for path in zip_files]
                valid_dates = [date for date in dates if date is not None]
                datasets.append(
                    DatasetInfo(
                        symbol=symbol_dir.name,
                        interval=interval_dir.name,
                        zip_count=len(zip_files),
                        start_date=min(valid_dates) if valid_dates else None,
                        end_date=max(valid_dates) if valid_dates else None,
                        path=str(interval_dir),
                    )
                )

    return {
        "root": str(root),
        "dataset_count": len(datasets),
        "datasets": [dataset.to_dict() for dataset in datasets],
    }
