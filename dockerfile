FROM python:3.11-slim

ENV BASE_API_ORIGINS=* \
    BASE_API_HOST=0.0.0.0 \
    BASE_API_PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get clean  \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
    
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN uv sync --frozen --no-cache

CMD [ "/app/.venv/bin/uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000" ]