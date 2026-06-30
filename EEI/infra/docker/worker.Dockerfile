FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN python -m pip install --disable-pip-version-check --no-cache-dir uv==0.11.22

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY apps ./apps
COPY config ./config
COPY data ./data
COPY infra ./infra
COPY scripts ./scripts
COPY specs ./specs

CMD [".venv/bin/python", "-m", "apps.worker.app.main", "supervise", "--worker-id", "eei-compose-worker", "--max-jobs-per-cycle", "1", "--max-outbox-per-cycle", "5", "--poll-interval-seconds", "5"]
