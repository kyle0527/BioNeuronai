#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: ./scripts/release.sh [--repository testpypi|pypi]

Builds the distribution, publishes it to the selected PyPI repository, and
pushes the git tag that matches the project version. Requires TWINE_USERNAME
and TWINE_PASSWORD (or TWINE_API_KEY) to be configured for authentication.
USAGE
}

REPO="pypi"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repository)
      REPO="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v python &>/dev/null; then
  echo "python command is required" >&2
  exit 1
fi

if ! command -v twine &>/dev/null; then
  echo "twine is required (pip install twine)" >&2
  exit 1
fi

if ! python -c "import build" &>/dev/null; then
  echo "python -m build is required (pip install build)" >&2
  exit 1
fi

VERSION=$(python -c 'import tomllib, pathlib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])')
TAG="v${VERSION}"

echo "Running test suite before release..."
pytest tests -q

echo "Cleaning previous build artifacts..."
rm -rf dist build *.egg-info

set -x
python -m build
python -m twine upload --repository "${REPO}" dist/*
set +x

if git rev-parse "${TAG}" >/dev/null 2>&1; then
  echo "Git tag ${TAG} already exists, skipping tag push." >&2
else
  git tag "${TAG}"
  git push origin "${TAG}"
fi

echo "Release ${VERSION} uploaded to ${REPO}."
