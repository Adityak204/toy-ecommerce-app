FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy service source
COPY services/auth-service/app ./app

# Copy public & private keys
# COPY ./keys/public_key.pem ./keys/public_key.pem
# COPY ./keys/private_key.pem ./keys/private_key.pem

EXPOSE 8003

ENV PYTHONUNBUFFERED=1

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]