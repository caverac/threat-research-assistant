FROM python:3.12-slim

# faiss-cpu needs libgomp for OpenMP
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock ./
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/ingestion/pyproject.toml packages/ingestion/pyproject.toml
COPY packages/embeddings/pyproject.toml packages/embeddings/pyproject.toml
COPY packages/retrieval/pyproject.toml packages/retrieval/pyproject.toml
COPY packages/recommender/pyproject.toml packages/recommender/pyproject.toml
COPY packages/assistant/pyproject.toml packages/assistant/pyproject.toml
COPY packages/api/pyproject.toml packages/api/pyproject.toml

# Stub packages so uv can resolve workspace members
RUN for pkg in core ingestion embeddings retrieval recommender assistant api; do \
        mkdir -p "packages/${pkg}/src/${pkg}" && \
        touch "packages/${pkg}/src/${pkg}/__init__.py"; \
    done

RUN uv sync --frozen --no-dev --no-install-workspace

# Copy actual source code
COPY packages/core/src packages/core/src
COPY packages/ingestion/src packages/ingestion/src
COPY packages/embeddings/src packages/embeddings/src
COPY packages/retrieval/src packages/retrieval/src
COPY packages/recommender/src packages/recommender/src
COPY packages/assistant/src packages/assistant/src
COPY packages/api/src packages/api/src

RUN uv sync --frozen --no-dev

EXPOSE 8000

ENTRYPOINT ["uv", "run", "uvicorn", "api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
