# Quick Reference: Common Merge Conflict Patterns

This guide provides quick solutions for common merge conflict scenarios in BioNeuronAI.

## Pattern 1: Duplicate Neuron Implementations

### Scenario
- `core.py` has `BioNeuron` 
- `improved_core.py` has `ImprovedBioNeuron`
- Both are being actively developed

### Symptoms
```
<<<<<<< HEAD
from .core import BioNeuron
=======
from .improved_core import ImprovedBioNeuron as BioNeuron
>>>>>>> pr-branch
```

### Resolution
```python
# In __init__.py - support both temporarily
from .core import BioNeuron as ClassicBioNeuron
from .improved_core import ImprovedBioNeuron

# Default export (use improved)
BioNeuron = ImprovedBioNeuron

# Provide alias for backward compatibility
__all__ = ['BioNeuron', 'ClassicBioNeuron', 'ImprovedBioNeuron']
```

### Commands
```bash
# Edit the file
vim src/bioneuronai/__init__.py

# Accept both versions and merge manually
# Keep both imports, add compatibility layer
```

---

## Pattern 2: Function Signature Changes

### Scenario
- Main branch: `forward(inputs)`
- PR branch: `forward(inputs, context=None)`

### Symptoms
```python
<<<<<<< HEAD
def forward(self, inputs: Sequence[float]) -> float:
=======
def forward(self, inputs: Sequence[float], context: Optional[dict] = None) -> float:
>>>>>>> pr-branch
```

### Resolution
```python
def forward(self, inputs: Sequence[float], context: Optional[dict] = None) -> float:
    """Forward pass with optional context.
    
    Args:
        inputs: Input vector
        context: Optional context dict (new in v0.2.0)
    """
    # Use context if provided
    if context is not None:
        # New behavior
        pass
    # Existing behavior works without changes
    # ...
```

### Commands
```bash
# Accept incoming changes (PR version)
git checkout --theirs src/bioneuronai/core.py
git add src/bioneuronai/core.py

# Or manually edit to add default parameter
```

---

## Pattern 3: Import Reorganization

### Scenario
- Main: imports from `bioneuronai.core`
- PR: imports from `bioneuronai.neurons.core`

### Symptoms
```python
<<<<<<< HEAD
from bioneuronai.core import BioNeuron
=======
from bioneuronai.neurons.core import BioNeuron
>>>>>>> pr-branch
```

### Resolution Strategy A (Gradual migration):
```python
# In bioneuronai/core.py - create re-export
from .neurons.core import BioNeuron  # New location
import warnings

# Maintain old import path temporarily
warnings.warn(
    "Importing from bioneuronai.core is deprecated. "
    "Use bioneuronai.neurons.core instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['BioNeuron']  # Still accessible from old path
```

### Resolution Strategy B (Immediate migration):
```python
# Update all import statements
# Use find-replace across codebase
# Old: from bioneuronai.core import
# New: from bioneuronai.neurons.core import
```

### Commands
```bash
# Automated find and replace
find src/ tests/ examples/ -name "*.py" -exec sed -i \
  's/from bioneuronai\.core import/from bioneuronai.neurons.core import/g' {} +

# Verify changes
git diff
```

---

## Pattern 4: Configuration File Conflicts

### Scenario
Both branches add dependencies to `pyproject.toml`

### Symptoms
```toml
<<<<<<< HEAD
dependencies = [
    "numpy>=1.21.0",
    "fastapi>=0.110",
]
=======
dependencies = [
    "numpy>=1.21.0",
    "fastapi>=0.110",
    "typer>=0.9.0",
]
>>>>>>> pr-branch
```

### Resolution
```toml
dependencies = [
    "numpy>=1.21.0",
    "fastapi>=0.110",
    "typer>=0.9.0",  # From PR - accept addition
    "httpx>=0.24",    # From another PR - merge all
]
```

### Version Conflicts
```toml
# If versions conflict:
<<<<<<< HEAD
    "numpy>=1.21.0",
=======
    "numpy>=1.24.0",
>>>>>>> pr-branch

# Resolution: Take higher compatible version
    "numpy>=1.24.0",  # Higher version, still compatible
```

### Commands
```bash
# Manually edit pyproject.toml
# Sort dependencies alphabetically
# Use highest compatible versions
```

---

## Pattern 5: Test File Conflicts

### Scenario
Both branches add tests for the same feature

### Symptoms
```python
<<<<<<< HEAD
def test_basic_forward():
    neuron = BioNeuron(2)
    assert neuron.forward([0.5, 0.5]) >= 0
=======
def test_forward_with_context():
    neuron = BioNeuron(2)
    result = neuron.forward([0.5, 0.5], context={'mode': 'test'})
    assert result >= 0
>>>>>>> pr-branch
```

