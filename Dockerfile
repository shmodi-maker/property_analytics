# ============================================================
# Stage 1: Builder
# ============================================================

FROM python:3.13-slim AS builder

WORKDIR /build

COPY requirements.txt .

RUN pip install --no-cache-dir \
    --prefix=/install \
    -r requirements.txt


# ============================================================
# Stage 2: Runtime
# ============================================================

FROM python:3.13-slim AS runtime

LABEL maintainer="ZipAI"
LABEL description="Property Analytics API"

WORKDIR /app

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd \
        --uid 1000 \
        --gid appuser \
        --shell /bin/bash \
        --create-home \
        appuser

# Copy application
COPY . .

# Give application ownership to appuser
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8002

# Docker health check
HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=10s \
    --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:8002/health')" \
    || exit 1

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]