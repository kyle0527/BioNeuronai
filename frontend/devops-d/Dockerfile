# ============================================================
# BioNeuronAI DevOps Dashboard — Dockerfile
# Multi-stage: builder (npm build) → runtime (nginx serve)
# ============================================================

# ---------- Stage 1: builder ----------
FROM node:20-alpine AS builder

WORKDIR /app

# Accept API base URL at build time (default: same host port 8000)
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Install dependencies (cache layer)
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source and build
COPY . .
RUN npm run build

# ---------- Stage 2: runtime ----------
FROM nginx:1.27-alpine AS runtime

LABEL maintainer="BioNeuronAI Team" \
      description="BioNeuronAI DevOps Dashboard"

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
