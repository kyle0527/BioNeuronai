"""
生產級 IDOR (不安全直接對象引用) 檢測模組
包含完整的檢測邏輯，支持多種IDOR攻擊模式

基於真實滲透測試經驗設計，檢測水平和垂直特權升級
遵循 aiva_common.schemas 和四大模組架構標準
"""

from __future__ import annotations

import asyncio
import json
import re
import uuid
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

from .common.base_function_module import BaseFunctionModule, DetectionEngineProtocol
from .common.detection_config import IDORConfig
from .common.unified_smart_detection_manager import UnifiedSmartDetectionManager
from .security.novelty_analyzer import NoveltyAnalyzer

logger = get_logger(__name__)


class ProductionHorizontalIDOREngine(DetectionEngineProtocol):
    """生產級水平特權升級檢測引擎"""

    def __init__(self) -> None:
        self.novelty_analyzer = NoveltyAnalyzer(use_improved=True, novelty_threshold=0.3)

    def get_engine_name(self) -> str:
        return "Production Horizontal IDOR Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測水平IDOR漏洞"""
        findings: list[FindingPayload] = []
        target = task.target

        logger.info(f"開始水平IDOR檢測: {target.url}")
        self.novelty_analyzer.reset()

        # 提取原始ID參數
        original_ids = self._extract_id_parameters(target)
        if not original_ids:
            logger.debug("未找到ID參數")
            return findings

        # 獲取原始響應作為基準
        baseline_response = await self._get_baseline_response(target, client)
        if not baseline_response:
            return findings

        self.novelty_analyzer.learn_normal(baseline_response)

        # 生成測試ID
        test_ids = self._generate_test_ids(original_ids)

        # 測試每個ID參數
        for param_name, original_value in original_ids.items():
            for test_value in test_ids:
                try:
                    # 構建測試請求
                    modified_target = self._modify_target_parameter(
                        target, param_name, test_value
                    )
                    
                    test_response = await self._send_request(modified_target, client)
                    
                    # 分析響應
                    analysis = self._analyze_horizontal_response(
                        baseline_response,
                        test_response,
                        original_value,
                        test_value,
                        self.novelty_analyzer,
                    )
                    
                    if analysis["is_vulnerable"]:
                        finding = self._create_horizontal_finding(
                            task, target, param_name, original_value, 
                            test_value, test_response, analysis
                        )
                        findings.append(finding)
                        logger.info(f"發現水平IDOR: {param_name}={test_value}")
                        break  # 找到漏洞即停止測試該參數

                except Exception as e:
                    logger.debug(f"水平IDOR測試失敗 ({param_name}={test_value}): {e}")
                    continue

        return findings

    def _extract_id_parameters(self, target: FunctionTaskTarget) -> dict[str, str]:
        """提取ID參數"""
        id_params = {}
        
        # 從URL參數中提取
        if hasattr(target, 'parameter') and target.parameter:
            # 檢查參數名是否像ID
            if self._is_id_parameter(target.parameter):
                # 這裡需要實際的參數值，暫時使用示例值
                id_params[target.parameter] = "1"
        
        # 從URL路徑中提取數字ID
        url_str = str(target.url)
        
        # 提取路徑中的數字ID
        path_ids = re.findall(r'/(\d+)(?:/|$)', url_str)
        for i, id_value in enumerate(path_ids):
            id_params[f"path_id_{i}"] = id_value
        
        # 提取查詢參數中的ID
        if '?' in url_str:
            query_part = url_str.split('?', 1)[1]
            for param_pair in query_part.split('&'):
                if '=' in param_pair:
                    key, value = param_pair.split('=', 1)
                    if self._is_id_parameter(key) and value.isdigit():
                        id_params[key] = value
        
        return id_params

    def _is_id_parameter(self, param_name: str) -> bool:
        """判斷參數名是否為ID參數"""
        id_indicators = [
            'id', 'user_id', 'userId', 'account_id', 'accountId',
            'profile_id', 'profileId', 'order_id', 'orderId',
            'document_id', 'documentId', 'file_id', 'fileId',
            'message_id', 'messageId', 'post_id', 'postId'
        ]
        
        param_lower = param_name.lower()
        return any(indicator in param_lower for indicator in id_indicators)

    async def _get_baseline_response(
        self, target: FunctionTaskTarget, client: httpx.AsyncClient
    ) -> httpx.Response | None:
        """獲取基準響應"""
        try:
            return await self._send_request(target, client)
        except Exception as e:
            logger.error(f"無法獲取基準響應: {e}")
            return None

    async def _send_request(
        self, target: FunctionTaskTarget, client: httpx.AsyncClient
    ) -> httpx.Response:
        """發送請求"""
        if target.method.upper() == "GET":
            return await client.get(str(target.url), timeout=15.0, follow_redirects=False)
        elif target.method.upper() == "POST":
            return await client.post(str(target.url), timeout=15.0, follow_redirects=False)
        else:
            # 其他HTTP方法
            return await client.request(
                target.method, str(target.url), timeout=15.0, follow_redirects=False
            )

    def _generate_test_ids(self, original_ids: dict[str, str]) -> list[str]:
        """生成測試ID"""
        test_ids = []
        
        for original_value in original_ids.values():
            if original_value.isdigit():
                original_int = int(original_value)
                
                # 數字ID測試策略
                test_ids.extend([
                    str(original_int + 1),  # 下一個ID
                    str(original_int - 1),  # 上一個ID
                    str(original_int + 10), # 跳躍ID
                    str(original_int * 2),  # 倍數ID
                    "999999",               # 大數字ID
                    "0",                    # 零ID
                    "-1",                   # 負數ID
                ])
            else:
                # 字符串ID測試策略
                test_ids.extend([
                    original_value + "1",     # 追加數字
                    original_value[:-1] + "0", # 修改最後字符
                    str(uuid.uuid4()),        # 隨機UUID
                    "admin",                  # 常見用戶名
                    "user",
                    "test",
                ])
        
        # 去重並限制數量
        return list(set(test_ids))[:10]

    def _modify_target_parameter(
        self, target: FunctionTaskTarget, param_name: str, new_value: str
    ) -> FunctionTaskTarget:
        """修改目標參數"""
        # 創建新的目標對象
        new_url = str(target.url)
        
        if param_name.startswith("path_id_"):
            # 修改路徑中的ID
            path_ids = re.findall(r'/(\d+)(?:/|$)', new_url)
            if path_ids:
                # 替換第一個找到的數字ID
                old_id = path_ids[0]
                new_url = new_url.replace(f'/{old_id}', f'/{new_value}', 1)
        else:
            # 修改查詢參數
            if '?' in new_url:
                base_url, query = new_url.split('?', 1)
                params = []
                found = False
                
                for param_pair in query.split('&'):
                    if '=' in param_pair:
                        key, value = param_pair.split('=', 1)
                        if key == param_name:
                            params.append(f"{key}={new_value}")
                            found = True
                        else:
                            params.append(param_pair)
                    else:
                        params.append(param_pair)
                
                if not found:
                    params.append(f"{param_name}={new_value}")
                
                new_url = f"{base_url}?{'&'.join(params)}"
            else:
                new_url = f"{new_url}?{param_name}={new_value}"
        
        # 使用已定義的 FunctionTaskTarget 來保持型別正確
        return FunctionTaskTarget(url=new_url, method=target.method, parameter=param_name)

    def _analyze_horizontal_response(
        self,
        baseline: httpx.Response,
        test_response: httpx.Response,
        original_id: str,
        test_id: str,
        novelty_analyzer: NoveltyAnalyzer | None,
    ) -> dict[str, Any]:
        """分析水平IDOR響應"""
        result = {
            "is_vulnerable": False,
            "confidence": Confidence.LOW,
            "evidence": [],
            "access_type": "none",
            "novelty_score": 0.0,
            "manual_review": False,
        }
        
        # 1. HTTP狀態碼分析
        if test_response.status_code == 200 and baseline.status_code == 200:
            # 成功訪問，可能的IDOR
            result["evidence"].append(f"成功訪問其他用戶資源 (ID: {test_id})")
            result["is_vulnerable"] = True
            result["confidence"] = Confidence.MEDIUM
            result["access_type"] = "successful_access"
        
        # 2. 響應內容分析
        baseline_text = baseline.text
        test_text = test_response.text
        
        # 檢查是否返回了不同的用戶數據
        if self._has_different_user_data(baseline_text, test_text, original_id, test_id):
            # 確保 evidence 為列表，避免對非列表物件調用 append 時發生錯誤
            if not isinstance(result.get("evidence"), list):
                result["evidence"] = []
            result["evidence"].append("檢測到不同用戶的敏感數據")
            result["is_vulnerable"] = True
            result["confidence"] = Confidence.HIGH
            result["access_type"] = "data_exposure"
        
        # 3. 響應長度差異
        length_diff = abs(len(test_text) - len(baseline_text))
        if length_diff > 100:  # 顯著差異
            result["evidence"].append(f"響應內容長度差異: {length_diff} 字符")
            if not result["is_vulnerable"]:
                result["is_vulnerable"] = True
                result["confidence"] = Confidence.LOW
        
        # 4. 敏感信息洩露檢測
        sensitive_patterns = [
            r'email.*?[\w\.-]+@[\w\.-]+\.\w+',
            r'phone.*?\d{10,}',
            r'ssn.*?\d{3}-\d{2}-\d{4}',
            r'credit.*card.*?\d{4}.*?\d{4}.*?\d{4}.*?\d{4}',
            r'address.*?\d+.*?street',
        ]
        
        for pattern in sensitive_patterns:
            baseline_matches = len(re.findall(pattern, baseline_text, re.IGNORECASE))
            test_matches = len(re.findall(pattern, test_text, re.IGNORECASE))
            
            if test_matches > baseline_matches:
                result["evidence"].append(f"檢測到額外的敏感信息洩露")
                result["is_vulnerable"] = True
                result["confidence"] = Confidence.HIGH
                break
        
        if novelty_analyzer is not None:
            novelty = novelty_analyzer.score_response(test_response)
            result["novelty_score"] = novelty.score
            if novelty.is_novel:
                result["evidence"].append(f"新穎度分數 {novelty.score:.2f} 高於閾值")
                if result["is_vulnerable"]:
                    result["confidence"] = max(result["confidence"], Confidence.HIGH)
                else:
                    result["manual_review"] = True
                    result["confidence"] = max(result["confidence"], Confidence.MEDIUM)

        return result

    def _has_different_user_data(
        self, baseline_text: str, test_text: str, original_id: str, test_id: str
    ) -> bool:
        """檢測是否返回了不同用戶的數據"""
        # 檢查ID在響應中的出現
        original_in_baseline = original_id in baseline_text
        test_in_response = test_id in test_text
        
        # 如果測試ID出現在響應中，可能表示訪問了其他用戶的資源
        if test_in_response and not (original_id == test_id):
            return True
        
        # 檢查用戶名模式
        username_pattern = r'(?:username|user|name)["\':\s]*([a-zA-Z0-9_]+)'
        
        baseline_users = set(re.findall(username_pattern, baseline_text, re.IGNORECASE))
        test_users = set(re.findall(username_pattern, test_text, re.IGNORECASE))
        
        # 如果出現了不同的用戶名
        different_users = test_users - baseline_users
        if different_users:
            return True
        
        return False

    def _create_horizontal_finding(
        self,
        task: FunctionTaskPayload,
        target: FunctionTaskTarget,
        param_name: str,
        original_value: str,
        test_value: str,
        response: httpx.Response,
        analysis: dict[str, Any],
    ) -> FindingPayload:
        """創建水平IDOR檢測結果"""
        vulnerability = Vulnerability(
            name=VulnerabilityType.IDOR,
            severity=Severity.LOW,
            confidence=analysis["confidence"]
        )

        evidence_text = "; ".join(analysis["evidence"])
        evidence = FindingEvidence(
            payload=f"參數: {param_name}, 原值: {original_value}, 測試值: {test_value}",
            response=f"訪問類型: {analysis['access_type']}. 證據: {evidence_text}. "
                    f"響應狀態: {response.status_code}, 響應長度: {len(response.text)}",
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
                parameter=param_name,
                method=target.method
            ),
            evidence=evidence
        )


