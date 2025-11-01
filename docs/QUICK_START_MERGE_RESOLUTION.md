# Quick Start: Resolving Merge Conflicts
# 快速開始：解決合併衝突

**Purpose**: Step-by-step guide to start resolving merge conflicts  
**Time Required**: ~2-3 hours for Phase 1  
**Prerequisites**: Git, Python 3.8+, pytest

## Immediate Next Steps

### Step 1: Environment Setup (5 minutes)

```bash
# 1. Ensure you're on main branch
cd /path/to/BioNeuronai
git checkout main
git pull origin main

# 2. Verify Python environment
python --version  # Should be 3.8+
pip install -r requirements-dev.txt

# 3. Create reports directory
mkdir -p reports

# 4. Run baseline tests
pytest tests/ -v
```

### Step 2: Analyze Phase 1 Conflicts (10 minutes)

```bash
# Generate conflict report for Phase 1
python scripts/check_merge_conflicts.py --phase 1 --report reports/phase1_conflicts.md

# Review the report
cat reports/phase1_conflicts.md

# Or use a markdown viewer
code reports/phase1_conflicts.md  # VSCode
# or
open reports/phase1_conflicts.md  # macOS
```

### Step 3: Execute Phase 1 Merges (1-2 hours)

#### Option A: Interactive Mode (Recommended)

```bash
# Start interactive merge process
python scripts/batch_merge_prs.py --phase 1 --interactive

# The script will:
# 1. Fetch each PR branch
# 2. Attempt to merge
# 3. Stop on conflicts and prompt you
# 4. Guide you through resolution
```

#### Option B: Manual Merge (More Control)

##### Merge PR #25 First

```bash
# 1. Fetch the PR branch
git fetch origin pull/25/head:pr-25
git checkout pr-25

# 2. Try merging into main
git checkout main
git merge pr-25

# 3. If conflicts occur:
git status  # See conflicted files

# 4. Resolve conflicts in each file
# Open files with <<<<<<< markers
# Choose correct version or combine both

# 5. After resolving all conflicts:
git add .
git commit -m "Merge PR #25: Refactor BioNeuron architecture"

# 6. Validate
pytest tests/ -v
```

##### Then Merge PR #16

```bash
# Repeat process for PR #16
git fetch origin pull/16/head:pr-16
git checkout pr-16
git checkout main
git merge pr-16

# Resolve conflicts if any
# Test and commit
```

### Step 4: Validation (20 minutes)

After merging each PR:

```bash
# 1. Run full test suite
pytest tests/ -v --cov=bioneuronai

# 2. Check code style
black --check src/ tests/
isort --check src/ tests/

# 3. Type checking
mypy src/ --ignore-missing-imports

# 4. Lint
flake8 src/ tests/ --max-line-length=88

# 5. Try running examples
cd examples
python basic_demo.py
```

### Step 5: Update Progress (5 minutes)

```bash
# Update MERGE_PROGRESS.md with results
# Change status from ⏳ Pending to ✅ Merged
# Add any notes about conflicts encountered
```

## Common Conflict Scenarios

### Scenario 1: Both PRs Modify Same Function

**File**: `src/bioneuronai/core.py`

```python
<<<<<<< HEAD
def forward(self, inputs):
    # Original implementation
    return self._calculate(inputs)
=======
def forward(self, inputs, context=None):
    # New implementation with context
    return self._calculate_with_context(inputs, context)
>>>>>>> pr-25
```

**Resolution**: Keep the newer signature with optional parameter

```python
def forward(self, inputs, context=None):
    """Forward pass with optional context support."""
    if context is not None:
        return self._calculate_with_context(inputs, context)
    return self._calculate(inputs)
```

### Scenario 2: Different Import Paths

**File**: `src/bioneuronai/__init__.py`

```python
<<<<<<< HEAD
from .core import BioNeuron
=======
from .neurons.base import BaseNeuron
from .neurons.bio import BioNeuron
>>>>>>> pr-25
```

**Resolution**: Support both with re-exports

```python
# New structure
from .neurons.base import BaseNeuron
from .neurons.bio import BioNeuron

# Backward compatibility
from .core import BioNeuron as LegacyBioNeuron

__all__ = ['BaseNeuron', 'BioNeuron', 'LegacyBioNeuron']
```

### Scenario 3: Conflicting Test Files

**File**: `tests/test_core.py`

```python
<<<<<<< HEAD
def test_basic_forward():
    neuron = BioNeuron(2)
    result = neuron.forward([0.5, 0.5])
    assert result >= 0
=======
def test_forward_with_context():
    neuron = BioNeuron(2, strategy='hebbian')
    result = neuron.forward([0.5, 0.5], context={})
    assert result >= 0
>>>>>>> pr-25
```

