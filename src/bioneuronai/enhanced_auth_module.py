"""
增強的認證授權檢測模組 - 階段二功能模組成熟化
完整規劃實現，整合四種檢測引擎，符合四大模組架構標準

基於 MASTER_ROADMAP_2025.md 第二階段：功能模組成熟化需求
遵循 aiva_common.schemas 和 FINAL_UNIFICATION_AND_MODULARIZATION_REPORT 規範
"""

from __future__ import annotations

import base64

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
from ..common.detection_config import AuthConfig
from ..common.unified_smart_detection_manager import (
    DetectionDecision,
    DetectionRuleResult,
    UnifiedSmartDetectionManager,
)

logger = get_logger(__name__)


def _safe_elapsed_seconds(response: httpx.Response) -> float:
    try:
        return float(response.elapsed.total_seconds())
    except Exception:
        return 0.0


def _auth_response_features(
    response: httpx.Response,
    *,
    evidence_count: int = 0,
    success_hint: float = 0.0,
) -> list[float]:
    text = response.text or ""
    length_ratio = min(len(text) / 5000.0, 1.0)
    status_ratio = min(response.status_code / 600.0, 1.0)
    latency_ratio = min(_safe_elapsed_seconds(response) / 10.0, 1.0)
    evidence_score = min(evidence_count / 5.0, 1.0)
    keyword_bonus = 0.0
    keywords = ["token", "success", "dashboard", "admin", "welcome"]
    lowered = text.lower()
    if any(k in lowered for k in keywords):
        keyword_bonus = 0.3
    return [length_ratio, status_ratio, evidence_score, success_hint, min(1.0, latency_ratio + keyword_bonus)]


def _novelty_decision(
    smart_manager: UnifiedSmartDetectionManager,
    rule_confidence: Confidence,
    severity: Severity,
    response: httpx.Response,
    *,
    evidence_count: int = 0,
    success_hint: float = 0.0,
    context: dict[str, object] | None = None,
) -> tuple[DetectionDecision, list[float]]:
    features = _auth_response_features(
        response, evidence_count=evidence_count, success_hint=success_hint
    )
    decision = smart_manager.combine_rule_and_novelty(
        DetectionRuleResult(
            confidence=rule_confidence,
            severity=severity,
            metadata=context or {},
        ),
        features,
    )
    return decision, features

