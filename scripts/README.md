# Scripts README

This directory contains helper scripts for managing the BioNeuronAI repository.

## Merge Conflict Management Scripts

### check_merge_conflicts.py

Detects and analyzes merge conflicts across PRs.

**Usage Examples:**

```bash
# Check a specific PR
python scripts/check_merge_conflicts.py --pr 25

# Check multiple PRs
python scripts/check_merge_conflicts.py --pr-list 25,16,8

# Check all PRs in Phase 1
python scripts/check_merge_conflicts.py --phase 1

# Check all PRs and generate report
python scripts/check_merge_conflicts.py --all --report conflicts_report.md
```

**Options:**
- `--pr NUMBER`: Check a specific PR
- `--pr-list NUMBERS`: Check multiple PRs (comma-separated)
- `--phase 1-6`: Check all PRs in a phase
- `--all`: Check all PRs
- `--base BRANCH`: Base branch to check against (default: main)
- `--report FILE`: Generate markdown report

### batch_merge_prs.py

Systematically merge multiple PRs in priority order.

**Usage Examples:**

```bash
# Interactive merge of Phase 1 PRs
python scripts/batch_merge_prs.py --phase 1 --interactive

# Dry run to check what would happen
python scripts/batch_merge_prs.py --phase 1 --dry-run

# Merge all PRs in order
python scripts/batch_merge_prs.py --all --interactive

# Resume from a specific PR
python scripts/batch_merge_prs.py --phase 2 --start-from 14
```

**Options:**
- `--phase 1-6`: Merge PRs in a specific phase
- `--all`: Merge all PRs in priority order
- `--interactive`: Prompt for conflict resolution
- `--dry-run`: Check mergeability without merging
- `--base BRANCH`: Base branch (default: main)
- `--start-from NUMBER`: Resume from specific PR

## Workflow

### Recommended Merge Process

1. **Check for conflicts first:**
   ```bash
   python scripts/check_merge_conflicts.py --phase 1 --report phase1_conflicts.md
   ```

2. **Review the report** and plan resolution strategy

3. **Merge PRs interactively:**
   ```bash
   python scripts/batch_merge_prs.py --phase 1 --interactive
   ```

4. **For conflicts:**
   - Review conflicting files
   - Resolve manually
   - Stage resolved files: `git add <file>`
   - Continue the script

5. **Run tests after each merge:**
   ```bash
   pytest tests/ -v
   black src/ tests/
   ```

6. **Move to next phase** once current phase is complete

### CI Integration

The `.github/workflows/merge-validation.yml` workflow automatically:
- Detects merge conflicts on PR events
- Runs tests and validation
- Checks backward compatibility
- Comments on PRs with conflict details

## Script Dependencies

Both scripts use only Python standard library plus git command-line tools. No additional Python packages required for the scripts themselves.

## Troubleshooting

### "Could not fetch PR branch"

**Solution:** Ensure you have GitHub authentication configured:
```bash
gh auth login
```

Or use HTTPS with personal access token:
```bash
git config --global credential.helper store
```

### "Repository has uncommitted changes"

**Solution:** Commit or stash your changes:
```bash
git stash
# or
git add . && git commit -m "WIP"
```

### Merge conflicts during batch processing

**Solution:** The interactive mode will help you resolve:
1. Choose option 1 to resolve manually
2. Edit the conflicting files
3. Run `git add <resolved-files>`
4. Press ENTER to continue

## Advanced Usage

### Custom conflict resolution workflow

```bash
# 1. Generate detailed conflict report
python scripts/check_merge_conflicts.py --all --report full_analysis.md

# 2. Identify high-conflict PRs
cat full_analysis.md | grep "❌"

# 3. Merge low-conflict PRs first
python scripts/batch_merge_prs.py --pr-list 3,26,27,28 --interactive

# 4. Tackle high-conflict PRs one by one
python scripts/batch_merge_prs.py --pr 25 --interactive
```

### Testing before merge

```bash
# Dry run entire phase
python scripts/batch_merge_prs.py --phase 1 --dry-run

# Review what would be merged
# Then do it for real
python scripts/batch_merge_prs.py --phase 1 --interactive
```

## Contributing

When adding new scripts:
1. Add usage examples to this README
2. Include docstrings in the script
3. Add error handling for common cases
4. Make scripts executable: `chmod +x scripts/yourscript.py`