**Resolution**: Keep both tests

```python
def test_basic_forward():
    """Test basic forward without context."""
    neuron = BioNeuron(2)
    result = neuron.forward([0.5, 0.5])
    assert result >= 0

def test_forward_with_context():
    """Test forward with strategy and context."""
    neuron = BioNeuron(2, strategy='hebbian')
    result = neuron.forward([0.5, 0.5], context={})
    assert result >= 0

def test_backward_compatibility():
    """Ensure old API still works."""
    neuron = BioNeuron(2)
    # Old style should still work
    result1 = neuron.forward([0.5, 0.5])
    # New style should also work
    result2 = neuron.forward([0.5, 0.5], context=None)
    assert result1 >= 0 and result2 >= 0
```

## Troubleshooting

### Problem: Merge Script Fails

```bash
# Error: "Cannot fetch PR branch"
# Solution: Check network connection and GitHub access

# Try manual fetch
git fetch origin pull/25/head:pr-25
```

### Problem: Tests Fail After Merge

```bash
# 1. Check what tests are failing
pytest tests/ -v --tb=short

# 2. Review the test output
# Look for imports, API changes, etc.

# 3. Fix the issues
# Update tests or code as needed

# 4. Retest
pytest tests/ -v
```

### Problem: Too Many Conflicts

```bash
# If conflicts are overwhelming:

# 1. Abort the merge
git merge --abort

# 2. Try a different approach
# - Merge in smaller chunks
# - Cherry-pick specific commits
# - Consult with PR author

# 3. Document the issue
# Add note to MERGE_PROGRESS.md about deferring this PR
```

## Emergency Rollback

If something goes wrong after pushing:

```bash
# 1. Find the commit before the problematic merge
git log --oneline -10

# 2. Reset to that commit (if haven't pushed yet)
git reset --hard <commit-sha>

# 3. Or create a revert commit (if already pushed)
git revert <merge-commit-sha>
git push origin main
```

## Checklist Before Moving to Next Phase

After completing Phase 1:

- [ ] Both PRs merged to main
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Code style checks passing (`black --check`, `isort --check`)
- [ ] Type checks passing (`mypy src/`)
- [ ] Linter passing (`flake8 src/ tests/`)
- [ ] Examples running successfully
- [ ] MERGE_PROGRESS.md updated
- [ ] Conflict resolutions documented
- [ ] No regression in functionality

## What to Do After Phase 1

```bash
# 1. Review Phase 1 results
cat docs/MERGE_PROGRESS.md

# 2. Analyze Phase 2 conflicts
python scripts/check_merge_conflicts.py --phase 2 --report reports/phase2_conflicts.md

# 3. Proceed with Phase 2 merges
python scripts/batch_merge_prs.py --phase 2 --interactive

# 4. Continue through all phases
```

## Getting Help

If you encounter issues:

1. **Check Documentation**:
   - `docs/CONFLICT_RESOLUTION_QUICK_REFERENCE.md` - Common patterns
   - `docs/CONFLICT_RESOLUTION_EXECUTION_PLAN.md` - Detailed strategies

2. **Review Scripts**:
   - `scripts/README.md` - Script usage guide
   - Script source code for detailed behavior

3. **Ask for Review**:
   - Create an issue describing the specific conflict
   - Ask original PR author for guidance
   - Request code review from team

## Expected Timeline

- **Phase 1**: 2-4 hours (core architecture is critical)
- **Phase 2**: 3-4 hours (security refactoring)
- **Phase 3**: 1-2 hours (CLI is mostly independent)
- **Phase 4**: 2-3 hours (network building)
- **Phase 5**: 2-3 hours (AI features)
- **Phase 6**: 1-2 hours (documentation)

**Total**: 11-18 hours depending on conflict complexity

## Success Criteria

You've successfully completed the task when:

✅ All 12 PRs are merged into main  
✅ All tests passing  
✅ No regressions in functionality  
✅ Documentation updated  
✅ CHANGELOG.md reflects all changes  
✅ Progress tracking complete  

## Ready to Start?

Execute this command to begin:

```bash
python scripts/check_merge_conflicts.py --phase 1 --report reports/phase1_conflicts.md && \
echo "Phase 1 conflict report generated. Review reports/phase1_conflicts.md before proceeding."
```

Good luck! 加油！

---

**Created**: 2025-10-31  
**Status**: Ready to Execute  
**Next Action**: Run Phase 1 conflict analysis
