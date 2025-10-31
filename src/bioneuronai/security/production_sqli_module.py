"""
生產級 SQL 注入檢測模組 - 實用可部署版本
包含完整的檢測邏輯、錯誤處理和日誌記錄

基於真實滲透測試經驗設計，支持多種數據庫和注入技術
遵循 aiva_common.schemas 和四大模組架構標準
"""

from __future__ import annotations

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
from aiva_common.utils import get_logger

from .base import BaseDetectionModule, DetectionEngineProtocol
from .config import SQLiConfig
from .manager import UnifiedSmartDetectionManager
from .utils import (
    delay_between_requests,
    extract_keywords,
    generate_boolean_payload_pairs,
    generate_time_payloads,
    generate_union_payloads,
    log_detection_error,
    log_detection_start,
)

logger = get_logger(__name__)


class ProductionUnionSQLiEngine(DetectionEngineProtocol):
    """生產級聯合查詢型 SQL 注入檢測引擎"""

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

        log_detection_start(logger, self.get_engine_name(), str(target.url))

        # 1. 檢測列數
        column_count = await self._detect_column_count(target, client, smart_manager)
        if not column_count:
            logger.debug("無法檢測到有效的列數")
            return findings

        logger.debug(f"檢測到列數: {column_count}")

        # 2. 生成針對性的 Union payloads
        union_payloads = generate_union_payloads(column_count)

        # 3. 獲取基準響應
        baseline_response = await smart_manager.get_baseline_response(client, target)
        if not baseline_response:
            return findings

        # 4. 執行檢測
        for payload in union_payloads:
            try:
                detection_result = await self._test_union_payload(
                    target, payload, client, baseline_response, task, smart_manager
                )
                if detection_result:
                    findings.append(detection_result)
                    logger.info(f"發現 Union SQLi 漏洞: {payload[:50]}...")
                    break  # 找到漏洞即停止

            except Exception as e:
                log_detection_error(
                    logger,
                    f"Union payload 測試失敗 ({payload[:30]}...)",
                    e,
                )
                continue

        return findings

    async def _detect_column_count(
        self,
        target: FunctionTaskTarget,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> int | None:
        """使用 ORDER BY 技術檢測查詢的列數"""
        for col_num in range(1, 11):  # 檢測 1-10 列
            try:
                payload = f"' ORDER BY {col_num}--"
                response = await smart_manager.send_request(
                    client, target, payload=payload
                )
                
                # 檢查是否出現錯誤，表示列數已超出
                if self._has_database_error(response.text):
                    return col_num - 1 if col_num > 1 else None
                    
            except Exception as e:
                log_detection_error(
                    logger, f"列數檢測錯誤 (第{col_num}列)", e
                )
                continue

        return 3  # 默認假設 3 列

    async def _get_baseline_response(
        self, target: FunctionTaskTarget, client: httpx.AsyncClient
    ) -> httpx.Response | None:
        """獲取基準響應"""
        try:
            if target.method.upper() == "GET":
                return await client.get(str(target.url), timeout=10.0)
            else:
                return await client.post(str(target.url), timeout=10.0)
        except Exception as e:
            logger.error(f"無法獲取基準響應: {e}")
            return None

    async def _send_payload_request(
        self, target: FunctionTaskTarget, payload: str, client: httpx.AsyncClient
    ) -> httpx.Response:
        """發送包含 payload 的請求"""
        if target.method.upper() == "GET":
            params = {target.parameter: payload}
            return await client.get(str(target.url), params=params, timeout=15.0)
        else:
            data = {target.parameter: payload}
            return await client.post(str(target.url), data=data, timeout=15.0)

    async def _test_union_payload(
        self,
        target: FunctionTaskTarget,
        payload: str,
        client: httpx.AsyncClient,
        baseline_response: httpx.Response,
        task: FunctionTaskPayload,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> FindingPayload | None:
        """測試單個 Union payload"""
        try:
            response = await smart_manager.send_request(
                client, target, payload=payload
            )
            
            # 分析響應
            analysis_result = self._analyze_union_response(
                response, baseline_response, payload
            )
            
            if analysis_result["is_vulnerable"]:
                return self._create_finding(
                    task,
                    target,
                    payload,
                    response,
                    analysis_result,
                    smart_manager,
                )

        except Exception as e:
            log_detection_error(
                logger,
                f"Union payload 測試錯誤 ({payload[:30]}...)",
                e,
            )
            
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
        smart_manager: UnifiedSmartDetectionManager,
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

        return smart_manager.serialize_finding(
            task,
            vulnerability=vulnerability,
            evidence=evidence,
            target=FindingTarget(
                url=str(target.url),
                parameter=target.parameter,
                method=target.method
            ),
        )


class ProductionBooleanSQLiEngine(DetectionEngineProtocol):
    """生產級布林型 SQL 注入檢測引擎"""

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

        log_detection_start(logger, self.get_engine_name(), str(target.url))

        # 生成布林測試 payload 對
        boolean_pairs = generate_boolean_payload_pairs()

        for true_payload, false_payload in boolean_pairs:
            try:
                # 發送 TRUE 條件請求
                true_response = await smart_manager.send_request(
                    client, target, payload=true_payload
                )
                await delay_between_requests()

                # 發送 FALSE 條件請求
                false_response = await smart_manager.send_request(
                    client, target, payload=false_payload
                )
                
                # 分析響應差異
                if self._has_boolean_injection(true_response, false_response):
                    finding = self._create_boolean_finding(
                        task,
                        target,
                        true_payload,
                        false_payload,
                        true_response,
                        false_response,
                        smart_manager,
                    )
                    findings.append(finding)
                    logger.info(f"發現 Boolean SQLi 漏洞: {true_payload[:50]}...")
                    break

            except Exception as e:
                log_detection_error(
                    logger,
                    f"Boolean SQLi 測試失敗 ({true_payload[:30]}...)",
                    e,
                )
                continue

        return findings

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
        true_keywords = extract_keywords(true_text)
        false_keywords = extract_keywords(false_text)
        
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

    def _create_boolean_finding(
        self,
        task: FunctionTaskPayload,
        target: FunctionTaskTarget,
        true_payload: str,
        false_payload: str,
        true_response: httpx.Response,
        false_response: httpx.Response,
        smart_manager: UnifiedSmartDetectionManager,
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

        return smart_manager.serialize_finding(
            task,
            vulnerability=vulnerability,
            evidence=evidence,
            target=FindingTarget(
                url=str(target.url),
                parameter=target.parameter,
                method=target.method,
            ),
        )


class ProductionTimeSQLiEngine(DetectionEngineProtocol):
    """生產級時間型 SQL 注入檢測引擎"""

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

        log_detection_start(logger, self.get_engine_name(), str(target.url))

        # 測量基準響應時間
        baseline_time = await self._measure_baseline_time(target, client, smart_manager)
        if baseline_time is None:
            return findings

        logger.debug(f"基準響應時間: {baseline_time:.2f}s")

        # 生成時間延遲 payloads
        time_payloads = generate_time_payloads()

        for payload, expected_delay in time_payloads:
            try:
                # 測量 payload 響應時間
                payload_time = await self._measure_payload_time(
                    target, payload, client, smart_manager
                )
                
                if payload_time is None:
                    continue

                # 檢測時間異常
                if self._has_time_anomaly(baseline_time, payload_time, expected_delay):
                    finding = self._create_time_finding(
                        task,
                        target,
                        payload,
                        baseline_time,
                        payload_time,
                        expected_delay,
                        smart_manager,
                    )
                    findings.append(finding)
                    logger.info(f"發現 Time-based SQLi 漏洞: {payload[:50]}...")
                    break

            except Exception as e:
                log_detection_error(
                    logger,
                    f"Time-based SQLi 測試失敗 ({payload[:30]}...)",
                    e,
                )
                continue

        return findings

    async def _measure_baseline_time(
        self,
        target: FunctionTaskTarget,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> float | None:
        """測量基準響應時間（多次測量取平均值）"""
        times = []
        
        for _ in range(3):  # 測量3次
            try:
                start_time = time.time()
                await smart_manager.send_request(client, target, timeout=20.0)
                end_time = time.time()
                
                times.append(end_time - start_time)
                await delay_between_requests(0.5)  # 間隔測量
                
            except Exception as e:
                log_detection_error(logger, "基準時間測量失敗", e)
                continue
        
        return sum(times) / len(times) if times else None

    async def _measure_payload_time(
        self,
        target: FunctionTaskTarget,
        payload: str,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> float | None:
        """測量包含 payload 的請求響應時間"""
        try:
            start_time = time.time()
            
            await smart_manager.send_request(
                client,
                target,
                payload=payload,
                timeout=30.0,
            )
            
            end_time = time.time()
            return end_time - start_time
            
        except Exception as e:
            log_detection_error(logger, "Payload 時間測量失敗", e)
            return None

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
        smart_manager: UnifiedSmartDetectionManager,
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

        return smart_manager.serialize_finding(
            task,
            vulnerability=vulnerability,
            evidence=evidence,
            target=FindingTarget(
                url=str(target.url),
                parameter=target.parameter,
                method=target.method,
            ),
        )


class ProductionSQLiModule(BaseDetectionModule):
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


