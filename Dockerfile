# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY pyproject.toml constraints.txt ./
COPY app/ app/
COPY src/ src/
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --constraint constraints.txt .

FROM python:3.11-slim-bookworm AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:/app/src" \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    MODEL_PATH=/app/models/model.pkl USE_ONNX=false
RUN groupadd --gid 10001 triagem \
    && useradd --uid 10001 --gid triagem --create-home triagem
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=triagem:triagem app/ app/
COPY --chown=triagem:triagem src/ src/
RUN mkdir -p models data/raw data/processed \
    && chown -R triagem:triagem models data
USER triagem
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
