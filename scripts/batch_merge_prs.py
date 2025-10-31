#!/usr/bin/env python3
"""
BioNeuronAI Batch PR Merge Helper

This script assists with systematically merging multiple PRs in priority order.
It handles fetching, conflict detection, and provides guidance for resolution.

Usage:
    # Interactive mode - merges PRs one by one
    python scripts/batch_merge_prs.py --interactive
    
    # Merge specific phase
    python scripts/batch_merge_prs.py --phase 1
    
    # Dry run - check what would be merged
    python scripts/batch_merge_prs.py --phase 1 --dry-run
    
    # Resume from specific PR
    python scripts/batch_merge_prs.py --phase 1 --start-from 16
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


class MergeStatus(Enum):
    """Status of a merge attempt."""
    SUCCESS = "success"
    CONFLICT = "conflict"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class PRInfo:
    """Information about a Pull Request."""
    number: int
    title: str
    phase: int
    priority: str


@dataclass
class MergeResult:
    """Result of a merge attempt."""
    pr_info: PRInfo
    status: MergeStatus
    message: str
    conflicting_files: List[str] = None


# PR 配置 - 與 check_merge_conflicts.py 保持一致
PR_PHASES = {
    1: [  # High Priority - Core Architecture
        PRInfo(25, "Refactor BioNeuron architecture with strategy base class", 1, "HIGH"),
        PRInfo(16, "Introduce shared neuron base and align BioLayer API", 1, "HIGH"),
        PRInfo(8, "Add parameterized LIF and STDP neuron types", 1, "HIGH"),
    ],
    2: [  # Medium Priority - Feature Modules
        PRInfo(20, "Introduce shared security package and tests", 2, "MEDIUM"),
        PRInfo(14, "Refactor security modules into dedicated package", 2, "MEDIUM"),
        PRInfo(13, "Improve vectorization and add concurrency safeguards", 2, "MEDIUM"),
        PRInfo(6, "Add persistence support and online learning safeguards", 2, "MEDIUM"),
    ],
    3: [  # CLI and Tools
        PRInfo(19, "Refactor CLI into Typer app and add Streamlit dashboard", 3, "MEDIUM"),
        PRInfo(5, "Add Typer-based CLI with dashboard streaming", 3, "MEDIUM"),
        PRInfo(15, "Add configurable network builder and CLI config support", 3, "MEDIUM"),
    ],
    4: [  # Network Building
        PRInfo(24, "Add configurable network builder and examples", 4, "LOW"),
        PRInfo(23, "Refine improved neuron learning flow", 4, "LOW"),
        PRInfo(30, "Improve network learning APIs and validation checks", 4, "LOW"),
        PRInfo(33, "Refine BioNet serialization and persistence", 4, "LOW"),
    ],
    5: [  # AI Features
        PRInfo(29, "Refine novelty router tool matching and fallback", 5, "LOW"),
        PRInfo(22, "Refine novelty analyzer feature space", 5, "LOW"),
        PRInfo(10, "Add novelty-aware tool gating manager", 5, "LOW"),
        PRInfo(12, "Add curiosity module and reinforcement learning demo", 5, "LOW"),
        PRInfo(21, "Add curiosity-driven RL demo and batching support", 5, "LOW"),
    ],
    6: [  # Documentation and Release
        PRInfo(18, "Add documentation site and CI automation", 6, "LOW"),
        PRInfo(17, "Add release roadmap and enterprise documentation", 6, "LOW"),
        PRInfo(4, "Add release automation and unified API", 6, "LOW"),
        PRInfo(3, "docs: add bilingual documentation suite", 6, "LOW"),
        PRInfo(26, "Polish README usage example", 6, "LOW"),
        PRInfo(28, "Add httpx dependency to development requirements", 6, "LOW"),
        PRInfo(27, "Ignore generated curiosity benchmark artifacts", 6, "LOW"),
    ],
}


class PRMergeHelper:
    """Helper for merging PRs systematically."""
    
    def __init__(self, base_branch: str = "main", dry_run: bool = False):
        self.base_branch = base_branch
        self.dry_run = dry_run
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
    
    def _run_git(self, *args, check=False) -> subprocess.CompletedProcess:
        """Run a git command."""
        return subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            cwd=self.repo_root,
            check=check
        )
    
    def ensure_clean_state(self) -> bool:
        """Ensure repository is in clean state."""
        result = self._run_git("status", "--porcelain")
        if result.stdout.strip():
            print("❌ Error: Repository has uncommitted changes.")
            print("   Please commit or stash your changes first.")
            return False
        return True
    
    def update_base_branch(self) -> bool:
        """Update the base branch to latest."""
        print(f"📥 Updating {self.base_branch} branch...")
        
        # Checkout base branch
        result = self._run_git("checkout", self.base_branch)
        if result.returncode != 0:
            print(f"❌ Error: Could not checkout {self.base_branch}")
            return False
        
        # Pull latest
        result = self._run_git("pull", "origin", self.base_branch)
        if result.returncode != 0:
            print(f"❌ Error: Could not pull latest {self.base_branch}")
            return False
        
        print(f"✅ {self.base_branch} updated successfully\n")
        return True
    
    def fetch_pr(self, pr_number: int) -> bool:
        """Fetch a PR branch."""
        result = self._run_git(
            "fetch", "origin", f"pull/{pr_number}/head:pr-{pr_number}"
        )
        return result.returncode == 0
    
    def merge_pr(self, pr_info: PRInfo, interactive: bool = False) -> MergeResult:
        """Attempt to merge a PR."""
        print(f"\n{'='*70}")
        print(f"Processing PR #{pr_info.number}: {pr_info.title}")
        print(f"Priority: {pr_info.priority} | Phase: {pr_info.phase}")
        print(f"{'='*70}\n")
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No actual merge will be performed")
        
        # Ensure we're on base branch
        self._run_git("checkout", self.base_branch)
        
        # Fetch PR
        print(f"📥 Fetching PR #{pr_info.number}...")
        if not self.fetch_pr(pr_info.number):
            return MergeResult(
                pr_info=pr_info,
                status=MergeStatus.ERROR,
                message="Could not fetch PR branch"
            )
        
        # Checkout PR branch
        self._run_git("checkout", f"pr-{pr_info.number}")
        
        # Check for conflicts
        print(f"🔄 Testing merge with {self.base_branch}...")
        result = self._run_git("merge", "--no-commit", "--no-ff", self.base_branch)
        
        if result.returncode != 0:
            # Conflicts detected
            conflicting_files = self._get_conflicting_files()
            self._run_git("merge", "--abort")
            
            print(f"\n❌ MERGE CONFLICTS DETECTED")
            print(f"\nConflicting files ({len(conflicting_files)}):")
            for file in conflicting_files:
                print(f"  - {file}")
            
            if interactive:
                print("\n" + "="*70)
                print("Conflict Resolution Options:")
                print("  1. Resolve manually now (opens editor)")
                print("  2. Skip this PR for now")
                print("  3. Abort merge process")
                choice = input("\nYour choice (1/2/3): ").strip()
                
                if choice == "1":
                    return self._handle_manual_resolution(pr_info, conflicting_files)
                elif choice == "2":
                    return MergeResult(
                        pr_info=pr_info,
                        status=MergeStatus.SKIPPED,
                        message="Skipped by user",
                        conflicting_files=conflicting_files
                    )
                else:
                    print("\n🛑 Merge process aborted by user")
                    sys.exit(0)
            
            return MergeResult(
                pr_info=pr_info,
                status=MergeStatus.CONFLICT,
                message=f"Conflicts in {len(conflicting_files)} file(s)",
                conflicting_files=conflicting_files
            )
        
        # No conflicts
        if self.dry_run:
            print("✅ No conflicts detected (would merge successfully)")
            self._run_git("merge", "--abort")
            return MergeResult(
                pr_info=pr_info,
                status=MergeStatus.SUCCESS,
                message="Would merge successfully (dry run)"
            )
        
        # Commit the merge
        print("✅ No conflicts - committing merge...")
        self._run_git("commit", "-m", f"Merge PR #{pr_info.number}: {pr_info.title}")
        
        # Checkout base and merge
        self._run_git("checkout", self.base_branch)
        self._run_git("merge", f"pr-{pr_info.number}", "--ff-only")
        
        print(f"✅ PR #{pr_info.number} merged successfully!")
        
        return MergeResult(
            pr_info=pr_info,
            status=MergeStatus.SUCCESS,
            message="Merged successfully"
        )
    
    def _get_conflicting_files(self) -> List[str]:
        """Get list of files with conflicts."""
        result = self._run_git("diff", "--name-only", "--diff-filter=U")
        if result.stdout:
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        return []
    
    def _handle_manual_resolution(self, pr_info: PRInfo, conflicting_files: List[str]) -> MergeResult:
        """Handle manual conflict resolution."""
        print("\n📝 Opening conflicts for manual resolution...")
        print("   After resolving conflicts:")
        print("   1. Stage resolved files: git add <file>")
        print("   2. Press ENTER here to continue")
        
        # Re-attempt the merge so conflicts are visible
        self._run_git("merge", "--no-ff", self.base_branch)
        
        input("\nPress ENTER when ready to continue...")
        
        # Check if conflicts are resolved
        remaining_conflicts = self._get_conflicting_files()
        if remaining_conflicts:
            print(f"\n⚠️  Warning: {len(remaining_conflicts)} file(s) still have conflicts")
            choice = input("Continue anyway? (y/n): ").strip().lower()
            if choice != 'y':
                self._run_git("merge", "--abort")
                return MergeResult(
                    pr_info=pr_info,
                    status=MergeStatus.SKIPPED,
                    message="Manual resolution incomplete",
                    conflicting_files=remaining_conflicts
                )
        
        # Commit the merge
        self._run_git("commit", "--no-edit")
        
        # Merge to base
        self._run_git("checkout", self.base_branch)
        self._run_git("merge", f"pr-{pr_info.number}", "--ff-only")
        
        print(f"✅ PR #{pr_info.number} merged after manual resolution!")
        
        return MergeResult(
            pr_info=pr_info,
            status=MergeStatus.SUCCESS,
            message="Merged successfully (manual resolution)"
        )


def print_summary(results: List[MergeResult]):
    """Print summary of merge results."""
    print("\n" + "="*70)
    print("MERGE SUMMARY")
    print("="*70 + "\n")
    
    success = [r for r in results if r.status == MergeStatus.SUCCESS]
    conflicts = [r for r in results if r.status == MergeStatus.CONFLICT]
    skipped = [r for r in results if r.status == MergeStatus.SKIPPED]
    errors = [r for r in results if r.status == MergeStatus.ERROR]
    
    print(f"✅ Successfully merged: {len(success)}")
    print(f"❌ Conflicts detected: {len(conflicts)}")
    print(f"⏭️  Skipped: {len(skipped)}")
    print(f"🔴 Errors: {len(errors)}")
    print(f"\nTotal processed: {len(results)}\n")
    
    if conflicts:
        print("\n" + "-"*70)
        print("PRs with conflicts (need manual resolution):")
        print("-"*70)
        for r in conflicts:
            print(f"\nPR #{r.pr_info.number}: {r.pr_info.title}")
            print(f"  Files: {len(r.conflicting_files)}")
            for file in r.conflicting_files[:5]:  # Show first 5
                print(f"    - {file}")
            if len(r.conflicting_files) > 5:
                print(f"    ... and {len(r.conflicting_files) - 5} more")


def main():
    parser = argparse.ArgumentParser(
        description="Batch merge PRs for BioNeuronAI"
    )
    parser.add_argument(
        "--phase", type=int, choices=[1, 2, 3, 4, 5, 6],
        help="Merge all PRs in a specific phase"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Merge all PRs in priority order"
    )
    parser.add_argument(
        "--interactive", action="store_true",
        help="Interactive mode - prompt for conflict resolution"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Dry run - check mergeability without actually merging"
    )
    parser.add_argument(
        "--base", type=str, default="main",
        help="Base branch (default: main)"
    )
    parser.add_argument(
        "--start-from", type=int,
        help="Resume from specific PR number"
    )
    
    args = parser.parse_args()
    
    if not (args.phase or args.all):
        parser.print_help()
        return 1
    
    helper = PRMergeHelper(base_branch=args.base, dry_run=args.dry_run)
    
    # Check clean state
    if not args.dry_run and not helper.ensure_clean_state():
        return 1
    
    # Update base branch
    if not helper.update_base_branch():
        return 1
    
    # Determine PRs to merge
    prs_to_merge = []
    if args.phase:
        prs_to_merge = PR_PHASES[args.phase]
    elif args.all:
        for phase in range(1, 7):
            prs_to_merge.extend(PR_PHASES[phase])
    
    # Filter by start-from if specified
    if args.start_from:
        prs_to_merge = [pr for pr in prs_to_merge if pr.number >= args.start_from]
    
    print(f"\n🚀 Starting merge process for {len(prs_to_merge)} PR(s)")
    if args.dry_run:
        print("   (DRY RUN MODE - no actual merges will be performed)")
    print()
    
    results = []
    for pr in prs_to_merge:
        result = helper.merge_pr(pr, interactive=args.interactive)
        results.append(result)
        
        if not args.interactive and result.status == MergeStatus.CONFLICT:
            print(f"\n⚠️  Stopping at first conflict. Resolve PR #{pr.number} and re-run.")
            break
    
    print_summary(results)
    
    # Return error code if any conflicts or errors
    has_issues = any(r.status in [MergeStatus.CONFLICT, MergeStatus.ERROR] for r in results)
    return 1 if has_issues else 0


if __name__ == "__main__":
    sys.exit(main())
