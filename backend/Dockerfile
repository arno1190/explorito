FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Dependencies come from pyproject.toml + uv.lock (single source of truth).
# Dev image keeps the dev group (pytest, etc.) — unlike prod's --no-dev.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Default command (overridden by docker-compose, which re-syncs on start).
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
