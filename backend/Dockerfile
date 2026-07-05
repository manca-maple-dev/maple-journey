FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/. .

# Non-root user for security
RUN useradd -m -u 1001 maple && chown -R maple:maple /app
USER maple

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-8000}/api/health || exit 1'

CMD sh -c 'python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2'
