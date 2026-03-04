# Use a Python 3.13 image
FROM python:3.13-slim AS builder

# Install build dependencies (for cvxpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    & rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy everything
COPY . .

# Install dependencies and the project into a virtual environment
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install the project
RUN uv pip install .

# Final stage
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy the virtual environment and application code from the builder
COPY --from=builder /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Command to run the application
ENTRYPOINT ["python", "-m", "cold_pickup_mpc.app"]