class WeakCredentialEngine(DetectionEngineProtocol):
    """弱憑證檢測引擎 - 檢測弱密碼和默認憑證"""

    def get_engine_name(self) -> str:
        return "Weak Credential Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測弱憑證和默認密碼"""
        findings: list[FindingPayload] = []

        # 常見弱憑證組合 (用戶名:密碼)
        weak_credentials = [
            ("admin", "admin"), ("admin", "password"), ("admin", "123456"),
            ("administrator", "administrator"), ("root", "root"), ("root", "toor"),
            ("guest", "guest"), ("test", "test"), ("user", "user"),
            ("sa", "sa"), ("oracle", "oracle"), ("postgres", "postgres"),
            ("mysql", "mysql"), ("demo", "demo"), ("default", "default")
        ]

        target = task.target
        
        # 檢測登錄表單字段
        login_fields = await self._identify_login_fields(target, client)
        if not login_fields:
            return findings

        for username, password in weak_credentials:
            try:
                # 構建登錄數據
                login_data = {
                    login_fields["username"]: username,
                    login_fields["password"]: password
                }
                
                # 添加其他可能的表單字段
                if login_fields.get("csrf_token"):
                    csrf_token = await self._get_csrf_token(target, client)
                    if csrf_token:
                        login_data[login_fields["csrf_token"]] = csrf_token

                response = await client.post(
                    str(target.url),
                    data=login_data,
                    timeout=15.0,
                    follow_redirects=True
                )

                success = await self._is_successful_login(response, username)
                decision, features = _novelty_decision(
                    smart_manager,
                    rule_confidence=Confidence.HIGH if success else Confidence.LOW,
                    severity=Severity.LOW,
                    response=response,
                    evidence_count=1,
                    success_hint=1.0 if success else 0.0,
                    context={
                        "engine": self.get_engine_name(),
                        "username": username,
                    },
                )

                if success:
                    smart_manager.feedback(features, confirmed_anomaly=True)
                    vulnerability = Vulnerability(
                        name=VulnerabilityType.WEAK_AUTHENTICATION,
                        severity=decision.severity,
                        confidence=decision.confidence,
                    )

                    evidence = FindingEvidence(
                        payload=f"弱憑證：{username}:{password}",
                        response=(
                            f"Novelty={decision.novelty_score:.2f}, Risk={decision.risk_label}. "
                            + response.text[:500]
                        ),
                        response_time_delta=_safe_elapsed_seconds(response),
                    )

                    finding = FindingPayload(
                        finding_id=new_id("finding"),
                        task_id=task.task_id,
                        scan_id=task.scan_id,
                        status="detected",
                        vulnerability=vulnerability,
                        target=FindingTarget(
                            url=str(target.url),
                            parameter="credentials",
                            method="POST"
                        ),
                        evidence=evidence
                    )
                    findings.append(finding)
                    logger.info(f"發現弱憑證: {username}:{password}")
                    break
                else:
                    smart_manager.feedback(features, confirmed_anomaly=False)

            except Exception as e:
                logger.debug(f"弱憑證檢測錯誤 ({username}): {e}")
                continue

        return findings

    async def _identify_login_fields(
        self, target: FunctionTaskTarget, client: httpx.AsyncClient
    ) -> dict[str, str]:
        """識別登錄表單字段"""
        try:
            response = await client.get(str(target.url), timeout=10.0)
            html_content = response.text.lower()
            
            fields = {}
            
            # 尋找用戶名字段
            username_patterns = [
                r'name=["\']([^"\']*(?:user|login|email|account)[^"\']*)["\']',
                r'id=["\']([^"\']*(?:user|login|email|account)[^"\']*)["\']'
            ]
            
            # 尋找密碼字段
            password_patterns = [
                r'name=["\']([^"\']*(?:pass|pwd)[^"\']*)["\']',
                r'id=["\']([^"\']*(?:pass|pwd)[^"\']*)["\']',
                r'type=["\']password["\'][^>]*name=["\']([^"\']*)["\']'
            ]
            
            # CSRF token 模式
            csrf_patterns = [
                r'name=["\']([^"\']*(?:csrf|token|authenticity)[^"\']*)["\']',
                r'id=["\']([^"\']*(?:csrf|token|authenticity)[^"\']*)["\']'
            ]
            
            import re
            
            # 搜索用戶名字段
            for pattern in username_patterns:
                match = re.search(pattern, html_content)
                if match:
                    fields["username"] = match.group(1)
                    break
            else:
                fields["username"] = "username"  # 默認值
            
            # 搜索密碼字段
            for pattern in password_patterns:
                match = re.search(pattern, html_content)
                if match:
                    fields["password"] = match.group(1)
                    break
            else:
                fields["password"] = "password"  # 默認值
                
            # 搜索CSRF token字段
            for pattern in csrf_patterns:
                match = re.search(pattern, html_content)
                if match:
                    fields["csrf_token"] = match.group(1)
                    break
            
            return fields
            
        except Exception as e:
            logger.debug(f"識別登錄字段失敗: {e}")
            return {"username": "username", "password": "password"}

    async def _get_csrf_token(
        self, target: FunctionTaskTarget, client: httpx.AsyncClient
    ) -> str | None:
        """獲取CSRF token"""
        try:
            response = await client.get(str(target.url), timeout=10.0)
            html_content = response.text
            
            import re
            
            # 常見的 CSRF token 模式
            csrf_patterns = [
                r'name=["\'][^"\']*csrf[^"\']*["\'][^>]*value=["\']([^"\']*)["\']',
                r'value=["\']([^"\']*)["\'][^>]*name=["\'][^"\']*csrf[^"\']*["\']',
                r'content=["\']([^"\']*)["\'][^>]*name=["\']csrf-token["\']',
                r'<meta[^>]*csrf[^>]*content=["\']([^"\']*)["\']'
            ]
            
            for pattern in csrf_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.debug(f"獲取CSRF token失敗: {e}")
            return None

    async def _is_successful_login(
        self, response: httpx.Response, username: str
    ) -> bool:
        """多維度判斷是否成功登錄"""
        # 1. HTTP狀態碼檢查
        if response.status_code in [200, 302, 301]:
            response_text = response.text.lower()
            
            # 2. 成功指標檢查
            success_indicators = [
                "dashboard", "welcome", "profile", "logout", "admin panel",
                "儀表板", "歡迎", "個人資料", "登出", "管理面板",
                "successfully logged", "login successful", "welcome back",
                f"welcome {username.lower()}", f"hello {username.lower()}"
            ]
            
            # 3. 失敗指標檢查 (如果存在失敗指標，則不是成功登錄)
            failure_indicators = [
                "invalid", "incorrect", "failed", "error", "wrong",
                "無效", "錯誤", "失敗", "不正確",
                "login failed", "authentication failed", "access denied"
            ]
            
            # 4. 重定向檢查
            if response.status_code in [302, 301]:
                location = response.headers.get("location", "").lower()
                if any(indicator in location for indicator in ["dashboard", "admin", "profile", "home"]):
                    return True
            
            # 5. 響應內容檢查
            has_success = any(indicator in response_text for indicator in success_indicators)
            has_failure = any(indicator in response_text for indicator in failure_indicators)
            
            # 6. Cookie檢查 (會話cookie通常表示成功登錄)
            session_cookies = ["session", "auth", "token", "jsessionid", "phpsessid"]
            has_session_cookie = any(cookie in response.cookies for cookie in session_cookies)
            
            return has_success and not has_failure or has_session_cookie
            
        return False
        """判斷是否成功登錄"""
        success_indicators = [
            "dashboard", "welcome", "logout", "profile",
            "歡迎", "儀表板", "成功登錄"
        ]

        response_text = response.text.lower()
        return any(indicator in response_text for indicator in success_indicators)


