# ============================================================
# BioNeuronAI — Multi-stage Dockerfile
# Stage 1: builder  (compile ta-lib C library + Python deps)
# Stage 2: runtime  (lean production image)
# ============================================================

# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder

# System dependencies for ta-lib and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        wget \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Build ta-lib C library from source
# NOTE: ta-lib 0.4.0 has a Makefile race condition in gen_code when using
# parallel jobs (-j>1), so we build with -j1 (sequential) to avoid it.
RUN wget -q https://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr/local \
    && make -j1 \
    && make install \
    && cd .. \
    && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Install Python dependencies into an isolated prefix
WORKDIR /install
COPY pyproject.toml ./

RUN pip install --upgrade pip --no-cache-dir \
    && pip install --prefix=/install/pkg --no-cache-dir \
        pydantic>=2.0.0 \
        numpy>=1.24.0 \
        pandas>=2.0.0 \
        "torch>=2.0.0" \
        "sentence-transformers>=2.0.0" \
        "websocket-client>=1.7.0" \
        "requests>=2.31.0" \
        "python-dotenv>=1.0.0" \
        "aiohttp>=3.9.0" \
        "regex>=2023.0.0" \
        "faiss-cpu>=1.7.0" \
        "scikit-learn>=1.3.0" \
        "fastapi>=0.111.0" \
        "uvicorn[standard]>=0.30.0" \
        "schedule>=1.2.0" \
        ta-lib \
    && pip install --prefix=/install/pkg --no-cache-dir -e ".[visualization,notifications]" 2>/dev/null || true


# ---------- Stage 2: runtime ----------
FROM python:3.11-slim AS runtime

LABEL maintainer="BioNeuronAI Team" \
      version="2.1" \
      description="AI-driven cryptocurrency futures trading system"

# Runtime system libs required by ta-lib shared object
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy ta-lib shared library from builder
COPY --from=builder /usr/local/lib/libta_lib* /usr/local/lib/
COPY --from=builder /usr/local/include/ta-lib /usr/local/include/ta-lib
RUN ldconfig

# Copy installed Python packages
COPY --from=builder /install/pkg /usr/local

# ---- Application ----
WORKDIR /app

# Source code (exclude heavy artifacts via .dockerignore)
COPY src/       ./src/
COPY config/    ./config/
COPY backtest/  ./backtest/
COPY main.py    ./
COPY pyproject.toml ./

# Model weights (large but required for AI inference)
COPY model/     ./model/

# Persistent data directories
RUN mkdir -p /app/data /app/logs

# Non-root user for security
RUN useradd --no-create-home --shell /bin/false bioneuron \
    && chown -R bioneuron:bioneuron /app

USER bioneuron

# API server port
EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/src

# Default: CLI mode. Override CMD for API mode:
#   docker run <image> uvicorn bioneuronai.api.app:app --host 0.0.0.0
ENTRYPOINT ["python"]
CMD ["main.py", "status"]
