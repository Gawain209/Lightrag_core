# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
COPY pyproject.toml .
COPY lightrag_core/ ./lightrag_core/

# Install dependencies
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir sentence-transformers faiss-cpu pyyaml python-multipart

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser lightrag_core/ ./lightrag_core/
COPY --chown=appuser:appuser config.yaml .

# Create data directory for persistent storage
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

USER appuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "lightrag_core.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