class SessionFixationEngine(DetectionEngineProtocol):
    """會話固定攻擊檢測引擎"""

    def get_engine_name(self) -> str:
        return "Session Fixation Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測會話固定攻擊漏洞"""
        findings: list[FindingPayload] = []

        for target in [task.target]:
            try:
                # 第一步：獲取初始會話ID
                initial_response = await client.get(str(target.url))
                try:
                    smart_manager.record_normal_profile(
                        _auth_response_features(initial_response, success_hint=0.0)
                    )
                except Exception:
                    logger.debug("無法記錄會話固定基準響應")
                initial_session = self._extract_session_id(initial_response)

                if not initial_session:
                    continue

                # 第二步：使用固定會話ID登錄
                login_data = {"username": "test", "password": "test"}
                login_response = await client.post(
                    str(target.url),
                    data=login_data,
                    cookies={"sessionid": initial_session}
                )

                # 第三步：檢查登錄後會話ID是否改變
                new_session = self._extract_session_id(login_response)

                success_hint = 1.0 if initial_session == new_session else 0.0
                decision, features = _novelty_decision(
                    smart_manager,
                    rule_confidence=Confidence.MEDIUM,
                    severity=Severity.LOW,
                    response=login_response,
                    evidence_count=1,
                    success_hint=success_hint,
                    context={
                        "engine": self.get_engine_name(),
                        "initial_session": bool(initial_session),
                    },
                )

                if initial_session == new_session:
                    smart_manager.feedback(features, confirmed_anomaly=True)
                    vulnerability = Vulnerability(
                        name=VulnerabilityType.WEAK_AUTHENTICATION,
                        severity=decision.severity,
                        confidence=decision.confidence,
                    )

                    evidence = FindingEvidence(
                        payload=f"固定會話ID: {initial_session}",
                        response=(
                            f"Novelty={decision.novelty_score:.2f}, Risk={decision.risk_label}. "
                            + login_response.text[:500]
                        ),
                        response_time_delta=_safe_elapsed_seconds(login_response),
                    )

                    finding = FindingPayload(
                        finding_id=new_id("finding"),
                        task_id=task.task_id,
                        scan_id=task.scan_id,
                        status="detected",
                        vulnerability=vulnerability,
                        target=FindingTarget(
                            url=str(target.url),
                            parameter="session_id",
                            method="POST"
                        ),
                        evidence=evidence
                    )
                    findings.append(finding)
                else:
                    smart_manager.feedback(features, confirmed_anomaly=False)

            except Exception as e:
                logger.debug(f"會話固定檢測錯誤: {e}")
                continue

        return findings

    def _extract_session_id(self, response: httpx.Response) -> str | None:
        """提取會話ID"""
        cookies = response.cookies
        for cookie_name in ["sessionid", "JSESSIONID", "PHPSESSID", "ASP.NET_SessionId"]:
            if cookie_name in cookies:
                return cookies[cookie_name]
        return None


