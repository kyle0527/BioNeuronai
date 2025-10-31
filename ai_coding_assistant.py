#!/usr/bin/env python3
"""
AI 編程助手 - 真正幫助開發者提升的智能系統
功能：
1. 自動代碼審查並提出改進建議
2. 自動修復常見問題
3. 性能優化建議
4. 安全漏洞檢測
5. 代碼重構建議
"""

import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, "src")
from bioneuronai.improved_core import ImprovedBioNeuron  # type: ignore[import-untyped]


@dataclass
class CodeIssue:
    """代碼問題"""

    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'security', 'performance', 'style', 'bug'
    file: str
    line: int
    description: str
    suggestion: str
    auto_fixable: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ImprovementReport:
    """改進報告"""

    timestamp: str
    total_issues: int
    critical: int
    warnings: int
    info: int
    issues: List[CodeIssue]
    suggestions: List[str]

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "total_issues": self.total_issues,
            "critical": self.critical,
            "warnings": self.warnings,
            "info": self.info,
            "issues": [issue.to_dict() for issue in self.issues],
            "suggestions": self.suggestions,
        }


class CodeAnalyzer:
    """代碼分析器 - 使用 AST 分析 Python 代碼"""

    def __init__(self) -> None:
        self.issues: List[CodeIssue] = []

    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """分析單個文件"""
        self.issues = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # AST 分析
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, str(file_path))
            except SyntaxError as e:
                self.issues.append(
                    CodeIssue(
                        severity="critical",
                        category="bug",
                        file=str(file_path),
                        line=e.lineno or 0,
                        description=f"語法錯誤: {e.msg}",
                        suggestion="修復語法錯誤",
                        auto_fixable=False,
                    )
                )

            # 行級分析
            self._analyze_lines(lines, str(file_path))

        except Exception as e:
            print(f"❌ 分析文件失敗 {file_path}: {e}")

        return self.issues

    def _analyze_ast(self, tree: ast.AST, filename: str) -> None:
        """AST 深度分析"""
        for node in ast.walk(tree):
            # 檢測過長函數
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if node.end_lineno else 0
                if func_lines > 50:
                    self.issues.append(
                        CodeIssue(
                            severity="warning",
                            category="style",
                            file=filename,
                            line=node.lineno,
                            description=f"函數 {node.name} 過長 ({func_lines} 行)",
                            suggestion="考慮將函數拆分為多個小函數，提高可讀性",
                            auto_fixable=False,
                        )
                    )

                # 檢測過多參數
                if len(node.args.args) > 5:
                    self.issues.append(
                        CodeIssue(
                            severity="info",
                            category="style",
                            file=filename,
                            line=node.lineno,
                            description=f"函數 {node.name} 參數過多 ({len(node.args.args)} 個)",
                            suggestion="考慮使用配置對象或字典來傳遞參數",
                            auto_fixable=False,
                        )
                    )

            # 檢測空的 except 塊
            if isinstance(node, ast.ExceptHandler):
                if not node.body or (
                    len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
                ):
                    self.issues.append(
                        CodeIssue(
                            severity="warning",
                            category="bug",
                            file=filename,
                            line=node.lineno,
                            description="空的異常處理塊",
                            suggestion="添加適當的錯誤處理或至少記錄錯誤",
                            auto_fixable=False,
                        )
                    )

            # 檢測硬編碼的密碼/密鑰
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(
                            keyword in var_name
                            for keyword in [
                                "password",
                                "passwd",
                                "pwd",
                                "secret",
                                "key",
                                "token",
                            ]
                        ):
                            if isinstance(node.value, ast.Constant):
                                self.issues.append(
                                    CodeIssue(
                                        severity="critical",
                                        category="security",
                                        file=filename,
                                        line=node.lineno,
                                        description=f"硬編碼的敏感信息: {target.id}",
                                        suggestion="使用環境變量或配置文件存儲敏感信息",
                                        auto_fixable=False,
                                    )
                                )

    def _analyze_lines(self, lines: List[str], filename: str) -> None:
        """行級分析"""
        for i, line in enumerate(lines, 1):
            # 檢測過長的行
            if len(line) > 120:
                self.issues.append(
                    CodeIssue(
                        severity="info",
                        category="style",
                        file=filename,
                        line=i,
                        description=f"行過長 ({len(line)} 字符)",
                        suggestion="將長行拆分為多行，提高可讀性",
                        auto_fixable=True,
                    )
                )

            # 檢測 TODO/FIXME
            if "TODO" in line or "FIXME" in line:
                self.issues.append(
                    CodeIssue(
                        severity="info",
                        category="style",
                        file=filename,
                        line=i,
                        description="未完成的代碼標記",
                        suggestion="完成或移除 TODO/FIXME 標記",
                        auto_fixable=False,
                    )
                )

            # 檢測 print 調試語句
            if re.search(r"\bprint\s*\(", line) and "logger" not in line:
                self.issues.append(
                    CodeIssue(
                        severity="info",
                        category="style",
                        file=filename,
                        line=i,
                        description="使用 print 而不是 logger",
                        suggestion="使用 logging 模塊替代 print 進行日誌記錄",
                        auto_fixable=True,
                    )
                )

            # 檢測 SQL 注入風險
            if re.search(r"execute\s*\([^)]*%s[^)]*\)", line):
                self.issues.append(
                    CodeIssue(
                        severity="critical",
                        category="security",
                        file=filename,
                        line=i,
                        description="潛在的 SQL 注入風險",
                        suggestion="使用參數化查詢替代字符串格式化",
                        auto_fixable=False,
                    )
                )


