FROM python:3.13-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the lockfile and pyproject.toml to install dependencies
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: use the exact versions from uv.lock
# --no-install-project: install only dependencies, not the project itself (better caching)
# --no-dev: do not install development dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the project
COPY . .

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uv", "run", "app.py"]