class ProductionVerticalIDOREngine(DetectionEngineProtocol):
    """生產級垂直特權升級檢測引擎"""

    def __init__(self) -> None:
        self.novelty_analyzer = NoveltyAnalyzer(use_improved=True, novelty_threshold=0.35)

    def get_engine_name(self) -> str:
        return "Production Vertical IDOR Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測垂直IDOR漏洞（特權升級）"""
        findings: list[FindingPayload] = []
        target = task.target

        logger.info(f"開始垂直IDOR檢測: {target.url}")
        self.novelty_analyzer.reset()

        try:
            baseline_response = await client.get(str(target.url), timeout=10.0)
        except Exception:
            baseline_response = None

        if baseline_response is not None:
            self.novelty_analyzer.learn_normal(baseline_response)

        # 檢測管理員路徑和功能
        admin_paths = self._generate_admin_paths(target)
        
        for admin_path in admin_paths:
            try:
                # 構建管理員路徑請求
                admin_target = self._create_admin_target(target, admin_path)
                response = await self._send_request(admin_target, client)
                
                # 分析響應
                analysis = self._analyze_vertical_response(
                    response, admin_path, self.novelty_analyzer
                )
                
                if analysis["is_vulnerable"]:
                    finding = self._create_vertical_finding(
                        task, target, admin_path, response, analysis
                    )
                    findings.append(finding)
                    logger.info(f"發現垂直IDOR: {admin_path}")

            except Exception as e:
                logger.debug(f"垂直IDOR測試失敗 ({admin_path}): {e}")
                continue

        return findings

    def _generate_admin_paths(self, target: FunctionTaskTarget) -> list[str]:
        """生成管理員路徑"""
        base_url = str(target.url)
        
        # 從基礎URL提取路徑結構
        if '://' in base_url:
            base_path = base_url.split('://', 1)[1]
            if '/' in base_path:
                base_path = '/' + '/'.join(base_path.split('/')[1:-1])
            else:
                base_path = ''
        else:
            base_path = ''
        
        admin_paths = [
            f"{base_path}/admin",
            f"{base_path}/admin/",
            f"{base_path}/admin/users",
            f"{base_path}/admin/dashboard",
            f"{base_path}/admin/settings",
            f"{base_path}/administrator",
            f"{base_path}/manage",
            f"{base_path}/management",
            f"{base_path}/control",
            f"{base_path}/panel",
            "/admin",
            "/admin/",
            "/administrator",
            "/manage",
            "/control",
            "/panel",
        ]
        
        return admin_paths

    def _create_admin_target(self, target: FunctionTaskTarget, admin_path: str):
        """創建管理員路徑目標"""
        base_url = str(target.url)
        
        if '://' in base_url:
            scheme_and_host = base_url.split('://', 1)[0] + '://' + base_url.split('://', 1)[1].split('/')[0]
            admin_url = scheme_and_host + admin_path
        else:
            admin_url = admin_path
        
        class AdminTarget:
            def __init__(self, url: str, method: str):
                self.url = url
                self.method = method
                self.parameter = None
        
        return AdminTarget(admin_url, target.method)

    async def _send_request(self, target, client: httpx.AsyncClient) -> httpx.Response:
        """發送請求"""
        return await client.get(str(target.url), timeout=15.0, follow_redirects=False)

    def _analyze_vertical_response(
        self,
        response: httpx.Response,
        admin_path: str,
        novelty_analyzer: NoveltyAnalyzer | None,
    ) -> dict[str, Any]:
        """分析垂直IDOR響應並引入新穎度評分"""
        result = {
            "is_vulnerable": False,
            "confidence": Confidence.LOW,
            "evidence": [],
            "privilege_level": "none",
            "novelty_score": 0.0,
            "manual_review": False,
        }

        response_text = response.text.lower()

        # 1. 成功訪問管理員頁面
        if response.status_code == 200:
            result["evidence"].append(f"成功訪問管理員路徑: {admin_path}")

            admin_indicators = [
                "admin", "dashboard", "users", "settings", "configuration",
                "manage", "control", "delete", "edit all", "system",
                "管理", "儀表板", "用戶管理", "系統設置", "控制面板"
            ]

            found_indicators = [
                indicator for indicator in admin_indicators
                if indicator in response_text
            ]

            if found_indicators:
                result["is_vulnerable"] = True
                result["confidence"] = Confidence.HIGH
                result["privilege_level"] = "admin"
                result["evidence"].append(
                    f"檢測到管理員功能: {', '.join(found_indicators[:3])}"
                )

        # 2. 重定向到非登入頁面（可能繞過）
        elif response.status_code in [301, 302, 303, 307, 308]:
            location = response.headers.get("location", "").lower()
            if "login" not in location and "auth" not in location:
                result["is_vulnerable"] = True
                result["confidence"] = Confidence.MEDIUM
                result["privilege_level"] = "partial"
                result["evidence"].append(f"異常重定向到: {location}")

        # 3. 檢查響應中的敏感API端點
        api_patterns = [
            r'/api/admin/',
            r'/api/users/',
            r'/api/system/',
            r'api.*delete',
            r'api.*create',
            r'api.*update'
        ]

        for pattern in api_patterns:
            if re.search(pattern, response_text):
                result["is_vulnerable"] = True
                result["confidence"] = max(result["confidence"], Confidence.MEDIUM)
                result["privilege_level"] = "api_access"
                result["evidence"].append(f"檢測到敏感API端點: {pattern}")
                break

        if novelty_analyzer is not None:
            novelty = novelty_analyzer.score_response(response)
            result["novelty_score"] = novelty.score
            if novelty.is_novel:
                result["evidence"].append(f"新穎度分數 {novelty.score:.2f} 高於閾值")
                if result["is_vulnerable"]:
                    result["confidence"] = max(result["confidence"], Confidence.HIGH)
                else:
                    result["manual_review"] = True
                    result["confidence"] = max(result["confidence"], Confidence.MEDIUM)

        return result

    def _create_vertical_finding(
        self,
        task: FunctionTaskPayload,
        target: FunctionTaskTarget,
        admin_path: str,
        response: httpx.Response,
        analysis: dict[str, Any],
    ) -> FindingPayload:
        """創建垂直IDOR檢測結果"""
        vulnerability = Vulnerability(
            name=VulnerabilityType.IDOR,
            severity=Severity.LOW,
            confidence=analysis["confidence"]
        )

        evidence_text = "; ".join(analysis["evidence"])
        evidence = FindingEvidence(
            payload=f"管理員路徑訪問: {admin_path}",
            response=f"特權級別: {analysis['privilege_level']}. 證據: {evidence_text}. "
                    f"狀態碼: {response.status_code}, 響應長度: {len(response.text)}, "
                    f"新穎度: {analysis.get('novelty_score', 0.0):.2f}",
            response_time_delta=response.elapsed.total_seconds()
        )

        return FindingPayload(
            finding_id=new_id("finding"),
            task_id=task.task_id,
            scan_id=task.scan_id,
            status="detected",
            vulnerability=vulnerability,
            target=FindingTarget(
                url=admin_path,
                parameter="admin_access",
                method="GET"
            ),
            evidence=evidence
        )


class ProductionIDORModule(BaseFunctionModule):
    """生產級 IDOR 檢測模組"""

    def __init__(self, config: IDORConfig | None = None) -> None:
        detection_engines = [
            ProductionHorizontalIDOREngine(),
            ProductionVerticalIDOREngine(),
        ]

        super().__init__(ModuleName.FUNC_IDOR, config or IDORConfig(), detection_engines)

    def get_module_name(self) -> str:
        return "Production IDOR Detection Module"

    def get_supported_vulnerability_types(self) -> list[VulnerabilityType]:
        return [VulnerabilityType.IDOR]

    def get_topic(self) -> Topic:
        return Topic.TASK_FUNCTION_IDOR

    def get_vulnerability_type(self) -> VulnerabilityType:
        return VulnerabilityType.IDOR