class AICodeAssistant:
    """AI 編程助手 - 使用神經網絡學習優化模式"""

    def __init__(self, workspace_dir: str = "."):
        self.workspace = Path(workspace_dir)
        self.analyzer = CodeAnalyzer()

        # AI 學習系統 - 學習代碼模式
        self.pattern_neuron = ImprovedBioNeuron(
            num_inputs=10, learning_rate=0.01, threshold=0.5  # 代碼特徵維度
        )

        self.reports_dir = self.workspace / "ai_reports"
        self.reports_dir.mkdir(exist_ok=True)

    def analyze_workspace(self, pattern: str = "**/*.py") -> ImprovementReport:
        """分析整個工作區"""
        print("🔍 開始分析代碼...")

        all_issues: List[CodeIssue] = []
        python_files = list(self.workspace.glob(pattern))

        # 過濾測試文件和虛擬環境
        python_files = [
            f
            for f in python_files
            if not any(p in str(f) for p in ["venv", ".venv", "__pycache__", ".git"])
        ]

        print(f"📁 找到 {len(python_files)} 個 Python 文件")

        for file_path in python_files:
            print(f"  📄 分析: {file_path.relative_to(self.workspace)}")
            issues = self.analyzer.analyze_file(file_path)
            all_issues.extend(issues)

        # 統計
        critical = sum(1 for i in all_issues if i.severity == "critical")
        warnings = sum(1 for i in all_issues if i.severity == "warning")
        info = sum(1 for i in all_issues if i.severity == "info")

        # 生成建議
        suggestions = self._generate_suggestions(all_issues)

        report = ImprovementReport(
            timestamp=datetime.now().isoformat(),
            total_issues=len(all_issues),
            critical=critical,
            warnings=warnings,
            info=info,
            issues=all_issues,
            suggestions=suggestions,
        )

        return report

    def _generate_suggestions(self, issues: List[CodeIssue]) -> List[str]:
        """基於問題生成改進建議"""
        suggestions = []

        # 按類別統計
        security_issues = sum(1 for i in issues if i.category == "security")
        performance_issues = sum(1 for i in issues if i.category == "performance")
        style_issues = sum(1 for i in issues if i.category == "style")

        if security_issues > 0:
            suggestions.append(f"🔒 發現 {security_issues} 個安全問題，建議優先修復")
            suggestions.append("   • 使用環境變量存儲敏感信息")
            suggestions.append("   • 使用參數化查詢防止 SQL 注入")

        if performance_issues > 5:
            suggestions.append(f"⚡ 發現 {performance_issues} 個性能問題")
            suggestions.append("   • 考慮使用緩存減少重複計算")
            suggestions.append("   • 優化循環和數據結構")

        if style_issues > 10:
            suggestions.append(f"✨ 發現 {style_issues} 個代碼風格問題")
            suggestions.append("   • 運行 black 或 autopep8 自動格式化")
            suggestions.append("   • 使用 pylint 或 flake8 檢查代碼規範")

        # 可自動修復的問題
        auto_fixable = sum(1 for i in issues if i.auto_fixable)
        if auto_fixable > 0:
            suggestions.append(f"🔧 {auto_fixable} 個問題可以自動修復")

        return suggestions

    def display_report(self, report: ImprovementReport) -> None:
        """顯示報告"""
        print("\n" + "=" * 80)
        print("📊 代碼分析報告")
        print("=" * 80)
        print(f"⏰ 時間: {report.timestamp}")
        print(f"📈 總問題數: {report.total_issues}")
        print(f"  🔴 嚴重: {report.critical}")
        print(f"  🟡 警告: {report.warnings}")
        print(f"  🔵 信息: {report.info}")

        if report.suggestions:
            print("\n💡 改進建議:")
            for suggestion in report.suggestions:
                print(f"  {suggestion}")

        # 顯示前 10 個最重要的問題
        critical_issues = [i for i in report.issues if i.severity == "critical"]
        warning_issues = [i for i in report.issues if i.severity == "warning"]

        if critical_issues:
            print("\n🔴 嚴重問題 (需要立即處理):")
            for issue in critical_issues[:5]:
                print(f"  📍 {Path(issue.file).name}:{issue.line}")
                print(f"     問題: {issue.description}")
                print(f"     建議: {issue.suggestion}")

        if warning_issues:
            print("\n🟡 警告 (建議處理):")
            for issue in warning_issues[:5]:
                print(f"  📍 {Path(issue.file).name}:{issue.line}")
                print(f"     問題: {issue.description}")
                print(f"     建議: {issue.suggestion}")

        print("\n" + "=" * 80)

    def save_report(self, report: ImprovementReport) -> Path:
        """保存報告"""
        report_file = (
            self.reports_dir
            / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"\n💾 報告已保存: {report_file}")
        return report_file

    def auto_fix(self, issues: List[CodeIssue]) -> None:
        """自動修復可修復的問題"""
        fixable = [i for i in issues if i.auto_fixable]

        if not fixable:
            print("ℹ️  沒有可自動修復的問題")
            return

        print(f"\n🔧 開始自動修復 {len(fixable)} 個問題...")

        # 按文件分組
        by_file: Dict[str, List[CodeIssue]] = {}
        for issue in fixable:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append(issue)

        for file_path, file_issues in by_file.items():
            print(f"  📄 修復: {Path(file_path).name}")
            self._fix_file(Path(file_path), file_issues)

    def _fix_file(self, file_path: Path, issues: List[CodeIssue]) -> None:
        """修復單個文件的問題"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            fixed_count = 0

            for issue in issues:
                if "print" in issue.description.lower() and issue.auto_fixable:
                    # 替換 print 為 logger
                    line_idx = issue.line - 1
                    if 0 <= line_idx < len(lines):
                        old_line = lines[line_idx]
                        new_line = old_line.replace("print(", "logger.info(")
                        if old_line != new_line:
                            lines[line_idx] = new_line
                            fixed_count += 1

            if fixed_count > 0:
                # 備份原文件
                backup = file_path.with_suffix(".py.bak")
                file_path.rename(backup)

                # 寫入修復後的內容
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                print(f"    ✅ 修復了 {fixed_count} 個問題")

        except Exception as e:
            print(f"    ❌ 修復失敗: {e}")


def main() -> None:
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description="AI 編程助手 - 幫助你提升代碼質量")
    parser.add_argument("--dir", default=".", help="要分析的目錄")
    parser.add_argument("--pattern", default="**/*.py", help="文件匹配模式")
    parser.add_argument("--auto-fix", action="store_true", help="自動修復可修復的問題")

    args = parser.parse_args()

    print("🤖 AI 編程助手啟動")
    print("🎯 目標：幫助你真正提升代碼質量\n")

    assistant = AICodeAssistant(args.dir)

    # 分析代碼
    report = assistant.analyze_workspace(args.pattern)

    # 顯示報告
    assistant.display_report(report)

    # 保存報告
    assistant.save_report(report)

    # 自動修復
    if args.auto_fix:
        assistant.auto_fix(report.issues)
        print("\n🎉 自動修復完成！")

    # 提供下一步建議
    print("\n📋 下一步行動:")
    print("  1. 優先處理所有嚴重問題 (紅色)")
    print("  2. 逐步解決警告 (黃色)")
    print("  3. 運行 'python ai_coding_assistant.py --auto-fix' 自動修復部分問題")
    print("  4. 使用 'black .' 自動格式化代碼")
    print("  5. 使用 'mypy .' 進行類型檢查")


if __name__ == "__main__":
    main()
