# Contributing to BioNeuronAI

Thank you for your interest in contributing! This guide outlines the development workflow, quality checks, and review process that keep the project healthy.

## Development Workflow
1. Fork the repository and clone your fork.
2. Create a branch describing the change: `git checkout -b feature/my-improvement`.
3. Install dependencies with documentation extras: `pip install -e .[dev,docs]`.
4. Implement your changes with clear docstrings and tests.
5. Run the full quality checklist (see below).
6. Submit a Pull Request using the provided template.

## Quality Checklist
Run all commands from the project root before opening a PR:

```bash
pytest tests/ -v
pytest tests/ --cov=bioneuronai
black .
isort .
mypy src
sphinx-build -b html docs docs/_build/html
python smart_assistant.py --non-interactive --output smart_report.json
```

If any command generates artifacts (e.g., coverage reports, Smart Learning Assistant output), include them in the PR description if relevant.

## Commit Guidelines
- Write descriptive commit messages using the imperative mood.
- Group related changes into a single commit; split unrelated updates.
- Keep diffs focused and avoid formatting-only commits unless necessary.

## Documentation Standards
- Prefer comprehensive docstrings; they are surfaced automatically in the Sphinx API reference.
- Update `docs/architecture.md` when the learning rules, novelty computation, or module boundaries change.
- Add usage examples or diagrams to `docs/overview.md` when introducing new high-level features.

## Review Process
- Automated CI runs the quality checklist on every push.
- At least one maintainer review is required before merging.
- Address review feedback promptly; use follow-up commits rather than force-pushing when conversations are still open.

## Reporting Issues
Use the issue templates in `.github/ISSUE_TEMPLATE/` to report bugs or request features. Provide reproduction steps, environment details, and screenshots/logs when applicable.

## Code of Conduct
Contributors are expected to uphold respectful communication. Treat others with empathy and collaborate in good faith.
