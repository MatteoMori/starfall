# Start from a base Python image
FROM python:3.13-slim

# Install curl (needed to fetch uv)
RUN apt-get update && apt-get install -y curl build-essential \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency definitions first (for caching)
COPY pyproject.toml uv.lock ./

# Install dependencies from lock file
RUN uv sync --frozen

# Copy your application code
COPY . .

# Run your app (example: adjust as needed)
CMD ["uv", "run", "crewai", "run"]
