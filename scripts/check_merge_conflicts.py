#!/usr/bin/env python3
"""
BioNeuronAI Merge Conflict Detection Script

This script helps identify and analyze potential merge conflicts across PRs.
It can be run locally or in CI to catch conflicts early.

Usage:
    python scripts/check_merge_conflicts.py --pr 25
    python scripts/check_merge_conflicts.py --pr-list 25,16,8 --base main
    python scripts/check_merge_conflicts.py --all --report conflicts_report.md
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ConflictInfo:
    """Information about a merge conflict."""
    
    pr_number: int
    pr_title: str
    conflicting_files: List[str]
    base_branch: str
    conflict_summary: str


@dataclass
class PRInfo:
    """Information about a Pull Request."""
    
    number: int
    title: str
    branch: str
    phase: int
    priority: str


# PR 優先順序配置
PR_PHASES = {
    # Phase 1: High Priority - Core Architecture
    1: [
        PRInfo(25, "Refactor BioNeuron architecture with strategy base class", "pr-25", 1, "HIGH"),
        PRInfo(16, "Introduce shared neuron base and align BioLayer API", "pr-16", 1, "HIGH"),
        PRInfo(8, "Add parameterized LIF and STDP neuron types", "pr-8", 1, "HIGH"),
    ],
    # Phase 2: Medium Priority - Feature Modules
    2: [
        PRInfo(20, "Introduce shared security package and tests", "pr-20", 2, "MEDIUM"),
        PRInfo(14, "Refactor security modules into dedicated package", "pr-14", 2, "MEDIUM"),
        PRInfo(13, "Improve vectorization and add concurrency safeguards", "pr-13", 2, "MEDIUM"),
        PRInfo(6, "Add persistence support and online learning safeguards", "pr-6", 2, "MEDIUM"),
    ],
    # Phase 3: CLI and Tools
    3: [
        PRInfo(19, "Refactor CLI into Typer app and add Streamlit dashboard", "pr-19", 3, "MEDIUM"),
        PRInfo(5, "Add Typer-based CLI with dashboard streaming", "pr-5", 3, "MEDIUM"),
        PRInfo(15, "Add configurable network builder and CLI config support", "pr-15", 3, "MEDIUM"),
    ],
    # Phase 4: Network Building
    4: [
        PRInfo(24, "Add configurable network builder and examples", "pr-24", 4, "LOW"),
        PRInfo(23, "Refine improved neuron learning flow", "pr-23", 4, "LOW"),
        PRInfo(30, "Improve network learning APIs and validation checks", "pr-30", 4, "LOW"),
        PRInfo(33, "Refine BioNet serialization and persistence", "pr-33", 4, "LOW"),
    ],
    # Phase 5: AI Features
    5: [
        PRInfo(29, "Refine novelty router tool matching and fallback", "pr-29", 5, "LOW"),
        PRInfo(22, "Refine novelty analyzer feature space", "pr-22", 5, "LOW"),
        PRInfo(10, "Add novelty-aware tool gating manager", "pr-10", 5, "LOW"),
        PRInfo(12, "Add curiosity module and reinforcement learning demo", "pr-12", 5, "LOW"),
        PRInfo(21, "Add curiosity-driven RL demo and batching support", "pr-21", 5, "LOW"),
    ],
    # Phase 6: Documentation and Release
    6: [
        PRInfo(18, "Add documentation site and CI automation", "pr-18", 6, "LOW"),
        PRInfo(17, "Add release roadmap and enterprise documentation", "pr-17", 6, "LOW"),
        PRInfo(4, "Add release automation and unified API", "pr-4", 6, "LOW"),
        PRInfo(3, "docs: add bilingual documentation suite", "pr-3", 6, "LOW"),
        PRInfo(26, "Polish README usage example", "pr-26", 6, "LOW"),
        PRInfo(28, "Add httpx dependency to development requirements", "pr-28", 6, "LOW"),
        PRInfo(27, "Ignore generated curiosity benchmark artifacts", "pr-27", 6, "LOW"),
    ],
}


class MergeConflictChecker:
    """Check for merge conflicts between branches."""
    
    def __init__(self, base_branch: str = "main"):
        self.base_branch = base_branch
        self.repo_root = self._get_repo_root()
    
    def _get_repo_root(self) -> Path:
        """Get the repository root directory."""
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    
    def _run_git(self, *args) -> subprocess.CompletedProcess:
        """Run a git command."""
        return subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            cwd=self.repo_root
        )
    
    def fetch_pr_branch(self, pr_number: int) -> bool:
        """Fetch a PR branch from GitHub."""
        result = self._run_git(
            "fetch", "origin", f"pull/{pr_number}/head:pr-{pr_number}"
        )
        return result.returncode == 0
    
    def check_conflicts(self, pr_info: PRInfo) -> Optional[ConflictInfo]:
        """Check if a PR has conflicts with the base branch."""
        # Save current branch
        current_branch = self._run_git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        
        try:
            # Try to fetch the PR branch
            if not self.fetch_pr_branch(pr_info.number):
                print(f"⚠️  Could not fetch PR #{pr_info.number}")
                return None
            
            # Checkout PR branch
            self._run_git("checkout", f"pr-{pr_info.number}")
            
            # Try merge (dry-run)
            result = self._run_git("merge", "--no-commit", "--no-ff", self.base_branch)
            
            if result.returncode != 0:
                # Conflicts detected
                conflicting_files = self._get_conflicting_files()
                summary = self._analyze_conflicts(conflicting_files)
                
                # Abort the merge
                self._run_git("merge", "--abort")
                
                return ConflictInfo(
                    pr_number=pr_info.number,
                    pr_title=pr_info.title,
                    conflicting_files=conflicting_files,
                    base_branch=self.base_branch,
                    conflict_summary=summary
                )
            else:
                # No conflicts, abort the merge anyway
                self._run_git("merge", "--abort")
                return None
                
        finally:
            # Return to original branch
            self._run_git("checkout", current_branch)
    
    def _get_conflicting_files(self) -> List[str]:
        """Get list of files with conflicts."""
        result = self._run_git("diff", "--name-only", "--diff-filter=U")
        if result.stdout:
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        return []
    
    def _analyze_conflicts(self, files: List[str]) -> str:
        """Analyze the type of conflicts."""
        conflict_types = {
            "core": [],
            "tests": [],
            "docs": [],
            "config": [],
            "other": []
        }
        
        for file in files:
            if "core" in file or "neuron" in file:
                conflict_types["core"].append(file)
            elif "test" in file:
                conflict_types["tests"].append(file)
            elif "doc" in file or "README" in file:
                conflict_types["docs"].append(file)
            elif "pyproject.toml" in file or "requirements" in file:
                conflict_types["config"].append(file)
            else:
                conflict_types["other"].append(file)
        
        summary_parts = []
        for ctype, cfiles in conflict_types.items():
            if cfiles:
                summary_parts.append(f"{ctype}: {len(cfiles)} file(s)")
        
        return ", ".join(summary_parts) if summary_parts else "Unknown"


def generate_markdown_report(conflicts: List[ConflictInfo], output_file: str):
    """Generate a markdown report of conflicts."""
    with open(output_file, 'w') as f:
        f.write("# BioNeuronAI Merge Conflicts Report\n\n")
        f.write(f"**Total PRs with conflicts**: {len(conflicts)}\n\n")
        
        if not conflicts:
            f.write("✅ **No conflicts detected!**\n")
            return
        
        f.write("## Conflicts by PR\n\n")
        
        for conflict in conflicts:
            f.write(f"### PR #{conflict.pr_number}: {conflict.pr_title}\n\n")
            f.write(f"**Conflict Summary**: {conflict.conflict_summary}\n\n")
            f.write(f"**Conflicting Files** ({len(conflict.conflicting_files)}):\n\n")
            for file in conflict.conflicting_files:
                f.write(f"- `{file}`\n")
            f.write("\n")
        
        f.write("\n## Recommended Resolution Order\n\n")
        f.write("Resolve conflicts in priority order:\n\n")
        
        # Sort by phase
        sorted_conflicts = sorted(conflicts, key=lambda c: c.pr_number)
        for phase in range(1, 7):
            phase_conflicts = [c for c in sorted_conflicts if any(
                pr.number == c.pr_number for pr in PR_PHASES.get(phase, [])
            )]
            if phase_conflicts:
                f.write(f"\n### Phase {phase}\n\n")
                for c in phase_conflicts:
                    f.write(f"- [ ] PR #{c.pr_number}: {c.pr_title}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Check for merge conflicts in BioNeuronAI PRs"
    )
    parser.add_argument(
        "--pr", type=int, help="Check a specific PR number"
    )
    parser.add_argument(
        "--pr-list", type=str, help="Comma-separated list of PR numbers"
    )
    parser.add_argument(
        "--all", action="store_true", help="Check all PRs"
    )
    parser.add_argument(
        "--base", type=str, default="main", help="Base branch (default: main)"
    )
    parser.add_argument(
        "--report", type=str, help="Output markdown report file"
    )
    parser.add_argument(
        "--phase", type=int, choices=[1, 2, 3, 4, 5, 6],
        help="Check all PRs in a specific phase"
    )
    
    args = parser.parse_args()
    
    checker = MergeConflictChecker(base_branch=args.base)
    prs_to_check = []
    
    # Determine which PRs to check
    if args.pr:
        # Find PR info
        for phase_prs in PR_PHASES.values():
            for pr in phase_prs:
                if pr.number == args.pr:
                    prs_to_check = [pr]
                    break
    elif args.pr_list:
        pr_numbers = [int(n.strip()) for n in args.pr_list.split(',')]
        for phase_prs in PR_PHASES.values():
            prs_to_check.extend([pr for pr in phase_prs if pr.number in pr_numbers])
    elif args.phase:
        prs_to_check = PR_PHASES[args.phase]
    elif args.all:
        for phase_prs in PR_PHASES.values():
            prs_to_check.extend(phase_prs)
    else:
        parser.print_help()
        return 1
    
    print(f"🔍 Checking {len(prs_to_check)} PR(s) for conflicts with '{args.base}'...\n")
    
    conflicts = []
    for pr in prs_to_check:
        print(f"Checking PR #{pr.number}: {pr.title}...")
        conflict = checker.check_conflicts(pr)
        if conflict:
            print(f"  ❌ CONFLICTS DETECTED: {conflict.conflict_summary}")
            conflicts.append(conflict)
        else:
            print(f"  ✅ No conflicts")
        print()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {len(conflicts)} PR(s) with conflicts out of {len(prs_to_check)} checked")
    print(f"{'='*60}\n")
    
    # Generate report if requested
    if args.report:
        generate_markdown_report(conflicts, args.report)
        print(f"📄 Report saved to: {args.report}\n")
    
    # Exit with error code if conflicts found
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