### Resolution
```python
def test_basic_forward():
    """Test basic forward pass without context."""
    neuron = BioNeuron(2)
    assert neuron.forward([0.5, 0.5]) >= 0

def test_forward_with_context():
    """Test forward pass with context."""
    neuron = BioNeuron(2)
    result = neuron.forward([0.5, 0.5], context={'mode': 'test'})
    assert result >= 0

def test_forward_backward_compatibility():
    """Ensure old code still works."""
    neuron = BioNeuron(2)
    # Old style (no context) should still work
    result1 = neuron.forward([0.5, 0.5])
    # New style with context
    result2 = neuron.forward([0.5, 0.5], context={})
    assert result1 >= 0 and result2 >= 0
```

### Commands
```bash
# Keep both tests
git checkout --ours tests/test_core.py
git checkout --theirs --patch tests/test_core.py
# Manually merge in editor

# Run tests to verify
pytest tests/test_core.py -v
```

---

## Pattern 6: Class Inheritance Conflicts

### Scenario
- Main: `class BioNeuron:`
- PR: `class BioNeuron(BaseNeuron):`

### Symptoms
```python
<<<<<<< HEAD
class BioNeuron:
    def __init__(self, num_inputs):
=======
class BioNeuron(BaseNeuron):
    def __init__(self, num_inputs, **kwargs):
        super().__init__(**kwargs)
>>>>>>> pr-branch
```

### Resolution
```python
class BioNeuron(BaseNeuron):
    """Bio-inspired neuron with Hebbian learning.
    
    Inherits from BaseNeuron (new in v0.2.0).
    Maintains backward compatibility with v0.1.x API.
    """
    
    def __init__(self, num_inputs, threshold=0.8, learning_rate=0.01, 
                 memory_len=5, seed=None, **kwargs):
        # New: call parent initializer
        super().__init__(**kwargs)
        
        # Existing initialization code
        self.num_inputs = num_inputs
        # ...
```

---

## Pattern 7: Module Restructuring

### Scenario
Files moved from one package to another

### Symptoms
```
<<<<<<< HEAD
src/bioneuronai/security_module.py
=======
src/bioneuronai/security/auth.py
src/bioneuronai/security/detection.py
>>>>>>> pr-branch
```

### Resolution
```python
# Step 1: Create new package structure
mkdir -p src/bioneuronai/security/

# Step 2: Move and split files
# Move relevant code to new locations

# Step 3: Add re-exports for compatibility
# In src/bioneuronai/security_module.py
from .security.auth import *
from .security.detection import *
import warnings

warnings.warn(
    "security_module is deprecated. Import from bioneuronai.security instead.",
    DeprecationWarning
)
```

### Commands
```bash
# Create new structure
mkdir -p src/bioneuronai/security/
touch src/bioneuronai/security/__init__.py

# Move files
git mv src/bioneuronai/enhanced_auth_module.py src/bioneuronai/security/auth.py

# Update imports everywhere
grep -r "from bioneuronai.enhanced_auth_module" . --include="*.py" | \
  cut -d: -f1 | sort -u | \
  xargs sed -i 's/from bioneuronai\.enhanced_auth_module/from bioneuronai.security.auth/g'
```

---

## Quick Decision Tree

```
Conflict in file?
│
├─ pyproject.toml / requirements.txt
│  └─ Merge all dependencies, use highest compatible versions
│
├─ __init__.py (exports)
│  └─ Export both versions, mark old as deprecated
│
├─ core.py / improved_core.py
│  └─ Merge features, maintain one implementation with strategy pattern
│
├─ test_*.py
│  └─ Keep all tests, add compatibility tests
│
├─ README.md / docs/
│  └─ Merge all documentation, remove duplicates
│
└─ Other .py files
   ├─ Function signature change?
   │  └─ Add optional parameters with defaults
   │
   ├─ New feature addition?
   │  └─ Keep both features
   │
   ├─ Refactoring?
   │  └─ Use new structure, add compatibility layer
   │
   └─ Bug fix?
      └─ Keep the fix, merge if both fix same issue
```

---

## Useful Git Commands

```bash
# Show conflict summary
git diff --name-only --diff-filter=U

# Show full conflict details
git diff

# Accept all changes from one side (use carefully!)
git checkout --theirs path/to/file  # Take PR version
git checkout --ours path/to/file    # Keep main version

# Accept changes selectively (interactive)
git checkout --patch --theirs path/to/file

# After resolving, mark as resolved
git add path/to/file

# If you mess up, restart conflict resolution
git checkout --conflict=merge path/to/file

# Abort entire merge
git merge --abort

# Show merge conflicts in different format
git diff --diff-filter=U --name-only
git diff --check
```

---

## Validation Checklist

After resolving any conflict:

```bash
# 1. Ensure code runs
python -c "import bioneuronai; print('OK')"

# 2. Run tests
pytest tests/ -v

# 3. Check examples
python examples/basic_demo.py

# 4. Verify style
black --check src/ tests/
isort --check src/ tests/

# 5. Type check
mypy src/ --ignore-missing-imports

# 6. Check for common issues
flake8 src/ tests/ --max-line-length=88
```

---

This quick reference should cover 90% of conflicts you'll encounter. For complex cases, refer to the full [Merge Conflict Resolution Guide](MERGE_CONFLICT_RESOLUTION_GUIDE.md).
