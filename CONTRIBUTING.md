# Contributing to BioNeuronAI

Thank you for helping us evolve BioNeuronAI! This document outlines the workflow,
quality gates, and coding conventions for contributors.

## Getting Started

1. **Fork** the repository and create a feature branch from `main`:
   ```bash
   git checkout -b feature/<concise-topic>
   ```
2. **Install dependencies** in an isolated environment:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```
3. **Run tests** before pushing:
   ```bash
   pytest --maxfail=1 --disable-warnings tests
   ```

## Code Quality Checklist

- Format Python code with **Black** and **isort**:
  ```bash
  black .
  isort .
  ```
- Type-check critical modules with **mypy**:
  ```bash
  mypy src/bioneuronai examples
  ```
- Keep functions small, documented, and typed. Follow the public API surface in
  `src/bioneuronai/__init__.py` when adding new modules.
- Update or add tests alongside code changes. Prefer deterministic seeds when
  dealing with randomness.

## Commit & PR Guidelines

- Write descriptive commit messages using the imperative mood, e.g.
  `Add curiosity-aware tool gating example`.
- Squash trivial fixups before opening a PR.
- Every PR **must** include:
  - A summary of the change and its motivation.
  - A checklist confirming that tests pass and documentation was updated.
  - Links to related issues when applicable.
- New features should document usage via README updates or example scripts.

## Release Workflow

Automated PyPI publishing is handled by GitHub Actions. Maintainers can create a
GitHub release with semantic version tags (e.g. `v0.2.0`). The CI workflow will
run tests, build wheels, and publish to PyPI using the `PYPI_API_TOKEN` secret.

Questions? Start a discussion or file an issue with the appropriate template in
`.github/ISSUE_TEMPLATE/`.
