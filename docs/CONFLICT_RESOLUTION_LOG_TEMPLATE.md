# Conflict Resolution Log Template

Use this template to document how conflicts were resolved for each PR.

## PR #[NUMBER]: [TITLE]

**Date:** YYYY-MM-DD  
**Resolver:** @username  
**Phase:** [1-6]  
**Priority:** [HIGH/MEDIUM/LOW]

### Conflict Summary

Brief description of the nature of the conflicts.

### Conflicting Files

- `path/to/file1.py` - Description of conflict
- `path/to/file2.py` - Description of conflict
- ...

### Resolution Strategy

Describe the approach taken to resolve conflicts:

#### Option Chosen
- [ ] Keep incoming changes (PR version)
- [ ] Keep current changes (main version)
- [ ] Merge both (manual integration)
- [ ] Refactor to new approach

#### Rationale

Why this resolution strategy was chosen:
- Maintains backward compatibility
- Aligns with architectural goals
- Preserves functionality from both versions
- ...

### Detailed Resolution Steps

#### File: `path/to/file1.py`

**Conflict Type:** [Code change / Feature addition / Refactoring / API change]

**Resolution:**
```python
# What was changed and why
# Show key snippets of the resolution
```

**Justification:**
Explain why this specific resolution was chosen.

#### File: `path/to/file2.py`

**Conflict Type:** [...]

**Resolution:**
```python
# Resolution code
```

**Justification:**
...

### API Changes

List any API changes that resulted from conflict resolution:

#### Breaking Changes
- `function_name(old_params)` → `function_name(new_params)`
- Removed: `deprecated_function()`
- ...

#### New Features
- Added: `new_function()` - Description
- ...

#### Deprecated
- `old_api()` - Will be removed in version X.Y
- ...

### Migration Guide

If backward compatibility is affected, provide migration guidance:

```python
# Old code
old_usage_example()

# New code
new_usage_example()
```

### Testing

#### Tests Added/Modified
- `test_new_feature()` - Tests the merged functionality
- Modified `test_existing()` - Updated for API changes

#### Test Results
```bash
# Paste test output
pytest tests/ -v
# All tests passed
```

#### Manual Verification
- [ ] Ran examples/basic_demo.py
- [ ] Ran examples/advanced_demo.py
- [ ] Checked CLI functionality
- [ ] Verified documentation builds

### Code Quality Checks

```bash
# Linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Type checking
mypy src/

# All passed: ✅
```

### Dependencies

#### Added
- `package-name>=version` - Reason for addition

#### Updated
- `package-name>=old-version` → `>=new-version` - Reason for update

#### Removed
- `package-name` - Reason for removal

### Documentation Updates

- [ ] Updated README.md
- [ ] Updated API documentation
- [ ] Updated examples
- [ ] Updated CHANGELOG.md
- [ ] Updated migration guide

### Follow-up Tasks

- [ ] Create issue for refactoring X
- [ ] Update related PRs (#XX, #YY)
- [ ] Notify maintainers of API changes
- [ ] Schedule deprecation of old API

### Review Checklist

Before finalizing the merge:

- [ ] All conflicts resolved
- [ ] Tests pass
- [ ] Code style consistent
- [ ] Type hints correct
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Performance impact assessed
- [ ] Security implications considered

### Notes

Any additional notes, gotchas, or considerations for future reference:

---

## Example Resolution

For reference, here's an example of how to fill this out:

### PR #25: Refactor BioNeuron architecture with strategy base class

**Date:** 2025-10-31  
**Resolver:** @merge-bot  
**Phase:** 1  
**Priority:** HIGH

#### Conflict Summary

PR #25 introduces a strategy pattern for neuron types, conflicting with the existing `BioNeuron` implementation in `core.py`. Both versions have different approaches to neuron activation and learning.

#### Conflicting Files

- `src/bioneuronai/core.py` - Complete rewrite with strategy pattern
- `src/bioneuronai/__init__.py` - Export changes
- `tests/test_core.py` - Test updates for new API

#### Resolution Strategy

**Option Chosen:** ✅ Merge both (manual integration)

**Rationale:**
- The strategy pattern provides better extensibility
- Need to maintain backward compatibility with existing code
- Can provide adapter for old API

#### Detailed Resolution

**File: `src/bioneuronai/core.py`**

**Conflict Type:** Architectural refactoring

**Resolution:**
```python
# Keep new strategy-based architecture
class NeuronStrategy(ABC):
    @abstractmethod
    def activate(self, potential: float) -> float:
        pass

# Add backward-compatible BioNeuron class
class BioNeuron:
    def __init__(self, num_inputs, threshold=0.8, learning_rate=0.01, 
                 memory_len=5, seed=None, strategy=None):
        # New parameter: strategy (defaults to classic behavior)
        self.strategy = strategy or ClassicActivationStrategy(threshold)
        # ... rest of implementation
```

**Justification:**
Preserves existing API while enabling new strategy pattern. Existing code continues to work without modification.

---

*Copy this template for each PR conflict resolution.*
