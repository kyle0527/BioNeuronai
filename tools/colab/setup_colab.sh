#!/usr/bin/env bash
# BioNeuronAI — Google Colab setup (Python 3.13 via micromamba + GPU torch)
#
# Usage (from repo root, after clone):
#   bash tools/colab/setup_colab.sh
#
# Environment:
#   BIONEURONAI_ROOT   repo root (default: current directory)
#   MAMBA_ROOT_PREFIX  micromamba root (default: /content/micromamba)
#   SKIP_TORCH=1       do not reinstall torch (keep existing CUDA build)
#   SMOKE_ONLY=1       only run smoke after env exists
#
set -euo pipefail

ROOT="${BIONEURONAI_ROOT:-$(pwd)}"
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-/content/micromamba}"
ENV_NAME="${ENV_NAME:-bioneuronai}"
MAMBA_BIN="${MAMBA_ROOT_PREFIX}/bin/micromamba"

cd "$ROOT"
echo "==> BioNeuronAI Colab setup"
echo "    ROOT=$ROOT"
echo "    MAMBA_ROOT_PREFIX=$MAMBA_ROOT_PREFIX"
echo "    ENV=$ENV_NAME"

if [[ "${SMOKE_ONLY:-0}" == "1" ]]; then
  # shellcheck disable=SC1091
  eval "$("$MAMBA_BIN" shell hook -s bash)"
  micromamba activate "$ENV_NAME"
  python -c "import sys; print('python', sys.version)"
  python -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
  python main.py status || true
  exit 0
fi

# --- system packages (TA-Lib C library) ---
if command -v apt-get >/dev/null 2>&1; then
  echo "==> apt packages for TA-Lib build"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq build-essential wget curl bzip2 ca-certificates git \
    >/dev/null
  if [[ ! -f /usr/local/lib/libta_lib.so ]] && [[ ! -f /usr/lib/libta_lib.so ]]; then
    echo "==> building TA-Lib 0.4.0 C library"
    TMP_TA="$(mktemp -d)"
    (
      cd "$TMP_TA"
      wget -q https://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
      tar -xzf ta-lib-0.4.0-src.tar.gz
      cd ta-lib
      ./configure --prefix=/usr/local
      make -j1
      make install
      ldconfig || true
    )
    rm -rf "$TMP_TA"
  else
    echo "==> TA-Lib C library already present"
  fi
fi

# --- micromamba ---
# Official layout: extract `bin/micromamba` into MAMBA_ROOT_PREFIX
if [[ ! -x "$MAMBA_BIN" ]]; then
  echo "==> installing micromamba into $MAMBA_ROOT_PREFIX"
  mkdir -p "$MAMBA_ROOT_PREFIX"
  curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xvj -C "$MAMBA_ROOT_PREFIX" bin/micromamba
  MAMBA_BIN="$MAMBA_ROOT_PREFIX/bin/micromamba"
  chmod +x "$MAMBA_BIN"
fi
if [[ ! -x "$MAMBA_BIN" ]]; then
  echo "ERROR: micromamba binary not found at $MAMBA_BIN"
  exit 1
fi

# shellcheck disable=SC1091
eval "$("$MAMBA_BIN" shell hook -s bash)"
export PATH="$(dirname "$MAMBA_BIN"):${PATH:-}"
alias micromamba="$MAMBA_BIN" 2>/dev/null || true
micromamba() { "$MAMBA_BIN" "$@"; }
export -f micromamba 2>/dev/null || true

if ! micromamba env list | grep -qE "[[:space:]]${ENV_NAME}[[:space:]]"; then
  echo "==> creating env ${ENV_NAME} with Python 3.13"
  micromamba create -y -n "$ENV_NAME" python=3.13 pip
else
  echo "==> env ${ENV_NAME} already exists"
fi

micromamba activate "$ENV_NAME"
python -c "import sys; assert sys.version_info[:2]==(3,13), sys.version; print('python', sys.version)"

# --- pip: project without torch pins from pyproject ---
echo "==> pip install project (no-deps) then runtime deps"
python -m pip install -U pip setuptools wheel hatchling
python -m pip install -e "$ROOT" --no-deps

# Core deps from pyproject, excluding torch stack (install CUDA torch separately)
python -m pip install \
  "pydantic==2.13.4" \
  "numpy>=2.0" \
  "pandas>=2.2" \
  "websocket-client==1.9.0" \
  "requests>=2.32" \
  "python-dotenv==1.2.2" \
  "aiohttp>=3.10" \
  "regex>=2024.0" \
  "faiss-cpu>=1.8" \
  "fastapi>=0.115" \
  "uvicorn[standard]>=0.30" \
  "schedule==1.2.2" \
  "scikit-learn>=1.5" \
  "sentence-transformers>=3.0" \
  "google-cloud-storage>=2.18" \
  "google-cloud-secret-manager>=2.20" \
  "typing_extensions>=4.12"

# TA-Lib Python binding (after C lib)
python -m pip install "TA-Lib==0.6.8" || python -m pip install TA-Lib || {
  echo "WARNING: TA-Lib pip install failed; technical indicators may break"
}

# --- GPU torch (do not use +cpu pins from pyproject) ---
if [[ "${SKIP_TORCH:-0}" != "1" ]]; then
  echo "==> installing CUDA torch (cu128 wheels; matches recent Colab)"
  python -m pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
  python -m pip install torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu128 \
    || python -m pip install torch torchvision torchaudio
fi

python -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"
python -c "import bioneuronai; print('bioneuronai import OK')"

export PYTHONPATH="${ROOT}/src:${ROOT}${PYTHONPATH:+:$PYTHONPATH}"
echo "==> smoke: main.py status"
python "$ROOT/main.py" status || {
  echo "WARNING: main.py status returned non-zero (see log above)"
}

echo ""
echo "==> setup done"
echo "    Activate later:"
echo "      eval \"\$($MAMBA_BIN shell hook -s bash)\""
echo "      micromamba activate $ENV_NAME"
echo "      cd $ROOT"
echo "      export PYTHONPATH=$ROOT/src:$ROOT"
