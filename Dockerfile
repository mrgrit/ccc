# ── Stage 1: UI Build ──
FROM node:22-slim AS ui-builder
WORKDIR /build
COPY apps/ccc-ui/package*.json ./
RUN npm install --silent
COPY apps/ccc-ui/ ./
RUN npm run build

# ── Stage 2: API ──
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl sshpass openssh-client libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir open-interpreter --no-deps 2>/dev/null || true

COPY apps/ apps/
COPY packages/ packages/
COPY contents/ contents/

# UI 빌드 결과 복사
COPY --from=ui-builder /build/dist/ apps/ccc-ui/dist/

ENV PYTHONPATH=/app

EXPOSE 9100

CMD ["python", "-m", "uvicorn", "apps.ccc_api.src.main:app", "--host", "0.0.0.0", "--port", "9100"]