class TokenValidationEngine(DetectionEngineProtocol):
    """令牌驗證檢測引擎 - 檢測JWT和其他令牌的安全性"""

    def get_engine_name(self) -> str:
        return "Token Validation Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測令牌驗證漏洞"""
        findings: list[FindingPayload] = []

        for target in [task.target]:
            try:
                # 檢測 JWT 'none' 算法漏洞
                findings.extend(
                    await self._check_jwt_none_algorithm(target, client, task, smart_manager)
                )

                # 檢測令牌篡改
                findings.extend(
                    await self._check_token_tampering(target, client, task, smart_manager)
                )

            except Exception as e:
                logger.debug(f"令牌驗證檢測錯誤: {e}")
                continue

        return findings

    async def _check_jwt_none_algorithm(
        self,
        target: FunctionTaskTarget,
        client: httpx.AsyncClient,
        task: FunctionTaskPayload,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測JWT使用不安全的'none'算法"""
        findings: list[FindingPayload] = []

        try:
            # 創建一個使用 'none' 算法的JWT
            header = {"alg": "none", "typ": "JWT"}
            payload = {"user": "admin", "role": "admin"}

            header_b64 = base64.urlsafe_b64encode(
                str(header).encode()
            ).decode().rstrip("=")
            payload_b64 = base64.urlsafe_b64encode(
                str(payload).encode()
            ).decode().rstrip("=")

            jwt_token = f"{header_b64}.{payload_b64}."

            # 嘗試使用這個token訪問受保護資源
            response = await client.get(
                str(target.url),
                headers={"Authorization": f"Bearer {jwt_token}"}
            )

            success = response.status_code == 200
            decision, features = _novelty_decision(
                smart_manager,
                rule_confidence=Confidence.HIGH if success else Confidence.LOW,
                severity=Severity.LOW,
                response=response,
                evidence_count=0,
                success_hint=1.0 if success else 0.0,
                context={
                    "engine": self.get_engine_name(),
                    "check": "jwt_none",
                },
            )

            if success:
                smart_manager.feedback(features, confirmed_anomaly=True)
                vulnerability = Vulnerability(
                    name=VulnerabilityType.WEAK_AUTHENTICATION,
                    severity=decision.severity,
                    confidence=decision.confidence,
                )

                evidence = FindingEvidence(
                    payload=jwt_token,
                    response=f"Novelty={decision.novelty_score:.2f}, Risk={decision.risk_label}",
                    response_time_delta=_safe_elapsed_seconds(response),
                )

                finding = FindingPayload(
                    finding_id=new_id("finding"),
                    task_id=task.task_id,
                    scan_id=task.scan_id,
                    status="detected",
                    vulnerability=vulnerability,
                    target=FindingTarget(
                        url=str(target.url),
                        parameter="JWT",
                        method="GET"
                    ),
                    evidence=evidence
                )
                findings.append(finding)
            else:
                smart_manager.feedback(features, confirmed_anomaly=False)

        except Exception as e:
            logger.debug(f"JWT none算法檢測錯誤: {e}")

        return findings

    async def _check_token_tampering(
        self,
        target: FunctionTaskTarget,
        client: httpx.AsyncClient,
        task: FunctionTaskPayload,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測令牌篡改漏洞"""
        findings: list[FindingPayload] = []

        try:
            # 篡改令牌（修改用戶名為admin）
            tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4ifQ.signature"

            response = await client.get(
                str(target.url),
                headers={"Authorization": f"Bearer {tampered_token}"}
            )

            success = response.status_code == 200
            decision, features = _novelty_decision(
                smart_manager,
                rule_confidence=Confidence.MEDIUM if success else Confidence.LOW,
                severity=Severity.LOW,
                response=response,
                evidence_count=1,
                success_hint=1.0 if success else 0.0,
                context={
                    "engine": self.get_engine_name(),
                    "check": "token_tampering",
                },
            )

            if success:
                smart_manager.feedback(features, confirmed_anomaly=True)
                vulnerability = Vulnerability(
                    name=VulnerabilityType.WEAK_AUTHENTICATION,
                    severity=decision.severity,
                    confidence=decision.confidence,
                )

                evidence = FindingEvidence(
                    payload=tampered_token,
                    response=(
                        f"Novelty={decision.novelty_score:.2f}, Risk={decision.risk_label}. "
                        + response.text[:300]
                    ),
                    response_time_delta=_safe_elapsed_seconds(response),
                )

                finding = FindingPayload(
                    finding_id=new_id("finding"),
                    task_id=task.task_id,
                    scan_id=task.scan_id,
                    status="detected",
                    vulnerability=vulnerability,
                    target=FindingTarget(
                        url=str(target.url),
                        parameter="JWT",
                        method="GET"
                    ),
                    evidence=evidence
                )
                findings.append(finding)
            else:
                smart_manager.feedback(features, confirmed_anomaly=False)

        except Exception as e:
            logger.debug(f"令牌篡改檢測錯誤: {e}")

        return findings


class AuthBypassEngine(DetectionEngineProtocol):
    """授權繞過檢測引擎"""

    def get_engine_name(self) -> str:
        return "Authorization Bypass Detection Engine"

    async def detect(
        self,
        task: FunctionTaskPayload,
        client: httpx.AsyncClient,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測授權繞過漏洞"""
        findings: list[FindingPayload] = []

        for target in [task.target]:
            try:
                # 檢測無令牌訪問
                findings.extend(
                    await self._check_no_token_access(target, client, task, smart_manager)
                )

                # 檢測HTTP方法覆寫
                findings.extend(
                    await self._check_http_method_override(target, client, task, smart_manager)
                )

            except Exception as e:
                logger.debug(f"授權繞過檢測錯誤: {e}")
                continue

        return findings

    async def _check_no_token_access(
        self,
        target: FunctionTaskTarget,
        client: httpx.AsyncClient,
        task: FunctionTaskPayload,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測無令牌時是否能訪問受保護資源"""
        findings: list[FindingPayload] = []

        try:
            response = await client.get(str(target.url))

            # 如果沒有令牌也能成功訪問（200狀態碼）
            success = response.status_code == 200
            decision, features = _novelty_decision(
                smart_manager,
                rule_confidence=Confidence.HIGH if success else Confidence.LOW,
                severity=Severity.LOW,
                response=response,
                evidence_count=1,
                success_hint=1.0 if success else 0.0,
                context={
                    "engine": self.get_engine_name(),
                    "check": "no_token",
                },
            )

            if success:
                smart_manager.feedback(features, confirmed_anomaly=True)
                vulnerability = Vulnerability(
                    name=VulnerabilityType.ACCESS_CONTROL,
                    severity=decision.severity,
                    confidence=decision.confidence,
                )

                evidence = FindingEvidence(
                    payload="無授權令牌訪問",
                    response=(
                        f"Novelty={decision.novelty_score:.2f}, Risk={decision.risk_label}. "
                        + response.text[:300]
                    ),
                    response_time_delta=_safe_elapsed_seconds(response),
                )

                finding = FindingPayload(
                    finding_id=new_id("finding"),
                    task_id=task.task_id,
                    scan_id=task.scan_id,
                    status="detected",
                    vulnerability=vulnerability,
                    target=FindingTarget(
                        url=str(target.url),
                        parameter="authorization",
                        method="GET"
                    ),
                    evidence=evidence
                )
                findings.append(finding)
            else:
                smart_manager.feedback(features, confirmed_anomaly=False)

        except Exception as e:
            logger.debug(f"無令牌訪問檢測錯誤: {e}")

        return findings

    async def _check_http_method_override(
        self,
        target: FunctionTaskTarget,
        client: httpx.AsyncClient,
        task: FunctionTaskPayload,
        smart_manager: UnifiedSmartDetectionManager,
    ) -> list[FindingPayload]:
        """檢測HTTP方法覆寫繞過"""
        findings: list[FindingPayload] = []

        # 常見的方法覆寫標頭
        override_headers = [
            ("X-HTTP-Method-Override", "GET"),
            ("X-HTTP-Method", "GET"),
            ("X-Method-Override", "GET")
        ]

        for header_name, method in override_headers:
            try:
                response = await client.post(
                    str(target.url),
                    headers={header_name: method}
                )

                success = response.status_code == 200
                decision, features = _novelty_decision(
                    smart_manager,
                    rule_confidence=Confidence.MEDIUM if success else Confidence.LOW,
                    severity=Severity.LOW,
                    response=response,
                    evidence_count=1,
                    success_hint=1.0 if success else 0.0,
                    context={
                        "engine": self.get_engine_name(),
                        "check": "method_override",
                        "header": header_name,
                    },
                )

                if success:
                    smart_manager.feedback(features, confirmed_anomaly=True)
                    vulnerability = Vulnerability(
                        name=VulnerabilityType.ACCESS_CONTROL,
                        severity=decision.severity,
                        confidence=decision.confidence,
                    )

                    evidence = FindingEvidence(
                        payload=f"使用{header_name}標頭覆寫為{method}方法",
                        response=(
                            f"Novelty={decision.novelty_score:.2f}, Risk={decision.risk_label}. "
                            + response.text[:300]
                        ),
                        response_time_delta=_safe_elapsed_seconds(response),
                    )

                    finding = FindingPayload(
                        finding_id=new_id("finding"),
                        task_id=task.task_id,
                        scan_id=task.scan_id,
                        status="detected",
                        vulnerability=vulnerability,
                        target=FindingTarget(
                            url=str(target.url),
                            parameter=header_name,
                            method="POST"
                        ),
                        evidence=evidence
                    )
                    findings.append(finding)
                    break
                else:
                    smart_manager.feedback(features, confirmed_anomaly=False)

            except Exception as e:
                logger.debug(f"HTTP方法覆寫檢測錯誤: {e}")
                continue

        return findings


class EnhancedAuthModule(BaseFunctionModule):
    """增強的認證授權檢測模組 - 整合四種檢測引擎"""

    def __init__(self, config: AuthConfig | None = None):
        # 初始化四個檢測引擎
        detection_engines = [
            WeakCredentialEngine(),
            SessionFixationEngine(),
            TokenValidationEngine(),
            AuthBypassEngine()
        ]

        super().__init__(
            module_name=ModuleName.FUNC_AUTH,
            config=config or AuthConfig(),
            detection_engines=detection_engines
        )

    def get_module_name(self) -> str:
        return "Enhanced Authentication Authorization Detection Module"

    def get_supported_vulnerability_types(self) -> list[VulnerabilityType]:
        return [
            VulnerabilityType.WEAK_AUTHENTICATION,
            VulnerabilityType.ACCESS_CONTROL
        ]

    def get_topic(self) -> Topic:
        """獲取模組對應的消息主題"""
        return Topic.TASK_FUNCTION_AUTH

    def get_vulnerability_type(self) -> VulnerabilityType:
        """獲取模組對應的漏洞類型"""
        return VulnerabilityType.WEAK_AUTHENTICATION

    # BaseFunctionModule 提供完整的 _execute_detection 實現，使用 self.detection_engines
